param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-fA-F0-9]{64}$')]
    [string]$ExpectedManifestSha256,
    [switch]$CheckStaged
)

$ErrorActionPreference = 'Stop'
$checkpointRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
$manifestRelative = 'docs/validation/research_checkpoint_v2/checkpoint_manifest_v2.json'

function Assert-SafeRelativePath([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or $RelativePath -ne $RelativePath.Trim() -or
        [IO.Path]::IsPathRooted($RelativePath) -or $RelativePath.Contains([string][char]92) -or
        $RelativePath -match '(^|/)\.\.?(/|$)|[\x00-\x1f:*?\[\]]' -or
        $RelativePath -match '^(\.git/|\.local/|\.venv/|venv/|models/|bin/|results/|private/|data/private/|\.pytest|\.cache/)' -or
        $RelativePath -match '(?i)\.(gguf|safetensors|pem|key|p12|pfx|pyc)$') {
        throw 'Unsafe or nonliteral checkpoint path.'
    }
    foreach ($segment in $RelativePath.Split('/')) {
        if ($segment.Length -eq 0 -or $segment.EndsWith('.') -or $segment.EndsWith(' ')) {
            throw 'Windows-normalized or empty path segment rejected.'
        }
    }
    $fullPath = [IO.Path]::GetFullPath((Join-Path $checkpointRoot $RelativePath))
    if (-not $fullPath.StartsWith($checkpointRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Checkpoint path escapes repository.'
    }
    $normalizedRelative = $fullPath.Substring($checkpointRoot.Length + 1).Replace([char]92, [char]47)
    if ($normalizedRelative -cne $RelativePath) { throw 'Path is not in canonical relative form.' }
    $item = Get-Item -LiteralPath $fullPath -Force
    if ($item.PSIsContainer) { throw 'An allowlist entry must be a file, never a directory.' }
    $ancestor = $item
    while ($null -ne $ancestor -and $ancestor.FullName -ne $checkpointRoot) {
        if (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point rejected.' }
        if ($ancestor -is [IO.FileInfo]) { $ancestor = $ancestor.Directory } else { $ancestor = $ancestor.Parent }
    }
    return $fullPath
}

$manifestPath = Assert-SafeRelativePath $manifestRelative
if ((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash -ne $ExpectedManifestSha256) {
    throw 'Manifest does not match the separately supplied checkpoint hash.'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.schema_version -ne 'personaslm_manual_checkpoint_v2') { throw 'Unexpected manifest schema.' }
$allowlistPath = Assert-SafeRelativePath $manifest.allowlist.path
if ((Get-FileHash -LiteralPath $allowlistPath -Algorithm SHA256).Hash -ne $manifest.allowlist.sha256) {
    throw 'Allowlist hash mismatch.'
}
$paths = @([IO.File]::ReadAllLines($allowlistPath))
if ($paths.Count -ne $manifest.allowlist.count -or @($paths | Sort-Object -Unique).Count -ne $paths.Count) {
    throw 'Allowlist count or uniqueness mismatch.'
}
foreach ($requiredPath in @($manifestRelative, $manifest.allowlist.path,
        'docs/validation/research_checkpoint_v2/verify_checkpoint_v2.ps1')) {
    if (@($paths | Where-Object { $_ -ceq $requiredPath }).Count -ne 1) {
        throw 'Checkpoint control files must each occur exactly once.'
    }
}
foreach ($path in $paths) { $null = Assert-SafeRelativePath $path }
$boundPaths = @($manifest.files | ForEach-Object { $_.path })
$expectedPaths = @($paths | Where-Object { $_ -ne $manifestRelative })
if (@(Compare-Object $expectedPaths $boundPaths).Count -ne 0 -or $boundPaths.Count -ne $expectedPaths.Count) {
    throw 'Every allowlisted file except the externally hashed manifest must have one binding.'
}
foreach ($binding in $manifest.files) {
    $fullPath = Assert-SafeRelativePath $binding.path
    if ((Get-Item -LiteralPath $fullPath).Length -ne $binding.bytes -or
        (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash -ne $binding.sha256) {
        throw "Changed checkpoint file: $($binding.path)"
    }
}

Push-Location $checkpointRoot
try {
    $head = git rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $head -ne $manifest.repository.base_head) { throw 'Repository HEAD changed.' }
    $branch = git branch --show-current
    if ($LASTEXITCODE -ne 0 -or $branch -ne $manifest.repository.branch) { throw 'Research branch changed.' }
    $staged = @(git -c core.quotePath=false diff --cached --no-renames --name-only)
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the Git index.' }
    if ($CheckStaged) {
        if (@(Compare-Object $paths $staged).Count -ne 0) { throw 'Staged paths do not exactly match allowlist.' }
        foreach ($path in $paths) {
            $indexEntry = @(git --literal-pathspecs ls-files --stage -- $path)
            if ($LASTEXITCODE -ne 0 -or $indexEntry.Count -ne 1 -or
                $indexEntry[0] -notmatch '^100(?:644|755) [0-9a-f]+ 0\t') {
                throw 'Only regular stage-zero file blobs are permitted.'
            }
        }
        foreach ($binding in $manifest.files) {
            $stageOid = git rev-parse ":$($binding.path)"
            if ($LASTEXITCODE -ne 0) { throw 'Missing staged blob.' }
            $workingOid = git hash-object --path=$($binding.path) -- $binding.path
            if ($LASTEXITCODE -ne 0 -or $stageOid -ne $workingOid) { throw "Staged content differs: $($binding.path)" }
        }
        $stageManifestOid = git rev-parse ":$manifestRelative"
        $workingManifestOid = git hash-object --path=$manifestRelative -- $manifestRelative
        if ($LASTEXITCODE -ne 0 -or $stageManifestOid -ne $workingManifestOid) { throw 'Staged manifest differs.' }
        git diff --cached --check
    } else {
        if ($staged.Count -ne 0) { throw 'Index is not empty; preserve it and review the existing staging manually.' }
        git diff --check
    }
    if ($LASTEXITCODE -ne 0) { throw 'Git whitespace check failed.' }
} finally {
    Pop-Location
}
[PSCustomObject]@{
    status = 'PASS_HASH_BOUND_MANUAL_CHECKPOINT'
    files = $paths.Count
    staged_checked = [bool]$CheckStaged
    git_add_commit_push_executed = $false
    reproducibility = $manifest.reproducibility.status
} | ConvertTo-Json
