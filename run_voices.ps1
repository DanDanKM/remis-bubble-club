# Records the character voices for Remi's Bubble Club with ElevenLabs.
# Paste your API key when asked. It is kept only for this run and is never written to disk.
param([string]$Country)
Set-Location $PSScriptRoot
if (-not $env:ELEVENLABS_API_KEY) {
  $sec = Read-Host -AsSecureString "Paste your ElevenLabs API key, then press Enter (nothing shows while you paste)"
  $env:ELEVENLABS_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}
Write-Host ""
Write-Host "Checking the line list..." -ForegroundColor Cyan
python make_voices.py --list | Select-Object -Last 1
Write-Host ""
Write-Host "Recording. This takes a few minutes; finished clips are kept if it stops." -ForegroundColor Cyan
if ($Country) { python make_voices.py --country $Country 2>&1 | Tee-Object -FilePath voices-log.txt } else { python make_voices.py 2>&1 | Tee-Object -FilePath voices-log.txt }
Write-Host ""
if (Test-Path "voices\manifest.json") {
  $n = (Get-ChildItem voices -Recurse -Filter *.mp3).Count
  Write-Host "Done: $n clips in $PSScriptRoot\voices. Tell Claude the voices folder is ready." -ForegroundColor Green
} else {
  Write-Host "No manifest was written. Copy the message above to Claude." -ForegroundColor Yellow
}
