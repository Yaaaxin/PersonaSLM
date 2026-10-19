"""Authored fixtures only; no archive bodies, weights, tokenizer or inference."""
import copy
import json
from pathlib import Path

import pytest

import ami_english_execution_v1 as ami
from test_english_sfh_registration_v1 import authored_case


def fixture(monkeypatch, tmp_path, count=4):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ami, 'PRIVATE', Path('.local/ami'))
    monkeypatch.setattr(ami, 'OUT', Path('public/ami'))
    monkeypatch.setattr(ami, 'MANIFEST', ami.PRIVATE / 'development/frozen_manifest_v1.json')
    monkeypatch.setattr(ami, 'BASELINE', Path('public/baseline.json'))
    monkeypatch.setattr(ami, 'ARCHIVE', Path('.local/authored.zip'))
    monkeypatch.setattr(ami, 'DECISION', Path('public/conditional_decision.json'))
    monkeypatch.setattr(ami, 'POLICIES', (Path('public/source_policy.json'), Path('public/metadata_policy.json'), ami.DECISION))
    monkeypatch.setattr(ami, 'source_hashes', lambda: {'authored_adapter.py': 'authored-sha'})
    def save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return ami.original.sha(path)
    baseline_sha = save(ami.BASELINE, {'cumulative_generations': ami.BASE_GENERATIONS,
                                     'cumulative_inference_seconds': ami.BASE_SECONDS})
    monkeypatch.setattr(ami, 'BASELINE_SHA', baseline_sha)
    archive_sha = save(ami.ARCHIVE, {'authored': True})
    monkeypatch.setattr(ami, 'ARCHIVE_SHA', archive_sha)
    hashes = {ami.BASELINE.as_posix(): baseline_sha, ami.ARCHIVE.as_posix(): archive_sha}
    hashes.update({p.as_posix(): save(p, {'authored': True}) for p in ami.POLICIES[:2]})
    hashes[ami.DECISION.as_posix()] = save(ami.DECISION, {
        'schema': 'ami_conditional_experiment_decision_v1', 'status': 'CONDITIONAL_NOT_EXECUTION_GO',
        'source_policy_sha256': hashes[ami.POLICIES[0].as_posix()],
        'finite_design': {'speakers': 4, 'contexts_per_speaker': 2, 'total_generation_attempts': 80,
                         'preserved_validation_generation_reserve': 160, 'remaining_after_complete_batch': 332,
                         'baseline': {'generations': ami.BASE_GENERATIONS, 'inference_seconds': ami.BASE_SECONDS},
                         'ram_gates_bytes': ami.RAM_GATES,
                         'maximum_inference_seconds': 3600, 'maximum_wall_seconds': 5400}})
    material = {'study_id': ami.STUDY, 'corpus': 'AMI', 'cases': [
        authored_case(f'AUTHORED{i}', j) for i in range(count) for j in range(2)]}
    protocol = {'study_id': ami.STUDY, 'corpus': 'AMI', 'batch': 'development', 'speaker_count': count,
                'reserve_generations': 160, 'model': ami.original.MODEL, 'runtime': ami.original.RUNTIME,
                'ram_gates_bytes': ami.RAM_GATES, 'source_hashes': ami.source_hashes(), 'input_hashes': hashes,
                'prior_receipt': {'path': ami.BASELINE.as_posix(), 'sha256': baseline_sha},
                'allocation': {'maximum_inference_seconds': 1000, 'maximum_wall_seconds': 2000}}
    bindings = {'material': {'path': (ami.PRIVATE / 'material.json').as_posix()},
                'protocol': {'path': (ami.OUT / 'protocol.json').as_posix()},
                'qualification': {'path': (ami.OUT / 'qualification.json').as_posix()}}
    bindings['material']['sha256'] = save(Path(bindings['material']['path']), material)
    bindings['protocol']['sha256'] = save(Path(bindings['protocol']['path']), protocol)
    qualification = {'study_id': ami.STUDY, 'corpus': 'AMI', 'decision': 'GO_DEVELOPMENT',
                     'material_sha256': bindings['material']['sha256'],
                     'protocol_sha256': bindings['protocol']['sha256'], 'privacy_audit_complete': True,
                     'source_qualification_complete': True, 'human_semantic_labels_available': False}
    bindings['qualification']['sha256'] = save(Path(bindings['qualification']['path']), qualification)
    return material, protocol, qualification, bindings, save


def amend(name, value, bindings, save):
    bindings[name]['sha256'] = save(Path(bindings[name]['path']), value)


