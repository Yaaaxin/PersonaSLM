param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{64}$')]
    [string]$ExpectedManifestSha256,
    [Parameter(Mandatory = $true)]
    [long]$ExpectedManifestBytes,
    [switch]$Staged
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$baseHead = '8b7f8fdd8eec8358528da86398659f876c70a6dd'
$branchName = 'research/autonomous-personaslm'
$manifestRelative = 'docs/validation/research_checkpoint_v7/checkpoint_manifest_v7.json'
$allowlistRelative = 'docs/validation/research_checkpoint_v7/public_git_allowlist_v7.txt'
$verifierRelative = 'docs/validation/research_checkpoint_v7/verify_checkpoint_v7.ps1'
$humanRelative = 'docs/validation/research_checkpoint_v7/human_checkpoint_v7.ps1'

# Reuse the v3-v5 path/hash/index checks; never reapply old scientific snapshots.
function Get-SafeFile([string]$relative) {
    if ($relative -cnotmatch '^(docs|tools|tests)/' -or $relative.Contains('\')) {
        throw 'Only forward-slash docs/tools/tests relative paths are permitted'
    }
    $current = $repo
    foreach ($part in $relative.Split('/')) {
        if ($part -cnotmatch '^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$') { throw 'Unsafe path segment' }
        $current = Join-Path $current $part
        $item = Get-Item -LiteralPath $current -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point is not permitted' }
    }
    if ($relative -ceq 'docs/research_development_log.md' -or $item.PSIsContainer) {
        throw 'Private development log or directory is not a checkpoint file'
    }
    if (-not ([IO.Path]::GetFullPath($current)).StartsWith($repo + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Path escaped repository'
    }
    return $current
}

function Read-Git([string[]]$Arguments) {
    if ($Arguments[0] -cnotin @('rev-parse', 'branch', 'diff', 'ls-files', 'hash-object', 'check-attr')) { throw 'Read-only Git command required' }
    $result = @(& git --no-optional-locks --literal-pathspecs -C $repo @Arguments)
    if ($LASTEXITCODE -ne 0) { throw ('Git inspection failed: ' + ($Arguments -join ' ')) }
    return $result
}

foreach ($name in @('GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE')) {
    if ([Environment]::GetEnvironmentVariable($name)) { throw ('Unset repository redirection before verification: ' + $name) }
}
if (((Get-Item -LiteralPath $repo -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Repository root is a reparse point' }
if ((Read-Git @('rev-parse', 'HEAD')) -cne $baseHead) { throw 'Unexpected HEAD; refresh checkpoint rather than restoring work' }
if ((Read-Git @('branch', '--show-current')) -cne $branchName) { throw 'Unexpected branch' }
$top = Read-Git @('rev-parse', '--show-toplevel')
if ([IO.Path]::GetFullPath($top) -ine $repo) { throw 'Unexpected repository root' }
$manifestPath = Get-SafeFile $manifestRelative
if ($ExpectedManifestBytes -le 0 -or (Get-Item -LiteralPath $manifestPath).Length -ne $ExpectedManifestBytes) { throw 'v7 manifest size differs from independent anchor' }
if ((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash -ine $ExpectedManifestSha256) { throw 'v7 manifest SHA-256 differs from independent anchor' }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema_version -cne 'personaslm_manual_research_checkpoint_v7' -or $manifest.source_head -cne $baseHead -or $manifest.branch -cne $branchName) { throw 'v7 manifest identity mismatch' }
$allowed = @(Get-Content -LiteralPath (Get-SafeFile $allowlistRelative) -Encoding UTF8)
if ($allowed.Count -ne $manifest.allowlisted_file_count -or @($allowed | Sort-Object -Unique).Count -ne $allowed.Count) { throw 'Allowlist count or uniqueness mismatch' }
foreach ($required in @($manifestRelative, $allowlistRelative, $verifierRelative, $humanRelative)) {
    if (@($allowed | Where-Object { $_ -ceq $required }).Count -ne 1) { throw 'Missing required v7 control' }
}
$bound = @($manifest.files.path)
$expected = @($allowed | Where-Object { $_ -cne $manifestRelative })
if ($bound.Count -ne $manifest.hash_bound_file_count -or @($bound | Sort-Object -Unique).Count -ne $bound.Count -or
    @(Compare-Object $expected $bound -CaseSensitive).Count -ne 0) { throw 'Manifest/allowlist scope mismatch' }
foreach ($file in $manifest.files) {
    $path = Get-SafeFile $file.path
    if ((Get-Item -LiteralPath $path).Length -ne $file.bytes) { throw ('v7 file size mismatch: ' + $file.path) }
    if ($file.sha256 -cnotmatch '^[0-9a-f]{64}$' -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ine $file.sha256) { throw ('v7 file SHA-256 mismatch: ' + $file.path) }
    if ($file.git_blob_oid -cnotmatch '^[0-9a-f]{40}$') { throw 'Invalid frozen Git blob identity' }
}
foreach ($file in $manifest.base_dependencies) {
    $path = Join-Path $repo $file.path
    if ($file.path -cnotin @('.gitattributes', '.gitignore') -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ine $file.sha256) { throw 'Base Git policy bytes changed' }
}
# Do not run unreviewed clean filters while calculating prospective Git objects.
$attributes = @(Read-Git (@('check-attr', 'filter', 'working-tree-encoding', 'ident', '--') + $allowed))
if ($attributes.Count -ne 3 * $allowed.Count -or @($attributes | Where-Object { $_ -cnotmatch ': (filter|working-tree-encoding|ident): unspecified$' }).Count -ne 0) { throw 'Unreviewed Git content transformation' }
$prospective = @{}
foreach ($file in $manifest.files) {
    $oid = Read-Git @('hash-object', ('--path=' + $file.path), '--', $file.path)
    if ($oid -cne $file.git_blob_oid) { throw ('Prospective Git content differs: ' + $file.path) }
    $prospective[$file.path] = $oid
}
$prospective[$manifestRelative] = Read-Git @('hash-object', ('--path=' + $manifestRelative), '--', $manifestRelative)
$stagedPaths = @(Read-Git @('diff', '--cached', '--name-only', '--no-renames'))
if (-not $Staged) {
    if ($stagedPaths.Count -ne 0) { throw 'Index is not empty; preserve and review existing staged work manually' }
} else {
    if (@(Compare-Object $allowed $stagedPaths -CaseSensitive).Count -ne 0) { throw 'Staged paths differ from exact v7 allowlist' }
    $entries = @(Read-Git (@('ls-files', '--stage', '--') + $allowed))
    $seen = @{}
    foreach ($entry in $entries) {
        if ($entry -cnotmatch '^100644 ([0-9a-f]{40}) 0\t(.+)$') { throw 'Index entry is not an ordinary stage-zero file' }
        $oid, $relative = $Matches[1], $Matches[2]
        if ($seen.ContainsKey($relative) -or -not $prospective.ContainsKey($relative) -or $oid -cne $prospective[$relative]) { throw ('Staged content differs: ' + $relative) }
        $seen[$relative] = $true
    }
    if ($seen.Count -ne $allowed.Count) { throw 'Missing staged index entries' }
}
[pscustomobject]@{
    status = 'PASS'; version = 'v7'; source_head = $baseHead; branch = $branchName
    files = $allowed.Count; manifest_sha256 = $ExpectedManifestSha256.ToLowerInvariant()
    manifest_bytes = $ExpectedManifestBytes; staged_checked = [bool]$Staged
    git_mutation = $false; scientific_reproduction_claim = $false
} | ConvertTo-Json
