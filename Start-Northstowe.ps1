param([switch]$Share)
$ErrorActionPreference = 'Stop'
$mapRoot = $PSScriptRoot
$runtimeDir = Join-Path $mapRoot '.local-runtime'
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
$statePath = Join-Path $runtimeDir 'processes.json'
$state = @{ server = $null; tunnel = $null; shareUrl = $null }
if (Test-Path -LiteralPath $statePath) {
  $saved = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
  foreach ($key in @('server','tunnel','shareUrl')) { $state[$key] = $saved.$key }
}
function Save-State { $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding UTF8 }
function Map-Health {
  try { return (Invoke-RestMethod -Uri 'http://127.0.0.1:4173/healthz' -TimeoutSec 2).app -eq 'northstowe-responsibility-map' } catch { return $false }
}
function Same-Process($record) {
  if (!$record) { return $false }
  $proc = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
  return $proc -and $proc.StartTime.ToUniversalTime().Ticks -eq ([datetime]$record.started).ToUniversalTime().Ticks
}
if (!(Test-Path -LiteralPath (Join-Path $mapRoot 'local-dist/index.html'))) { throw 'Build the app first: pnpm run local:build' }
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$nodePath = if ($nodeCommand) { $nodeCommand.Source } else { Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' }
if (!(Test-Path -LiteralPath $nodePath)) { throw 'Node.js 22.13 or newer is required.' }
if (!(Map-Health)) {
  $serverScript = Join-Path $mapRoot 'scripts/local-server.mjs'
  $proc = Start-Process -FilePath $nodePath -ArgumentList ('"' + $serverScript + '"') -WorkingDirectory $mapRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'server.log') -RedirectStandardError (Join-Path $runtimeDir 'server-error.log')
  $state.server = @{ pid = $proc.Id; started = $proc.StartTime.ToUniversalTime().ToString('o'); executable = $nodePath; script = $serverScript }
  Save-State
  for ($attempt=0; $attempt -lt 20; $attempt++) { if (Map-Health) { break }; Start-Sleep -Milliseconds 250 }
  if (!(Map-Health)) { throw 'Local app did not start. See .local-runtime/server-error.log; port 4173 may already be in use.' }
}
Write-Output 'Local map: http://localhost:4173/'
if ($Share) {
  if ((Same-Process $state.tunnel) -and $state.shareUrl) {
    Write-Output ('Share with others: ' + $state.shareUrl)
    return
  }
  $tunnelExe = Join-Path $runtimeDir 'cloudflared.exe'
  $expectedHash = '2837888cc0f5d58f15b6dc478376de90b4d3ba5241c7947455d1e0a0df429712'
  if (!(Test-Path -LiteralPath $tunnelExe)) {
    Write-Output 'Downloading Cloudflare Tunnel 2026.9.1 from the official release...'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/cloudflare/cloudflared/releases/download/2026.9.1/cloudflared-windows-amd64.exe' -OutFile $tunnelExe
  }
  if ((Get-FileHash -LiteralPath $tunnelExe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) { throw 'Cloudflare executable does not match the published release checksum.' }
  $tunnelLog = Join-Path $runtimeDir 'tunnel.log'
  $proc = Start-Process -FilePath $tunnelExe -ArgumentList @('tunnel','--no-autoupdate','--url','http://127.0.0.1:4173','--protocol','http2') -WorkingDirectory $runtimeDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'tunnel-output.log') -RedirectStandardError $tunnelLog
  $state.tunnel = @{ pid = $proc.Id; started = $proc.StartTime.ToUniversalTime().ToString('o'); executable = $tunnelExe }
  $state.shareUrl = $null
  Save-State
  for ($attempt=0; $attempt -lt 100; $attempt++) {
    if (Test-Path -LiteralPath $tunnelLog) {
      $logText = Get-Content -LiteralPath $tunnelLog -Raw
      if ($logText -match 'https://[a-z0-9-]+\.trycloudflare\.com') { $state.shareUrl = $Matches[0]; break }
    }
    if ($proc.HasExited) { throw ('Sharing stopped; see ' + $tunnelLog) }
    Start-Sleep -Milliseconds 300
  }
  Save-State
  if (!$state.shareUrl) { throw ('No sharing URL received; see ' + $tunnelLog) }
  $state.shareUrl | Set-Content -LiteralPath (Join-Path $runtimeDir 'share-url.txt') -Encoding UTF8
  Write-Output ('Share with others: ' + $state.shareUrl)
  Write-Output 'Keep this computer awake and connected. The link changes after sharing restarts.'
}
