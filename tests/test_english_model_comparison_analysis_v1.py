import copy
import math

import pytest

import english_model_comparison_analysis_v1 as analysis
from test_english_sfh_model_comparison_v1 import material


def rows(model):
    result = []
    for speaker in range(5):
        for case in range(2):
            for condition in analysis.independent.CONDITIONS:
                factor = int(condition[1:]) if condition.startswith('C') else 7
                value = 10 + speaker + case + 3 * bool(factor & 1) + 5 * bool(factor & 2)
                if model == 'instruct':
                    value += 2 + 4 * bool(factor & 1)
                result.append({'request_id': f'{model}_{speaker}_{case}_{condition}', 'speaker_id': f'fixture_{speaker}',
                    'case_id': f'case_{speaker}_{case}', 'condition': condition,
                    'phase': 'MAIN' if condition.startswith('C') else 'DIAGNOSTIC',
                    'measurements': dict.fromkeys(analysis.METRICS, float(value))})
    return result


def test_matched_model_effects_use_complete_speaker_pairs_and_two_formulas():
    base, instruct = rows('base'), rows('instruct')
    paired = analysis.paired_rows(base, list(reversed(instruct)))
    result = analysis.summarize(paired)
    effects = result['all_speakers']['factorial_effects']['output_tokens']
    assert effects['S']['mean'] == 4 and effects['S']['n'] == 5
    assert effects['S']['leave_one_speaker_out_mean_range'] == [4, 4]
    assert all(abs(effects[name]['mean']) < 1e-12 for name in ('F', 'H', 'SF', 'SH', 'FH', 'SFH'))
    assert len(result['speaker_profiles']) == 5
    assert result['all_speakers']['condition_summary']['output_tokens']['C0']['mean'] == 2


def test_missing_native_measurement_is_not_zero_and_complete_speaker_policy_is_retained():
    base, instruct = rows('base'), rows('instruct')
    instruct[0]['measurements']['native_prefill_seconds'] = None
    result = analysis.estimates(analysis.paired_rows(base, instruct))
    effect = result['factorial_effects']['native_prefill_seconds']['S']
    assert effect['n'] == 4 and effect['incomplete_speakers'] == 1
    assert result['condition_summary']['native_prefill_seconds']['C0']['missing_or_inapplicable'] == 1


@pytest.mark.parametrize('damage', ['missing', 'duplicate', 'context', 'phase'])
def test_invalid_matching_fails_closed(damage):
    base, instruct = rows('base'), rows('instruct')
    if damage == 'missing': instruct.pop()
    if damage == 'duplicate': instruct[1] = copy.deepcopy(instruct[0])
    if damage == 'context': instruct[0]['case_id'] = 'different'
    if damage == 'phase': instruct[0]['phase'] = 'DIAGNOSTIC'
    with pytest.raises(ValueError):
        analysis.paired_rows(base, instruct)


