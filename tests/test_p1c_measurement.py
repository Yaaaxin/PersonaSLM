"""Offline tests: no model completion is executed."""
import copy
import csv
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_measurement as m


def test_review_retains_pre_generation_ids_and_order():
    plan=m.c.load(m.c.p.MANIFEST)
    rows=m.frozen_review_order(plan)
    assert len(rows)==72
    assert rows[0]['anonymous_response_id']=='PC001'
    assert rows[0]['request_identity']==['p1c_05_current','R0T0']
    assert rows[-1]['anonymous_response_id']=='PC072'
    assert m.PRESENTATION_SEED==715005


def test_review_rejects_wrong_treatment_join():
    plan=copy.deepcopy(m.c.load(m.c.p.MANIFEST))
    plan['requests'][42]['condition']='R1T1'
    with pytest.raises((ValueError,RuntimeError,AssertionError)):
        m.frozen_review_order(plan)


def test_review_refuses_existing_destination(tmp_path):
    with pytest.raises(FileExistsError):
        m.prepare(tmp_path)


def test_real_masked_package_preserves_units_applicability_and_blank_ratings():
    root=Path('docs/validation/p1c/calibration_v1/measurement_v1')
    with (root/'semantic_scoring_view_v1.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    audit=m.c.load(root/'execution_integrity_v1.json')
    native={r['request_key']:r['result'] for r in audit['rows']}
    mapping={r['anonymous_response_id']:r for r in m.c.load(root/'protected_treatment_mapping_v1.json')['rows']}
    assert len(rows)==len(mapping)==len(native)==72
    assert len({r['anonymous_case_id'] for r in rows})==12
    assert not {'condition','factor_assignment','frozen_structural_status','raw_full_continuation','native_termination'}.intersection(rows[0])
    for row in rows:
        original=native[mapping[row['anonymous_response_id']]['request_key']]
        assert row['raw_first_reply']==original['parsed_response']
        assert m.d.text_hash(row['raw_first_reply'])==row['first_reply_sha256']==original['first_reply_sha256']
        assert all(value=='' for key,value in row.items() if key.startswith('human_'))
        assert row['researcher_confirmation']==row['reviewer_id']==row['review_timestamp']==''
        for metric,value in original['frozen_request']['applicability'].items():
            if metric!='structural_status':assert row['applicable_'+metric]==str(value)
        assert row['applicable_persona_fidelity']=='False'


def test_frozen_review_file_hashes_and_optional_notes_are_not_human_ratings():
    root=Path('docs/validation/p1c/calibration_v1/measurement_v1')
    for name,digest in m.c.load(root/'review_integrity_v1.json')['files'].items():
        assert m.d.sha(root/name)==digest
    support=Path('docs/validation/p1c/calibration_v1/review_support_v1')
    with (support/'AI_review_observations_UNCONFIRMED_v1.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==72
    for row in rows:
        assert row['status']=='UNCONFIRMED_ANALYTICAL_OBSERVATION'
        assert row['human_decision']==row['human_corrections']==row['reviewer_id']==row['review_timestamp']==''
        assert m.d.text_hash(row['model_span_quotation'])==row['first_reply_sha256']
        assert len(json.loads(row['reference_fact_ids']))==len(json.loads(row['trusted_source_quotations']))
