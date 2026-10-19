param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{64}$')]
    [string]$ExpectedManifestSha256,
    [switch]$Staged
)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$baseHead = '8b7f8fdd8eec8358528da86398659f876c70a6dd'
$manifestRelative = 'docs/validation/research_checkpoint_v3/checkpoint_manifest_v3.json'
$allowlistRelative = 'docs/validation/research_checkpoint_v3/public_git_allowlist_v3.txt'
$verifierRelative = 'docs/validation/research_checkpoint_v3/verify_checkpoint_v3.ps1'

function Get-SafeFile([string]$relative) {
    if ($relative -cnotmatch '^(docs|tools|tests)/' -or $relative.Contains('\')) {
        throw 'Only forward-slash docs/tools/tests relative paths are permitted'
    }
    $parts = $relative.Split('/')
    $current = $repo
    foreach ($part in $parts) {
        if ($part -cnotmatch '^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$') {
            throw 'Unsafe path segment'
        }
        $current = Join-Path $current $part
        $item = Get-Item -LiteralPath $current -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Reparse points are not permitted'
        }
    }
    if ($relative -ceq 'docs/research_development_log.md' -or $item.PSIsContainer) {
        throw 'Raw development log or directory is not a checkpoint file'
    }
    $canonical = [IO.Path]::GetFullPath($current)
    if (-not $canonical.StartsWith($repo + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Path escaped repository'
    }
    return $canonical
}

if (((Get-Item -LiteralPath $repo -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Repository root is a reparse point'
}
$head = (& git --no-optional-locks -C $repo rev-parse HEAD)
if ($LASTEXITCODE -ne 0 -or $head -cne $baseHead) { throw 'Unexpected HEAD; reassess checkpoint' }
$branch = (& git --no-optional-locks -C $repo branch --show-current)
if ($LASTEXITCODE -ne 0 -or $branch -cne 'research/autonomous-personaslm') { throw 'Unexpected branch' }
$manifestPath = Get-SafeFile $manifestRelative
if ((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash -ine $ExpectedManifestSha256) {
    throw 'Manifest hash differs from independently supplied anchor'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.base_head -cne $baseHead -or $manifest.schema_version -cne 'personaslm_incremental_checkpoint_v3') {
    throw 'Manifest identity mismatch'
}
$allowed = @(Get-Content -LiteralPath (Get-SafeFile $allowlistRelative) -Encoding UTF8)
if ($allowed.Count -ne $manifest.allowlisted_file_count -or @($allowed | Select-Object -Unique).Count -ne $allowed.Count) {
    throw 'Allowlist count or uniqueness mismatch'
}
foreach ($required in @($manifestRelative, $allowlistRelative, $verifierRelative)) {
    if (@($allowed | Where-Object { $_ -ceq $required }).Count -ne 1) { throw 'Missing required checkpoint file' }
}
$bound = @($manifest.files | ForEach-Object { $_.path })
$expectedBound = @($allowed | Where-Object { $_ -cne $manifestRelative })
if (@($bound | Select-Object -Unique).Count -ne $bound.Count -or
    @(Compare-Object -ReferenceObject $expectedBound -DifferenceObject $bound -CaseSensitive).Count -ne 0) {
    throw 'Manifest must bind every allowlisted file except itself exactly once'
}
foreach ($file in $manifest.files) {
    $path = Get-SafeFile $file.path
    if ($file.sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ine $file.sha256 -or
        (Get-Item -LiteralPath $path).Length -ne $file.bytes) {
        throw ('File hash/size mismatch: ' + $file.path)
    }
}
$stagedPaths = @(& git --no-optional-locks -C $repo diff --cached --name-only --no-renames)
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect index' }
if (-not $Staged) {
    if ($stagedPaths.Count -ne 0) { throw 'Index must be empty before manual staging' }
} else {
    if (@(Compare-Object -ReferenceObject $allowed -DifferenceObject $stagedPaths -CaseSensitive).Count -ne 0) {
        throw 'Staged paths differ from exact allowlist'
    }
    foreach ($relative in $allowed) {
        $null = Get-SafeFile $relative
        $indexEntry = @(& git --no-optional-locks -C $repo ls-files --stage -- $relative)
        if ($LASTEXITCODE -ne 0 -or $indexEntry.Count -ne 1 -or
            $indexEntry[0] -cnotmatch '^100644 [0-9a-f]{40} 0\t') {
            throw ('Index entry is not one ordinary stage-zero file: ' + $relative)
        }
        $expectedBlob = (& git --no-optional-locks -C $repo hash-object ('--path=' + $relative) -- $relative)
        if ($LASTEXITCODE -ne 0) { throw 'Cannot hash prospective Git blob' }
        $actualBlob = (& git --no-optional-locks -C $repo rev-parse --verify (':' + $relative))
        if ($LASTEXITCODE -ne 0 -or $actualBlob -cne $expectedBlob) { throw ('Index content differs: ' + $relative) }
    }
}
[pscustomobject]@{
    status = 'PASS'; base_head = $baseHead; files = $allowed.Count
    staged_checked = [bool]$Staged; git_mutation = $false
    manifest_sha256 = $ExpectedManifestSha256.ToLowerInvariant()
} | ConvertTo-Json
