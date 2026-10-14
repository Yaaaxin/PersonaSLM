"""Seal approved P1c analysis and additive research records without inference."""
from collections import Counter
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import statistics
import subprocess
import p1c_semantic_review as a
import p1c_annotation_review_check as check
import p1c_confirmed_reporting as reporting
import p1c_calibration as calibration

ROOT=reporting.ROOT
RESULT=Path('results/p1c_annotation_gate/v1')


def sealed(directory,name):
    m=a.read(directory/name)
    for f,digest in m['files'].items():a.require(a.sha(directory/f)==digest,'Sealed file differs: '+f)
    return m


def preserve():
    baseline=a.read(RESULT/'baseline.json')
    changed=[p for p,d in baseline['files'].items() if a.sha(p)!=d]
    a.require(set(changed)<={'docs/research_development_log.md'},'Entry file changed: '+str(changed))
    a.require(Path('docs/research_development_log.md').read_bytes().startswith((RESULT/'development_log.before.md').read_bytes()),'Log not append-only')
    historical=a.read('results/p1c_final_review/v1/baseline.json')['historical_artifacts']
    for p,d in historical.items():a.require(a.sha(p)==d,'Historical output changed: '+p)
    check.verify()
    original=a.read(a.ROOT/'measurement_v1/execution_integrity_v1.json')
    actual=calibration.audit()
    a.require(actual==original,'Execution reconstruction changed')
    a.require(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==baseline['head'],'Git HEAD changed')
    return {'entry_source_files':len(baseline['files']),'allowed_append_only_changes':changed,
        'historical_files_unchanged':len(historical),'actual_raw_run_reconstruction_equal':True,
        'original_http_responses':actual['http_response_bytes_verified'],
        'actual_model_backend_hash_verification':'PASS at task entry; immutable evidence in source_verification_01.json',
        'packet_hash':a.sha(check.PACKET),'git_head':baseline['head']}


