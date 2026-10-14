"""Report completed authorized calibration and remaining scientific gates."""
from collections import Counter
from pathlib import Path
import csv
import json
import statistics
import subprocess
import p1d_budget_calibration as b
from p1d_budget_measurement import OUT as M
from p1d_budget_analysis import OUT as A
from p1d_budget_continuation_diagnostics import OUT as D

F=Path('docs/validation/p1d/final_preparation_v1')

def md(name,text):
    with (Path('docs')/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def run():
    audit=b.load(M/'execution_integrity_v1.json');assert audit['results']==audit['attempted']==144
    plan=b.load(b.FROZEN);stats=b.load(M/'budget_structural_summary_v1.json');dist=b.load(A/'distributions_v1.json')
    allstats={r['budget']:r for r in dist if r['family']=='ALL'};qual=b.load(A/'budget_qualification_v1.json')
    assert not any(r['provisional_qualification'] for r in qual),'Use a revised report if a budget qualifies'
    proposals=b.load(A/'primary_AI_proposals_UNCONFIRMED_v1.json');provenance=b.load(A/'annotation_analysis_provenance_v1.json')
    joined=b.load(A/'provisional_analysis_dataset_v1.json')
    no_history={cap:dict(Counter(r['task_success'] for r in joined if r['condition']=='H_none' and r['budget']==cap)) for cap in (96,192,256)}
    components={cap:{'required':sum(len(r['components']) for r in joined if r['budget']==cap),
        'present':sum(c['presence']=='PRESENT' for r in joined if r['budget']==cap for c in r['components']),
        'supported':sum(c['support']=='PRESENT' for r in joined if r['budget']==cap for c in r['components'])} for cap in (96,192,256)}
    effects=b.load(A/'cluster_sensitivity_v1.json');diag=b.load(D/'summary_v1.json')
    with (D/'boundary_candidate_views_v1.csv').open(encoding='utf-8-sig',newline='') as f:candidates=list(csv.DictReader(f))
    original={x['request']['request_id']:x['result']['response_status']['first_span']['text'] for x in audit['rows']}
    comparable={}
    for method in sorted({r['method'] for r in candidates}):
        group=[r for r in candidates if r['method']==method and r['start']!='']
        comparable[method]={'candidates':len(group),'abstentions':144-len(group),
            'same_content_after_outer_whitespace_trim':sum(r['candidate_text'].strip()==original[r['request_id']].strip() for r in group),
            'whitespace_only_difference':sum(r['candidate_text']!=original[r['request_id']] and r['candidate_text'].strip()==original[r['request_id']].strip() for r in group),
            'non_whitespace_content_difference':sum(r['candidate_text'].strip()!=original[r['request_id']].strip() for r in group)}
    b.save(D/'boundary_text_comparability_v1.json',{'version':'boundary_content_comparability_v1','methods':comparable,
        'source_sha256':{str(p):b.sha256(p) for p in (D/'boundary_candidate_views_v1.csv',M/'execution_integrity_v1.json')},
        'primary_bytes_modified':False,'independent_accuracy':None,'interpretation':'Offset/whitespace changes are not automatically semantic boundary changes. Case-sensitive literal stops can abstain on uppercase role transitions.'})
    segments=[Path(r['path']) for r in audit['segments']];events=[e for folder in segments for e in b.read_events(folder)]
    summaries=[b.load(p/'summary.json') for p in segments];assert all(s['status']=='PASS' for s in summaries)
    payloads=[e['data']['payload'] for e in events if e['kind']=='http_request' and e['data']['route']=='/completion']
    assert len(payloads)==144
    for q,p in zip(plan['requests'],payloads):
        assert p['prompt']==q['input_token_ids'] and p['n_predict']==q['max_new_tokens'] and p['seed']==q['seed']
        assert p['temperature']==0 and p['top_p']==1 and p['cache_prompt'] is False and p['stop']==[]
    raw=[e['data']['response'] for e in events if e['kind']=='p1d_budget_raw_generation']
    settings=[]
    for q,r in zip(plan['requests'],raw):
        s=r['generation_settings'];assert s['n_predict']==s['max_tokens']==q['max_new_tokens']
        settings.append({k:v for k,v in s.items() if k not in ('n_predict','max_tokens')})
    assert all(s==settings[0] for s in settings),'Unexpected effective decoding difference'
    native_cost={cap:{'mean_prompt_ms':statistics.mean(r['timings']['prompt_ms'] for q,r in zip(plan['requests'],raw) if q['max_new_tokens']==cap),
        'mean_generation_ms':statistics.mean(r['timings']['predicted_ms'] for q,r in zip(plan['requests'],raw) if q['max_new_tokens']==cap),
        'mean_reported_generated_tokens_per_second':statistics.mean(r['timings']['predicted_per_second'] for q,r in zip(plan['requests'],raw) if q['max_new_tokens']==cap)} for cap in (96,192,256)}
    memories=[e['data'] for e in events if e['kind']=='memory_observation' and e['data']['status']=='observed']
    peak=max(x['process']['peak_working_set'] for x in memories)
    errors=[e for e in events if e['kind']=='failure'];assert not errors
    finished=[e['created_utc'] for e in events if e['kind']=='run_finished']
    started=b.load(segments[0]/'manifest.json')['created_utc']
    elapsed=sum(s['elapsed_seconds'] for s in summaries)
    with (M/'paired_prefix_diagnostics_v1.csv').open(encoding='utf-8',newline='') as f:pairs=list(csv.DictReader(f))
    prefix={f'{lo}-{hi}':{'blocks':48,'same_first_span':sum(r['first_span_text_equal']=='True' for r in pairs if int(r['lower_budget'])==lo and int(r['higher_budget'])==hi),
        'lower_token_prefix':sum(r['lower_is_token_prefix']=='True' for r in pairs if int(r['lower_budget'])==lo and int(r['higher_budget'])==hi)} for lo,hi in ((96,192),(96,256),(192,256))}
    inventory={'version':'p1d_budget_completed_engineering_v1','registered_authorization_sha256':b.sha256(b.AUTH),'manifest_sha256':b.MANIFEST_SHA,
        'started_utc':started,'finished_utc':finished,'elapsed_seconds':elapsed,'requests_attempted':144,'http_completion_requests':len(payloads),
        'successful_raw_responses':audit['raw_responses'],'validated_results':audit['results'],'failed_requests':len(errors),'remaining_authorized_requests':0,
        'generated_tokens':sum(x['result']['generated_tokens'] for x in audit['rows']),'memory_observations':len(memories),
        'peak_server_working_set_bytes':peak,'memory_scope':'Windows process peak for full server lifetime; not a separate peak attributable to each cap',
        'segments':[p.as_posix() for p in segments],'model':plan['model'],'native_tokenizer_identity':plan['native_tokenizer_identity'],
        'full_HTTP_payload_order_and_tokens_match':True,'all_raw_results_reconstructed':True,'prefix_diagnostics':prefix,
        'effective_decoding_identical_except_caps':True,'effective_common_settings':settings[0],'native_cost_by_budget':native_cost,
        'new_independent_validation_requests':0,'new_instruct_requests':0,'human_semantic_confirmations':0,'main_study_decision':'NO_GO',
        'postflight_events':sum(e['kind']=='postflight' for e in events),'source_sha256':{str(p):b.sha256(p) for p in (b.FROZEN,b.AUTH,M/'execution_integrity_v1.json',A/'annotation_analysis_provenance_v1.json',Path(__file__))}}
    b.save(b.OUT/'engineering_summary_v1.json',inventory)
    table='\n'.join(f"| {cap} | {stats[str(cap)]['completed']} | {stats[str(cap)]['native_stop_types']} | {stats[str(cap)]['structure']} | {stats[str(cap)]['identifiable']}/48 | {stats[str(cap)]['latency_mean_seconds']:.2f} |" for cap in (96,192,256))
    md('P1d_budget_calibration_engineering_report_v1.md',f'''# P1d bounded CPU calibration — engineering report v1

Maintainer: Yaxin ZHENG. Exactly **144 authorized Base requests completed successfully; zero failures, zero retries, zero additional generation requests**. The 1,728 Base and 288 Instruct independent-study targets remain unauthorized.

## Authorization and frozen configuration

The user-authorized manifest is [the original candidate v2](validation/p1d/scientific_validation_v1/budget_calibration_manifest_candidate_v2.json), SHA-256 `{b.MANIFEST_SHA}`. The [frozen byte copy](validation/p1d/budget_calibration_v1/frozen_manifest_v2.json) is identical. Its historical proposal-status fields were preserved; [separate genuine researcher authorization](validation/p1d/budget_calibration_v1/researcher_authorization_v1.json) is operative. Human decision time is null; actual software registration time is recorded.

Model: Qwen3.5-2B-Base Q4_K_M, SHA-256 `{plan['model']['model_sha256']}`. Backend: llama.cpp b11573 / commit 0f701c882, server SHA-256 `{plan['model']['backend_sha256']}`. The tokenizer executable and all 29 DLL hashes are in the frozen manifest and actual preflight. CPU threads/batch 4, context 4,096, GPU layers 0, seed 42, temperature 0, top_p 1, cache_prompt=false, stop=[]; only per-request output cap varies. Effective backend defaults and full payloads are retained, including returned generated token IDs.

## Execution and integrity

Actual software start: `{started}`. Finish: `{finished[-1]}`. Runner elapsed: **{elapsed/60:.2f} minutes**. Eight registered development cases/speakers, six cells and three caps; no independent candidate ID is included. All 48 prompt/token sequences agree across caps, and live native tokenization verified their saved IDs before the first completion. Input range is 1,633–1,807. No context truncation occurred.

| Output cap | Successful requests | Native stops | Frozen structural status | Identifiable units | Mean wall latency, seconds |
| --- | --- | --- | --- | --- | --- |
{table}

Generated tokens: **{inventory['generated_tokens']:,}**. Observed server peak working set: **{peak:,} bytes ({peak/2**30:.3f} GiB)** across {len(memories)} observations. This is lifetime process peak, not isolated per-budget RAM. Latencies include prompt processing and response transfer on the actual workstation; concurrent light research/tool activity prevents treating them as clean hardware benchmarks.

All effective server-returned generation settings match after excluding only `n_predict`/`max_tokens`. The engineering JSON separately reports native prompt-processing milliseconds, generation milliseconds and token throughput for each cap. These backend timings are not process CPU-time measurements. No timing extrapolation from these shorter development prompts certifies main-cohort cost.

All 144 write-ahead identities, HTTP completion payloads, raw HTTP response bytes, raw texts, token counts/IDs, order and reconstructed parser results match. Postflight rechecked model/backend/source identities. Native `limit` is normalized to `length`; both are retained, and neither is a semantic failure label.

Raw run directory: `{segments[0].as_posix()}`. Its `events/`, `manifest.json`, `summary.json`, server logs and `source_snapshot/` preserve complete provenance. [Engineering summary](validation/p1d/budget_calibration_v1/engineering_summary_v1.json) and [execution reconstruction](validation/p1d/budget_calibration_v1/measurement_v1/execution_integrity_v1.json) bind these records. Runtime failures: none. Offline engineering corrections and test results are separately documented in the development log and final reproducibility seal.

## Reproduction without new inference

The executed command was `.venv/Scripts/python.exe tools/p1d_budget_calibration.py run --preflight docs/validation/p1d/budget_calibration_v1/preflight_v1.json`. The consumed authorization must not be reused to rerun it.

Read-only reconstruction: `.venv/Scripts/python.exe tools/p1d_budget_calibration.py audit --output results/p1d_budget_calibration/reconstruction_NEW.json` (choose an unused path). Semantic/statistical reconstruction: `.venv/Scripts/python.exe tools/p1d_budget_analysis.py --verify`. New output creation refuses overwrites. No historical protocol, raw experiment, annotation or main candidate bank was modified.
''')
    semtable='\n'.join(f"| {cap} | {allstats[cap]['factual']} | {allstats[cap]['temporal']} | {allstats[cap]['task_success']} | {allstats[cap]['semantic_completeness']} |" for cap in (96,192,256))
    ordinal='\n'.join(f"| {cap} | {allstats[cap]['relevance']} | {allstats[cap]['coherence']} | {allstats[cap]['persona_fidelity']} |" for cap in (96,192,256))
    latency='\n'.join(f"| {r['higher_budget']} minus {r['lower_budget']} | {r['all_eligible_paired_estimate']:.2f} | {r['speaker_bootstrap_sensitivity_interval'][0]:.2f}, {r['speaker_bootstrap_sensitivity_interval'][1]:.2f} |" for r in effects if r['metric']=='latency_seconds')
    md('P1d_budget_calibration_scientific_report_v1.md',f'''# P1d output-policy calibration — scientific report v1

Maintainer: Yaxin ZHENG. This is development evidence on eight authored cases, not independent P1d validation. All **144 semantic records are AI-assisted proposals; zero researcher adoptions or independent human annotations are registered**.

## Question, controls and primary measurement

Does changing only the output cap from 96 to 192 or 256 improve first-answer delivery and measurement adequacy? Eight development cases × six conditions are paired across caps. Prompts, evidence, requested dates, references, fixed context, model and decoding remain fixed. Budget order is frozen. Main E/V effect signs are neither estimated for policy selection nor used to choose a cap; the original S/F/H research programme remains central.

The [measurement plan](P1d_budget_measurement_plan_v1.md) retains original `response_status_v1` spans and separate relevance, factual, temporal, coherence, task, component, completeness and narrow style outcomes. Reaching the cap is not automatically task failure. Claims, components and ordinal evidence were separately assessed. Exact identical measurement inputs share a documented AI assessment across {provenance['exact_review_groups']} groups; this is not independent repeat annotation. Review files omit budget/condition labels, but the analyst prepared execution materials and can access the mapping, so complete blinding is not claimed.

## AI-proposed semantic observations, full denominator

| Cap | Factual labels /48 | Temporal labels /48 | Task labels /48 | Semantic completeness /48 |
| --- | --- | --- | --- | --- |
{semtable}

| Cap | Relevance /48 | Coherence /48 | Narrow style fidelity /48 |
| --- | --- | --- | --- |
{ordinal}

Required-component slot counts (separate presence and support judgments): `{components}`. Slots within a response/case are not independent observations. No missing component is converted automatically into an incorrect factual claim.

See [all 144 masked item proposals](validation/p1d/budget_calibration_v1/analysis_v1/primary_AI_proposals_UNCONFIRMED_v1.csv), including exact spans, ledger evidence, components, distinct justifications, uncertainty, alternatives and blank researcher fields. The [JSON version](validation/p1d/budget_calibration_v1/analysis_v1/primary_AI_proposals_UNCONFIRMED_v1.json) preserves nested evidence. Case/family distributions and complete paired contributions remain machine-readable.

The dominant observed content is a future promise, question replay or simulated USER RESPONSE, with requested values absent in the primary spans. A changed person in a repeated question is a referential/relevance defect, not automatically an incorrect factual assertion. Generic policy echoes can receive a supported-claim proposal while still failing temporal selection and complete delivery. Their alternative Unverifiable interpretation is explicitly retained. A simulated lack-of-ledger statement has unresolved speaker attribution and a documented Incorrect alternative if adjudicated as the assistant denying supplied evidence.

The no-additional-history arm has these AI-proposed task outcomes (eight cases per cap): `{no_history}`. A delivery problem also present without additional history cannot be attributed solely to the historical packages. Repetition of a fixed-context commitment motivates a formatting hypothesis, but observational overlap does not prove that commitment or the template caused the failure. The purpose of repairing measurement is to make the original persona-conditioning question testable, not to replace it with a parser-only study.

Unverifiable therefore includes **no evaluable answer claim** and **interpretation/attribution uncertainty**, rather than a common falsehood category. Boundary-unresolved, structurally unscorable, N/A and administrative Missing remain different states. All source applicability flags are retained. Factual Correct-label incidence and Correct/(Correct+Incorrect) are reported separately; an assessable-only rate based on a few policy statements is not task accuracy. No score was changed to manufacture variance.

The [metric-discrimination table](validation/p1d/budget_calibration_v1/analysis_v1/metric_discrimination_v1.json) preserves factual/task/completeness cross-tabs, relevance/coherence pairings, ordinal ceilings and invariant endpoints. Conceptual separation and distinct AI rationales do not establish independent human measurement reliability. A clear, coherent commitment can still fail the task; any endpoint with no observed variation cannot discriminate conditions in this sample and is retained rather than retrospectively dropped.

## Boundaries and truncation

The original structural classifications remain unchanged. Paired first-span/token-prefix counts are `{prefix}`. The [continuation diagnostics](validation/p1d/budget_calibration_v1/boundary_diagnostics_v1/summary_v1.json) compare seven extraction views, preserving all candidate offsets and original text. Native EOS, literal stops, role/section and fence-aware baselines are known techniques; the new locality and header diagnostics are adaptations, not independent ground truth.

The [content-comparability supplement](validation/p1d/budget_calibration_v1/boundary_diagnostics_v1/boundary_text_comparability_v1.json) distinguishes whitespace-only offset differences from non-whitespace content changes. The existing literal-stop baseline is case-sensitive and can abstain when only uppercase role transitions occur. Its candidate count is not an independent accuracy score; the prospective stopping proposal explicitly lists title-case and uppercase variants rather than hiding this baseline limitation.

Reference-value literal checks in full raw continuations are reported separately from semantic scores. They do not recognize paraphrases or certify boundary correctness. Longer tails can repeat dialogue without delivering an answer. A heading cut can shorten a promise but cannot establish that an omitted answer was present. No primary span was replaced, and no generation-time stop/template effect is inferred from offline cutting.

## Paired uncertainty and qualification

All three budget differences are reported across all metrics. Six condition-block contributions are averaged within each of eight case/speaker clusters; 10,000 whole-speaker draws use seed 716707. [Cluster/LOSO results and unknown bounds](validation/p1d/budget_calibration_v1/analysis_v1/cluster_sensitivity_v1.json) preserve complete-case alternatives separately and never renormalize missing factorial cells. Ordinal means are descriptive; full categories and paired signs remain available. There are no confirmatory p-values. Degenerate intervals for invariant delivery outcomes describe this sample and are not evidence of population certainty.

| Paired cap difference | Mean added wall seconds | 95% speaker-bootstrap sensitivity interval |
| --- | --- | --- |
{latency}

The unchanged rule requires at least 44/48 semantically complete replies and at most 2/48 unresolved boundaries. **None of the three caps provisionally qualifies under the AI proposals. No adequate primary output policy is selected.** Human adoption is pending, but automatic main-study execution is not warranted. The 96-token setting remains only the preserved reference, not an endorsed adequate validation policy.

The minimal next hypothesis is that explicit current-user turn framing, with and without conventional stops, may improve task delivery. It is untested and requires a separate bounded authorization. A prospective 16-request candidate uses only the same eight development cases and reuses existing original-baseline results; it does not alter the 144 completed requests or authorize any main-study generation.

The [frozen prompt-format comparison](validation/p1d/final_preparation_v1/frozen_prompt_format_comparison_v1.json) verifies a concrete difference: all 72 P1c prompts mark the current question with `User:`, whereas these 144 P1d prompts place an unmarked question below `CURRENT QUESTION`. Their fixed-context assistant utterances also differ (an invitation to specify an assignment versus a ledger-use commitment). Evidence length and task composition differ as well. This is a rationale for a controlled framing diagnostic, not an isolated between-wave causal explanation or permission to change completed prompts.

## Scientific scope and next independent validation

These eight cases share ledger construction and shorter prompts than the candidate bank. They do not estimate independent-template, real-speaker or population effects, nor establish that Base models generally cannot answer. The main 288-case bank remains unfrozen and AI-proposed VALID_WITH_LIMITATIONS, with diagnostic controls, template dependencies and independent-annotation gaps. A task-delivery floor makes an independent history-effect test scientifically uninformative until measurement adequacy is resolved. This is a validity safeguard, not selection for positive persona effects.

## Algorithmic Opportunity Assessment

1. **Observed Failure Modes:** repeated commitments and role/question continuations warrant delivery and boundary diagnosis; causal attribution remains untested.
2. **Existing Methods and Published Prior Art:** native termination, conventional stops/templates, grammar constraints, CoVe, RARR, DCCD, temporal retrieval and FPPS are relevant existing baselines.
3. **Potential Algorithmic Improvements:** no original gap has been established; first test the smallest known format/stopping repair and uncertainty-preserving verification.
4. **Validation Feasibility:** offline locality adds no P1c recoveries; fair supplied-date retrieval succeeds on the curated development pool. Independent span/claim labels, equal compute and persona fidelity remain required.
5. **Publication Value:** preserve this negative development result and the empirical S/F/H path. See [the detailed update](P1d_algorithmic_development_update_v2.md); no algorithm originality or PLOS ONE readiness follows from this calibration.
''')
    diagnostic=F/'format_diagnostic_manifest_proposed_v1.json'
    sources=[b.AUTH,b.FROZEN,b.OUT/'engineering_summary_v1.json',A/'primary_AI_proposals_UNCONFIRMED_v1.csv',A/'primary_AI_proposals_UNCONFIRMED_v1.json',A/'annotation_analysis_provenance_v1.json',A/'budget_qualification_v1.json',
        diagnostic,F/'format_diagnostic_tokenizer_validation_v1.json',F/'stratified_case_review_v1.csv',F/'stratified_control_review_masked_v1.csv',F/'template_dependency_assessment_v1.json',F/'instruct_official_tokenizer_check_v1.json',
        Path('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json'),Path('docs/validation/p1d/independent_candidates_v4/base_candidate_prompts_v1.json'),Path('docs/validation/p1d/independent_candidates_v4/native_tokenizer_validation_v1.json'),
        Path('docs/validation/p1d/proposed_v1/contrast_specification_v1.json'),Path('docs/validation/p1d/proposed_v1/analysis_policy_proposal_v1.json'),Path('docs/P1d_protocol_addendum_proposed.md')]
    packet={'version':'p1d_execution_readiness_packet_v3','maintainer':'Yaxin ZHENG','main_decision':'NO_GO','approved_plan_not_reopened':True,
        'completed_authorized_development':144,'remaining_authorized_requests':0,'main_Base_target':1728,'main_Instruct_target':288,'main_requests_authorized':0,
        'candidate_bank_frozen':False,'main_executable_manifest_exists':False,'proposed_separate_development_requests':16,'separate_development_authorized':0,
        'recommended_output_policy':'No cap qualified; retain 96 only as diagnostic reference, not accepted main policy',
        'scientific_gates':['Human adoption/correction of AI semantic proposals','Resolve delivery/format adequacy before main freeze',
            'Adopt/revise case and diagnostic-control materials with explicit scope','Resolve conditional-template target versus independent-template ambition',
            'Independent measurement validation or explicit documented limitation with appropriate study classification',
            'Traceable local Instruct configuration, or explicit separately authorized Base-only route retaining deferred model plan',
            'Final validated scientific/runtime manifest and explicit inference authorization'],
        'next_actual_decision':'One consolidated review may adopt/correct 144 AI proposals and separately authorize/defer the exact 16-request development format diagnostic. Neither authorizes 2016 main requests.',
        'source_sha256':{p.as_posix():b.sha256(p) for p in sources},'human_decisions_registered_this_report':0}
    b.save(F/'execution_readiness_packet_v3.json',packet)
    md('P1d_execution_readiness_packet_v3.md',f'''# P1d consolidated execution decision — v3

Maintainer: Yaxin ZHENG. First submission target: PLOS ONE. **Main independent validation: NO-GO.** The approved P1d prospective plan remains adopted; no repeat adoption approval is requested. The original S/F/H programme and historical protocols/results remain intact.

## Completed scope and current evidence

Exactly 144 authorized development requests succeeded, with no failures or retries; the authorization is consumed. See the [engineering report](P1d_budget_calibration_engineering_report_v1.md) and [scientific report](P1d_budget_calibration_scientific_report_v1.md). None of 96/192/256 tokens meets the prespecified completion criterion under the unconfirmed AI assessment. Increasing the cap is therefore not an adequate demonstrated repair, and no primary validation budget is recommended as adequate.

| Readiness dimension | Current evidence | Remaining GO condition |
| --- | --- | --- |
| Technical | Authorized manifest, 144 actual payloads/results, model/backend/token IDs and postflight verified | Freeze only a scientifically adequate final configuration; no failed request or extra retry is hidden |
| Stimulus validity | 288 AI VALID_WITH_LIMITATIONS, references reconstructed unchanged | Researcher scoped adoption/corrections; no automatic human PASS |
| Control validity | 288 actual token matches; diagnostic procedural content | Review leakage/priming; retain LENGTH_MATCHED_DIAGNOSTIC_CONTROL, never strict neutrality by token equality |
| Output/measurement | Complete masked 144-item evidence packet; cap comparison failed qualification | Adopt/correct proposals, resolve first-answer delivery, independently validate scoring/boundaries where feasible |
| Independence/statistics | 144 speakers, 288 cases, 247 question strings, 16 grammars/four ancestors | Decide restricted fixed-template target or prospective diversification amendment; no empirical ICC claim |
| Base model | Pinned 2B Base configuration verified and calibrated | Validated output/format policy; stronger measurement readiness before independent inference |
| Instruct model | Official rendering and 288 upstream-tokenizer roundtrips verified | Local traceable GGUF, native template/tokenizer/stop/RAM/runtime checks; no substitution |
| Reproducibility | Original materials and negative results preserved, exact hashes below | Final main-study request manifest remains unavailable because scientific/configuration gates are unresolved |
| Authorization | 144 development scope completed; main scope not authorized | Explicit new authorization for a specified validated manifest |

The unchanged main candidate bank is `independent_candidates_v4`, SHA-256 `170e43772e0e45753638228a8c2fc2bf2d5a9f06830374b22887a5929486afbd`. Base native evidence remains 1,728 prompts at 1,946–2,085 tokens, 288/288 active/control matches. These are candidate checks, not a confirmatory freeze. E/V retains entity/value/lexical and interval/value package interpretations. E1V1 deliberately supplies answer support; H_none is shorter. The 16 registered contrasts and six-comparison primary family are unchanged.

The [stratified review guide](P1d_stratified_scientific_review_guide_v1.md) provides 64 full cases and 64 masked control assessments covering 32 strata and all 16 grammars, alongside the full 288-case audit. This risk-prioritized sample is not an independent human review of every case. [Template accounting](validation/p1d/final_preparation_v1/template_dependency_assessment_v1.json) shows 12–24 instances per grammar, ancestor counts 72/96/72/48, and 62 records in repeated-question groups. Fresh names do not remove shared linguistic ancestry. Existing simulation results are retained, not rerun: illustrative main/interaction half-widths and poor new-template coverage depend on hypothetical sharing/missingness assumptions, not measured ICCs.

The [Instruct update](P1d_instruct_arm_readiness_v2.md) supports only its registered 24-speaker/48-case/all-six-cell matched subset. A future **Base-only 1,728-request option is also currently NO-GO**, and must be explicitly authorized separately if adopted; it does not silently cancel the 288 Instruct target. Neither option is a pure post-training experiment.

## One concrete next researcher checkpoint

**Decision A — semantic adoption.** Inspect and adopt with limitations, correct specified records, or defer the [144-item AI proposal](validation/p1d/budget_calibration_v1/analysis_v1/primary_AI_proposals_UNCONFIRMED_v1.csv). CSV SHA-256: `{b.sha256(A/'primary_AI_proposals_UNCONFIRMED_v1.csv')}`. JSON SHA-256: `{b.sha256(A/'primary_AI_proposals_UNCONFIRMED_v1.json')}`. Preserve the generic-policy-claim and simulated-user attribution alternatives. Approval would register researcher-adopted AI assistance, not independently produced human labels. No review timestamp or agreement statistic will be invented.

**Decision B — separate bounded diagnostic, if desired.** Authorize or defer [format_diagnostic_manifest_proposed_v1.json](validation/p1d/final_preparation_v1/format_diagnostic_manifest_proposed_v1.json), SHA-256 `{b.sha256(diagnostic)}`. It proposes **16 new Base requests only**: the same eight development cases, H_none, explicit current User marker with/without conventional stops, fixed 96-token cap, at most 1,536 generated tokens. Existing original-baseline outputs are reused; no duplicate baseline generation. Exact prompt differences and native tokenizer logs are attached. It is not an official Base template, pure framing mechanism test or main-study authorization. Compare all outcomes, preserve failures, stop on integrity/runtime/OOM/45-minute ceiling, no retries. No generation has been performed for this proposal.

These are genuine human measurement and new-execution gates under the user's instructions, not software-enum approvals. Approval of A does not imply B. Approval of B does not approve main-study materials, a changed primary policy or the 2,016-request cohort. Rejection/deferral preserves all current evidence and causes no extra inference. Do not approve the unready main study merely to finish an engineering milestone.

The [machine-readable packet](validation/p1d/final_preparation_v1/execution_readiness_packet_v3.json) binds all exact sources, including the actual adopted addendum SHA-256 `{b.sha256(Path('docs/P1d_protocol_addendum_proposed.md'))}`. Human decisions remain blank/unregistered. A final executable main manifest will only be produced after the listed scientific and configuration issues are resolved. The [final reproducibility seal](validation/p1d/final_preparation_v1/reproducibility_manifest_v1.json) records targeted tests, source preservation and Git status. No commit or push was performed.
''')
    print(json.dumps({'engineering':inventory['requests_attempted'],'semantic_proposals':len(proposals),'main_decision':'NO_GO',
        'next_diagnostic_sha256':b.sha256(diagnostic),'packet_sha256':b.sha256(Path('docs/P1d_execution_readiness_packet_v3.md'))},indent=2))

if __name__=='__main__':run()
