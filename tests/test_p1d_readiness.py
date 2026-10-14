import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import p1d_approval as approval
from p1d_design import CELLS, OUT, read, sha, render, check_case, WEIGHTS
from p1d_stimulus_preparation import DEST, semantic_checks
from p1d_registered_statistics import categorical_summary, paired_summary, paired_model_rows, model_contrast_bounds, checked_registry
from p1d_verifier_date_scope import check, challenge_bank


def test_registered_approval_is_plan_only_and_matches_original_seal():
    objects = approval.verify()
    record = read(approval.AUTH / 'researcher_plan_approval_corrected_v1.json')
    assert record['approval_objects_sha256'] == objects
    assert record['authorized_inference_requests'] == 0
    assert record['human_review_timestamp'] is None
    assert record['researcher_id'] == 'Yaxin_ZHENG'
    assert sha(record['correction_source']['path']) == record['correction_source']['sha256']


def test_registration_refuses_overwrite():
    with pytest.raises(FileExistsError):
        approval.register()


def test_approval_rejects_changed_source(tmp_path):
    seal = read(approval.SEAL)
    target = tmp_path / approval.SEAL
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(seal), encoding='utf-8')
    for path in {**seal['approval_objects'], **approval.EXPECTED}:
        dest = tmp_path / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(Path(path).read_bytes())
    with (tmp_path / approval.PACKET).open('ab') as f:
        f.write(b'changed')
    with pytest.raises(ValueError, match='Reviewed content changed'):
        approval.verify(tmp_path)


def test_development_revision_not_validation_and_no_human_approval():
    data = read(DEST / 'development_examples_v5.json')
    assert len(data['cases']) == 16
    assert not data['independent_validation']
    followups = [c for c in data['cases'] if c['family']=='context_followup']
    assert sum(c['target_entity']==c['persona_entity'] for c in followups) == 2
    for date_type in ('current','historical'):
        assert sorted(c['target_entity']==c['persona_entity'] for c in followups if c['date_type']==date_type) == [False,True]
    for c in data['cases']:
        assert check_case(c)
        assert c['human_validity_decision'] == ''
        assert semantic_checks(c)['semantic_neutrality'] == 'NOT_ESTABLISHED'


def test_native_tokens_prompts_and_shared_inputs_are_exact():
    cases={c['case_id']:c for c in read(DEST/'development_examples_v5.json')['cases']}
    rows=read(DEST/'development_prompts_v5.json')
    assert len(rows)==96 and len({(r['case_id'],r['condition']) for r in rows})==96
    from p1d_design import th
    for r in rows:
        c=cases[r['case_id']]
        assert r['prompt']==render(c,c['histories'][r['condition']]['text'])
        assert r['prompt_sha256']==th(r['prompt'])
        assert r['input_tokens']==len(r['input_token_ids'])
        assert r['context_fit_256'] and not r['generation_authorized']
    for cid in cases:
        group=[r for r in rows if r['case_id']==cid]
        for field in ('trusted_evidence_sha256','question_sha256','context_sha256','reference_sha256'):
            assert len({r[field] for r in group})==1
        assert len({r['input_tokens'] for r in group if r['condition']!='H_none'})==1


def test_historical_seal_unchanged():
    for path,h in read(approval.SEAL)['artifact_sha256'].items():
        assert sha(path)==h, path


def test_official_metadata_is_exact_not_model_validation():
    folder=DEST/'official_instruct_metadata'; record=read(folder/'provenance_v1.json')
    assert record['model_generations']==0 and not record['weights_downloaded']
    for f in record['files']:
        assert sha(folder/f['file'])==f['sha256']
    assert record['local_gguf_sha256'] is None
    assert record['eos_token']=='<|im_end|>'


def test_registered_weights_not_redefined():
    assert checked_registry()==WEIGHTS
    assert len(WEIGHTS)==16
    assert all(sum(w.values())==0 for w in WEIGHTS.values())


def test_categorical_estimands_keep_unknown_and_missing_distinct():
    s=categorical_summary(['Correct','Incorrect','Unverifiable','Missing','Not Applicable'],[True]*4+[False])
    assert s['eligible']==4 and s['inapplicable']==1
    assert s['assessed_only_accuracy']==.5
    assert s['label_incidence']['Correct']==.25
    assert s['correct_outcome_identification_bounds']==[.25,.75]
    assert s['counts']['Unverifiable']==s['counts']['Missing']==1
    with pytest.raises(ValueError, match='applicability'):
        categorical_summary(['Not Applicable'],[True])


def toy_rows():
    return [{'case_id':f'c{s}{j}','speaker_id':f's{s}',
             'values':dict(zip(CELLS,[0,0,1,1,0,0]))} for s in range(3) for j in range(2)]


