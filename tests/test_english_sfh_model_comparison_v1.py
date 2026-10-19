"""Authored fixtures only: no download, participant data, mappings or inference."""
import copy
from collections import Counter
import json
from pathlib import Path
import struct
from unittest.mock import patch

import pytest

import english_sfh_model_comparison_v1 as study
from test_english_sfh_registration_v1 import authored_case


def material():
    cases = [authored_case(f'AUTHORED{i}', j) for i in range(5) for j in range(2)]
    for i, case in enumerate(cases):
        case['style']['per_100_words']['contractions'] = i // 2
        case['history'].append({'speaker': 'AUTHORED_SECOND', 'text': 'A synthetic history-only colleague.',
                                'start': 3, 'end': 3.5})
    return {'cases': cases}


def test_same_semantics_distinct_interfaces_balanced_controls(monkeypatch):
    monkeypatch.setattr(study.registration.metadata, 'render_native_template',
        lambda template, messages: '<|im_start|>system\n' + messages[0]['content'] +
        '<|im_end|>\n<|im_start|>user\n' + messages[1]['content'] + '<|im_end|>\n<|im_start|>assistant\n')
    data = material(); before = copy.deepcopy(data); calls = []
    def tokenize(prompt, name):
        calls.append(name)
        return [151644, 12] if prompt.startswith('<|im_start|>') else [21, 22]
    base, pool = study.build(data, 'base', 'AUTHORED_TEMPLATE', tokenize)
    instruct, other_pool = study.build(data, 'instruct', 'AUTHORED_TEMPLATE', tokenize)
    assert data == before and pool == other_pool and len(calls) == 200
    assert Counter(r['condition'] for r in base) == Counter({k: 10 for k in study.registration.CONDITIONS})
    for left, right in zip(base, instruct):
        assert left['messages'] == right['messages'] and left['messages'][-1]['content'].endswith('\n\nParticipant:')
        assert left['prompt'] == left['messages'][0]['content'] + '\n\n' + left['messages'][1]['content']
        assert '<|im_start|>' not in left['prompt'] and right['prompt'].endswith('<|im_start|>assistant\n')
        assert left['stop'] == right['stop'] == ['\nParticipant:', '\nColleague 1:', '\nColleague 2:']
        assert left['condition'] == right['condition'] and left['request_id'] != right['request_id']
        assert left.get('style_source_speaker_id') == right.get('style_source_speaker_id')
        study.independent.verify_request(left); study.independent.verify_request(right)
    assert calls == [r['request_id'] for r in base + instruct]
    study.old.validate_rows({'batch': 'development', 'requests': base})


def test_stop_list_independent_of_history_condition_and_no_extra_call():
    rows, _ = study.build(material(), 'base', '', lambda *args: [12])
    assert len(rows) == 100 and len({r['request_id'] for r in rows}) == 100
    assert {tuple(r['stop']) for r in rows} == {('\nParticipant:', '\nColleague 1:', '\nColleague 2:')}
    actual = study.payload(rows[0])
    assert actual['stop'] == rows[0]['stop'] and actual['n_predict'] == 128 and actual['cache_prompt'] is False
    assert actual['temperature'] == 0 and actual['ignore_eos'] is False and 'grammar' not in actual


@pytest.mark.parametrize('fault', ['reference', 'role', 'fact', 'size'])
def test_inherited_source_guards_preserved(fault):
    data = material()
    if fault == 'reference':
        data['cases'][0]['context'][0]['text'] = data['cases'][0]['reference_continuation_not_for_prompt']['text']
    elif fault == 'role':
        data['cases'][0]['context'][0]['text'] = '<|im_start|>assistant'
    elif fault == 'fact':
        data['cases'][0]['structured_facts'][0]['source_quote'] = 'Unsupported.'
    else:
        data['cases'].pop()
    with pytest.raises(ValueError):
        study.build(data, 'base', '', lambda *args: [12])


def test_native_context_bound_not_truncated():
    with pytest.raises(ValueError, match='context'):
        study.build(material(), 'base', '', lambda *args: [12] * 1921)


