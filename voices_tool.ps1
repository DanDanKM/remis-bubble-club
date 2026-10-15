# Runs make_voices.py, e.g.
#   powershell -ExecutionPolicy Bypass -File .\voices_tool.ps1 --find jamaican --gender male
#   powershell -ExecutionPolicy Bypass -File .\voices_tool.ps1 --adopt irie <owner id> <voice id>
#   powershell -ExecutionPolicy Bypass -File .\voices_tool.ps1            (records missing lines)
# The API key is read from key.txt in this folder (paste the key there, nothing else). key.txt is ignored by git.
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)
Set-Location $PSScriptRoot
if (-not $env:ELEVENLABS_API_KEY -and -not (Test-Path "key.txt")) {
  Write-Host "No key yet. Opening key.txt in Notepad: paste your ElevenLabs API key, save, close Notepad, then run this again." -ForegroundColor Yellow
  notepad key.txt
  exit 1
}
python make_voices.py @Rest 2>&1 | Tee-Object -FilePath voices-log.txt
