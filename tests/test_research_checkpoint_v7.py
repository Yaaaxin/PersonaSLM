"""PowerShell checkpoint fixtures; Git is a rejecting mock, never a real write."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1]
CONTROL = Path('docs/validation/research_checkpoint_v7')
HEAD = '8b7f8fdd8eec8358528da86398659f876c70a6dd'
PS = shutil.which('powershell')
pytestmark = pytest.mark.skipif(PS is None, reason='Windows PowerShell required')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


@pytest.fixture
def checkpoint(tmp_path):
    folder = tmp_path / CONTROL
    folder.mkdir(parents=True)
    for name in ('verify_checkpoint_v7.ps1', 'human_checkpoint_v7.ps1'):
        shutil.copyfile(SOURCE / CONTROL / name, folder / name)
    sample = tmp_path / 'docs/sample.txt'
    sample.write_bytes(b'authored fixture\n')
    paths = sorted([str(CONTROL / name).replace('\\', '/') for name in (
        'verify_checkpoint_v7.ps1', 'human_checkpoint_v7.ps1',
        'public_git_allowlist_v7.txt', 'checkpoint_manifest_v7.json')] + ['docs/sample.txt'])
    (folder / 'public_git_allowlist_v7.txt').write_bytes(('\n'.join(paths) + '\n').encode())
    manifest = {'schema_version': 'personaslm_manual_research_checkpoint_v7',
                'source_head': HEAD, 'branch': 'research/autonomous-personaslm',
                'allowlisted_file_count': len(paths), 'hash_bound_file_count': len(paths) - 1,
                'base_dependencies': [], 'files': []}
    for path in paths:
        if path.endswith('/checkpoint_manifest_v7.json'):
            continue
        data = (tmp_path / path).read_bytes()
        manifest['files'].append({'path': path, 'bytes': len(data),
                                 'sha256': digest(data), 'git_blob_oid': blob(data)})
    (folder / 'checkpoint_manifest_v7.json').write_bytes(json.dumps(manifest).encode())
    return tmp_path, paths


def run(checkpoint, scenario='', human=False):
    root, paths = checkpoint
    manifest_path = root / CONTROL / 'checkpoint_manifest_v7.json'
    data = manifest_path.read_bytes()
    frozen = json.loads(data)
    oids = {f['path']: f['git_blob_oid'] for f in frozen['files']}
    oids[str(CONTROL / 'checkpoint_manifest_v7.json').replace('\\', '/')] = blob(data)
    (root / 'mock.json').write_text(json.dumps({'paths': paths, 'oids': oids}), encoding='utf-8')
    wrapper = r"""
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mock = Get-Content -Raw (Join-Path $root 'mock.json') | ConvertFrom-Json
$scenario = 'SCENARIO'
$global:staged = @()
$global:writes = @()
$global:commits = 0
function global:Read-Host { if ($args[0] -like 'Type STAGE*') { return 'STAGE v7' }; return 'COMMIT v7' }
function global:git {
    $a = @($args); $global:LASTEXITCODE = 0
    $operation = @($a | Where-Object { $_ -cin @('rev-parse','branch','check-attr','hash-object','diff','ls-files','add','commit','log') })
    if ($operation.Count -ne 1) { throw 'Unexpected Git mock request' }
    switch ($operation[0]) {
        'rev-parse' { if ($a[-1] -eq 'HEAD') { if ($scenario -eq 'head') { return 'wrong' }; return 'HEAD_VALUE' }; return $root }
        'branch' { return 'research/autonomous-personaslm' }
        'check-attr' {
            foreach ($p in $mock.paths) { foreach ($key in 'filter','working-tree-encoding','ident') {
                if ($scenario -eq 'filter' -and $key -eq 'filter') { "$($p): $($key): unsafe" } else { "$($p): $($key): unspecified" }
            } }; return
        }
        'hash-object' { return $mock.oids.PSObject.Properties[$a[-1]].Value }
        'diff' {
            if ($a -contains '--name-only') {
                if ($scenario -eq 'not_empty') { return 'docs/unreviewed.txt' }
                if ($scenario -in @('staged','extra','missing','blob','mode')) {
                    if ($scenario -eq 'extra') { 'docs/unreviewed.txt' }
                    if ($scenario -eq 'missing') { return @($mock.paths | Select-Object -Skip 1) }
                    return $mock.paths
                }
                return $global:staged
            }; return
        }
        'ls-files' {
            foreach ($p in $mock.paths) {
                $oid=$mock.oids.PSObject.Properties[$p].Value; $mode='100644'
                if ($scenario -eq 'blob') { $oid='0000000000000000000000000000000000000000' }
                if ($scenario -eq 'mode') { $mode='120000' }
                "$mode $oid 0`t$p"
            }; return
        }
        'add' {
            if (-not HUMAN_MODE -or $a[-1] -cnotin $mock.paths -or $a -cnotcontains '--literal-pathspecs') { throw 'Unsafe mocked staging' }
            $global:writes += $a[-1]; $global:staged += $a[-1]; return
        }
        'commit' { if (-not HUMAN_MODE -or $global:staged.Count -ne $mock.paths.Count) { throw 'Unsafe mocked commit' }; $global:commits++; return }
        'log' { return 'fixture commit only' }
        default { throw 'Unrecognized command; NEVER fall through to real Git' }
    }
}
try {
    & (Join-Path $root 'SCRIPT_PATH') -ExpectedManifestSha256 'ANCHOR' -ExpectedManifestBytes BYTE_COUNT FLAGS
    if (HUMAN_MODE -and ($global:commits -ne 1 -or @(Compare-Object $global:writes $mock.paths -CaseSensitive).Count -ne 0)) { throw 'Human command scope/order failed' }
    exit 0
} catch { Write-Output $_.Exception.Message; exit 7 }
"""
    staged = scenario in {'staged', 'extra', 'missing', 'blob', 'mode'}
    script = CONTROL / ('human_checkpoint_v7.ps1' if human else 'verify_checkpoint_v7.ps1')
    replacements = {'SCENARIO': scenario, 'HEAD_VALUE': HEAD, 'HUMAN_MODE': '$true' if human else '$false',
                    'SCRIPT_PATH': script.as_posix(), 'ANCHOR': digest(data), 'BYTE_COUNT': str(len(data)),
                    'FLAGS': '-StageAndCommit' if human else '-Staged' if staged else ''}
    for key, value in replacements.items():
        wrapper = wrapper.replace(key, value)
    if scenario == 'anchor':
        wrapper = wrapper.replace(digest(data), '0' * 64)
    if scenario == 'size':
        wrapper = wrapper.replace('-ExpectedManifestBytes ' + str(len(data)), '-ExpectedManifestBytes 1')
    path = root / 'mock_verify.ps1'
    path.write_text(wrapper, encoding='utf-8')
    return subprocess.run([PS, '-NoProfile', '-NonInteractive', '-File', str(path)],
                          capture_output=True, text=True, timeout=40)


@pytest.mark.parametrize('scenario', ['', 'staged'])
def test_worktree_and_exact_virtual_index_pass(checkpoint, scenario):
    result = run(checkpoint, scenario)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status":  "PASS"' in result.stdout


@pytest.mark.parametrize('scenario, message', [
    ('anchor', 'SHA-256'), ('size', 'size'), ('head', 'HEAD'), ('filter', 'transformation'),
    ('not_empty', 'not empty'), ('extra', 'Staged paths'), ('missing', 'Staged paths'),
    ('blob', 'Staged content'), ('mode', 'ordinary stage-zero')])
def test_rejects_unsafe_or_incomplete_scope(checkpoint, scenario, message):
    result = run(checkpoint, scenario)
    assert result.returncode == 7
    assert message in result.stdout


@pytest.mark.parametrize('changed', [b'different size\n', b'Authored fixture\n'])
def test_changed_scientific_bytes_are_not_repaired(checkpoint, changed):
    (checkpoint[0] / 'docs/sample.txt').write_bytes(changed)
    result = run(checkpoint)
    assert result.returncode == 7
    assert 'v7 file' in result.stdout
    assert (checkpoint[0] / 'docs/sample.txt').read_bytes() == changed


def test_entire_human_sequence_uses_exact_allowlist_with_mocked_writes_only(checkpoint):
    # PowerShell consumes -- for functions; check the native separator in source.
    source = (SOURCE / CONTROL / 'human_checkpoint_v7.ps1').read_text(encoding='utf-8')
    assert '& git --literal-pathspecs -C $repo add -- $path' in source
    result = run(checkpoint, human=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_allowlist_extra_file_is_rejected(checkpoint):
    path = checkpoint[0] / CONTROL / 'public_git_allowlist_v7.txt'
    path.write_bytes(path.read_bytes() + b'docs/unreviewed.txt\n')
    result = run(checkpoint)
    assert result.returncode == 7
    assert 'Allowlist count' in result.stdout
