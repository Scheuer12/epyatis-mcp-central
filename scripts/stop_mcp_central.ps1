$ErrorActionPreference = 'SilentlyContinue'

Write-Host "Stopping Epyatis MCP Central supervisor and server processes..."

# Stop supervisor PowerShell processes running start_mcp_central.ps1
Get-CimInstance Win32_Process | Where-Object { 
    $_.CommandLine -like "*start_mcp_central.ps1*"
} | ForEach-Object { 
    Stop-Process -Id $_.ProcessId -Force
    Write-Host "Stopped supervisor process PID $($_.ProcessId)"
}

# Stop uvicorn/python process running central.main
Get-CimInstance Win32_Process | Where-Object { 
    $_.CommandLine -like "*central.main*"
} | ForEach-Object { 
    Stop-Process -Id $_.ProcessId -Force
    Write-Host "Stopped Central server process PID $($_.ProcessId)"
}

# Free port 8000 if still bound
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($connections) {
    foreach ($conn in $connections) {
        Stop-Process -Id $conn.OwningProcess -Force
        Write-Host "Terminated process on port 8000 (PID $($conn.OwningProcess))"
    }
}

Write-Host "Epyatis MCP Central stopped."