def measurement_report(d,analyses,boundaries):
    def eff(group,metric,c):return next(r for r in d[group] if r['metric']==metric and r['contrast']==c)
    def pp(v):return 'unidentified' if v is None else f'{100*v:+.2f}'
    def interval(v):return 'not identified' if v is None else '['+', '.join(pp(x) for x in v)+']'
    lines=[]
    for c in a.read('docs/validation/p1c/final_review_v1/estimand_registry_proposed_v1.json')['weights']:
        delta=eff('paired_boundary_sensitivity_effect_changes','factual_consistency__Correct_incidence',c)
        temporal=eff('paired_boundary_sensitivity_effect_changes','temporal_consistency__Incorrect_incidence',c)
        structural=eff('structural_effects','AMBIGUOUS',c)
        lines.append(f"| {c} | {pp(delta['estimate'])} | {interval(delta['percentile_cluster_interval'])} | {pp(temporal['estimate'])} | {pp(structural['estimate'])} |")
    btable=[]
    for r in boundaries:
        rating=r['reviewed_secondary_ratings']
        btable.append(f"| {r['anonymous_response_id']} | {r['native_termination']['stop_type']} | {r['actual_generated_tokens']} | {rating['factual_consistency']} | {rating['temporal_consistency']} | {rating['task_success']} |")
    return '''# P1c confirmed boundary and missingness robustness v1

Maintainer: Yaxin ZHENG. This report uses the researcher-adopted primary and secondary views, with no resampling of model outputs and no new ratings. Original response_status_v1 remains frozen.

## Structural and semantic cross-tabulation

All 72 requests succeeded: 64 CROSS_TURN and eight AMBIGUOUS, zero COMPLETE/TRUNCATED. All 64 identifiable first replies are semantically complete; their factual labels are 43 Correct, 20 Incorrect and one Unverifiable. Their temporal labels are 43 Correct, 15 Incorrect and six Unverifiable. Thus cross-turn continuation is compatible with either a correct or wrong complete first answer. It is not automatic factual failure. The eight AMBIGUOUS units retain primary factual/temporal Unverifiable, uncertain task/completeness and unscorable ordinal/component ratings.

All 64 CROSS_TURN outputs reached the token budget. Six ambiguous outputs also reached it; two ended by EOS. Budget termination is therefore compatible with 64 complete first replies. Both EOS outputs remain structurally ambiguous. Native termination and first-reply validity are separate observations. No causal output-budget claim follows without a controlled budget/template experiment.

## Eight sensitivity-only prefixes

Every candidate is a byte-preserved substring of the raw continuation, with raw/prefix hashes, parser trace and excluded tail in the immutable source. A section heading supports the proposed cut but is not a native turn token; document-continuation interpretations remain. All eight primary structural statuses stay AMBIGUOUS. The accepted sensitivity does not certify unique boundaries.

| ID | Native stop | Generated tokens | Secondary factual | Secondary temporal | Secondary task (1/0) |
| --- | --- | ---: | --- | --- | ---: |
'''+ '\n'.join(btable)+'''

The [confirmed eight-item export](validation/p1c/confirmed_semantic_v1/robustness_exports/eight_confirmed_sensitivity_records_v1.csv) retains original blank proposal-confirmation fields as source history and appends explicit registered scope. It does not pretend those original fields were independently entered by the researcher. PC023's two revised ordinal scores are included only in the accepted secondary view.

## All registered measurement-effect differences

Compute secondary-minus-primary **within output**, then apply the original contrast within case, then equal speaker means. This avoids subtracting means from differently selected assessable subsets. All values below are percentage points. F-C denotes Correct-label incidence, T-I temporal Incorrect-label incidence. Intervals are 10,000-draw whole-speaker bootstrap sensitivity, seed 715004, not guaranteed population confidence coverage.

| Contrast | Change in F-C effect | Resampling interval for change | Change in T-I effect | Primary AMBIGUOUS incidence effect |
| --- | ---: | --- | ---: | ---: |
'''+ '\n'.join(lines)+'''

R/T/RxT factual Correct-incidence effects move by +4.17/-4.17/+8.33 points, respectively, yielding zero secondary means. This is a property of these measurement views and six synthetic clusters, not proof that the primary is wrong or that the secondary is true. Some case contributions still cancel. Temporal Incorrect-incidence effects move by +4.17/-4.17/-8.33 points. Do not select a boundary rule according to these signs.

## Unknown outcomes and identification limits

Primary factual/task uncertainty includes eight unresolved boundaries and one interpretation issue. Temporal uncertainty additionally includes five entity/interval attribution issues. Secondary factual/task uncertainty leaves PC006; temporal uncertainty remains on nine units. No U label is recoded as a factual error. No unknown ordinal score is set to zero. All 72 outcomes remain eligible.

For scalar sensitivities, a case contrast is point identified only when every required nonzero-weight cell is known. Otherwise its original signed weights and the endpoint range produce lower/upper bounds. Speaker means retain both cases; no surviving-cell reweighting. Secondary-minus-primary scalar differences remain unknown if either value is unknown. Their conservative bounds span possible differences rather than fabricating paired values. Resampled bound endpoints and leave-one-speaker-out bounds are supplied separately from point-estimate intervals.

Categorical label incidence includes Unverifiable as an observed category, while C-versus-I sensitivity excludes U from assessability and discloses the selected cases. These represent different estimands. Null numeric scores are reason-preserving unscorability/uncertainty, not absent researcher decisions. Administrative missing confirmations are zero.

Six purposive clusters and only two speakers per task family limit all population interpretation. Apparent ambiguity differences can influence evaluation coverage; the study does not establish a latent response-boundary mechanism. No confirmatory significance tests or new endpoint hierarchy were introduced.

## Algorithmic Opportunity Assessment

**Observed Failure Modes:** headings can precede extra generated content, and native EOS does not guarantee a single reply. **Existing Methods and Published Prior Art:** the [offline baseline report](P1c_offline_boundary_baseline_assessment_v1.md) compares native stopping, literal roles, headings and a code-fence guard, and reviews constrained generation and verification. **Potential Algorithmic Improvements:** cautious abstention is a known engineering candidate; no original algorithm is established. **Validation Feasibility:** independent span adjudication and held-out quoted-role/heading examples are necessary, followed by separately authorized template/stop experiments where useful. **Publication Value:** measurement robustness can improve the empirical paper, but recovery of the eight inspected prefixes is not independently validated accuracy or publication readiness.
'''