def fake_rows(monkeypatch, material, protocol, bindings):
    monkeypatch.setattr(ami.original.shared.s, 'render', lambda template, messages: str(messages))
    with ami.scoped(protocol, bindings, material):
        calls = []
        rows, pooled = ami.build_requests(material, 'development', 'AUTHORED',
            lambda prompt, name: calls.append(name) or [1, 2, 3])
        ami.original.validate_rows({'batch': 'development', 'requests': rows})
    return rows, pooled, calls


def test_authored_exact80_cohort_and_no_native_calls(monkeypatch, tmp_path):
    material, protocol, _, bindings, _ = fixture(monkeypatch, tmp_path)
    monkeypatch.setattr(ami.original, 'memory', lambda *args: pytest.fail('No hardware work in validation'))
    assert ami.inputs(bindings) == (material, protocol)
    rows, _, calls = fake_rows(monkeypatch, material, protocol, bindings)
    assert len(rows) == len(calls) == 80
    assert [row['request_id'] for row in rows] == calls == [f'AMI_ENSFH_development_{i:04d}' for i in range(80)]
    assert {row['condition'] for row in rows} == set(ami.registration.CONDITIONS)


@pytest.mark.parametrize('count', [3, 5, 8])
def test_invalid_cohort_cannot_authorize(monkeypatch, tmp_path, count):
    _, _, _, bindings, _ = fixture(monkeypatch, tmp_path, count)
    with pytest.raises(ValueError, match='exactly4'):
        ami.inputs(bindings)


@pytest.mark.parametrize('change', ['pending', 'historical', 'changed_source', 'no_reserve', 'lower_ram'])
def test_prerequisites_fail_closed(monkeypatch, tmp_path, change):
    _, protocol, qualification, bindings, save = fixture(monkeypatch, tmp_path)
    if change == 'pending':
        qualification['decision'] = 'PENDING'
    elif change == 'historical':
        qualification['study_id'] = 'old_icsi_study'
    else:
        if change == 'changed_source':
            protocol['source_hashes'] = {}
        elif change == 'no_reserve':
            protocol['reserve_generations'] = 0
        else:
            protocol['ram_gates_bytes'] = [1, 1, 1]
        amend('protocol', protocol, bindings, save)
        qualification['protocol_sha256'] = bindings['protocol']['sha256']
    amend('qualification', qualification, bindings, save)
    with pytest.raises(ValueError):
        ami.inputs(bindings)


def test_source_mutation_and_path_escape_fail_closed(monkeypatch, tmp_path):
    _, _, _, bindings, save = fixture(monkeypatch, tmp_path)
    save(ami.ARCHIVE, {'changed_authored': True})
    with pytest.raises(ValueError, match='input changed'):
        ami.inputs(bindings)
    bindings['material']['path'] = 'public/private_material.json'
    with pytest.raises(ValueError, match='study area'):
        ami.inputs(bindings)


@pytest.mark.parametrize('field,value', [('maximum_inference_seconds', 3601),
                                        ('maximum_wall_seconds', 5401)])
def test_time_allocation_cannot_exceed_conditional_decision(monkeypatch, tmp_path, field, value):
    _, protocol, qualification, bindings, save = fixture(monkeypatch, tmp_path)
    protocol['allocation'][field] = value
    amend('protocol', protocol, bindings, save)
    qualification['protocol_sha256'] = bindings['protocol']['sha256']
    amend('qualification', qualification, bindings, save)
    with pytest.raises(ValueError, match='finite time allocation'):
        ami.inputs(bindings)


@pytest.mark.parametrize('field,value', [('speakers', 8), ('total_generation_attempts', 160),
                                       ('baseline', {'generations': 0, 'inference_seconds': 0})])
def test_conditional_design_and_baseline_cannot_be_redefined(monkeypatch, tmp_path, field, value):
    _, protocol, qualification, bindings, save = fixture(monkeypatch, tmp_path)
    decision = ami.original.load(ami.DECISION)
    decision['finite_design'][field] = value
    protocol['input_hashes'][ami.DECISION.as_posix()] = save(ami.DECISION, decision)
    amend('protocol', protocol, bindings, save)
    qualification['protocol_sha256'] = bindings['protocol']['sha256']
    amend('qualification', qualification, bindings, save)
    with pytest.raises(ValueError, match='design/baseline'):
        ami.inputs(bindings)


