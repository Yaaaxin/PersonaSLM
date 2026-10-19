"""Authored synthetic metadata only; never launch inference or access a corpus."""
import copy
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

import english_sfh_execution_v1 as runner


def manifest(batch='development'):
    rows = []
    for speaker in range(runner.SIZES[batch][0]):
        for case in range(2):
            for condition, factors in {**runner.shared.CONDITIONS, 'M_STYLE': None, 'N_STYLE': None}.items():
                row = {'phase': 'MAIN' if factors else 'DIAGNOSTIC',
                       'order': len(rows), 'request_id': f'AUTHORED{len(rows)}',
                       'speaker_id': f'S{speaker}', 'case_id': f'Q{case}', 'condition': condition,
                       'factors': factors.copy() if factors else None,
                       'messages': [{'role': 'user', 'content': 'Authored.'}],
                       'prompt': 'Authored.', 'input_token_ids': [1, 2], 'input_tokens': 2,
                       'prompt_sha256': runner.th('Authored.'),
                       'input_token_ids_sha256': runner.shared.value_sha256([1, 2])}
                if factors is None:
                    row['diagnostic_factors'] = {'F': 1, 'H': 1}
                    row['style_source_scope'] = ('mismatched_selected_speaker' if condition == 'M_STYLE'
                                                  else 'pooled_development')
                    row['style_source_speaker_id'] = (f'S{(speaker + 1) % runner.SIZES[batch][0]}'
                                                       if condition == 'M_STYLE' else None)
                row['request_sha256'] = runner.shared.value_sha256(row)
                rows.append(row)
    return {'batch': batch, 'requests': rows}


@pytest.mark.parametrize('batch', ['development', 'validation'])
def test_complete_balanced_allocation(batch):
    assert len(runner.validate_rows(manifest(batch))) == runner.SIZES[batch][0]


def test_missing_or_repeated_cell_rejected():
    value = manifest()
    value['requests'].pop()
    with pytest.raises(ValueError, match='allocation'):
        runner.validate_rows(value)
    value = manifest()
    value['requests'][1]['condition'] = 'C0'
    value['requests'][1]['factors'] = runner.shared.CONDITIONS['C0']
    with pytest.raises(ValueError, match='Duplicate factorial'):
        runner.validate_rows(value)


def test_request_tampering_and_overlong_prompt_rejected():
    value = manifest()
    value['requests'][0]['messages'][0]['content'] = 'Changed.'
    with pytest.raises(ValueError, match='request hash'):
        runner.validate_rows(value)
    value = manifest()
    value['requests'][0]['input_token_ids'] = [1] * 1921
    value['requests'][0]['input_tokens'] = 1921
    with pytest.raises(ValueError, match='context accounting'):
        runner.validate_rows(value)


def test_does_not_turn_controls_into_unaccounted_calls():
    value = manifest()
    value['requests'][0]['phase'] = 'CONTROL'
    with pytest.raises(ValueError, match='phase'):
        runner.validate_rows(value)


def test_diagnostics_cannot_enter_factorial_or_use_target_style():
    value = manifest()
    mismatch = next(r for r in value['requests'] if r['condition'] == 'M_STYLE')
    mismatch['factors'] = {'S': 1, 'F': 1, 'H': 1}
    with pytest.raises(ValueError, match='outside factorial'):
        runner.validate_rows(value)
    mismatch['factors'] = None
    mismatch['style_source_speaker_id'] = mismatch['speaker_id']
    mismatch['request_sha256'] = runner.shared.value_sha256({k: v for k, v in mismatch.items()
                                                            if k != 'request_sha256'})
    with pytest.raises(ValueError, match='another selected speaker'):
        runner.validate_rows(value)


def test_payload_frozen_free_generation_no_grammar_or_hidden_stop():
    row = manifest()['requests'][0]
    value = runner.payload(row)
    assert value['n_predict'] == 128 and value['prompt'] == row['input_token_ids']
    assert value['stop'] == [] and value['ignore_eos'] is False
    assert value['cache_prompt'] is False and value['temperature'] == 0.0
    assert 'grammar' not in value and value['return_tokens'] is True


def test_ram_threshold_not_rounded_down(monkeypatch):
    monkeypatch.setattr(runner.shared.s, 'memory_observation', lambda _: {
        'system': {'available_physical': runner.MIN_RAM - 1}})
    with pytest.raises(ValueError, match='RAM'):
        runner.memory(runner.MIN_RAM, 1)


def test_claim_blocks_rerun(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'PRIVATE', tmp_path)
    (tmp_path / 'development').mkdir()
    (tmp_path / 'development' / 'claim_v1.json').touch()
    with pytest.raises(ValueError, match='already claimed'):
        runner.unused('development')