def main():
    out=ROOT/'robustness_exports';final=ROOT/'reproducibility_manifest_v1.json'
    a.require(not out.exists() and not final.exists(),'Cannot overwrite closeout')
    records,analyses,joined=reporting.checked_inputs()
    dm=sealed(ROOT/'paired_diagnostics','manifest_v1.json')
    a.require(dm['reconstructed_twice'],'Diagnostics not reconstructed twice')
    sealed(ROOT/'exports','manifest_v1.json')
    d=a.read(ROOT/'paired_diagnostics/paired_measurement_diagnostics_v1.json')
    for name in ('structural_effects','paired_boundary_sensitivity_effect_changes'):
        a.write_csv(out/(name+'_summary_v1.csv'),[{k:r[k] for k in ('metric','contrast','estimate','eligible_cases','evaluable_cases','speaker_clusters','identification_bounds','percentile_cluster_interval')} for r in d[name]])
        a.write_csv(out/(name+'_case_contrasts_v1.csv'),[{'metric':r['metric'],'contrast':r['contrast'],**x} for r in d[name] for x in r['case_table']])
        a.write_csv(out/(name+'_speaker_sensitivity_v1.csv'),[{'metric':r['metric'],'contrast':r['contrast'],**x} for r in d[name] for x in r['speaker_table']])
    a.write_csv(out/'structural_semantic_crosstabs_v1.csv',d['primary_structure_semantic_crosstabs'])
    boundaries=a.read(a.ROOT/'semantic_integrity_v1/boundary_sensitivity_table_v1.json')
    secondary={r['anonymous_response_id']:r for r in records['secondary']}
    a.write_csv(out/'eight_confirmed_sensitivity_records_v1.csv',[{**r,
        'registered_reviewer_id':'Yaxin_ZHENG','registered_review_status':'RESEARCHER_CONFIRMED',
        'registered_scope':'SENSITIVITY_ONLY_NOT_UNIQUE','registered_ratings':secondary[r['anonymous_response_id']]['ratings'],
        'registered_human_timestamp':None,'primary_structural_status_unchanged':True} for r in boundaries])
    doc=Path('docs/P1c_confirmed_measurement_robustness_v1.md')
    a.require(not doc.exists(),'Cannot overwrite report')
    doc.write_text(measurement_report(d,analyses,boundaries),encoding='utf-8')
    # Reconstruct planning numbers from assumptions and original latency records.
    precision=a.read('docs/validation/p1c/independent_validation_proposal_v1/precision_sensitivity_v1.json')
    for row in precision['rows']:
        se=row['case_contrast_SD']*math.sqrt((1+row['assumed_ICC'])/(2*row['speakers']))
        a.require(math.isclose(row['normal_95_halfwidth'],1.96*se,rel_tol=1e-12),'Precision calculation differs')
        a.require(math.isclose(row['illustrative_six_test_bonferroni_halfwidth'],statistics.NormalDist().inv_cdf(1-.05/12)*se,rel_tol=1e-12),'Multiplicity planning differs')
    tests=a.read(RESULT/'tests_regression_02.json');a.require(tests['exit_code']==0,'Regression tests failed')
    a.require('85 passed' in tests['stdout'],'Unexpected test summary')
    verification=preserve()
    now=datetime.now(timezone.utc).isoformat()
    with Path('docs/research_development_log.md').open('a',encoding='utf-8',newline='\n') as f:
        f.write(f'''\n\n## {now} — P1c researcher adoption, official exploratory analysis and offline baselines\n\nMaintainer: Yaxin ZHENG. Software-recorded time only; human review time remains unknown. Entry HEAD {verification['git_head']}; working tree already contained previous uncommitted semantic review/integrity work.\n\nVerified exact packet 4989e36d8d862c5995221b470adb8c9620ba7023ffc8ebf9d492cda18f6fc817 and all source versions, six primary ordinal corrections/five records, two PC023 sensitivity corrections. Recomputed construct concordance and preserved all original fields. While this task was running, Yaxin ZHENG explicitly approved Option 1. Saved the actual statement, registered 72 researcher-adopted AI-assisted primary scores plus the sensitivity view, without fabricated human timestamps or independent reviewers. Registration preceded treatment joining. No repeated approval gate remains for this snapshot.\n\nUsed existing sealed tools/p1c_integrity_registration.py and unchanged 16-weight statistics. Both primary and secondary analyses reconstructed twice with exact numerical equality (10,000 whole-speaker draws, seed 715004). Primary factual/temporal Correct incidence: R -4.17pp, T +4.17pp, RxT -8.33pp; all become zero under sensitivity prefixes. Primary task R/T bounds [-12.50,+16.67]pp and RxT [-41.67,+16.67]pp remain unidentified; assessed-only contrasts are separate. Retained all categories, case contributions, six-cluster intervals/LOSO, ordinal thresholds and nested-family heterogeneity. No significance or pure-mechanism claims.\n\nNew tools: p1c_annotation_review_check.py, p1c_boundary_baselines.py, p1c_postconfirmation_diagnostics.py, p1c_confirmed_reporting.py, p1c_confirmed_closeout.py; tests/test_p1c_annotation_gate_and_baselines.py. New versioned data: annotation_gate_v1, confirmed_semantic_v1, boundary_baselines_v1, independent_validation_proposal_v1. New reports: final annotation verification, researcher-confirmed exploratory analysis, confirmed measurement robustness, offline boundary baseline assessment, independent validation proposal, novelty monitor v3. Existing reports and failed prior exports remain unchanged.\n\nCommands captured in results/p1c_annotation_gate/v1: source verifier; actual register/analyze; offline boundary baselines; paired diagnostics; confirmed reporting; targeted pytest and regression pytest. Initial targeted tests 60 passed; final relevant regression set {tests['stdout'].strip().splitlines()[-1]}. Earlier full 947-test result remains historical; no new full-suite count is asserted. Main analysis 419.04 seconds, additional paired diagnostics 211.81 seconds, no new generation. All planned numerical reconstructions matched. No scientific integrity failure or score change occurred during this analysis.\n\nOffline five-baseline investigation uses the existing 72 raw outputs and 12 explicitly authored software fixtures, not new model responses. Simple headings and fence-aware parsing recover the same 64 primary/eight candidate prefixes; no incremental real-output gain. Fence handling improves only authored fixture agreement and still fails quoted/document headings. Timing and traced Python memory are recorded with limits; no independent boundary accuracy, algorithm originality or improved generation claim.\n\nPrimary methods revisited: LongMemEval, What to Admit and How to Present, Decoupling Logic from Persona, Efficient Guided Generation, Chain-of-Verification. Full-method comparisons and peer-reviewed/preprint distinctions retained in monitor v3; stronger-baseline reproduction remains outstanding. Independent measurement review recommended before fresh empirical replication. Prospective 48/96-speaker allocations include explicit SD/ICC/multiplicity assumptions and actual-runtime proxies, not inference authorization.\n\nOriginal 72 responses/prompts/tokenizer records/labels reconstructed unchanged; 5,798 historical artifacts preserved. Exact approved protocol and manifest remain unchanged. Controls DIAGNOSTIC_ONLY, no-history shorter, family/speaker nesting, shared coding lineage, boundary and entity/time uncertainty remain visible. No inference, training, protocol adoption, commit or push.\n''')
    verification=preserve()
    paths=[]
    for directory in (ROOT,a.ROOT/'annotation_gate_v1',a.ROOT/'boundary_baselines_v1',Path('docs/validation/p1c/independent_validation_proposal_v1')):
        paths.extend(p for p in directory.rglob('*') if p.is_file())
    paths.extend(Path(p) for p in ('docs/P1c_final_annotation_verification_v1.md','docs/P1c_researcher_confirmed_exploratory_analysis_v1.md',
        'docs/P1c_confirmed_measurement_robustness_v1.md','docs/P1c_offline_boundary_baseline_assessment_v1.md',
        'docs/P1c_independent_validation_proposal_v1.md','docs/related_work_novelty_matrix_monitor_v3.md',
        'tools/p1c_annotation_review_check.py','tools/p1c_boundary_baselines.py','tools/p1c_postconfirmation_diagnostics.py',
        'tools/p1c_confirmed_reporting.py','tools/p1c_confirmed_closeout.py','tests/test_p1c_annotation_gate_and_baselines.py'))
    schemas=Counter()
    for path in paths:
        if path.suffix=='.json':a.read(path);schemas['json']+=1
        if path.suffix=='.csv':
            rows=a.rows(path);a.require(all(None not in r for r in rows),'CSV width error '+str(path));schemas['csv']+=1
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    a.require(diff.returncode==0,'Git diff check failed')
    a.write(final,{'version':'p1c_confirmed_analysis_closeout_v1','software_verified_utc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS','maintainer':'Yaxin ZHENG','human_semantic_confirmations':72,'approved_secondary_prefixes':8,
        'human_review_timestamp':None,'annotation_provenance':'Researcher-adopted AI-assisted review; no independent second reviewer or perfect-blinding claim',
        'preservation':verification,'artifact_sha256':{p.as_posix():a.sha(p) for p in paths},'schema_counts':dict(schemas),
        'tests':{'new_relevant_regression':'85 passed','capture':str(RESULT/'tests_regression_02.json'),'sha256':a.sha(RESULT/'tests_regression_02.json'),
            'previous_full_suite':'947 passed in prior preserved integrity capture; not rerun or relabeled'},
        'official_analysis':{'views':['primary','secondary_sensitivity_only'],'contrasts':16,'scalar_representations_per_view':24,
            'speaker_clusters':6,'paired_cases':12,'bootstrap_draws':10000,'bootstrap_seed':715004,'reconstructed_twice':True,
            'paired_measurement_diagnostics_reconstructed_twice':True},
        'statistics_source_sha256':{p:a.sha(p) for p in ('tools/p1c_integrity_registration.py','tools/p1c_semantic_analysis.py','tools/p1c_paired_statistics.py')},
        'independent_precision_formula_rechecked':24,'new_inference':0,'new_independent_human_ratings':0,
        'source_verification_before_confirmation':{'path':str(RESULT/'source_verification_01.json'),'sha256':a.sha(RESULT/'source_verification_01.json'),
            'note':'Its zero-human/zero-effects fields describe entry state before subsequent explicit adoption, not current state.'},
        'git_diff_check':'PASS','git_status':subprocess.check_output(['git','status','--short'],text=True),
        'development_log_sha256':a.sha('docs/research_development_log.md')})
    print(json.dumps({'status':'PASS','confirmed':72,'contrasts':16,'schema_counts':dict(schemas),'preservation':verification,'new_inference':0},indent=2))


if __name__=='__main__':main()
