# setup_autostart.ps1
$ErrorActionPreference = 'Stop'

$wsh = New-Object -ComObject WScript.Shell
$startupFolder = [System.Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder 'EpyatisMCPCentral.lnk'
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = 'wscript.exe'
$shortcut.Arguments = '"C:\Users\Scheuer\Documents\antigravity\adventurous-nobel\scripts\start_central_silent.vbs"'
$shortcut.WorkingDirectory = 'C:\Users\Scheuer\Documents\antigravity\adventurous-nobel'
$shortcut.Description = 'Starts Epyatis MCP Central Supervisor silently on login'
$shortcut.Save()

Write-Host "Created startup shortcut at: $shortcutPath"

try {
    $action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument '"C:\Users\Scheuer\Documents\antigravity\adventurous-nobel\scripts\start_central_silent.vbs"' -WorkingDirectory 'C:\Users\Scheuer\Documents\antigravity\adventurous-nobel'
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 365)
    Register-ScheduledTask -TaskName 'EpyatisMCPCentral' -Action $action -Trigger $trigger -Settings $settings -Force
    Write-Host "Successfully registered ScheduledTask EpyatisMCPCentral"
} catch {
    Write-Host "Scheduled task registration note: $($_.Exception.Message)"
}
