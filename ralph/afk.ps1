param(
  [int]$Iterations = 5
)

$logDir = "ralph/logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

for ($i = 1; $i -le $Iterations; $i++) {
  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $iterationLabel = "{0:D3}" -f $i
  $logPath = Join-Path $logDir "$timestamp-iteration-$iterationLabel.log"

  Write-Host "Starting Ralph iteration $i..."
  Write-Host "Logging to $logPath"

  $output = powershell -ExecutionPolicy Bypass -File "ralph/once.ps1"
  $output | Set-Content -Path $logPath
  Write-Host $output

  if ($output -match "NO MORE TASKS") {
    Write-Host "Ralph complete after $i iterations."
    exit 0
  }
}

Write-Host "Ralph stopped after $Iterations iterations."
