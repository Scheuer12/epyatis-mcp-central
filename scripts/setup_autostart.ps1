# setup_autostart.ps1
$ErrorActionPreference = 'Stop'

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$baseDir = Split-Path -Parent $scriptDir
$vbsPath = Join-Path $scriptDir 'start_central_silent.vbs'

$wsh = New-Object -ComObject WScript.Shell
$startupFolder = [System.Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder 'EpyatisMCPCentral.lnk'
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = 'wscript.exe'
$shortcut.Arguments = "`"$vbsPath`""
$shortcut.WorkingDirectory = $baseDir
$shortcut.Description = 'Starts Epyatis MCP Central Supervisor silently on login'
$shortcut.Save()

Write-Host "Created startup shortcut at: $shortcutPath"

try {
    $action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument "`"$vbsPath`"" -WorkingDirectory $baseDir
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 365)
    Register-ScheduledTask -TaskName 'EpyatisMCPCentral' -Action $action -Trigger $trigger -Settings $settings -Force
    Write-Host "Successfully registered ScheduledTask EpyatisMCPCentral"
} catch {
    Write-Host "Scheduled task registration note: $($_.Exception.Message)"
}
