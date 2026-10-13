$ErrorActionPreference = 'Stop'
$statePath = Join-Path $PSScriptRoot '.local-runtime/processes.json'
if (!(Test-Path -LiteralPath $statePath)) { Write-Output 'No recorded map processes.'; return }
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
foreach ($key in @('tunnel','server')) {
  $record = $state.$key
  if (!$record) { continue }
  $proc = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
  if (!$proc) { continue }
  if ($proc.StartTime.ToUniversalTime().Ticks -ne ([datetime]$record.started).ToUniversalTime().Ticks) { Write-Warning ('PID has been reused; leaving it alone: ' + $record.pid); continue }
  $details = Get-CimInstance Win32_Process -Filter ('ProcessId = ' + [int]$record.pid)
  if ($details.ExecutablePath -ne $record.executable) { Write-Warning ('Executable mismatch; leaving it alone: ' + $record.pid); continue }
  if ($key -eq 'server' -and !$details.CommandLine.Contains($record.script)) { Write-Warning 'Server command mismatch; leaving it alone.'; continue }
  Stop-Process -Id $record.pid
  Write-Output ('Stopped map ' + $key)
}
