# Saves your ElevenLabs API key into key.txt (ignored by git) so the voice scripts can use it.
Set-Location $PSScriptRoot
$k = Read-Host "Paste your ElevenLabs API key here (right-click to paste) and press Enter"
$k = $k.Trim().Trim('"').Trim("'")
if ($k -notmatch '^sk_[0-9a-fA-F]{20,}$') {
  Write-Host "That doesn't look like an ElevenLabs key (they start with sk_ followed by letters and numbers). Nothing saved. Run this again." -ForegroundColor Yellow
  exit 1
}
Set-Content -Path key.txt -Value $k -NoNewline -Encoding ascii
Write-Host "Saved to key.txt ($($k.Length) characters). You can close this tab." -ForegroundColor Green