def test_native_values_are_preserved_and_semantics_are_not_created():
    request = {'request_id': 'authored', 'speaker_id': 'x', 'case_id': 'y', 'condition': 'C0', 'phase': 'MAIN',
               'input_tokens': 7, 'messages': [{'content': 'A wholly authored source conversation.'}]}
    response = {'content': '', 'tokens_predicted': 0, 'stop_type': 'word',
                'timings': {'prompt_ms': 200.0, 'predicted_ms': 50.0}}
    observed = {'response': response, 'latency_seconds': 0.3}
    checked = {k: request[k] for k in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')}
    checked['measurements'] = analysis.independent.measurements(request, response, 0.3)
    result = analysis.technical_rows([request], {'authored': observed}, [checked])[0]['measurements']
    assert result['native_prefill_seconds'] == 0.2 and result['native_decode_seconds'] == 0.05
    assert result['native_stop_word'] == 1 and result['output_tokens'] == 0
    assert set(result) == set(analysis.METRICS) and 'source_fivegram_coverage' not in result
    response['timings']['prompt_ms'] = math.nan
    with pytest.raises(ValueError, match='Invalid native timing'):
        analysis.technical_rows([request], {'authored': observed}, [checked])


def test_no_overwrite_before_actual_audit(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis, 'OUT', tmp_path)
    monkeypatch.setattr(analysis, 'PRIVATE', tmp_path / 'private')
    (tmp_path / 'technical_analysis_v1.json').write_text('authored prior evidence')
    monkeypatch.setattr(analysis, 'calculate', lambda *args: pytest.fail('Must fail before reading outputs'))
    with pytest.raises(ValueError, match='No overwrite'):
        analysis.analyze('a', 'b', 'write')


def test_helper_scope_does_not_mutate_frozen_metrics():
    original_primary = analysis.primary.METRICS
    original_independent = analysis.independent.METRICS
    analysis.estimates(rows('base'))
    assert analysis.primary.METRICS is original_primary
    assert analysis.independent.METRICS is original_independent


def test_changed_receipt_anchor_stops_before_controller_validation(monkeypatch):
    monkeypatch.setattr(analysis, 'sha', lambda p: 'actual')
    monkeypatch.setattr(analysis.controller, 'execute', lambda *a: pytest.fail('Must reject bad anchor first'))
    with pytest.raises(ValueError, match='Externally anchored'):
        analysis.audit_run('base', 'different')


def test_partial_allocation_is_not_delivered_or_scored_as_complete(monkeypatch):
    monkeypatch.setattr(analysis, 'sha', lambda p: 'bound')
    monkeypatch.setattr(analysis, 'load', lambda p: {'status': 'PARTIAL', 'manifest_sha256': 'bound'})
    monkeypatch.setattr(analysis.controller, 'execute', lambda *a: {})
    with pytest.raises(ValueError, match='Both complete100'):
        analysis.audit_run('base', 'bound')


def archive_fixture(monkeypatch, tmp_path):
    controller = analysis.controller
    source = material(); template = 'AUTHORED_TEMPLATE'
    generated, pooled = controller.build(source, 'base', template, lambda *args: [12, 13])
    template_path = tmp_path / 'official.jinja'; template_path.write_text(template, encoding='utf-8')
    monkeypatch.setattr(analysis, 'PRIVATE', tmp_path)
    protocol = {name: {'path': name + '.json', 'sha256': name + '_hash'} for name in ('human_rubric', 'model_storage')}
    artifact = {'models': {'base': {'metadata_files': []}}}
    inputs = {controller.PROTOCOL.as_posix(): 'protocol', controller.artifacts.RECEIPT.as_posix(): 'artifact',
        controller.MATERIAL.as_posix(): controller.MATERIAL_SHA, controller.OLD_MANIFEST.as_posix(): controller.OLD_MANIFEST_SHA,
        controller.BASELINE.as_posix(): controller.BASELINE_SHA, template_path.as_posix(): controller.old.th(template)}
    inputs.update({v['path']: v['sha256'] for v in protocol.values()})
    plan = {'schema': controller.STUDY, 'batch': 'base', 'language': 'en', 'model': {'authored': True},
        'runtime': controller.RUNTIME, 'source_head': 'FROZEN_OLD_HEAD', 'source_hashes': {'authored.py': 'source_hash'},
        'authorization': {'decision': 'AUTHORIZED', 'maximum_attempts': 100},
        'allocation': {'maximum_inference_seconds': 3600, 'maximum_wall_seconds': 5400},
        'scientific_prerequisites': {'approved_for_execution': True, 'human_semantic_labels_available': False},
        'cases': source['cases'], 'requests': generated, 'pooled_development_style': pooled, 'input_hashes': inputs,
        'bindings': {'protocol_sha256': 'protocol', 'artifact_receipt_sha256': 'artifact'},
        'prior_receipt': {'path': controller.BASELINE.as_posix(), 'sha256': controller.BASELINE_SHA},
        'template_path': template_path.as_posix(), 'template_sha256': controller.old.th(template)}
    monkeypatch.setattr(controller, 'inputs', lambda *args: (protocol, artifact, source, {'authored': True}, template))
    monkeypatch.setattr(controller, 'source_hashes', lambda: {'authored.py': 'source_hash'})
    monkeypatch.setattr(controller, 'baseline', lambda _: (788, controller.BASE_SECONDS))
    monkeypatch.setattr(controller, 'execute', lambda *args: pytest.fail('Archival analysis must not call execution validator'))
    return plan


def test_legitimate_head_advance_does_not_block_byte_identical_archival_analysis(monkeypatch, tmp_path):
    plan = archive_fixture(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(analysis.controller.subprocess, 'check_output', lambda *args, **kw:
        calls.append(args) or 'LEGITIMATE_NEW_HEAD')
    result = analysis.archival_plan(plan, 'base')
    assert result['baseline_generations'] == 788 and calls == []
    assert plan['source_head'] == 'FROZEN_OLD_HEAD'


@pytest.mark.parametrize('damage', ['source', 'prompt', 'input', 'allocation', 'model', 'template'])
def test_archival_head_independence_does_not_weaken_bytes_scope_or_requests(monkeypatch, tmp_path, damage):
    plan = archive_fixture(monkeypatch, tmp_path)
    if damage == 'source':
        monkeypatch.setattr(analysis.controller, 'source_hashes', lambda: {'authored.py': 'CHANGED'})
    elif damage == 'prompt':
        row = plan['requests'][0]; row['messages'][1]['content'] += ' Authored tampering.'
        row['request_sha256'] = analysis.controller.old.shared.value_sha256({k: v for k, v in row.items() if k != 'request_sha256'})
    elif damage == 'input':
        del plan['input_hashes'][analysis.controller.MATERIAL.as_posix()]
    elif damage == 'allocation':
        plan['authorization']['maximum_attempts'] = 200
    elif damage == 'model':
        plan['model'] = {'authored': False}
    else:
        plan['template_sha256'] = 'changed'
    with pytest.raises(ValueError):
        analysis.archival_plan(plan, 'base')