def test_conditional_decision_hash_must_be_in_protocol(monkeypatch, tmp_path):
    _, protocol, qualification, bindings, save = fixture(monkeypatch, tmp_path)
    del protocol['input_hashes'][ami.DECISION.as_posix()]
    amend('protocol', protocol, bindings, save)
    qualification['protocol_sha256'] = bindings['protocol']['sha256']
    amend('qualification', qualification, bindings, save)
    with pytest.raises(ValueError, match='prospectively bound'):
        ami.inputs(bindings)


def test_scoped_constants_restore_after_error_and_preserve_gates(monkeypatch, tmp_path):
    material, protocol, _, bindings, _ = fixture(monkeypatch, tmp_path)
    previous = (ami.original.PRIVATE, ami.original.OUT, ami.original.SIZES, ami.original.validate,
                ami.registration.build_requests, ami.original.MIN_RAM, ami.original.READY_RAM, ami.original.LIVE_RAM)
    with pytest.raises(RuntimeError, match='Authored'):
        with ami.scoped(protocol, bindings, material):
            assert ami.original.PRIVATE == ami.PRIVATE and ami.original.OUT == ami.OUT
            assert ami.original.SIZES == {'development': (4, 80), 'validation': (8, 160)}
            assert [ami.original.MIN_RAM, ami.original.READY_RAM, ami.original.LIVE_RAM] == ami.RAM_GATES
            raise RuntimeError('Authored scope failure')
    assert previous == (ami.original.PRIVATE, ami.original.OUT, ami.original.SIZES, ami.original.validate,
                        ami.registration.build_requests, ami.original.MIN_RAM, ami.original.READY_RAM, ami.original.LIVE_RAM)


def test_manifest_write_binds_adapter_and_does_not_overwrite(monkeypatch, tmp_path):
    material, protocol, _, bindings, _ = fixture(monkeypatch, tmp_path)
    with ami.scoped(protocol, bindings, material):
        ami.original.write(ami.MANIFEST, {'source_hashes': {'old.py': 'old'}})
        with pytest.raises((ValueError, FileExistsError)):
            ami.original.write(ami.MANIFEST, {'source_hashes': {}})
    plan = ami.original.load(ami.MANIFEST)
    assert plan['study_id'] == ami.STUDY and plan['corpus'] == 'AMI'
    assert plan['ami_registration'] == bindings
    assert plan['source_hashes'] == {'old.py': 'old', **ami.source_hashes()}


def test_material_reconstruction_rejects_changed_prompt_or_identity(monkeypatch, tmp_path):
    material, protocol, _, bindings, _ = fixture(monkeypatch, tmp_path)
    rows, pooled, _ = fake_rows(monkeypatch, material, protocol, bindings)
    template = ami.PRIVATE / 'template.jinja'
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text('AUTHORED', encoding='utf-8')
    plan = {'study_id': ami.STUDY, 'corpus': 'AMI', 'ami_registration': bindings, 'cases': material['cases'],
            'allocation': protocol['allocation'], 'prior_receipt': protocol['prior_receipt'],
            'source_hashes': ami.source_hashes(), 'input_hashes': {v['path']: v['sha256'] for v in bindings.values()},
            'template_path': template.as_posix(), 'requests': rows, 'pooled_development_style': pooled}
    with ami.scoped(protocol, bindings, material):
        ami.check_plan(plan, material, protocol, bindings)
        changed = copy.deepcopy(plan)
        changed['requests'][0]['prompt'] = 'An unauthorized prompt'
        with pytest.raises(ValueError, match='exactly reconstruct'):
            ami.check_plan(changed, material, protocol, bindings)
        changed = copy.deepcopy(plan)
        changed['study_id'] = 'historical'
        with pytest.raises(ValueError, match='identity/material'):
            ami.check_plan(changed, material, protocol, bindings)


def test_register_delegates_only_after_qualification(monkeypatch, tmp_path):
    material, protocol, _, bindings, _ = fixture(monkeypatch, tmp_path)
    calls = []
    def authored_register(*args):
        calls.append(args)
        assert ami.original.BASE_GENERATIONS == 788 and ami.original.BASE_SECONDS == ami.BASE_SECONDS
        assert ami.original.PRIVATE == ami.PRIVATE and ami.original.SIZES['development'] == (4, 80)
        return {'status': 'AUTHORED_NOT_NATIVE'}
    monkeypatch.setattr(ami.registration, 'register', authored_register)
    result = ami.register(*(v for name in ('material', 'protocol', 'qualification')
                            for v in (bindings[name]['path'], bindings[name]['sha256'])))
    assert len(calls) == 1 and result['study_id'] == ami.STUDY


