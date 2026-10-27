$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $scriptDir "stop_mcp_central.ps1")

Start-Sleep -Seconds 2

$startScript = Join-Path $scriptDir "start_mcp_central.ps1"
Start-Process -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", $startScript) `
    -WindowStyle Hidden

Write-Host "Epyatis MCP Central supervisor started."