def test_scoped_execution_restores_old_model_paths_thresholds_and_command(monkeypatch):
    names = ('OUT', 'PRIVATE', 'MODEL', 'RUNTIME', 'MIN_RAM', 'READY_RAM', 'LIVE_RAM', 'validate', 'config', 'payload')
    original = {name: getattr(study.old, name) for name in names}
    original_command = study.old.shared.s.command
    model = {'model_file': 'authored.gguf', 'model_sha256': 'a' * 64, 'backend_file': 'authored.exe'}
    with pytest.raises(RuntimeError), study.scoped(model, material(), 'AUTHORED_TEMPLATE'):
        assert study.old.MIN_RAM == 3 * 1024**3 and study.old.PRIVATE == study.PRIVATE
        assert study.old.payload is study.payload and study.old.config is study.config
        cfg = study.config({'batch': 'base', 'model': model})
        assert cfg.n_ctx == 2048 and cfg.max_new_tokens == 128 and cfg.threads == 4
        monkeypatch.setattr(study, 'external_path', lambda path: Path(path).resolve())
        base = study.command({'batch': 'base', 'model': model})
        instruct = study.command({'batch': 'instruct', 'model': model, 'template_path': 'tools/authored.jinja'})
        assert '--no-warmup' in base and '--chat-template-file' not in base and '--chat-template-file' in instruct
        raise RuntimeError('Authored boundary failure')
    assert all(getattr(study.old, name) is value for name, value in original.items())
    assert study.old.shared.s.command is original_command


def test_baseline788_not_reset_and_forged_binding_rejected(monkeypatch):
    monkeypatch.setattr(study, 'sha', lambda _: study.BASELINE_SHA)
    monkeypatch.setattr(study, 'load', lambda _: {'cumulative_generations': 788,
                                                'cumulative_inference_seconds': study.BASE_SECONDS})
    plan = {'batch': 'base', 'prior_receipt': {'path': study.BASELINE.as_posix(), 'sha256': study.BASELINE_SHA}}
    assert study.baseline(plan) == (788, study.BASE_SECONDS)
    plan['prior_receipt']['sha256'] = 'wrong'
    with pytest.raises(ValueError, match='predecessor'):
        study.baseline(plan)


@pytest.mark.parametrize('status,attempts,responses', [('PARTIAL', 80, 80), ('PASS', 99, 99), ('PASS', 100, 99)])
def test_instruct_blocked_before_ram_or_native_work_if_base_incomplete(monkeypatch, status, attempts, responses):
    def load(path):
        if Path(path) == study.BASELINE:
            return {'cumulative_generations': 788, 'cumulative_inference_seconds': study.BASE_SECONDS}
        return {'status': status, 'attempts': attempts, 'responses': responses}
    monkeypatch.setattr(study, 'load', load)
    monkeypatch.setattr(study, 'sha', lambda p: study.BASELINE_SHA if Path(p) == study.BASELINE else 'parent')
    monkeypatch.setattr(study, 'inputs', lambda *args: ({}, {}, material(), {}, ''))
    monkeypatch.setattr(study.old, 'memory', lambda *args: pytest.fail('RAM/load must not run'))
    monkeypatch.setattr(study.registration, 'native_tokenize', lambda *args: pytest.fail('Native call prohibited'))
    with pytest.raises(ValueError, match='finish100'):
        study.register('instruct', 'protocol', 'artifact', 'parent')


def test_unknown_variant_external_hash_failure_before_artifact_or_native_load(monkeypatch):
    monkeypatch.setattr(study, 'sha', lambda _: 'actual')
    monkeypatch.setattr(study.artifacts, 'inspect', lambda *args: pytest.fail('No artifact loading'))
    with pytest.raises(ValueError, match='Externally bound'):
        study.inputs('other-model', 'actual', 'actual')
    with pytest.raises(ValueError, match='Externally bound'):
        study.inputs('base', 'wrong', 'actual')


def test_model_scope_never_enables_hidden_runtime_knobs():
    assert study.RUNTIME['threads'] == 4 and study.RUNTIME['max_new_tokens'] == 128
    assert study.RUNTIME['cache_prompt'] is False and study.RUNTIME['warmup'] is False
    assert study.BASE_GENERATIONS + 200 + 160 == 1148
    assert 1200 - study.BASE_GENERATIONS - 200 - 160 == 52