def test_paired_cluster_resampling_and_unknown_bounds_reproducible():
    rows=toy_rows();rows[0]['values']['E1V1']=None
    a=paired_summary(rows,'E',repeats=40)
    assert a==paired_summary(rows,'E',repeats=40)
    assert a['eligible_cases']==6 and a['eligible_speakers']==3 and a['complete_cases']==5
    assert a['all_eligible_identification_bounds']==[11/12,1]
    assert a['complete_case_equal_evaluable_speaker_mean']==1
    assert len(a['leave_one_speaker_out'])==3
    with pytest.raises(ValueError, match='Duplicate'):
        paired_summary(rows+[rows[0]],'E',repeats=4)


def test_unknown_cells_not_renormalized_for_all_contrasts():
    for name,w in WEIGHTS.items():
        rows=toy_rows()
        for r in rows:
            r['values']={c:None for c in CELLS}
        s=paired_summary(rows,name,repeats=5)
        assert s['all_eligible_identification_bounds']==[sum(min(0,x) for x in w.values()),sum(max(0,x) for x in w.values())]
        assert s['complete_case_equal_evaluable_speaker_mean'] is None
        assert s['bootstrap_draws_without_evaluable_cases']==5


def test_limited_paired_model_contrasts_and_signed_bounds():
    base=toy_rows(); inst=copy.deepcopy(base[:2])
    for r in inst:
        r['values']['E1V1']=0
    rows=paired_model_rows(base,inst)
    assert len(rows)==2
    assert model_contrast_bounds(rows[0],'E')['complete_case_difference']==-.5
    rows[0]['instruct_values']['E1V1']=None
    assert model_contrast_bounds(rows[0],'E')['lower']==-.5
    assert model_contrast_bounds(rows[0],'E')['upper']==0
    inst[0]['speaker_id']='wrong'
    with pytest.raises(ValueError,match='Unmatched'):
        paired_model_rows(base,inst)


def test_claim_date_scope_and_task_delivery_are_separate():
    case=read(OUT/'development_examples_v3.json')['cases'][0]
    bank=challenge_bank(case)
    for f in bank:
        r=check(f['payload'],f['facts'],f['query'])
        assert r['factual']==f['authored_expected_factual'], f['id']
        assert r['task_success']==f['authored_expected_success'], f['id']
    old=next(f for f in bank if f['id']=='true_explicit_historical_answer')
    r=check(old['payload'],old['facts'],old['query'])
    assert r['factual']=='Correct' and not r['task_success']


def test_invalid_dates_abstain_instead_of_crashing_or_false_error():
    c=read(OUT/'development_examples_v3.json')['cases'][0]
    f=challenge_bank(c)[0]
    p=copy.deepcopy(f['payload'])
    p['assertions'][0]['claim_date']='2048-02-31'
    assert check(p,f['facts'],f['query'])['factual']=='Unverifiable'


def test_independent_candidates_balanced_but_not_frozen():
    from collections import Counter
    import p1d_independent_candidates_v2 as candidates
    data=read(candidates.DEST/'candidate_bank_v1.json')
    assert data['freeze_status']=='NOT_FROZEN'
    assert not data['algorithm_tuning_permitted']
    assert candidates.construct()==data['cases']
    assert candidates.validate(data['cases'])['unique_reference_reconstructions']==288
    for family in {c['family'] for c in data['cases']}:
        for date_type in ('current','historical'):
            cs=[c for c in data['cases'] if c['family']==family and c['date_type']==date_type]
            assert set(Counter(c['domain']['id'] for c in cs).values())=={9}
    assert all(c['semantic_validity_decision']=='' for c in data['cases'])
    old_ids={c['case_id'] for c in read(OUT/'development_examples_v3.json')['cases']}
    assert not old_ids & {c['case_id'] for c in data['cases']}


def test_independent_candidate_prompts_preserve_pairing_and_reference():
    import p1d_independent_candidates_v2 as candidates
    cs={c['case_id']:c for c in read(candidates.DEST/'candidate_bank_v1.json')['cases']}
    rows=read(candidates.DEST/'base_candidate_prompts_v1.json')
    assert len(rows)==1728 and len({r['candidate_request_id'] for r in rows})==1728
    from p1d_design import th
    for r in rows:
        assert r['prompt']==candidates.prompt(cs[r['case_id']],r['condition'])
        assert th(r['prompt'])==r['prompt_sha256']
        assert not r['generation_authorized']
        assert r['reference']==cs[r['case_id']]['required_components']
    for c in cs.values():
        rs=[r for r in rows if r['case_id']==c['case_id']]
        for k in ('question_sha256','trusted_evidence_sha256','fixed_context_sha256'):
            assert len({r[k] for r in rs})==1


def test_boundary_review_masking_and_blank_real_human_fields():
    import csv
    folder=DEST/'independent_measurement'
    with (folder/'boundary_review_blinded_v1.csv').open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);rows=list(reader);fields=reader.fieldnames
    assert len(rows)==72 and len({r['review_id'] for r in rows})==72
    assert not {'condition','original_parser_status','first_reply','model','prior_rating'} & set(fields)
    from p1d_design import th
    for r in rows:
        assert th(r['unchanged_raw_continuation'])==r['raw_text_sha256']
        assert r['reviewer_id']==r['accepted_spans_json']==r['actual_submission_timestamp']==''
    assert read(folder/'provenance_v1.json')['human_ratings']==0


