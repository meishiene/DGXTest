param(
    [string]$Config = "configs/live_run_config.example.json",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonCommand = $venvPython
}
else {
    $pythonCommand = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $pythonCommand) {
    throw "Python executable not found. Activate the environment or install Python first."
}

$commandArgs = @("-m", "src.main", "--config", $Config)
if ($DryRun) {
    $commandArgs += "--dry-run"
}

& $pythonCommand @commandArgs
exit $LASTEXITCODE
