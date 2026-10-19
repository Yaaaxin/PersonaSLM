"""Seal completed P1 milestones and append truthful research history. No inference."""
import hashlib
import json
from pathlib import Path
import random
import subprocess
import p1_measurement_run as r
from p1d_design import csvwrite


def main():
    out=r.OUT
    r.s.require(not (out/'reproducibility_manifest_v1.json').exists(),'Already sealed; do not repeat')
    tests=r.s.load(out/'targeted_regression_v1.json')
    r.s.require(tests['exit_code']==0 and tests['passed']==71,'Required targeted tests did not pass')
    ledger=r.cumulative()
    r.s.require(ledger['attempted']=={'A_C0':32,'B_FACTORIAL':0,'C_DIAGNOSTIC':16},'Unexpected inference inventory')
    seal_path=Path('docs/validation/p5/oracle_diagnostic_v1/reproducibility_manifest_v1.json')
    previous=r.s.load(seal_path)
    for p,h in previous['artifact_sha256'].items():r.s.require(r.s.sha256(Path(p))==h,'Prior artifact changed before append: '+p)
    log=Path('docs/research_development_log.md');old=log.read_bytes()
    r.s.require(r.s.sha256(log)==r.s.load(out/'preservation_baseline_v1.json')['log_sha256'],'Research log changed unexpectedly')
    snapshot=out/'research_development_log_before_v1.md'
    with snapshot.open('xb') as f:f.write(old)
    # Truly separate human panels; no AI scores, reference truth in fidelity panel,
    # condition labels, or invented reviewer identities.
    source=[]
    for category in ('A_C0','C_DIAGNOSTIC'):
        for x in r.s.load(out/category/'measurement_v1'/'masked_evidence_v1.json'):
            source.append((category,x))
    random.Random(731801).shuffle(source);quality=[];fidelity=[];mapping=[];states=[]
    for i,(category,x) in enumerate(source):
        pid=f'PR{i+1:03d}'
        mapping.append({'panel_id':pid,'original_review_id':x['review_id'],'category':category,'raw_sha256':x['raw_sha256']})
        quality.append({'panel_id':pid,'question':x['question'],'evaluation_date':x['reference_date'],
            'trusted_evidence':x['trusted_evidence'],'reference_components':x['reference'],'raw_output':x['raw_output'],
            'native_stop':x['native_stop'],'factual':'','temporal':'','task_success':'','delivered':'','supported':'',
            'semantic_completeness':'','relevance':'','coherence':'','boundary_judgment':'','evidence_citations':'',
            'uncertainty':'','reviewer_id':'','independent_before_AI_key':'','human_timestamp':None})
        fidelity.append({'panel_id':pid,'question':x['question'],'target_profile':x['fidelity_target'],'raw_output':x['raw_output'],
            'linguistic_fidelity':'','LF_opportunity':'','LF_evidence':'','behavioral_fidelity':'','BF_opportunity':'',
            'BF_evidence':'','acknowledgment_observed':'','response_act_order':'','alternative_score':'',
            'uncertainty':'','reviewer_id':'','independent_before_AI_key':'','human_timestamp':None})
        a=next(z for z in r.s.load(out/category/'measurement_v1'/'AI_proposals_UNCONFIRMED_v1.json') if z['review_id']==x['review_id'])
        states.append({'review_id':x['review_id'],'factual_state':'SCORED','temporal_state':'INTERPRETATION_UNCERTAIN' if a['temporal']=='Unverifiable' else 'SCORED',
            'boundary_state':'AI_PROPOSED_RECOVERABLE_NOT_HUMAN_CERTIFIED','original_structural_status':x['original_structural_status']['status'],
            'LF_state':a['fidelity_state']['linguistic'],'BF_state':a['fidelity_state']['behavioral'],
            'missing':False,'empty_response':False,'temporal_applicable':True,
            'stale_endpoint_state':'NOT_APPLICABLE_TO_CALIBRATION_OR_OUTPUT_INSTRUCTION_DIAGNOSTIC',
            'researcher_confirmation':''})
    csvwrite(out/'independent_quality_panel_v1.csv',quality)
    csvwrite(out/'independent_fidelity_panel_v1.csv',fidelity)
    r.s.save(out/'protected_review_panel_mapping_v1.json',mapping)
    r.s.save(out/'measurement_state_register_v1.json',states)
    # A non-circular index binds completed reports and actual pending reviews.
    reports=[Path('docs/P1_C0_measurement_calibration_report_v1.md'),Path('docs/P1_measurement_diagnostic_and_decision_report_v1.md')]
    review=[out/'A_C0/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv',out/'C_DIAGNOSTIC/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv',
            out/'consolidated_researcher_review_index_v1.csv',out/'fidelity_construct_audit_v1.json']
    r.s.save(out/'final_decision_bindings_v1.json',{'status':'SCIENTIFIC_NO_GO_NOT_PERMISSION_REJECTION',
        'registered_utc':r.s.b.utc_now(),'report_sha256':{str(p):r.s.sha256(p) for p in reports},
        'pending_review_sha256':{str(p):r.s.sha256(p) for p in review},'human_confirmation':None,
        'review_provenance':'Researcher may adopt/correct AI proposals; no independent human judgment inferred.',
        'existing_development_authorization':'Remains active; no need to repeat it. No further batch scheduled while readiness remains inadequate.',
        'confirmatory_freeze':'Not requested as ready and not adopted; future protocol/material/execution approval remains mandatory.'})
    now=r.s.b.utc_now()
    entry=f'''

## {now} — P1 accelerated measurement calibration and bounded diagnostic

Maintainer: Yaxin ZHENG. Phase: P1 only. Research questions: true C0 adequacy,
metric discrimination and automatic-scoring feasibility for the core S/F/H programme.
Research Protocol v1.1 and adopted supplements are unchanged; v1.2 remains proposed.

The researcher authorized160 new development attempts with independent32/80/48 caps,
replacing an unexecuted proposal, and explicitly reconfirmed continuation after releasing
memory. Initial read-only memory observations were below the unchanged3GiB gate;
no generation occurred until complete file/runtime/resource preflight passed. No
unrelated process was accessed or stopped and no model configuration was substituted.

Constructed32 C0 calibration cases and a disjoint eight-case80-request S/F/H bank
before observing calibration outputs. Shared four task ancestors, five normalized
question templates and two authored profile types remain limitations. Native GGUF,
official tokenizer and live server arrays agree. All sixteen active/control length
pairs match; controls remain diagnostic, not semantically neutral.

Executed32 C0 requests:32 success,0 failure/retry;21 EOS and11 budget stops.
AI proposals:11/32 task success,29/32 complete forms,29/64 supported components.
Dated comparison task success0/8. The 80-95% diagnostic target was not met; no
case was removed, no own-C0-based factorial selection occurred, and no target chasing
was used. Item-level AI proposals remain unconfirmed.

Registered and executed one16-request category-C diagnostic on calibration00-07,
with unchanged evidence/questions and concise versus date-slot output instructions.
All16 succeeded with EOS and complete answer forms. AI task success2/8 versus1/8;
both fail the predeclared all-family readiness rule. Paired original C0 success was1/8.
No instruction is adopted for the pilot. B_FACTORIAL remains scientifically NO-GO.
Total attempts48; remaining A0/B80/C32 =112, no category transfers or retries.

Frozen automatic scorer v1 shared restricted FC/TC assignment and missed explicit
typed labels. Kept v1 and added v2 with separate temporal checks, label-syntax handling
and negation deferral. No original rating/output was overwritten. Full metric-specific
confusion/coverage and original-parser sensitivity remain available. BF has zero
ordering opportunities, not zero fidelity. Existing authored fidelity counterexamples
reveal a presence-versus-order opportunity mismatch requiring prospective review.
The diagnostic's pooled16-output iid interval was preserved in summary_v1 but
superseded by summary_v2 with eight whole-case resampling. No population effect claim.

P5 is closed as completed development engineering/science with its prior2/8 versus8/8
AI proposals still pending confirmation. Evidence package differences do not identify
pure retrieval, sufficiency or Persona effects. No new P5/P2/P3/P4/P6 work or inference.
P0 frozen, P1 active/measurement-blocked, P2/P3/P4/P6 paused. ESCP negative results remain.

Commands: p1_measurement_materials.py; p1_measurement_run.py preflight/run/audit for
A_C0 and C_DIAGNOSTIC; p1_measurement_review.py; p1_calibration_annotation.py;
p1_diagnostic_annotation.py; p1_measurement_analysis.py; closeout/finalize scripts.
The cumulative ledger, exclusive attempt claims, hash-chained raw HTTP journals,
native token logs, source snapshots and full configurations preserve every request.
Four early material-build failures and an initial3-failed/33-passed targeted suite
were corrected before inference. Subsequent36/38/39/44 test passes are documented.
Final applicable suite:71 passed,0 failed (exact command/output in targeted_regression_v1).

Reports: docs/P1_C0_measurement_calibration_report_v1.md and
docs/P1_measurement_diagnostic_and_decision_report_v1.md, one combined engineering/
scientific report per milestone. Machine artifacts: docs/validation/p1/measurement_pilot_v1/.
Prepared paired estimators were validated only with synthetic fixtures; there are no
actual C3-C0 or other factorial estimates. Independent quality/fidelity panels contain
no AI scores or fabricated reviewers. Human adoption and independent evaluation are
distinct. Remaining meaningful step: independent masked measurement review and
prospective rubric/task-readiness resolution before any confirmatory freeze.

No Git commit/push, training, main-cohort inference, independent-validation inference,
human rating fabrication, algorithm novelty claim or manuscript-readiness claim.
'''
    with log.open('ab') as f:f.write(entry.encode('utf-8'))
    r.s.require(log.read_bytes().startswith(old),'Historical log prefix changed')
    for p,h in previous['artifact_sha256'].items():
        if p!='docs/research_development_log.md':r.s.require(r.s.sha256(Path(p))==h,'Historical source modified: '+p)
    preservation={'previous_seal_path':str(seal_path),'previous_seal_sha256':r.s.sha256(seal_path),
        'unchanged_artifacts':len(previous['artifact_sha256'])-1,'append_only_log':str(log),
        'old_log_sha256':hashlib.sha256(old).hexdigest(),'old_log_bytes':len(old),
        'preserved_log_snapshot':str(snapshot),'new_log_sha256':r.s.sha256(log),
        'old_prefix_verified':True,'historical_outputs_and_protocols_changed':False}
    r.s.save(out/'historical_preservation_v1.json',preservation)
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    r.s.require(diff.returncode==0,'Git diff whitespace check failed')
    files=list(out.rglob('*'))+list(r.ROOT.rglob('*'))+reports+[log]
    files+=list(Path('tools').glob('p1_measurement*.py'))+[Path('tools/p1_calibration_annotation.py'),Path('tools/p1_diagnostic_annotation.py'),Path('tools/p1_factorial_descriptive.py')]
    files+=[Path('tests/test_p1_measurement_pilot.py'),Path('tests/test_p1_factorial_descriptive.py')]
    files=sorted({p for p in files if p.is_file() and '__pycache__' not in p.parts})
    json_count=csv_count=0
    import csv
    for p in files:
        if p.suffix=='.json':r.s.load(p);json_count+=1
        elif p.suffix=='.csv':
            with p.open(encoding='utf-8',newline='') as f:list(csv.DictReader(f))
            csv_count+=1
    manifest={'version':'p1_measurement_reproducibility_v1','maintainer':'Yaxin ZHENG','sealed_utc':r.s.b.utc_now(),
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_status':subprocess.check_output(['git','status','--short'],text=True),'git_diff_check':diff.stdout+diff.stderr,
        'execution_scope':ledger,'scientific_status':'NO_GO_FACTORIAL_AND_CONFIRMATORY','researcher_adopted_semantic_ratings':0,
        'historical_preservation':preservation,'targeted_tests':tests,'valid_JSON':json_count,'valid_CSV':csv_count,
        'artifact_sha256':{p.as_posix():r.s.sha256(p) for p in files},
        'publication_scope':'Development measurement evidence only; no factorial findings, novelty or independent validation.'}
    target=out/'reproducibility_manifest_v1.json';r.s.save(target,manifest)
    print(json.dumps({'sealed_artifacts':len(files),'valid_json':json_count,'valid_csv':csv_count,'tests_passed':tests['passed'],
        'attempts':ledger['total_attempted'],'remaining':ledger['total_remaining'],'reproducibility_sha256':r.s.sha256(target)},indent=2))


if __name__=='__main__':main()