def test_development_budget_anchor(monkeypatch):
    monkeypatch.setattr(runner, 'sha', lambda _: runner.BASELINE_SHA)
    monkeypatch.setattr(runner, 'load', lambda _: {
        'cumulative_generations': 688, 'cumulative_inference_seconds': runner.BASE_SECONDS})
    plan = {'batch': 'development', 'prior_receipt': {
        'path': runner.BASELINE.as_posix(), 'sha256': runner.BASELINE_SHA}}
    assert runner.baseline(plan) == (688, runner.BASE_SECONDS)
    changed = copy.deepcopy(plan)
    changed['prior_receipt']['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='baseline binding'):
        runner.baseline(changed)


def test_partial_run_accounts_failed_attempt_and_never_retries(monkeypatch, tmp_path):
    rows = manifest()['requests'][:2]
    plan = {'batch': 'development', 'requests': rows, 'source_hashes': {}, 'input_hashes': {},
            'allocation': {'maximum_inference_seconds': 100, 'maximum_wall_seconds': 200}}
    fresh = {'status': 'PASS', 'batch': 'development', 'manifest_sha256': 'frozen',
             'identity': {}, 'baseline': {'generations': 688, 'inference_seconds': runner.BASE_SECONDS}}
    records, writes, routes = [], {}, []

    class Journal:
        def __init__(self, *args):
            self.directory = tmp_path
            self.previous_hash = 'terminal'

        def write(self, kind, value):
            records.append((kind, value))

        def finish(self, **value):
            self.write('run_finished', value)

    class Server:
        def __init__(self, *args):
            self.process = SimpleNamespace(pid=1)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def assert_running(self):
            pass

    class Client:
        def __init__(self, *args, **kwargs):
            self.calls = 0

        def request(self, route, payload=None):
            routes.append(route)
            if route == '/props':
                return {}
            if route == '/tokenize':
                return {'tokens': [1, 2]}
            self.calls += 1
            if self.calls == 2:
                raise TimeoutError('Authored failed call')
            return {'content': 'Authored response.', 'tokens_predicted': 3, 'stop_type': 'eos'}

    observation = {'system': {'available_physical': runner.MIN_RAM},
                   'process': {'peak_working_set': 123}}
    monkeypatch.setattr(runner, 'preflight', lambda *args: fresh)
    monkeypatch.setattr(runner, 'validate', lambda *args: (plan, 688, runner.BASE_SECONDS))
    monkeypatch.setattr(runner, 'load', lambda *args: fresh)
    monkeypatch.setattr(runner, 'local', lambda path, parent=None: path)
    monkeypatch.setattr(runner, 'write', lambda path, value: writes.update({str(path): value}))
    monkeypatch.setattr(runner, 'sha', lambda *args: 'sha')
    monkeypatch.setattr(runner, 'memory', lambda *args: observation)
    monkeypatch.setattr(runner.shared.s, 'memory_observation', lambda *args: observation)
    monkeypatch.setattr(runner.shared.b, 'writer_lock', lambda *args: nullcontext())
    monkeypatch.setattr(runner.shared.b, 'RunJournal', Journal)
    monkeypatch.setattr(runner.shared.s, 'Server', Server)
    monkeypatch.setattr(runner.shared.b, 'LlamaClient', Client)
    monkeypatch.setattr(runner.shared.b, 'validate_server_properties', lambda *args: {})
    monkeypatch.setattr(runner.shared.b, 'validate_completion', lambda *args: None)
    result = runner.run('manifest', 'frozen', 'preflight')
    assert result['status'] == 'PARTIAL'
    assert result['attempts'] == 2 and result['responses'] == 1
    assert result['cumulative_generations'] == 690 and result['failed_seconds'] > 0
    assert result['cumulative_inference_seconds'] == runner.BASE_SECONDS + result['completion_inference_seconds']
    assert routes.count('/completion') == 2 and result['retries'] == 0
    assert sum(kind == 'english_sfh_raw' for kind, _ in records) == 1
    assert records[-1][0] == 'run_finished' and result['peak_observed_process_lifetime_working_set'] == 123


def test_snapshots_small_inputs_but_preserves_archive_hash_only(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / 'source.py'
    metadata = tmp_path / 'qualified.json'
    archive = tmp_path / 'dataset.zip'
    source.write_text('# Authored fixture\n', encoding='utf-8')
    metadata.write_text('{"authored":true}', encoding='utf-8')
    archive.write_bytes(b'Authored archive stand-in, not participant data')
    plan = {'source_hashes': {'source.py': runner.sha(source)},
            'input_hashes': {'qualified.json': runner.sha(metadata), 'dataset.zip': runner.sha(archive)}}
    events = []
    journal = SimpleNamespace(directory=tmp_path / 'run', write=lambda kind, value: events.append((kind, value)))
    runner.snapshot_inputs(journal, plan)
    assert (journal.directory / 'source_snapshot/source.py').read_bytes() == source.read_bytes()
    assert (journal.directory / 'input_snapshot/qualified.json').read_bytes() == metadata.read_bytes()
    assert not (journal.directory / 'input_snapshot/dataset.zip').exists()
    assert events[0][0] == 'hash_only_input' and events[0][1]['sha256'] == runner.sha(archive)
