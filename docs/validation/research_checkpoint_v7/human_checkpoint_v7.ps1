param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{64}$')]
    [string]$ExpectedManifestSha256,
    [Parameter(Mandatory = $true)]
    [long]$ExpectedManifestBytes,
    [switch]$StageAndCommit
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$verifier = Join-Path $PSScriptRoot 'verify_checkpoint_v7.ps1'
$verify = @{ ExpectedManifestSha256 = $ExpectedManifestSha256; ExpectedManifestBytes = $ExpectedManifestBytes }
& $verifier @verify
if (-not $StageAndCommit) { return }

# HUMAN-ONLY mode. The research agent tests only the read-only default on this repo.
if ((Read-Host 'Type STAGE v7 to stage ONLY the reviewed allowlist') -cne 'STAGE v7') { throw 'Cancelled; no staging performed' }
& $verifier @verify
$paths = @(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'public_git_allowlist_v7.txt') -Encoding UTF8)
foreach ($path in $paths) {
    & git --literal-pathspecs -C $repo add -- $path
    if ($LASTEXITCODE -ne 0) { throw ('Staging failed; preserve partial index and review manually: ' + $path) }
}
& $verifier @verify -Staged
# Preserve the hash-bound literature note's existing final blank line. Check
# trailing spaces, space-before-tab and conflict markers without rewriting it.
& git --no-optional-locks -c 'core.whitespace=blank-at-eol,space-before-tab,-blank-at-eof' -C $repo diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Staged whitespace/conflict check failed; do not modify frozen evidence just to pass it' }
& git --no-optional-locks -C $repo diff --cached --stat
if ($LASTEXITCODE -ne 0) { throw 'Cannot show staged summary' }
& git --no-optional-locks -C $repo diff --cached --name-only --no-renames
if ($LASTEXITCODE -ne 0) { throw 'Cannot show staged paths' }
if ((Read-Host 'Review the exact scope; type COMMIT v7 to create the local commit (no push)') -cne 'COMMIT v7') { throw 'Cancelled; staged work is preserved for manual review' }
& $verifier @verify -Staged
& git -C $repo commit -m 'research: checkpoint English persona evidence and novelty synthesis'
if ($LASTEXITCODE -ne 0) { throw 'Commit did not succeed; inspect Git output without resetting scientific work' }
& git --no-optional-locks -C $repo log -1 --oneline
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect resulting commit' }
# This checkpoint is anchored to the pre-commit HEAD. Do not rerun it after commit
# and mistake the expected HEAD change for corruption. No push/config/history edit.