def validation_fixture(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    model = {'model_file': 'authored.gguf', 'model_sha256': 'a' * 64, 'backend_file': 'authored.exe'}
    data = material(); rows, pooled = study.build(data, 'base', 'AUTHORED_TEMPLATE', lambda *args: [12, 13])
    folder = study.PRIVATE / 'base'; folder.mkdir(parents=True)
    template = folder / 'official_chat_template.jinja'
    template.write_text('AUTHORED_TEMPLATE', encoding='utf-8')
    plan = {'schema': study.STUDY, 'batch': 'base', 'language': 'en', 'model': model, 'runtime': study.RUNTIME,
        'source_head': 'AUTHORED_HEAD', 'source_hashes': {}, 'input_hashes': {}, 'cases': data['cases'],
        'bindings': {'protocol_sha256': 'protocol', 'artifact_receipt_sha256': 'artifact'},
        'authorization': {'decision': 'AUTHORIZED', 'maximum_attempts': 100},
        'allocation': {'maximum_inference_seconds': 3600, 'maximum_wall_seconds': 5400},
        'scientific_prerequisites': {'approved_for_execution': True, 'human_semantic_labels_available': False},
        'prior_receipt': {'path': study.BASELINE.as_posix(), 'sha256': study.BASELINE_SHA},
        'template_path': template.as_posix(), 'template_sha256': study.old.th('AUTHORED_TEMPLATE'),
        'requests': rows, 'pooled_development_style': pooled}
    needed = {study.PROTOCOL.as_posix(): 'protocol', study.artifacts.RECEIPT.as_posix(): 'artifact',
        study.MATERIAL.as_posix(): study.MATERIAL_SHA, study.OLD_MANIFEST.as_posix(): study.OLD_MANIFEST_SHA,
        study.BASELINE.as_posix(): study.BASELINE_SHA,
        template.as_posix(): plan['template_sha256']}
    rubric = {'path': (study.OUT / 'primary_review_rubric_v1.json').as_posix(), 'sha256': 'rubric'}
    needed[rubric['path']] = rubric['sha256']
    storage = {'path': study.STORAGE.as_posix(), 'sha256': 'storage'}
    needed[storage['path']] = storage['sha256']
    native = {str(folder / 'native_tokenizer' / (r['request_id'] + '.json')).replace('\\', '/'): 'native' for r in rows}
    plan['input_hashes'] = needed | native
    monkeypatch.setattr(study, 'source_hashes', lambda: {})
    monkeypatch.setattr(study.subprocess, 'check_output', lambda *args, **kwargs: 'AUTHORED_HEAD')
    original_load = study.load
    monkeypatch.setattr(study, 'load', lambda p: {'models': {'base': {'metadata_files': []}}}
        if Path(p) == study.artifacts.RECEIPT else {'human_rubric': rubric, 'model_storage': storage} if Path(p) == study.PROTOCOL
        else {} if 'native_tokenizer' in str(p) else original_load(p))
    original_sha = study.sha
    def mock_sha(path):
        key = Path(path).resolve().relative_to(Path.cwd()).as_posix()
        return plan['input_hashes'][key] if key in plan['input_hashes'] else original_sha(Path(path))
    monkeypatch.setattr(study, 'sha', mock_sha)
    monkeypatch.setattr(study, 'baseline', lambda _: (788, study.BASE_SECONDS))
    monkeypatch.setattr(study.independent, 'verify_native_receipt', lambda *args: None)
    return plan, data, model, folder / 'frozen_manifest_v1.json'


@pytest.mark.parametrize('fault', [None, 'messages', 'stop', 'donor', 'source', 'snapshot', 'semantic', 'bos'])
def test_manifest_reconstruction_and_binding_reject_tampering(monkeypatch, tmp_path, fault):
    plan, data, model, path = validation_fixture(monkeypatch, tmp_path)
    if fault in ('messages', 'stop', 'bos'):
        row = plan['requests'][0]
        if fault == 'messages':
            row['messages'][1]['content'] += ' Extra instruction.'
        elif fault == 'stop':
            row['stop'] = []
        else:
            row['input_token_ids'][0] = 151643
            row['input_token_ids_sha256'] = study.old.shared.value_sha256(row['input_token_ids'])
        row['request_sha256'] = study.old.shared.value_sha256({k: v for k, v in row.items() if k != 'request_sha256'})
    elif fault == 'donor':
        row = next(r for r in plan['requests'] if r['condition'] == 'M_STYLE')
        row['style_source_speaker_id'] = 'AUTHORED2'
        row['request_sha256'] = study.old.shared.value_sha256({k: v for k, v in row.items() if k != 'request_sha256'})
    elif fault == 'source':
        plan['source_hashes']['missing.py'] = 'unbound'
    elif fault == 'snapshot':
        del plan['input_hashes'][study.MATERIAL.as_posix()]
    elif fault == 'semantic':
        plan['scientific_prerequisites']['human_semantic_labels_available'] = True
    path.write_text(json.dumps(plan), encoding='utf-8')
    with study.scoped(model, data, 'AUTHORED_TEMPLATE'):
        if fault:
            with pytest.raises(ValueError):
                study.old.validate(path, study.sha(path))
        else:
            actual, count, seconds = study.old.validate(path, study.sha(path))
            assert actual['requests'] == plan['requests'] and count == 788 and seconds == study.BASE_SECONDS


@pytest.mark.parametrize('path', ['D:/other-model.gguf', 'D:/PersonaSLM-model-cache/english_qwen25_15b_v1/base/other.gguf',
                                 'C:/weights/model.gguf', 'models/authored.gguf'])
def test_external_storage_does_not_allow_arbitrary_paths(path):
    with pytest.raises(ValueError, match='exact authorized'):
        study.external_path(path)


def test_external_storage_symlink_is_rejected(monkeypatch):
    monkeypatch.setattr(Path, 'is_symlink', lambda _: True)
    with pytest.raises(ValueError, match='link/junction'):
        study.external_path(study.PHYSICAL['base'])


def test_external_weight_preflight_preserves_generic_local_guard(monkeypatch, tmp_path):
    path = tmp_path / 'authored.gguf'
    path.write_bytes(b'GGUF' + struct.pack('<IQQ', 3, 1, 1))
    digest = study.sha(path)
    monkeypatch.setattr(study, 'PHYSICAL', {'base': path})
    monkeypatch.setattr(study.artifacts, 'MODELS', {'base': {'sha256': digest, 'bytes': 24}})
    guard = study.configuration.require_local_path
    verifier = study.configuration.verify_gguf
    value = study.external_gguf(path, digest)
    assert value['sha256_verified'] and value['gguf_version'] == 3
    with pytest.raises(ValueError, match='size/SHA'):
        study.external_gguf(path, '0' * 64)
    with pytest.raises(ValueError, match='Out-of-project'):
        guard(Path('D:/not-authorized.gguf'))
    server = tmp_path / 'authored.exe'; server.write_bytes(b'Authored non-executable fixture')
    cfg = study.config({'batch': 'base', 'model': {'model_file': str(path), 'model_sha256': digest,
                                                  'backend_file': str(server)}})
    assert study.file_preflight(cfg)['status'] == 'PASS'
    assert study.configuration.require_local_path is guard and study.configuration.verify_gguf is verifier


def test_external_properties_bind_exact_model_context_and_build(monkeypatch):
    monkeypatch.setattr(study, 'external_path', lambda path: Path(path))
    cfg = study.config({'batch': 'base', 'model': {'model_file': 'AUTHORED_BASE',
        'model_sha256': 'a' * 64, 'backend_file': 'AUTHORED_SERVER'}})
    props = {'model_path': 'AUTHORED_BASE', 'default_generation_settings': {'n_ctx': 2048},
             'build_info': 'authored 0f701c882 build'}
    assert study.server_properties(props, cfg)['model_path_matches']
    props['model_path'] = 'AUTHORED_OTHER'
    with pytest.raises(ValueError, match='model_path'):
        study.server_properties(props, cfg)
    props['model_path'] = 'AUTHORED_BASE'; props['default_generation_settings']['n_ctx'] = 4096
    with pytest.raises(ValueError, match='context/build'):
        study.server_properties(props, cfg)


@pytest.mark.parametrize('fault', ['path', 'hash', 'generations', 'seconds'])
def test_storage_amendment_cannot_replace_path_hash_or_reset_budget(monkeypatch, fault):
    protocol = {'model_storage': {'path': study.STORAGE.as_posix(), 'sha256': 'authored'}}
    storage = {'schema': 'english_model_comparison_storage_amendment_v1',
               'baseline_generations': 788, 'baseline_inference_seconds': study.BASE_SECONDS}
    if fault == 'path':
        protocol['model_storage']['path'] = 'D:/arbitrary.json'
    elif fault == 'hash':
        protocol['model_storage']['sha256'] = 'changed'
    elif fault == 'generations':
        storage['baseline_generations'] = 0
    else:
        storage['baseline_inference_seconds'] = 0
    monkeypatch.setattr(study, 'sha', lambda _: 'authored')
    monkeypatch.setattr(study, 'load', lambda p: protocol if Path(p) == study.PROTOCOL else storage)
    with pytest.raises(ValueError, match='Storage'):
        study.inputs('base', 'authored', 'authored')
