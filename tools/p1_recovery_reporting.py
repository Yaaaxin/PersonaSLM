"""One reviewer CSV and one consolidated P1 recovery report; no fabricated scores."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import subprocess

import p1_recovery_design as d
import p1_recovery_run as run

s, OUT, OLD = d.s, d.OUT, d.OLD
REPORT=Path('docs/P1_measurement_recovery_2x2_report_v1.md')
METRICS=('task_success','factual','temporal','semantic_completeness','relevance','coherence','delivered','supported')


def distributions(rows):
    return {k:dict(Counter(str(r[k]) for r in rows)) for k in METRICS}


def reviewer_rows():
    original=s.load(OUT/'original_C0_audit_v1.json'); rows=[]
    for entry in original:
        c=entry['case'];ai=entry['original_AI'];auto=entry['automatic_v2'];res=entry['original_result']
        rows.append({'case_id':c['case_id'],'task_family':c['family'],'condition':'D0' if entry['D0_reused_in_2x2'] else 'C0_AUDIT_ONLY',
            'decision_gate_eligible':entry['D0_reused_in_2x2'],'record_state':'ARCHIVED_COMPLETED_REUSED_NO_INFERENCE',
            'speaker_id':c['speaker_id'],'construction_ancestor':c['construction_ancestor'],'question':c['question'],
            'evidence_excerpt':c['trusted_evidence'],'reference_answer':c['reference'],'required_components':c['reference'],
            'requested_date':c['requested_date'],'evaluation_timestamp':c['evaluation_date'],'model_output':res['raw_response'],
            'automatic_score':auto['task_success'],'ai_assisted_label':ai['task_success'],
            'automatic_factual':auto['factual'],'ai_factual':ai['factual'],'automatic_temporal':auto['temporal'],'ai_temporal':ai['temporal'],
            'automatic_completeness':auto['semantic_completeness'],'ai_completeness':ai['semantic_completeness'],
            'AI_component_delivery':ai['delivered'],'AI_component_support':ai['supported'],'required_count':ai['required'],
            'agreement_flag':'DISAGREEMENT' if entry['disagreement_metrics'] else 'AGREEMENT',
            'task_agreement_flag':auto['task_success']==ai['task_success'],'disagreement_metrics':entry['disagreement_metrics'],
            'proposed_failure_type':entry['proposed_failure_type'],'evidence_rationale':entry['evidence_rationale'],
            'reference_validity_check':entry['reference_audit']['status'],'alternative_interpretation':ai['alternative'],
            'uncertainty':ai['uncertainty'],'original_structural_status':ai['original_structural_status'],
            'boundary_interpretation':'AI identifies full first-response candidate; original parser status preserved',
            'native_stop':ai['native_stop'],'latency_seconds':ai['latency_seconds'],'request_id':ai['request_id'],
            'prompt_sha256':entry['original_request']['prompt_sha256'],'raw_output_sha256':ai['raw_sha256'],
            'source_proposal_path':(OLD/'A_C0/measurement_v1/AI_proposals_UNCONFIRMED_v1.json').as_posix(),
            'source_proposal_sha256':s.sha256(OLD/'A_C0/measurement_v1/AI_proposals_UNCONFIRMED_v1.json'),
            'raw_run_directory':entry['original_run_directory'],'Q1_aliases':[],
            'researcher_decision':'','researcher_notes':'','researcher_factual':'','researcher_temporal':'','researcher_completeness':'',
            'provenance':'Original AI-assisted proposal preserved; source audit AI-assisted, not independent human validation'})
    # Explicit inventory placeholders preserve all 32 condition-level targets.
    # They are not model failures, semantic proposals, or spent requests.
    plan=s.load(run.MANIFEST);policy=s.load(OUT/'prospective_policy_v1.json');reqs={(r['case_id'],r['condition']):r for r in plan['requests']}
    if list((d.ROOT/'runs').glob('*')):
        raise ValueError('Actual run exists: export and review its outputs before final reporting; never fabricate its annotations')
    for c in d.select_cases(d.cases()):
        for con in ('D1','D2','D3'):
            r=reqs.get((c['case_id'],con));spec=policy['Q1_specs'].get(c['case_id'])
            cc=run.construct(c,con,spec) if r else None
            rows.append({'case_id':c['case_id'],'task_family':c['family'],'condition':con,'decision_gate_eligible':True,
                'record_state':'NOT_GENERATED_RAM_PREFLIGHT' if r else 'NOT_GENERATED_Q1_PRIORITY_UNRESOLVED',
                'speaker_id':c['speaker_id'],'construction_ancestor':c['construction_ancestor'],
                'question':cc['question'] if cc else '', 'evidence_excerpt':cc['trusted_evidence'] if cc else d.organized_evidence(c) if con=='D3' else c['trusted_evidence'],
                'reference_answer':cc['reference'] if cc else [],'required_components':cc['reference'] if cc else [],
                'requested_date':c['requested_date'],'evaluation_timestamp':c['evaluation_date'],'model_output':'',
                'automatic_score':'NOT_EVALUATED_NO_OUTPUT','ai_assisted_label':'NOT_EVALUATED_NO_OUTPUT',
                'agreement_flag':'NOT_APPLICABLE_NO_OUTPUT','task_agreement_flag':'','disagreement_metrics':[],
                'proposed_failure_type':[],'evidence_rationale':'No new output exists. Unexecuted inventory is not a model error or semantic missing outcome.',
                'reference_validity_check':'PASS_OBJECTIVE_CHECKS' if cc else 'Q1_COMPONENT_SELECTION_UNRESOLVED',
                'request_id':r['request_id'] if r else c['case_id']+'_recovery_'+con,
                'prompt_sha256':r['prompt_sha256'] if r else '', 'raw_output_sha256':'','raw_run_directory':'',
                'Q1_aliases':spec['aliases'] if con in ('D2','D3') and spec else [],
                'researcher_decision':'','researcher_notes':'','researcher_factual':'','researcher_temporal':'','researcher_completeness':'',
                'provenance':'Prospective inventory only; no AI score, human rating or inference fabricated'})
    rows.sort(key=lambda r:({'DISAGREEMENT':0,'AGREEMENT':1,'NOT_APPLICABLE_NO_OUTPUT':2}[r['agreement_flag']],not r['decision_gate_eligible'],r['case_id'],r['condition']))
    return rows


def export():
    rows=reviewer_rows();keys=list(dict.fromkeys(k for r in rows for k in r))
    path=OUT/'consolidated_researcher_review_v1.csv'
    with path.open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for r in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
    original=s.load(OUT/'original_C0_audit_v1.json'); selected=[r for r in original if r['D0_reused_in_2x2']]
    ai=[r['original_AI'] for r in original]
    summary={'version':'p1_recovery_offline_audit_v1','original_outputs':32,'D0_reused':8,'new_attempts':0,'human_ratings':0,
        'original_AI_distributions':distributions(ai),'D0_AI_distributions':distributions([r['original_AI'] for r in selected]),
        'task_family':{f:{'full_C0_n':8,'full_C0_AI_success':sum(r['original_AI']['task_success']=='Success' for r in original if r['case']['family']==f),
                         'selected_D0_n':2,'selected_D0_AI_success':sum(r['original_AI']['task_success']=='Success' for r in selected if r['case']['family']==f)} for f in d.FAMILIES},
        'original_Auto_AI_agreement':{},
        'failure_tags':dict(Counter(t for r in original for t in r['proposed_failure_type'])),
        'reference_check_pass':sum(r['reference_audit']['status'].startswith('PASS') for r in original),
        'question_review':'No non-unique reference or substantive question ambiguity found in the original32; negative-answer completeness and temporal construct application still disputed.',
        'automatic_caveat':'Agreement is not accuracy. Restricted syntax abstention is not automatically a scorer error. Original v1 shared FC/TC assignment is preserved; v2 remains conservative.',
        'decision':d.adjudicated_decision([{'condition':r['condition'],'researcher_decision':r['researcher_decision']} for r in rows if r['decision_gate_eligible']]),
        'reviewer_csv_rows':len(rows),'actual_observation_rows':32,'prospective_unexecuted_rows':24}
    from p1_measurement_scoring import agreement
    summary['original_Auto_AI_agreement']={k:agreement([r['automatic_v2'][k] for r in original],[r['original_AI'][k] for r in original]) for k in METRICS}
    summary['D0_Auto_AI_agreement']={k:agreement([r['automatic_v2'][k] for r in selected],[r['original_AI'][k] for r in selected]) for k in METRICS}
    s.save(OUT/'offline_audit_summary_v1.json',summary)
    return {'reviewer_csv':path.as_posix(),'rows':len(rows),'observed':32,'unexecuted':24,'status':summary['decision']['status']}


def finalize():
    s.require(not REPORT.exists(),'Preserve report version')
    x=s.load(OUT/'offline_audit_summary_v1.json');p=s.load(run.MANIFEST);ledger=d.old.cumulative()
    s.require(ledger['total_attempted']==48 and not list((d.ROOT/'runs').glob('*')),'New execution must be analyzed before reporting')
    preflights=sorted(OUT.glob('preflight_v*.json'));last=s.load(preflights[-1]);tests=s.load(OUT/'targeted_regression_v1.json')
    s.require(last['status']=='BLOCKED','Successful preflight requires continuation, not blocked closeout')
    s.save(OUT/'cumulative_authorization_ledger_v1.json',ledger|{'recorded_utc':s.b.utc_now(),
        'this_scope_authorized_maximum':24,'this_scope_attempted':0,'latest_scope_factorial_execution_authorized':False,
        'remaining_after_full24_if_later_completed':{'A_C0':0,'B_FACTORIAL':80,'C_DIAGNOSTIC':8,'total':88},
        'actual_remaining_now':112,'reserved_for_recovery':0})
    fam='\n'.join(f"| {f} | {v['full_C0_AI_success']}/8 | {v['selected_D0_AI_success']}/2 |" for f,v in x['task_family'].items())
    failures='\n'.join(f'- {k}: {v}' for k,v in x['failure_tags'].items())
    agrees='\n'.join(f"| {k} | {v['agreement']}/{v['paired_comparable']} | {x['D0_Auto_AI_agreement'][k]['agreement']}/{x['D0_Auto_AI_agreement'][k]['paired_comparable']} |" for k,v in x['original_Auto_AI_agreement'].items())
    report=f'''# P1 measurement recovery: consolidated O/Q diagnostic record v1

Maintainer: Yaxin ZHENG. Official paper: Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models. First submission target: PLOS ONE.

**Execution blocked by the unchanged physical-memory gate. New generations: 0. Scientific decision: SCIENTIFIC DECISION PENDING REVIEW.** No configuration is selected, and no S/F/H pilot v2 is generated or executed as a qualified design.

## Scientific scope and original source audit

This P1-only development intervention tests measurement feasibility for the original S/F/H programme. It estimates neither Persona effects nor population mechanisms. Protocol v1.1 is retained; v1.2 remains proposed. The adopted P1d addendum is preserved within its existing scope, not replaced. P0 is frozen; P1 active; P2/P3/P4 paused; P5 diagnostic closed with semantic adoption outstanding; P6 paused, including the prior null ESCP contribution.

All32 original C0 raw outputs, questions, trusted facts, timestamps, component references, automatic scores and AI proposals were inspected. The complete original HTTP/request/result inventory reconstructed. All32 references passed explicit unique entity/attribute/date witness checks, including relational chain links. The audit found no reference-answer error or non-unique original answer. This is objective checking plus AI-assisted source review, not human scientific certification.

Original scores remain untouched: task Success11/32; complete-answer forms29/32; supported components29/64. The new audit retains the original task recommendations pending human review. False unavailability in cases02/22 can count as delivered but wrong answers; treating it as missing component delivery is a preserved alternative. Case07 supplies incompatible March answers. Cases10/30 conflate wrong entity with temporal scope; case30's Incorrect temporal alternative is especially plausible because the wrong entity's cited value also expires before September. No disputed label was silently revised.

| Task family | All original C0 AI success | Selected D0 AI success |
| --- | ---: | ---: |
{fam}

Failure tags are descriptive, can overlap, and do not prove an internal reasoning mechanism:

{failures}

## Frozen case selection and D0 reuse

Selection uses the first two lexically sorted calibration case IDs within each of the four fixed task families. It reads no performance field. The chosen IDs are p1_measure_calibration_00 through07. These were previously observed development cases; an outcome-independent selector is not an independently blinded sample. All have eight evidence rows and shared Alderbrook/block ancestry, limiting representativeness. The factorial pool remains disjoint and unexecuted; no factorial case was selected by its C0 result.

For every selected case, reconstructed true-C0 prompt UTF-8 bytes equal the archived original request exactly. The original request SHA, prompt SHA, token array, model, template, context, seed and decoding are retained. D0 reuses the eight original outputs and never appears in the new completion inventory. D0 AI task success1/8; complete forms6/8; supported components5/16. These are existing observations, not a new experiment.

## Prespecified O/Q intervention and component eligibility

D0=O0Q0 (archived); D1=O1Q0; D2=O0Q1; D3=O1Q1. O1 groups the exact original fact lines by entity and sorts by validity date, with entity headings. The fact multiset, provenance IDs, intervals and values remain identical. Questions/references are unchanged across O. Position, length, format and salience change, so O is an organization package, not pure retrieval.

Q1 retains a single original entity/date answer valid at the query date, with no answer inserted outside the unchanged evidence. The eligible six cases select Bay B5022, B5096, B5102, B5177, B5316 and B5361 respectively. The comparison-family cases select the September component under their existing requested_date. Q changes cardinality, complexity and competence; it is not pure reasoning and cannot share an identical task-success estimand with Q0.

**Prospective eligibility issue:** cases04/05 each have three valid entity components (bay/zone/gate). The user's rule does not explicitly order these multiple qualifying components. Under the instruction to stop affected Q1 requests, four D2/D3 requests are blocked before inference, not replaced or charged. A clarification was requested before any new output. No silence is recorded as approval. The remaining20 requests have valid frozen inputs: D1 eight, D2 six, D3 six. This partial inventory cannot establish a complete32-record decision panel; it does not redefine the requested 2x2 experiment.

Frozen Q1 aliases are full bay label and bare bay code. Normalization is Unicode NFKC, whitespace collapse, casefold, and at most one terminal period removal. The entire normalized response must equal an alias. Negation, contradictory extra answers, prose or markdown are never stripped to manufacture a match; unhandled forms remain Uncertain/Unverifiable for human review. A wrong exact bay is Failure/Incorrect; an absent record, observed empty answer, N/A and uncertain answer remain distinct. No aliases were adapted to new outputs. Q0 retains the original criteria and automatic v2 limitations.

## Engineering preflight and authorization

Frozen eligible manifest: `{run.MANIFEST.as_posix()}`. SHA-256: `{s.sha256(run.MANIFEST)}`. All20 inputs passed actual pinned GGUF/native tokenizer checks against the official tokenizer, including full prompt reconstruction. Input range {min(r['input_tokens'] for r in p['requests'])}–{max(r['input_tokens'] for r in p['requests'])} tokens, with96 output tokens within4096 context. Original/native token logs are preserved. The live server/tokenizer gate was not attempted after failed RAM preflight.

Model GGUF SHA-256 `{p['model']['model_sha256']}`; backend SHA-256 `{p['model']['backend_sha256']}`; template SHA-256 `{p['template_sha256']}`. Same Qwen/Qwen3.5-2B Q4_K_M, llama.cpp b11573, CPU-only four threads, context4096, output96, seed42, temperature0, top-p1, no custom stops/cache/warmup/retries. Partial third-party conversion lineage remains development-only. No model or configuration substitution occurred.

Most recent full preflight: `{preflights[-1].as_posix()}`; failure: {last['error']}. The3GiB threshold is unchanged. Earlier memory availability was sufficient at an initial observation, but this does not override a failed pre-generation check. No server was started, no request claim/attempt consumed, and no new latency, stop reason, output tokens or model RAM measurements exist. Missing telemetry is not fabricated. Exact preflight observations remain machine-readable.

Cumulative attempted: A_C032, B_FACTORIAL0, C_DIAGNOSTIC16 =48. Actual remaining: A0/B80/C32 =112. The authorized24-request recovery scope is unspent. If all24 are eventually completed, the remaining allocation would be80 factorial+8 diagnostic=88; this is not the current count. Factorial execution is explicitly excluded by the latest instruction even though its standing allocation remains unused.

## Measurement and reviewer package

| Endpoint | Original32 automatic/AI agreement | Selected D0 agreement |
| --- | ---: | ---: |
{agrees}

These rates measure system agreement, not accuracy or independent inter-rater reliability. Original automatic v1 coupled FC/TC; its record is preserved, while existing v2 independently checks temporal scope. V2 still defers prose and date attachment. Conservative abstention is not automatically an error. The actual disagreement rows and rationales are first in the consolidated CSV.

`{(OUT/'consolidated_researcher_review_v1.csv').as_posix()}` contains56 uniquely identified rows:32 actual archived observations (eight marked D0,24 audit-only), plus24 clearly marked unexecuted inventory rows. Exactly32 rows belong to the intended D0–D3 decision panel;24 of these have no new output. Human decisions/notes/metric corrections remain blank. No unexecuted row is counted as an actual model failure or semantic observation. Full evidence, raw text, original labels, hashes and source locations are supplied.

| Condition | Output availability | AI task success | Audited task success |
| --- | --- | --- | --- |
| D0 | 8 archived | 1/8 | Not available |
| D1 | 0/8 new | Not measured | Not available |
| D2 | 0/8 new;2 Q1-blocked | Not measured | Not available |
| D3 | 0/8 new;2 Q1-blocked | Not measured | Not available |

No O/Q effect estimate, confidence interval or family-level new result is calculated without outputs. Original family/metric distributions remain machine-readable. Original structural labels21 AMBIGUOUS/11 TRUNCATED are unchanged; native EOS alias compatibility and AI first-response interpretation are separate. Truncation is not factual failure. No independent boundary ground truth exists.

## Decision rule, fidelity and next action

Only researcher-audited labels for the complete32-record panel can trigger the gate: success >=6/8 AND automatic exact agreement >=7/8, fixed priority D0,D1,D2,D3. Unknown or missing labels cannot be silently excluded or counted as agreements. No configuration is recommended on the basis of the AI proposals. A selected family's0/2 outcome would justify only the specified disclosed prospective development restriction, not a permanent scope change. The subsequent80-request pilot requires separate authorization and its own eight-C0 audited >=6/8 continuation gate.

Q1 reduces already limited linguistic and behavioral opportunity. A correct bay code is not Persona Fidelity; unavailable fidelity opportunities are not zero. This diagnostic does not validate either fidelity construct. The main S/F/H programme and separate reliability/fidelity endpoints remain unchanged.

Next action: resolve the two chain-case Q1 component priorities prospectively, retain all versions, then repeat the unchanged full resource preflight when memory is available. The existing inference authorization does not need to be requested again for the bounded eligible diagnostic. Do not run the80-request pilot, introduce another prompt variant, substitute a model, or optimize additional tasks. The final scientific configuration decision still requires real researcher review; current status is **SCIENTIFIC DECISION PENDING REVIEW**.

## Verification and reproduction

Targeted regression: {tests['summary']}. Complete command/output are in `{(OUT/'targeted_regression_v1.json').as_posix()}`. One initial preparation error (undefined OLD alias) was fixed before any inference; partial registration files were preserved and checked before preparation resumed. A later recording command had a shell-quoting SyntaxError before execution and was corrected. Both errors and the resource failures are retained in `development_failures_v1.json`. No model request failed or was retried. Detailed model/backend/DLL/D0 checks are in `static_integrity_verification_v1.json`; its static PASS does not bypass the failed RAM or unattempted live gates.

Read-only validation: `.venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'tools'); import p1_recovery_run as r; r.validate()"`.
Fresh preflight: `.venv/Scripts/python.exe tools/p1_recovery_run.py preflight --output <new-workspace-json-path>`.
Eligible execution command, only with a successful fresh preflight: `.venv/Scripts/python.exe tools/p1_recovery_run.py run --preflight <successful-preflight-path>`.
The runner rejects existing batch claims and reserves every attempt before HTTP, uses the cumulative category ledger, verifies live token arrays, records raw response bodies/IDs, and cannot generate D0 or factorial cells. This report does not claim that the unexecuted runner has been empirically validated by new inference.

Reproducibility manifest: `{(OUT/'reproducibility_manifest_v1.json').as_posix()}`. The previous944-file milestone is preserved; research log updates are append-only. Git HEAD/dirty state, source hashes, test evidence, all candidate inputs and memory failures are recorded. No commit/push, training, paused-phase work, originality claim, independent validation claim or submission-readiness claim.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    log=Path('docs/research_development_log.md');before=(OUT/'research_development_log_before_v1.bin').read_bytes()
    s.require(log.read_bytes()==before,'Concurrent log change; reconcile before append')
    addition=f'''\n\n## {s.b.utc_now()} — P1 O/Q measurement recovery preparation and blocked preflight\n\nMaintainer: Yaxin ZHENG. P1 only; RQ1/RQ2 measurement feasibility, not Persona effect estimation.\nAudited32 archived C0 outputs/questions/evidence/references and preserved every original label.\nDeterministic first-two-per-family selector fixed cases00–07; eight D0 prompt byte comparisons\npassed and archived output reuse was verified without inference. Entity/date witness checks\npassed32 cases. Remaining disputes include negative-answer completeness, entity/temporal\nattribution and automatic prose/date-attachment coverage. Human semantic confirmations:0.\n\nPrepared exact O/Q transformations and full-answer Q1 normalization. Chain cases04/05 have\nthree eligible entity components; four Q1 requests are explicitly blocked pending priority\nclarification, no invented tie rule. Twenty unaffected requests were frozen and native-token\nverified. Full preflight failed unchanged3GiB available-RAM gate; new generations0, cumulative48,\nremaining A0/B80/C32=112. No category transfers, retries or factorial inference.\n\nOne original preparation NameError (OLD alias) corrected before inference; existing partial\nregistration records retained. Tests: {tests['summary']}. Commands: p1_recovery_design.py;\np1_recovery_run.py prepare/preflight; targeted pytest; p1_recovery_reporting.py export/finalize.\nOne consolidated report {REPORT.as_posix()}, one56-row reviewer CSV (32 observed,24 unexecuted),\nreproducibility manifest and current ledger in {OUT.as_posix()}.\nSCIENTIFIC DECISION PENDING REVIEW; no configuration selected, no qualified pilot-v2 manifest.\nP0 frozen; P1 active; P2/P3/P4 paused; P5 closed with semantic review pending; P6 paused.\nNo Git commit/push, model changes, new prompt variants, training or algorithm development.\n'''
    addition+='\nA recording-command quoting SyntaxError and a documentation patch-context mismatch were corrected without inference or historical edits; no test failures occurred.\n'
    with log.open('ab') as f:f.write(addition.encode())
    previous=s.load(OLD/'reproducibility_manifest_v1.json');mismatches=[]
    for path,h in previous['artifact_sha256'].items():
        if Path(path)==log:
            s.require(log.read_bytes().startswith(before) and s.th(before.decode())==h,'Historical log prefix changed')
        elif s.sha256(Path(path))!=h:mismatches.append(path)
    s.require(not mismatches,'Historical artifact change: '+str(mismatches))
    artifacts=[p for p in OUT.rglob('*') if p.is_file()]+[REPORT,log,Path('tools/p1_recovery_design.py'),Path('tools/p1_recovery_run.py'),Path(__file__),Path('tests/test_p1_recovery_2x2.py')]
    artifacts=[p.resolve().relative_to(Path.cwd()).as_posix() for p in artifacts]
    s.save(OUT/'reproducibility_manifest_v1.json',{'version':'p1_recovery_2x2_reproducibility_v1','maintainer':'Yaxin ZHENG',
        'sealed_utc':s.b.utc_now(),'artifact_sha256':{p:s.sha256(Path(p)) for p in sorted(set(artifacts))},
        'prior_manifest_sha256':s.sha256(OLD/'reproducibility_manifest_v1.json'),'prior_artifacts_checked':len(previous['artifact_sha256']),
        'historical_log_prefix_preserved':True,'new_generations':0,'ledger':ledger,'human_ratings':0,
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_status':subprocess.check_output(['git','status','--short'],text=True),
        'decision':x['decision'],'tests':tests['summary']})
    return {'report':REPORT.as_posix(),'new_generations':0,'status':x['decision']['status'],'ledger':ledger}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['export','finalize']);args=p.parse_args()
    print(json.dumps(globals()[args.action](),indent=2))
