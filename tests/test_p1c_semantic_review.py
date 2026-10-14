"""Scientific registration and statistical fixtures only; no model inference."""
import copy
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_semantic_review as a
import p1c_boundary_review as b
import p1c_semantic_analysis as s


def test_every_original_masked_field_preserved_and_no_human_rating():
    originals={r['anonymous_response_id']:r for r in a.rows(a.SOURCE)}
    proposed=a.read(s.PRIMARY)
    assert len(originals)==len(proposed)==72
    for r in proposed:
        assert all(r[k]==v for k,v in originals[r['anonymous_response_id']].items())
        assert a.text_sha(r['raw_first_reply'])==r['first_reply_sha256']
        assert all(v=='' for k,v in r.items() if k.startswith('human_'))
        assert r['researcher_proposal_decision']==r['researcher_corrections']==r['researcher_review_timestamp']==''
        s.validate_rating({k:r['AI_'+k] for k in a.FIELDS})


def test_stage_a_snapshot_and_stage_b_prefix_offsets():
    for phase in ('stage_a','stage_b'):
        root=a.OUT/phase
        for name,digest in a.read(root/'freeze_manifest_v1.json')['files'].items():assert a.sha(root/name)==digest
    records=a.read(b.OUT/'ambiguous_boundary_review_UNCONFIRMED_v1.json')
    assert len(records)==8
    for r in records:
        raw=r['raw_full_continuation']
        assert raw[r['proposed_start']:r['proposed_end']]==r['proposed_evaluation_view']
        assert r['original_structural_status']=='AMBIGUOUS'
        assert r['researcher_boundary_decision']==r['researcher_id']==r['review_timestamp']==''
        assert a.text_sha(r['proposed_evaluation_view'])==r['proposed_view_sha256']


def test_unconfirmed_actual_packet_cannot_be_registered(tmp_path):
    target=tmp_path/'registration'
    with pytest.raises(ValueError,match='Explicit annotation'):
        s.register(s.PREP/'researcher_confirmation_request_v1.json',target)
    assert not target.exists()


def test_no_overwrite_stage_a_or_stage_b():
    with pytest.raises(ValueError):a.stage_a()
    with pytest.raises(ValueError):b.stage_b()


@pytest.fixture
def approval_fixture():
    # Test-only approval; never written to a scientific registration directory.
    x=s.template();x.update(decision='ADOPT_PRIMARY_AND_SECONDARY_AS_SENSITIVITY',reviewer_id='Yaxin_ZHENG',
        review_status='RESEARCHER_CONFIRMED',decision_source='researcher',confirmation_statement='SYNTHETIC UNIT TEST ONLY')
    return x


@pytest.mark.parametrize('field,value',[('reviewer_id',''),('review_status','UNCONFIRMED'),('decision_source','AI'),('primary_sha256','0'*64),('confirmation_statement','')])
def test_missing_or_mismatched_confirmation_rejected(approval_fixture,field,value):
    approval_fixture[field]=value
    with pytest.raises(ValueError):s.confirmed_rows(approval_fixture)


def test_explicit_correction_preserved_without_erasing_proposal(approval_fixture):
    approval_fixture['corrections']=[{'view':'primary','anonymous_response_id':'PC006','ratings':{'factual_consistency':'Correct'},'reason':'SYNTHETIC fixture alternative reading'}]
    r=next(r for r in s.confirmed_rows(approval_fixture)['primary'] if r['anonymous_response_id']=='PC006')
    assert r['ratings']['factual_consistency']=='Correct'
    assert r['original_AI_proposal']['AI_factual_consistency']=='Unverifiable'
    assert r['researcher_correction']['reason'].startswith('SYNTHETIC')


@pytest.mark.parametrize('metric,value',[('task_success',True),('response_relevance',2.5),('temporal_consistency','Not Applicable'),('component_coverage',float('nan')),('factual_consistency','PASS')])
def test_invalid_rating_does_not_enter_analysis(metric,value):
    r={k:a.read(s.PRIMARY)[0]['AI_'+k] for k in a.FIELDS};r[metric]=value
    with pytest.raises(ValueError):s.validate_rating(r)


def test_unverifiable_incidence_is_not_incorrect_or_assessed_accuracy():
    r={k:a.read(s.PRIMARY)[0]['AI_'+k] for k in a.FIELDS};r['factual_consistency']='Unverifiable'
    metrics=s.scalar_metrics(r)
    assert metrics['factual_consistency__Correct_incidence'][0]==0
    assert metrics['factual_consistency__Incorrect_incidence'][0]==0
    assert metrics['factual_consistency__Unverifiable_incidence'][0]==1
    assert metrics['factual_consistency__assessed_C_vs_I_sensitivity'][0] is None


def test_paired_statistics_reproducible_with_registered_weights_and_unknowns():
    spec=copy.deepcopy(a.read(s.PREP/'analysis_specification_v1.json'))
    joined=[]
    for cid,speaker in spec['cases'].items():
        for condition in spec['condition_order']:
            ratings={'factual_consistency':'Correct','temporal_consistency':'Unverifiable',
                     'response_relevance':5,'conversational_coherence':4,'task_success':1,
                     'component_coverage':1.0,'semantic_completeness':'YES'}
            joined.append({'case_id':cid,'condition':condition,'family':'SYNTHETIC_UNIT_FIXTURE','ratings':ratings})
    x=s.analysis_payload(joined,spec,replicates=20)
    assert x==s.analysis_payload(joined,spec,replicates=20)
    assert len({r['contrast'] for r in x['effects']})==16
    for r in x['effects']:
        assert r['eligible_cases']==12 and r['speaker_clusters']==6
        if r['metric']=='temporal_consistency__assessed_C_vs_I_sensitivity':
            assert r['estimate'] is None and r['evaluable_cases']==0
            assert len(r['unknown_bound_cluster_sensitivity']['leave_one_speaker_out_bounds'])==6
        else:assert r['estimate']==0


def test_signed_unknown_interaction_bounds_and_cluster_resampling():
    weights={'a':1,'b':-1,'c':-1,'d':1}
    cases=[{'case_id':str(i),'speaker_id':str(i//2),'values':{'a':1,'b':None,'c':0,'d':0}} for i in range(12)]
    result=s.stats.summarize(cases,weights,replicates=20)
    assert result['estimate'] is None and result['identification_bounds']==[0,1]
    sensitivity=s.bound_sensitivity(result,20)
    assert sensitivity==s.bound_sensitivity(result,20)
    assert all(r['identification_bounds']==[0,1] for r in sensitivity['leave_one_speaker_out_bounds'])
    assert sensitivity['bootstrap_bound_endpoints']=={'lower_percentiles':[0,0],'upper_percentiles':[1,1]}
