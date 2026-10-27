$ErrorActionPreference = 'Stop'

# Mutex to ensure a single supervisor instance runs at a time
$mutex = [Threading.Mutex]::new($false, 'Local\EpyatisMCPCentralSupervisor')
$ownsMutex = $false
try { $ownsMutex = $mutex.WaitOne(0) }
catch [Threading.AbandonedMutexException] { $ownsMutex = $true }
if (-not $ownsMutex) { exit 0 }

try {
    $baseDir = "C:\Users\Scheuer\Documents\antigravity\adventurous-nobel"
    if ($PSScriptRoot) {
        $candidate = Split-Path -Parent $PSScriptRoot
        if (Test-Path (Join-Path $candidate ".venv\Scripts\python.exe")) {
            $baseDir = $candidate
        }
    }
    $python = Join-Path $baseDir ".venv\Scripts\python.exe"
    $logDir = Join-Path $baseDir "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    $serverProcess = $null
    $consecutiveFailures = 0

    while ($true) {
        try {
            # 1. If server process was never started or has terminated, restart it
            if (-not $serverProcess -or $serverProcess.HasExited) {
                # Check if port 8000 is already healthy (e.g. independently launched)
                $alreadyHealthy = $false
                try {
                    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -ErrorAction Stop
                    if ($resp.status -eq "healthy") {
                        $alreadyHealthy = $true
                    }
                } catch {
                    $alreadyHealthy = $false
                }

                if (-not $alreadyHealthy) {
                    # Free port 8000 if occupied by a stale/unresponsive process
                    $staleConns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
                    if ($staleConns) {
                        foreach ($conn in $staleConns) {
                            try {
                                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                            } catch {}
                        }
                        Start-Sleep -Seconds 1
                    }

                    # Launch MCP Central server
                    $serverProcess = Start-Process -FilePath $python `
                        -ArgumentList @("-m", "central.main") `
                        -WorkingDirectory $baseDir `
                        -WindowStyle Hidden `
                        -PassThru `
                        -RedirectStandardOutput (Join-Path $logDir "server.out.log") `
                        -RedirectStandardError (Join-Path $logDir "server.err.log")

                    Add-Content -LiteralPath (Join-Path $logDir "supervisor.log") -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Started Epyatis MCP Central (PID $($serverProcess.Id))"
                    
                    # Startup grace period for lifespan & upstream discovery
                    Start-Sleep -Seconds 10
                    $consecutiveFailures = 0
                }
            } else {
                # 2. Server process is running; verify responsiveness periodically
                try {
                    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop
                    if ($resp.status -eq "healthy") {
                        $consecutiveFailures = 0
                    } else {
                        $consecutiveFailures++
                    }
                } catch {
                    $consecutiveFailures++
                }

                # If unresponsive for 6 consecutive checks (30s) while process still exists, force recycle
                if ($consecutiveFailures -ge 6) {
                    Add-Content -LiteralPath (Join-Path $logDir "supervisor.log") -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Server unresponsive for 30s. Recycling PID $($serverProcess.Id)..."
                    try { Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue } catch {}
                    $serverProcess = $null
                    $consecutiveFailures = 0
                }
            }
        }
        catch {
            Add-Content -LiteralPath (Join-Path $logDir "supervisor.err.log") -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $($_.Exception.Message)"
        }

        Start-Sleep -Seconds 5
    }
}
finally {
    if ($ownsMutex) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
