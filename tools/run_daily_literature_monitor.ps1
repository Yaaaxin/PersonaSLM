param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$collector = Join-Path $repoRoot "tools\literature_monitor.py"
$config = Join-Path $repoRoot "docs\validation\literature_monitor_v1\config_v1.json"
$ledger = Join-Path $repoRoot "docs\validation\literature_monitor_v1\reviewed_ledger_v1.json"

foreach ($required in @($python, $collector, $config, $ledger)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required literature-monitor dependency is missing: $required"
    }
}

Push-Location -LiteralPath $repoRoot
try {
    & $python -B $collector validate --config $config --ledger $ledger
    if ($LASTEXITCODE -ne 0) {
        throw "Literature-monitor validation failed with exit code $LASTEXITCODE"
    }

    if ($ValidateOnly) {
        return
    }

    $outputDirectory = Join-Path $repoRoot ".local\literature-monitor"
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $output = Join-Path $outputDirectory "daily_snapshot_$stamp.json"
    & $python -B $collector collect --config $config --ledger $ledger --output $output
    if ($LASTEXITCODE -ne 0) {
        throw "Literature-monitor collection failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