def test_original_registration_writes_isolated_native_receipts_and_manifest(monkeypatch, tmp_path):
    material, protocol, qualification, bindings, save = fixture(monkeypatch, tmp_path)
    template = 'AUTHORED TEMPLATE'
    monkeypatch.setattr(ami.original, 'TEMPLATE_SHA', ami.original.th(template))
    monkeypatch.setattr(ami.original, 'memory', lambda *args: {'authored_memory': True})
    monkeypatch.setattr(ami.original.shared, '_tokenizer_identity', lambda: {'authored': True})
    monkeypatch.setattr(ami.original.shared, 'runtime_python_dependency_paths', lambda *args: ())
    monkeypatch.setattr(ami.original.shared.s, 'render', lambda _, messages: str(messages))
    monkeypatch.setattr(ami.registration.subprocess, 'check_output', lambda *args, **kwargs: 'AUTHORED_HEAD')
    monkeypatch.setattr(ami.registration.metadata, 'verified_template_runtime', lambda: {'authored': True})
    monkeypatch.setattr(ami.registration.metadata, 'gguf_metadata', lambda _: (
        {'general.architecture': 'qwen3', 'general.file_type': 7, 'tokenizer.chat_template': template}, {}))
    monkeypatch.setattr(ami.registration, 'META', Path('.local/model_metadata'))
    meta_hash = save(ami.registration.META / 'tokenizer_config.json', {'chat_template': template})
    monkeypatch.setattr(ami.registration, 'META_HASHES', {'tokenizer_config.json': meta_hash})
    monkeypatch.setattr(ami.registration.metadata, 'TEMPLATE_RUNTIME_PROVENANCE', Path('.local/vendor.json'))
    save(ami.registration.metadata.TEMPLATE_RUNTIME_PROVENANCE, {'package_file_sha256': {}})
    monkeypatch.setattr(ami.original.shared, 'TOKENIZER_SOURCE', Path('tools/authored_tokenizer.py'))
    for path in ('tools/authored_tokenizer.py', 'tests/test_english_sfh_registration_v1.py',
                 'tests/test_english_sfh_execution_v1.py', 'authored_adapter.py'):
        save(Path(path), {'authored_fixture': True})
    monkeypatch.setattr(ami, 'source_hashes', lambda: {'authored_adapter.py': ami.original.sha(Path('authored_adapter.py'))})
    protocol['source_hashes'] = ami.source_hashes()
    amend('protocol', protocol, bindings, save)
    qualification['protocol_sha256'] = bindings['protocol']['sha256']
    amend('qualification', qualification, bindings, save)
    real_sha = ami.original.sha
    identities = {Path(ami.original.MODEL['model_file']): ami.original.MODEL['model_sha256'],
                  Path(ami.original.MODEL['backend_file']): ami.original.MODEL['backend_sha256']}
    monkeypatch.setattr(ami.original, 'sha', lambda p: identities[Path(p)] if Path(p) in identities else real_sha(p))
    def authored_tokenize(prompt, receipt_path):
        ami.original.write(receipt_path, {'authored_tokens': [1, 2, 3], 'generation_requests': 0})
        return [1, 2, 3]
    monkeypatch.setattr(ami.registration, 'native_tokenize', authored_tokenize)
    monkeypatch.setattr(ami, '_VALIDATE', lambda path, digest: (
        ami.original.load(path), ami.BASE_GENERATIONS, ami.BASE_SECONDS))
    result = ami.register(*(v for name in ('material', 'protocol', 'qualification')
                            for v in (bindings[name]['path'], bindings[name]['sha256'])))
    plan = ami.original.load(ami.MANIFEST)
    assert result['requests'] == 80 and plan['study_id'] == ami.STUDY
    assert plan['source_hashes']['authored_adapter.py'] == ami.source_hashes()['authored_adapter.py']
    receipts = list((ami.PRIVATE / 'development/native_tokenizer').glob('*.json'))
    assert len(receipts) == 80 and all(p.name.startswith('AMI_ENSFH_development_') for p in receipts)
    assert not Path('.local/experiments/english_sfh_v1').exists()


def test_original_frozen_source_files_are_not_write_targets():
    assert ami.PRIVATE.as_posix().startswith('.local/experiments/english_sfh_v2/ami')
    assert ami.OUT.as_posix().endswith('english_real_speaker_stage_v2/ami')
    assert ami.MANIFEST.is_relative_to(ami.PRIVATE)
    assert ami.RESERVE == 160 and ami.BASE_GENERATIONS + 80 + ami.RESERVE <= 1200
