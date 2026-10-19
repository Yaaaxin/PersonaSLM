"""Authored scores and package records only; never access the actual condition map."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

import english_sfh_ordinal_v1 as ordinal


def fixture_rows():
    return [{'speaker_id': f'authored_s{s}', 'case_id': f'authored_s{s}_case{c}', 'condition': condition,
             'ratings': {domain: (5 if condition in ('C1', 'C3', 'C5', 'C7') else 0) for domain in ordinal.DOMAINS},
             'latency_seconds': float(index + 1)}
            for s in range(5) for c in range(2) for index, condition in enumerate(ordinal.CONDITIONS)]


def test_factor_scale_pairing_controls_and_zero_are_observed():
    result = ordinal.compute(fixture_rows())['domains']['relevance']
    assert result['condition_distributions']['C0'] == {'counts': [10, 0, 0, 0, 0, 0], 'observed': 10, 'missing': 0, 'central_categories': [0, 0]}
    for threshold in '12345':
        assert result['threshold_factorial']['S'][threshold]['mean_complete_speakers'] == 1
        assert result['threshold_factorial']['SF'][threshold]['mean_complete_speakers'] == 0
    assert result['paired_main']['S']['win']['allocated_units'] == 40
    assert result['paired_main']['S']['win']['full_design_bounds'] == [1, 1]
    assert result['style_controls']['correct_minus_no_style_at_FH']['paired']['win']['allocated_units'] == 10
    assert result['style_controls']['correct_minus_no_style_at_FH']['paired']['win']['mean_complete_speakers'] == 1


def test_interaction_is_factorial_scaled_not_unscaled_difference_in_differences():
    rows = fixture_rows()
    for row in rows:
        if row['condition'].startswith('C'):
            index = int(row['condition'][1:])
            row['ratings'] = dict.fromkeys(ordinal.DOMAINS, 5 if bool(index & 1) == bool(index & 2) else 0)
    result = ordinal.compute(rows)['domains']['coherence']['threshold_factorial']
    assert result['SF']['3']['mean_complete_speakers'] == 1
    assert result['S']['3']['mean_complete_speakers'] == 0


def test_missing_preserved_exact_bounds_whole_speaker_and_nested_completion_profiles():
    rows = fixture_rows(); rows[1]['ratings'] = dict.fromkeys(ordinal.DOMAINS)
    result = ordinal.compute(rows)['domains']['relevance']
    assert rows[1]['ratings']['relevance'] is None
    assert result['completion_category_scenarios'] == list(range(6))
    cut = result['threshold_factorial']['S']['1']
    assert cut['allocated_units'] == 80 and cut['observed_units'] == 79 and cut['complete_speakers'] == 4
    assert cut['full_design_bounds'] == pytest.approx([.975, 1])
    assert cut['full_design_completion_values'] == pytest.approx([.975, 1, 1, 1, 1, 1])
    assert result['threshold_factorial']['S']['5']['full_design_completion_values'] == pytest.approx([.975]*5+[1])
    pair = result['paired_main']['S']['win']
    assert pair['observed_units'] == 39 and pair['complete_speakers'] == 4
    assert pair['full_design_bounds'] == pytest.approx([.975, 1])
    assert result['paired_main']['S']['loss']['full_design_bounds'] == [0, 0]


def test_pair_order_invariant_to_strict_monotone_recoding_of_observed_categories():
    rows = fixture_rows()
    for row in rows:
        row['ratings'] = {k: 1 if v == 0 else 3 for k, v in row['ratings'].items()}
    before = ordinal.compute(rows)['domains']['relevance']['paired_main']
    for row in rows:
        row['ratings'] = {k: 0 if v == 1 else 5 for k, v in row['ratings'].items()}
    assert before == ordinal.compute(rows)['domains']['relevance']['paired_main']


@pytest.mark.parametrize('bad', ['5', 6, -1, True, float('nan')])
def test_invalid_ordinal_values_fail_instead_of_imputation(bad):
    rows = fixture_rows(); rows[0]['ratings']['relevance'] = bad
    with pytest.raises(ValueError, match='integer0'):
        ordinal.compute(rows)


def test_duplicate_unknown_and_two_missing_records_fail():
    rows = fixture_rows(); rows[-1] = copy.deepcopy(rows[0])
    with pytest.raises(ValueError, match='Duplicate'):
        ordinal.compute(rows)
    rows = fixture_rows(); rows[0]['condition'] = 'UNKNOWN'
    with pytest.raises(ValueError, match='unknown'):
        ordinal.compute(rows)
    rows = fixture_rows()
    rows[0]['ratings'] = rows[1]['ratings'] = dict.fromkeys(ordinal.DOMAINS)
    with pytest.raises(ValueError, match='At most one'):
        ordinal.compute(rows)


def authored_intake(monkeypatch):
    records = [{'review_id': f'authored_{i}', 'outcome_status': 'GENERATED', 'dossier': 'Authored common dossier.',
                'response': 'Authored response.'} for i in range(100)]
    rows = []
    for i, record in enumerate(records[:-1]):
        row = {'review_id': record['review_id'], **dict.fromkeys(ordinal.review.EDITABLE, '')}
        row.update(annotation_status='researcher', relevance=str(i % 6), coherence='0', linguistic_resemblance='5',
                   confidence='0.85', rationale='Authored explanation.', claim_evidence_json='[]')
        rows.append(row)
    content = ordinal.review.encode_csv(rows, ordinal.recovery.INPUT_FIELDS)
    digest = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(ordinal, 'SUBMISSION_SHA', digest)
    declaration = {'schema': 'english_sfh_blank_uncertainty_declaration_v1', 'author': 'PRINCIPAL_RESEARCHER',
                   'received_submission_sha256': digest, 'blank_entries_mean_uncertainty': True}
    return {'rows': records}, rows, content, declaration


def test_primary_intake_preserves_0_5_and_declared_unavailable_without_map(monkeypatch):
    package, submitted, content, declaration = authored_intake(monkeypatch)
    monkeypatch.setattr(Path, 'read_bytes', lambda self: pytest.fail('Intake must not read any map or other file'))
    primary, qc = ordinal.intake(package, content, declaration)
    assert len(primary) == 100 and primary[0]['ratings'] == {'relevance': 0, 'coherence': 0, 'linguistic_resemblance': 5}
    assert primary[-1]['ratings'] == dict.fromkeys(ordinal.DOMAINS)
    assert primary[-1]['primary_status'] == 'UNAVAILABLE' and qc['original_rubric_pass'] is False
    assert submitted[0]['annotation_status'] == 'researcher' and submitted[0]['confidence'] == '0.85'


@pytest.mark.parametrize('problem', ['unknown', 'outofrange', 'NA', 'modified_hash'])
def test_intake_rejects_unknown_ambiguous_or_changed_values(monkeypatch, problem):
    package, rows, content, declaration = authored_intake(monkeypatch)
    if problem == 'unknown': rows[0]['review_id'] = 'not_assigned'
    elif problem == 'outofrange': rows[0]['relevance'] = '6'
    elif problem == 'NA': rows[0]['relevance'] = 'NA'
    else: content += b'\n'
    if problem != 'modified_hash':
        content = ordinal.review.encode_csv(rows, ordinal.recovery.INPUT_FIELDS)
        digest = hashlib.sha256(content).hexdigest()
        monkeypatch.setattr(ordinal, 'SUBMISSION_SHA', digest)
        declaration['received_submission_sha256'] = digest
    with pytest.raises(ValueError):
        ordinal.intake(package, content, declaration)


def test_no_condition_mapping_access_without_authorization_or_valid_lock(monkeypatch, tmp_path):
    monkeypatch.setattr(ordinal, 'verify_lock', lambda _: pytest.fail('Unauthorized analysis reached lock IO'))
    with pytest.raises(ValueError, match='Explicit root'):
        ordinal.analyze('authored', False)
    path = tmp_path/'lock.json'; path.write_text('{}')
    monkeypatch.setattr(ordinal, 'LOCK', path)
    monkeypatch.undo()
    monkeypatch.setattr(ordinal, 'LOCK', path)
    with pytest.raises(ValueError, match='Hash-bound'):
        ordinal.verify_lock('0'*64)


def test_no_complete_speaker_provenance_is_invented_by_arithmetic():
    result = ordinal.compute(fixture_rows())
    assert set(result) == {'schema', 'speakers', 'contexts', 'responses', 'domains'}
    assert 'human_reviewer' not in repr(result)


def test_actual_lock_path_is_map_free_preserves_unknown_provenance_and_rejects_later_change(monkeypatch, tmp_path):
    package, _, content, uncertainty = authored_intake(monkeypatch)
    monkeypatch.setattr(ordinal.review, 'PRIVATE_ROOT', tmp_path)
    for name in ('LOCK', 'LOCKED_ROWS', 'SUBMISSION', 'RECEIPT', 'UNCERTAINTY', 'HUMAN_DECLARATION', 'MAPPING'):
        monkeypatch.setattr(ordinal, name, tmp_path/(name.lower()+'.json'))
    ordinal.SUBMISSION.write_bytes(content)
    ordinal.RECEIPT.write_text('{}')
    monkeypatch.setattr(ordinal, 'RECEIPT_SHA', ordinal.sha(ordinal.RECEIPT))
    ordinal.UNCERTAINTY.write_text(json.dumps(uncertainty))
    ordinal.HUMAN_DECLARATION.write_text(json.dumps({'submission_sha256': ordinal.SUBMISSION_SHA,
        'human_authorship': 'AFFIRMED_BY_PRINCIPAL_RESEARCHER', 'blinded_review': 'AFFIRMED_BY_PRINCIPAL_RESEARCHER'}))
    amendment = tmp_path/'amendment.json'
    amendment.write_text(json.dumps({'schema': 'personaslm_english_primary_ordinal_analysis_amendment_v1',
        'inputs': {'received_submission_sha256': ordinal.SUBMISSION_SHA},
        'scale': {'actual_categories': list(range(6)), 'equal_intervals': False}}))
    declaration = tmp_path/'declaration.txt'; declaration.write_text('Authored explicit scale declaration, not real human evidence.')
    monkeypatch.setattr(ordinal, 'AMENDMENT_SHA', ordinal.sha(amendment))
    monkeypatch.setattr(ordinal, 'DECLARATION_SHA', ordinal.sha(declaration))
    for module, path_name, hash_module, hash_name in (
        (ordinal.archive, 'ANALYSIS', ordinal, 'TECHNICAL_SHA'),
        (ordinal.archive, 'REPRODUCTION', ordinal, 'REPRODUCTION_SHA'),
        (ordinal.archive.resume, 'PARENT_MANIFEST', ordinal.archive.resume, 'PARENT_SHA')):
        path = tmp_path/(path_name+'.json'); path.write_text('{}')
        monkeypatch.setattr(module, path_name, path); monkeypatch.setattr(hash_module, hash_name, ordinal.sha(path))
    bound_source = tmp_path/'authored_source.py'; bound_source.write_text('# authored fixture\n')
    monkeypatch.setattr(ordinal, 'sources', lambda: {str(bound_source): ordinal.sha(bound_source)})
    monkeypatch.setattr(ordinal.review, 'load_package', lambda *args: package)
    original_read = Path.read_bytes
    def guarded_read(path):
        assert path != ordinal.MAPPING, 'Protected map must never be opened during lock/intake'
        return original_read(path)
    monkeypatch.setattr(Path, 'read_bytes', guarded_read)
    result = ordinal.lock(amendment, ordinal.AMENDMENT_SHA, declaration, ordinal.DECLARATION_SHA)
    lock, primary, _ = ordinal.verify_lock(result['lock_sha256'])
    assert lock['protected_mapping_opened'] is False and lock['condition_effects_calculated'] is False
    assert lock['provenance']['independent_of_project'] is False
    assert lock['provenance']['detailed_exposure_competence_aids_and_annotation_dates'] == 'UNKNOWN_NOT_INVENTED'
    assert lock['provenance']['absence_of_prior_exposure_verified'] is False
    assert primary[-1]['ratings'] == dict.fromkeys(ordinal.DOMAINS)
    with pytest.raises(ValueError, match='no overwrite'):
        ordinal.lock(amendment, ordinal.AMENDMENT_SHA, declaration, ordinal.DECLARATION_SHA)
    bound_source.write_text('# changed after lock\n')
    monkeypatch.setattr(ordinal.archive, 'reproduce', lambda *args: pytest.fail('Changed lock reached raw/map analysis'))
    with pytest.raises(ValueError, match='Locked source/input changed'):
        ordinal.analyze(result['lock_sha256'], True)


def test_join_requires_exact_response_dossier_display_hash_and_case(monkeypatch):
    rows = fixture_rows(); plan = {'requests': []}; technical = {'rows': []}; raw = {}; visible = []; links = []; locked = []
    dossiers = {}
    for i, row in enumerate(rows):
        request_id = f'authored_request_{i}'; review_id = f'authored_blind_{i}'
        request = {k: row[k] for k in ('speaker_id', 'case_id', 'condition')}
        plan['requests'].append(dict(request, request_id=request_id))
        technical['rows'].append(dict(request, request_id=request_id, measurements={'latency_seconds': row['latency_seconds']}))
        dossiers[row['case_id']] = 'Authored identical dossier for '+row['case_id']
        record = {'review_id': review_id, 'outcome_status': 'GENERATED', 'dossier': dossiers[row['case_id']], 'response': 'Authored response.'}
        visible.append(record); raw[request_id] = {'latency_seconds': row['latency_seconds'], 'response': {'content': record['response']}}
        links.append({'review_id': review_id, 'request_id': request_id, 'case_id': row['case_id'],
                      'display_sha256': hashlib.sha256(ordinal.review.json_bytes(record)).hexdigest()})
        locked.append({'review_id': review_id, 'ratings': row['ratings']})
    monkeypatch.setattr(ordinal.delivery_bridge, 'case_lookup', lambda plan: dossiers)
    monkeypatch.setattr(ordinal.delivery_bridge, 'dossier', lambda text: text)
    package = {'rows': visible}; mapping = {'sealed_source_sha256': ordinal.TECHNICAL_SHA, 'rows': links}
    assert ordinal.joined_rows(package, locked, mapping, plan, technical, raw) == rows
    for field, value in (('response', 'Changed response'), ('dossier', 'Changed dossier')):
        changed = copy.deepcopy(package); changed['rows'][0][field] = value
        with pytest.raises(ValueError, match='display/response/case/dossier'):
            ordinal.joined_rows(changed, locked, mapping, plan, technical, raw)
    changed = copy.deepcopy(mapping); changed['rows'][0]['case_id'] = 'wrong_case'
    with pytest.raises(ValueError, match='display/response/case/dossier'):
        ordinal.joined_rows(package, locked, changed, plan, technical, raw)
