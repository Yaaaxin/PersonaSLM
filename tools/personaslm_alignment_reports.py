"""Materialize current Instruct milestone reports and versioned research registry."""
from pathlib import Path
import json
import statistics
import time
import p1d_instruct_smoke as s
import escp_offline as e

O=s.OUT
M=O/'measurement_v1'
A=Path('docs/validation/research_alignment_v1')

def doc(name,text):
    p=Path('docs')/name
    if p.exists():
        s.require(p.read_text(encoding='utf-8')==text,'Refuse changed report overwrite: '+str(p));return
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    integrity=s.load(O/'execution_integrity_v1.json');summary=s.load(M/'summary_v1.json')
    rows=integrity['rows'];plan=s.load(s.FROZEN)
    run=next((s.ROOT/'runs').iterdir());events=[s.load(p) for p in sorted((run/'events').glob('*.json'))]
    mem=[x['data'] for x in events if x['kind']=='memory_observation' and x['data']['status']=='observed']
    peak=max(x['process']['peak_working_set'] for x in mem)
    request_table='\n'.join('| '+ ' | '.join(str(v) for v in [i,r['request']['request_id'],r['result']['generated_tokens'],r['result']['stop_reason'],round(r['result']['latency_seconds'],3)])+' |' for i,r in enumerate(rows))
    eng={'run':run.as_posix(),'run_manifest_sha256':s.sha256(run/'manifest.json'),'run_summary':s.load(run/'summary.json'),
        'frozen_manifest_sha256':s.sha256(s.FROZEN),'model':plan['model'],'template_sha256':plan['template_sha256'],
        'memory_observations':len(mem),'peak_working_set_bytes':peak,'memory_is_process_lifetime_peak':True,
        'first_event_utc':events[0]['created_utc'],'last_event_utc':events[-1]['created_utc'],
        'raw_event_count':len(events),'semantic_provenance':'AI_ONLY_UNCONFIRMED',
        'concurrency':'No local offline benchmark, testing or artifact preparation during inference; external browsing/light reads only. Not an isolated hardware laboratory.',
        'new_completion_attempts':8,'retries':0,'hidden_warmup':False,'failed_requests':0}
    ep=O/'engineering_summary_v1.json'
    if ep.exists():s.require(s.load(ep)==eng,'Engineering summary changed on resume')
    else:s.save(ep,eng)
    doc('P1d_instruct_feasibility_engineering_report_v1.md',f'''# P1d Instruct feasibility engineering report v1

Maintainer: Yaxin ZHENG. P3/P5, RQ3/4. Exactly eight explicitly authorized development attempts completed; no previous exact run existed. Software execution timestamps: {eng['first_event_utc']} through {eng['last_event_utc']}. Researcher decision time is not invented. Authorization is registered separately from the immutable proposed manifest's original zero-authorization field.

## Frozen identity and execution

- Manifest: `{s.SOURCE.as_posix()}`; SHA-256 `{s.SHA}`. Frozen byte copy: `{s.FROZEN.as_posix()}`.
- Qwen/Qwen3.5-2B candidate: `{plan['model']['model_file']}`; SHA-256 `{s.MODEL_SHA}`. Intended upstream revision `{plan['model']['intended_upstream_revision']}`; distributor revision `{plan['model']['artifact_revision']}`; reported quantizer b8185. Exact source-weight/conversion-command lineage remains partially verified and accepted only for this development test.
- Pinned llama.cpp b11573-0f701c882; executable SHA-256 `{plan['model']['backend_sha256']}`. Native tokenizer/DLL identities are in preflight. Official template SHA-256 `{plan['template_sha256']}`; non-thinking explicit token rendering, special-token parsing enabled.
- CPU-only, 4 generation/batch threads, context 4096, greedy temperature 0/top-p 1, seed 42, 96 output tokens, no stop strings, cache disabled, native EOS enabled. No speculative decoding, vision, hidden warmup or retries. Model-specific template differs from the historical Base text completion.
- All eight development identities, native token arrays (1642–1765 inputs), request hashes, order, parent references and full prompts passed preflight. Full validation-cohort cases were excluded. The 45-minute limit was respected: {eng['run_summary']['elapsed_seconds']:.3f} seconds total.

## Actual requests

| Order | Request | Generated tokens | Native stop | Latency seconds |
| --- | --- | ---: | --- | ---: |
{request_table}

Eight successful responses, zero failures, 341 generated tokens, seven native EOS and one output-budget termination. Mean request wall latency {summary['mean_latency_seconds']:.3f}s. All generated token arrays and native counts are preserved. Observed process lifetime peak working set: {peak} bytes ({peak/1024**3:.3f} GiB), from {len(mem)} observations; not per-condition peak RAM or total system RAM. No unobserved telemetry is invented.

## Storage, integrity and reproduction

Raw run: `{run.as_posix()}`. `events/` retains exact payloads, base64 raw HTTP bodies, native stops/timings/token IDs, memory and error/audit events in a hash chain. `server.log`, source snapshot, `manifest.json` and `summary.json` preserve environment and completion status. Manifest hash: `{eng['run_manifest_sha256']}`. `execution_integrity_v1.json` reconstructs all eight results from these records.

Executed once: `.venv/Scripts/python.exe tools/p1d_instruct_smoke.py run --preflight {O.as_posix()}/preflight_v1.json`. The exclusive claim prevents a second execution. **Do not rerun this generation command.** Read-only verification: `.venv/Scripts/python.exe tools/p1d_instruct_smoke.py audit --output {O.as_posix()}/fresh_integrity_check.json` (choose an unused output path); annotation reconstruction: `.venv/Scripts/python.exe tools/p1d_instruct_measurement.py --verify`. Final reproducibility and scoped regression records are in `{O.as_posix()}`.

Original structural statuses remain seven AMBIGUOUS and one TRUNCATED. The pinned parser expects native `eog`, whereas these raw responses say `eos` and end in token 248046. A separately saved alias sensitivity changes interpretation of stop evidence without modifying raw output, text spans or historical labels. Identifiable candidate spans are not independently adjudicated boundary ground truth.
''')
    mapping={r['anonymous_id']:r['case_id'] for r in s.load(M/'withheld_mapping_v1.json')}
    proposals=[dict(r,case_id=mapping[r['anonymous_id']]) for r in s.load(M/'AI_proposals_UNCONFIRMED_v1.json')]
    table='\n'.join('| '+' | '.join(str(v) for v in [r['case_id'],r['factual'],r['temporal'],r['task_success'],r['semantic_completeness'],sum(x['support']=='Supported' for x in r['required_components']),len(r['required_components'])])+' |' for r in proposals)
    doc('P1d_instruct_feasibility_scientific_report_v1.md',f'''# P1d Instruct feasibility scientific report v1

Maintainer: Yaxin ZHENG. Phase P3/P5; RQ3/4. All semantic judgments below are **AI-assisted proposals, not human-confirmed ratings**. Exactly eight H_none development cases were assessed individually against their full trusted ledger, requested date, question, context and required components. No persona-conditioning effect is estimated.

## Decision and outcome separation

The registered criterion was eight identifiable and semantically complete task answers with no answer-losing cut, followed by separate factual/temporal/fidelity assessment. It was not a rule to maximize factual accuracy. It is **not met**: five replies have complete requested-answer form, two are nonanswers and one is partial. Seven discourse utterances are syntactically finished, which is different from complete task answers. Only two tasks are correctly completed. Main P1d validation and the conditional all-cell S/F/H follow-up remain **NO-GO**.

| Development case | Factual | Temporal | Task | Answer completeness | Supported components | Required |
| --- | --- | --- | --- | --- | ---: | ---: |
{table}

Factual proposals: 2 Correct, 6 Incorrect. Temporal: 2 Correct, 5 Incorrect, 1 Unverifiable. Task: 2 Success, 6 Failure. Required components: 8/14 explicitly present, 3/14 supported. Three complete wrong answers demonstrate that factual consistency and completeness need not coincide. Relevance: five 5, two 3, one 2; coherence: five 5, two 3, one 2. Identical marginal counts do not imply joint label assignment; item-specific explanations are retained.

Mira, Owen and Vera use January values for May/November requests. Arlo denies evidence and claims November lies outside January–December; this is contradicted, not merely absent support. Tessa describes October–December records as applicable in May and ends mid-statement. Cleo denies the stipulated volunteer role; factual Incorrect uses the persona/context role evidence, while Unverifiable is retained as an alternative if adjudication restricts factual scope to ledger attributes alone. No temporal assertion is supplied by that denial, so temporal Unverifiable remains separate. Nolan's response correctly resolves the context target Quinn, and Ellis supplies the correct November locker.

## Structure, uncertainty and comparison

All eight primary spans are identifiable as candidates; none contains a generated extra role transition. Seven terminate natively at EOS and one at the token budget. Original parser statuses are preserved as seven AMBIGUOUS and one TRUNCATED. `boundary_alias_sensitivity_v1.json` documents the `eos`/`eog` interface mismatch; no alternate text is substituted and no independent boundary accuracy is claimed. Truncation is not the reason for labeling Tessa's explicit date claims incorrect.

Matching uses the exact eight historical Base H_none/96 request IDs and hashes. AI-proposed task success changes from 0/8 to 2/8, descriptively +25 percentage points; this is a noncontemporaneous model/template/quantization configuration comparison. Whole-speaker bootstrap sensitivity (8 purposive clusters, 10,000 draws, seed 716802) is [0, 62.5] percentage points; leave-one-speaker-out differences are 14.29–28.57 points. These are neither population coverage guarantees nor official human-confirmed semantic effects. Historical Base latency has different run conditions; no causal speed claim is made.

The original narrow brief/calm style proposals remain available but do not establish broad linguistic or behavioral fidelity. Behavioral fidelity was not predefined and is not retroactively scored. The new prospective fidelity protocol treats short-answer opportunity and independent review explicitly. Review was model-aware AI analysis, not a blind human study. A condition-masked, score-free human form is supplied; output content can still reveal model or configuration.

## Algorithmic Opportunity Assessment

1. **Observed Failure Modes:** Wrong intervals, false evidence-absence claims, incomplete relation-chain delivery and role denial occur under H_none. Historical persona override is not identified.
2. **Existing Methods and Published Prior Art:** Entity/time filtering, component checks, LongMemEval, FPPS, CoVe, RARR, typed admission and temporal graphs are relevant; see the v7 matrix.
3. **Potential Algorithmic Improvements:** Typed support/uncertainty witnesses and persona-preserving channels are a candidate scaffold only. The new offline rules tie a simple declarative baseline; no original algorithm or model improvement is established.
4. **Validation Feasibility:** A separately proposed eight-request P5 oracle-evidence test can estimate generation headroom before any new selector experiment. It changes evidence length, selection and positions jointly and cannot allocate unique causal blame.
5. **Publication Value:** These failures inform measurement and model adequacy for the core S/F/H study. They are not independent validation, a pure post-training effect or manuscript readiness.

## Review and next step

Full proposals: `{M.as_posix()}/AI_proposals_UNCONFIRMED_v1.csv` and JSON; raw text/evidence/reasons/alternatives/provenance are included. Human fields are blank. `independent_review_without_scores_v1.csv` supports review before exposure to proposals. No new administrative adoption is inferred. The consolidated next decision packet binds the optional future P5 scope and preserves all previous approvals.
''')
    # Extended bounded timing addresses coarse process-clock zeros without changing earlier results.
    timings={};fs=e.fixtures()
    for name,fn in [('escp_rules',e.verify),('declarative_reference',e.simple_rule_reference)]:
        samples=[]
        for _ in range(3):
            cpu=time.process_time_ns();wall=time.perf_counter_ns()
            for _ in range(10000):
                for f in fs:fn(f['evidence'],f['required'],f['claims'],abstains=f['abstains'])
            samples.append({'cpu_ns_per_fixture':(time.process_time_ns()-cpu)/(10000*len(fs)),
                            'wall_ns_per_fixture':(time.perf_counter_ns()-wall)/(10000*len(fs))})
        timings[name]=samples
    s.save(e.OUT/'extended_cost_measurement_v1.json',{'reason':'Initial 100-repeat process-clock samples included zero below-resolution values.',
        'repeat_count':10000,'batches':3,'fixtures':16,'measurements':timings,'recorded_utc':s.b.utc_now(),
        'scope':'Offline structured checks, same fixture order; no extraction/generation/I/O; not model latency or Persona Fidelity.'})
    parent=Path('docs/validation/p1d/format_calibration_v1/followup_v1/algorithm_opportunity_registry_update_v6.json')
    registry=s.load(parent);registry['version']='algorithm_opportunity_registry_v7'
    registry['parent']={'path':parent.as_posix(),'sha256':s.sha256(parent)}
    registry['primary_source_review']={'path':'docs/related_work_novelty_matrix_monitor_v7.md','sha256':s.sha256(Path('docs/related_work_novelty_matrix_monitor_v7.md'))}
    updates={'boundary':('Native EOS is now 7/8, but raw eos/eog alias differs; no independent boundary truth.','Retain native/legacy labels and alias sensitivity; do not invent a parser gain.'),
        'answer_components':('Five complete answer forms, only two correct tasks; two nonanswers and one partial relation chain.','Typed component witnesses implemented offline; simple declarative rules tie all 16 fixtures.'),
        'temporal_entity':('Three complete wrong-period answers and explicit false requested-date/evidence-absence assertions under H_none.','Proposed oracle evidence headroom diagnostic; no new retrieval generation yet.'),
        'persona_evidence':('H_none contains a persona profile but no added historical quotation; no S/F/H effect identified.','Separate linguistic/behavioral fidelity protocol and typed preservation channels; no measured model tradeoff.'),
        'memory_admission':('No admission comparison was generated. Zep/Mem0 and FC/PS directly overlap with ESCP.','Conservative typed channels implemented as known engineering, not a novel admission method.'),
        'interaction_adaptation':('No new factorial evidence; prior interactions remain exploratory.','Exact core S/F/H and fixed-F H1 weights restored prospectively; no adaptive algorithm justified.')}
    for entry in registry['entries']:
        entry['observed_failure'],entry['proposed_algorithm']=updates[entry['id']]
    registry['entries'].append({'id':'ESCP','classification':'ENGINEERING_ADAPTATION_RESEARCH_HYPOTHESIS',
        'observed_failure':'Wrong interval, unnecessary abstention and missing components motivate P5 localization, not a proven persona-override mechanism.',
        'published_solution':'Zep temporal graphs; Mem0 updates; FC/PS admission; FPPS; CoVe/RARR; established component rules.',
        'remaining_gap':'No residual superiority or distinct computational contribution demonstrated.',
        'proposed_algorithm':'Typed evidence state, conditional persona channels and component support certificates; structured extraction supplied.',
        'computational_distinction':'None established versus simple declarative reference; no original algorithm claim.',
        'fair_comparison':'Equal-information rule reference ties all fixtures; random/lexical/BM25/time filters and published methods remain full-pipeline baselines.',
        'independent_test':'New frozen cases, ambiguous extraction, reliable persona panels and matched end-to-end budgets.',
        'cpu_cost':'Extended process-time batches saved; excludes extraction and generation. No inference saving demonstrated.',
        'persona_cost':'Retained channels do not prove generated fidelity; independent linguistic/behavioral review required.',
        'falsification':'Reject novelty if same known rules match; reject improvement if delivery/fidelity/cost or independently adjudicated boundaries fail.'})
    registry['negative_findings_preserved']+=['Instruct strict eight-case answer-completeness gate failed.',
        'ESCP typed scaffold ties simple declarative rules on 16 authored fixtures; no original method supported.']
    s.save(A/'algorithm_opportunity_registry_v7.json',registry)
    print(json.dumps({'engineering':eng,'new_reports':2,'registry_entries':len(registry['entries'])},indent=2))

if __name__=='__main__':main()