def test_budget_proposal_and_model_subset_do_not_authorize_generation():
    model=read(DEST/'model_comparison_estimands_v1.json')
    budget=read(DEST/'output_budget_diagnostic_proposal_v1.json')
    assert model['instruct']['cases']==48 and model['extra_base_requests']==0
    assert model['instruct']['matched_cells']==list(CELLS)
    assert set(model['instruct']['family_counts'].values())=={12}
    assert budget['base_requests_if_separately_authorized']==8*6*3
    assert budget['authorized_requests']==0 and model['authorized_inference_requests']==0
    assert not budget['included_in_main_2016_targets']


def test_blank_boundary_form_cannot_be_registered_as_review():
    from p1d_independent_boundary_import import validate_returned,read_rows,REVIEW
    with pytest.raises(ValueError,match='reviewer identity'):
        validate_returned(read_rows(REVIEW))


def test_boundary_import_validates_offsets_and_never_infers_adoption():
    from p1d_independent_boundary_import import validate_returned,read_rows,REVIEW
    original=read_rows(REVIEW)[:1]
    r={**original[0],'reviewer_id':'SYNTHETIC_TEST_ONLY','reviewer_independence_declaration':'AUTHORED SOFTWARE TEST, NOT A REAL REVIEW',
       'boundary_disposition':'UNIQUE_DEFENSIBLE_SPAN','answer_delivered':'UNCERTAIN',
       'supporting_boundary_cues':'Authored test field, no empirical annotation.','accepted_spans_json':'[[0,1]]'}
    result=validate_returned([r],original)
    assert result[0]['researcher_adoption']=='NOT_INFERRED'
    assert result[0]['actual_submission_timestamp']==''
    with pytest.raises(ValueError,match='outside raw'):
        validate_returned([{**r,'accepted_spans_json':'[[0,999999]]'}],original)
    with pytest.raises(ValueError,match='Immutable'):
        validate_returned([{**r,'unchanged_raw_continuation':'changed'}],original)
    with pytest.raises(ValueError,match='Invalid character'):
        validate_returned([{**r,'accepted_spans_json':'[1]'}],original)


def test_ordinal_ceiling_and_paired_rank_diagnostics():
    from p1d_ordinal_statistics import distribution,paired_sign_rank,threshold_views
    assert distribution([5,5,None])['zero_observed_variance']
    rows=[{'case_id':str(i),'speaker_id':str(i//2),'values':dict.fromkeys(CELLS,3)} for i in range(4)]
    for r,value in zip(rows,[4,2,3,None]):r['values']['E1V1']=value
    r=paired_sign_rank(rows,'E1V1','E0V0')
    assert (r['positive'],r['negative'],r['ties'],r['unresolved_pairs'])==(1,1,1,1)
    assert r['positive_rank_sum']==r['negative_rank_sum']==1.5 and r['p_value'] is None
    views=threshold_views(rows)
    assert views['score_at_least_4'][0]['values']['E1V1']==1
    assert views['score_at_least_4'][3]['values']['E1V1'] is None
    with pytest.raises(ValueError):distribution([6])


def test_current_candidates_preserve_validity_and_explicit_case_worlds():
    from collections import defaultdict
    from p1d_candidate_material_repair import render
    folder=Path('docs/validation/p1d/independent_candidates_v4')
    cases=read(folder/'candidate_bank_v1.json')['cases']
    by_id={c['case_id']:c for c in cases}
    other_speakers=defaultdict(set)
    for c in cases:
        other_speakers[c['other_person']].add(c['speaker_id'])
        assert c['scenario_id']==c['case_id']
        assert c['semantic_validity_decision']==''
    assert len(other_speakers)==144 and all(len(v)==1 for v in other_speakers.values())
    native=read(folder/'native_tokenizer_validation_v1.json')
    assert native['active_matches']==native['control_matches']==288
    assert native['context_fit_256'] and native['new_generations']==0
    from p1d_design import th
    rows=read(folder/'base_candidate_prompts_v1.json')
    assert len(rows)==1728
    for r in rows:
        c=by_id[r['case_id']]
        assert r['prompt']==render(c,r['condition'])
        assert th(r['prompt'])==r['prompt_sha256']
        assert th(c['trusted_evidence'])==r['trusted_evidence_sha256']
        assert th(c['question'])==r['question_sha256']
    for v in ('v1','v2','v3','v4'):
        manifest=read(f'docs/validation/p1d/independent_candidates_{v}/candidate_provenance_manifest_v1.json')
        for p,h in manifest['artifact_sha256'].items():assert sha(p)==h


def test_official_template_discrepancy_not_hidden():
    folder=DEST/'official_instruct_metadata'
    inspection=read(folder/'template_consistency_inspection_v1.json')
    assert not inspection['byte_equal'] and not inspection['rendered_equivalence_tested']
    assert inspection['standalone_sha256']==sha(folder/'chat_template.jinja')
