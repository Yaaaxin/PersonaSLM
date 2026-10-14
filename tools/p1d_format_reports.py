"""Write concise versioned reports from the completed diagnostic; never execute inference."""
from pathlib import Path
import json
from collections import Counter
import p1d_format_calibration as f

A=f.OUT/'analysis_v1'
I=Path('docs/validation/p1d/instruct_preparation_v3')

def doc(name,text):
    with (Path('docs')/name).open('x',encoding='utf-8',newline='\n') as out:out.write(text.strip()+'\n')

def main():
    summary=f.load(A/'summary_v1.json');u=f.load(A/'paired_uncertainty_v1.json');plan=f.load(f.FROZEN)
    audit=f.load(f.OUT/'execution_integrity_v1.json');run=Path(audit['run_directory']);events=f.b.read_events(run)
    raw=[e['data']['response'] for e in events if e['kind']=='format_raw_generation']
    firstsettings={k:v for k,v in raw[0]['generation_settings'].items() if k!='stop'}
    f.require(all({k:v for k,v in x['generation_settings'].items() if k!='stop'}==firstsettings for x in raw),'Other effective decoding changes')
    f.require(all(x['generation_settings']['stop']==q['stop'] for x,q in zip(raw,plan['requests'])),'Effective stops differ')
    memories=[e['data'] for e in events if e['kind']=='memory_observation']
    peak=max(m['process']['peak_working_set'] for m in memories if m.get('status')=='observed')
    smoke=I/'minimal_instruct_smoke_manifest_proposed_v1.json';smokehash=f.sha256(smoke)
    model=f.load(I/'local_candidate_metadata_v1.json');token=f.load(I/'native_development_tokenizer_v1.json')
    started=f.load(run/'manifest.json')['created_utc'];finish=events[-1]['created_utc']
    engineering={'requests':16,'successful':16,'failures':0,'retries':0,'generated_tokens':sum(r['tokens_predicted'] for r in raw),
        'started_utc':started,'finished_utc':finish,'runner_elapsed_seconds':f.load(run/'summary.json')['elapsed_seconds'],
        'memory_observations':len(memories),'peak_working_set_bytes':peak,'effective_settings_equal_except_stop':True,
        'effective_settings_without_stop':firstsettings,'run_directory':run.as_posix(),'manifest_sha256':f.MANIFEST_SHA,
        'human_semantic_ratings':0,'concurrency_caveat':'Public model metadata/download and vocabulary-only checks overlapped some requests; no other model generation. Latency is observed wall time, not isolated CPU benchmark.',
        'stop_rule_note':'Fixed sixteen attempts consumed; neither run nor resume can silently allocate another attempt.'}
    f.save(f.OUT/'engineering_summary_v1.json',engineering)
    doc('P1d_format_diagnostic_engineering_report_v1.md',f'''# P1d authorized format diagnostic — engineering v1

Maintainer: Yaxin ZHENG. Exactly **16/16** authorized Base requests succeeded; zero failures, retries or additional completion requests. No Instruct or independent-validation inference was performed.

## Authorization and immutable configuration

The original [candidate](validation/p1d/final_preparation_v1/format_diagnostic_manifest_proposed_v1.json) and its byte-identical [frozen copy](validation/p1d/format_calibration_v1/frozen_manifest_v1.json) have SHA-256 `{f.MANIFEST_SHA}`. The original proposal's NOT_AUTHORIZED metadata is historical and unchanged; the separate [researcher authorization](validation/p1d/format_calibration_v1/researcher_authorization_v1.json), SHA-256 `{f.sha256(f.AUTH)}`, records the explicit current user decision. Human decision time is null; software registration time is actual. Initial Git HEAD: `4ac68b2d8ebeb9cd9b13ccdf79a081d0d4f0abf0`, clean working tree.

Model: Qwen3.5-2B-Base Q4_K_M, SHA-256 `{plan['model']['model_sha256']}`. Backend: llama.cpp b11573-0f701c882, SHA-256 `{plan['model']['backend_sha256']}`. CPU only, GPU layers zero, four threads and batch threads, context 4096, greedy temperature 0, top_p 1, seed 42, cache_prompt false, max96. No parameter other than the registered stop lists differs between the two new arms. Full native effective defaults are in [engineering_summary_v1.json](validation/p1d/format_calibration_v1/engineering_summary_v1.json), including sampler order, penalties and ignore_eos=false.

Eight original development identities, H_none, two arms, order seed716708 and exact frozen order were checked. Input lengths are 1635–1758. All eight arrays matched the live pinned backend before the first completion. Evidence, question content, references, fixed context and speaker identities matched source records; held-out overlap is zero. Model, tokenizer, 29 DLLs, sources and configuration passed postflight.

## Execution evidence

Actual UTC start `{started}`; finish `{finish}`. Runner elapsed {engineering['runner_elapsed_seconds']:.3f} seconds. Generated tokens: {engineering['generated_tokens']}. Native termination: eight limit, eight word, zero EOG. All eight word stops are registered strings. Returned IDs, native token counts and possible stop-token suffix differences are retained separately. Frozen structural results: eight CROSS_TURN and eight AMBIGUOUS; all sixteen have unit_identifiable=true.

Observed process peak working set: {peak} bytes ({peak/1024**3:.3f} GiB), from {len(memories)} observations. This is process lifetime peak, not a per-arm memory effect. No unsupported peak-RAM measurement is invented. Public metadata/download and vocabulary-only preparation overlapped part of execution; the paired latency difference is descriptive and not an isolated machine benchmark.

Raw outputs, HTTP byte bodies, token IDs, prompts, seeds, request order, server logs, memory and immutable source snapshots are under `{run.as_posix()}`. Each event is hash-chained. [execution_integrity_v1.json](validation/p1d/format_calibration_v1/execution_integrity_v1.json) reconstructs all sixteen results from original HTTP bodies and verifies actual payloads. Failure log inventory is empty; no failure is retried or hidden.

## Reproduction and validation

` .venv/Scripts/python.exe tools/p1d_format_calibration.py audit --output <NEW_UNUSED_PATH>` reconstructs the execution without generation. `.venv/Scripts/python.exe tools/p1d_format_analysis.py --verify` checks deterministic analysis outputs. Generation command used was `.venv/Scripts/python.exe tools/p1d_format_calibration.py run --preflight docs/validation/p1d/format_calibration_v1/preflight_v1.json`; do not repeat it: the attempt claim is exhausted and the runner refuses reruns.

The initial reconstruction check found only a Python tuple/JSON-array comparison defect. The original assembly source is archived as `analysis_v1/source_snapshot_v1.py`; verification now normalizes JSON representations. No raw data, AI rating or numerical result changed. Two successive reconstructions agreed. Final targeted regression evidence and every source/output digest are indexed by [reproducibility_manifest_v1.json](validation/p1d/format_calibration_v1/reproducibility_manifest_v1.json). Historical protocols/results remain untouched; the development log receives an append only.
''')
    table='\n'.join(f"| {arm} | 8 | {s['termination']} | {s['structural']} | 8/8 | 0/8 | {s['mean_latency_seconds']:.3f} |" for arm,s in summary.items())
    doc('P1d_format_diagnostic_scientific_report_v1.md',f'''# P1d format diagnostic — scientific v1

Maintainer: Yaxin ZHENG. First submission target: PLOS ONE. **No configuration qualified for main validation.** This is an eight-case development diagnostic, not independent replication or an E/V effect study. All sixteen semantic assessments below are AI proposals, unconfirmed. The previous 144 proposals also remain unconfirmed.

## Question and identified intervention

The failed 96/192/256-token sweep motivated a predeclared test of current-question role framing and conventional stops. Both new arms add `User:` immediately before the current question and preserve the terminal `Assistant:` prefix. Between the two new arms only the four frozen newline User/Assistant stop strings change. Compared with the historical original H_none/96 outputs, role markers, length/salience and optionally stops change, in a different run. The reference is preserved rather than regenerated. No pure cognitive framing mechanism is identified.

## Observations

| Arm | Requests | Native termination | Frozen structure | Recoverable first span | Complete task answers, AI | Mean wall s |
| --- | --- | --- | --- | --- | --- | --- |
{table}

All sixteen raw outputs and evidence were read item by item. Every first response promises ledger use and ends with USER RESPONSE or CURRENT QUESTION. Neither arm delivers any of its **14 required components**. Full continuations repeat promises or simulated user questions; they do not deliver hidden final answers. Arlo's no-stop continuation changes the simulated question to Arwen: this is outside the primary answer span and is not automatically an assistant factual assertion.

The stop arm produces 154 tokens versus 768 without stops. Its first-span content equals the no-stop first span after whitespace normalization in 8/8 pairs; exact text equality is 0/8 because the delimiter newline is removed. Conventional offline stop shadows reproduce the eight actual stop outputs exactly. This is implementation agreement, **not independent boundary accuracy**. First-span recoverability stays 8/8 in both arms. Visible cross-turn continuation is suppressed; actual native EOG remains 0/16.

Frozen AMBIGUOUS in the stop arm means `bounded_reply_semantics_not_certified`, with identifiable=true. It must not be confused with an unresolved first-span boundary or counted as a factual error. The retained section headings still pose discourse-scope uncertainty. A separately recorded heading-excluded prefix is also only a promise and does not rescue delivery; it does not replace primary text.

## Separate semantic endpoints and measurement limits

Per arm: factual Correct4/Unverifiable4/Incorrect0; temporal Unverifiable8; task Failure8; semantic completeness NO8; relevance3×8; coherence3×8; narrow persona-style fidelity4×8. Correct here refers only to four generic policy echoes about historical intervals, not correct requested answers. If these echoes are excluded from material factual claims, factual Unverifiable becomes8/8. Both interpretations leave delivery at0/8. There is no unsupported inference of temporal correctness from the generic rule.

Thus eight responses can be factual Correct while task Failure; the constructs are not copied. Relevance, coherence and fidelity have separate evidence, but each has zero observed variance. They cannot discriminate the two configurations in this sample. They are retained without altering scores to force variation. Generic-policy scope, ordinal anchors and section-heading ownership remain explicit adjudication issues.

The [16-item proposals](validation/p1d/format_calibration_v1/analysis_v1/primary_AI_proposals_UNCONFIRMED_v1.csv) contain evidence, alternatives, applicability and blank human fields. Initial AI review had configuration visibility; it is not claimed as blinded. The [independent-review form](validation/p1d/format_calibration_v1/analysis_v1/independent_review_without_AI_scores_v1.csv) hides assignments and AI scores for a future reviewer; linguistic/whitespace cues remain. No second human or agreement score exists.

## Paired uncertainty and historical comparison

Eight paired cases equal eight purposively chosen speaker clusters. Whole-speaker bootstrap sensitivity uses10000 draws, seed716710; leave-one-speaker-out values and all case contributions are retained. Stop-minus-no-stop mean latency is {u['latency_stop_minus_no_stop']['mean']:.3f}s, percentile interval [{u['latency_stop_minus_no_stop']['bootstrap_percentile_95'][0]:.3f}, {u['latency_stop_minus_no_stop']['bootstrap_percentile_95'][1]:.3f}]s. Concurrent non-generation preparation and system load limit timing generalization. These intervals do not guarantee population coverage.

All paired proposed task differences and their leave-one-out values are zero. Degenerate bootstrap intervals do not prove equivalence or absence of a population effect. Full-eight-case unknown-correctness difference bounds are [-.5,.5] factual and [-1,1] temporal under unrestricted unresolved labels, conditional on the generic-policy primary convention. Categorical incidence and assessable-case accuracy are different; there are no temporally assessable answers. Missing annotations0, but factual/temporal Unverifiable remain separate. There is no available-cell renormalization or confirmatory significance testing.

Exact historical request IDs/hashes are joined in [historical comparison](validation/p1d/format_calibration_v1/analysis_v1/historical_exact_id_comparison_v1.csv). Historical task completion was also0/8. New role labels move simulated user content outside the first span, while three additional cases now echo a supported generic policy. A rise in factual Correct-label incidence from1/8 to4/8 is therefore **not demonstrated requested-answer improvement**. Neither this comparison nor the eight paired stops is independent replication. Each of four task families has only two cases; all have zero proposed complete answers.

## Decision and Algorithmic Opportunity Assessment

This is closest to **Case B**, specifically continuation/measurement control without improved answer delivery; it also triggers the Case C operational constraint against expanding an unsuitable Base configuration. No arm meets the frozen8/8 complete-identifiable-answer qualification. Adding a User marker is insufficient here; larger budgets already failed to change the earlier first replies. Neither finding proves all Base prompts or models are incapable.

1. **Observed Failure Modes:** promise repetition, empty answer content and policy echoes surviving cleaner stopping.
2. **Existing Methods and Published Prior Art:** native EOG, standard stops, deterministic role extraction, official templates, structured checking and generation-time verification are established methods; see [algorithm update](P1d_algorithmic_development_update_v3.md).
3. **Potential Algorithmic Improvements:** no evidence justifies a novel boundary algorithm when conventional stops reproduce these cuts. Study model/template adequacy before inventing a repair method.
4. **Validation Feasibility:** an exact eight-request Instruct feasibility proposal is prepared separately, with no automatic main-policy change. Independent boundary annotation and all-condition coverage remain necessary.
5. **Publication Value:** the defensible development contribution is a separation of termination, recoverability, claim support and actual task delivery. It is not a new mechanism or publication-ready finding.

The empirical S/F/H programme remains intact. P1d history packages refine its history branch; P3 configuration sensitivity and P5 localization support rather than replace that question. No P4 real-person data or P6 generation/training was started.
''')
    doc('P1d_instruct_arm_readiness_v3.md',f'''# P1d Instruct preparation — v3

Maintainer: Yaxin ZHENG. **Local candidate prepared; generation remains unauthorized.** This supplements v2 without replacing the Base model or adopting a new primary model policy.

## Verified artifact and remaining provenance limits

The intended official model remains [Qwen/Qwen3.5-2B at 965dcc54bc9c0591873df0e9869c056a54d323d1](https://huggingface.co/Qwen/Qwen3.5-2B/tree/965dcc54bc9c0591873df0e9869c056a54d323d1). A current metadata fetch found a newer repository revision15852e8c16360a2fea060d615a32b45270f8a8fc; it is not silently adopted. The API lists the same weight LFS digest at both revisions (`aa33250c4fc64891ddfaba3a314fd9542ea371843c387178b425fbcc5ed680b1`, 4548221488 bytes). This is remote metadata equality, not a locally reproduced conversion.

Three public quantization repositories were checked at fixed revisions. The prepared candidate is [lmstudio-community/Qwen3.5-2B-GGUF](https://huggingface.co/lmstudio-community/Qwen3.5-2B-GGUF/tree/bb84e11355a036e28f080c7793fa6d22b7c4e344), revision `bb84e11355a036e28f080c7793fa6d22b7c4e344`, file `Qwen3.5-2B-Q4_K_M.gguf`, **1270808032 bytes**, SHA-256 `{model['sha256']}`. Local bytes match the distributor's LFS digest. Location: `{model['file']}` (ignored model directory; no weights enter Git).

The distributor reports llama.cpp b8185 quantization, but not its exact source-weight revision, complete conversion command or calibration provenance. Therefore **conversion lineage is PARTIALLY_VERIFIED**, not fully certified. It was chosen for a standard non-MTP-advertised Q4_K_M candidate with explicit quantizer build and size comparable to Base, before any Instruct response was observed. Bartowski's checked candidate advertises MTP addition and b9222; the checked Unsloth card does not supply an exact quantizer revision. No outcome-based model selection occurred. An exact local reconstruction from official weights remains an alternative if full conversion lineage is required.

## Tokenizer, template and runtime

All248070 official shared token IDs and247587 merges match the local candidate. Its architecture is qwen35 with24 layers; stored native context262144, proposed runtime4096. EOS metadata248046 corresponds to `<|im_end|>`. Native EOG behavior under generation remains **unmeasured**.

The embedded template bytes differ from the pinned official template; all eight proposed single-user development renderings nevertheless agree exactly. The proposal explicitly binds the official template file (`{f.sha256(Path('docs/validation/p1d/development_readiness_v1/official_instruct_metadata/chat_template.jinja'))}`), enable_thinking=false, and does not rely on implicit embedded-template precedence. Fixed dialogue remains quoted task content inside one user message; this differs from Base plain completion formatting.

The pinned b11573 vocabulary-only utility processed all eight prompts successfully, **1642–1765 tokens**, with special-token parsing enabled. Every full native token array equals the pinned official tokenizer result. These are eight development checks, not new native certification of all288 future Instruct prompts. No server, tensor evaluation, warmup or Instruct generation occurred. The original288 offline rendering/tokenizer checks remain separate evidence.

The local model is about1.184GiB; actual Instruct RAM/latency and tensor execution compatibility remain unknown. The Base process peaked at{peak/1024**3:.3f}GiB. A later post-run system-memory observation is retained; transient free RAM is not an Instruct measurement. The eventual smoke preflight should reserve memory headroom and run without concurrent model/tokenizer workloads. Official recommended sampled decoding differs from the proposed greedy comparability diagnostic; no claim of official benchmark reproduction is made.

## Exact prospective scope

[{smoke.name}](validation/p1d/instruct_preparation_v3/{smoke.name}), SHA-256 **`{smokehash}`**, proposes only **8 H_none development requests**, same eight cases, 96 tokens, seed42, CPU4, ctx4096, native EOG, no custom stops, no retries, maximum768 generated tokens. No generation is authorized. Acceptance requires8/8 identifiable complete answers with separately reported correctness, components and fidelity; success only supports further separately authorized all-condition measurement validation. Failure retains NO-GO.

The registered288 Instruct validation target remains24 speakers×2 cases×6 conditions, paired to a subset of1728 Base requests. This is a limited model-plus-template/quantization comparison, not pure post-training or full-cohort model interactions. An Instruct-first or replacement primary arm would require a prospective amendment; none is adopted here.
''')
    doc('P1d_material_measurement_followup_v1.md','''# P1d material and measurement follow-up — v1

Maintainer: Yaxin ZHENG. This targeted follow-up leaves the candidate bank, 16 contrasts and approved P1d plan unchanged. It does not repeat the previous full reference audit or register human validity decisions.

## Consequential transfer risk

The [288-case risk inventory](validation/p1d/format_calibration_v1/followup_v1/candidate_format_risk_inventory_v1.csv) checks only prompt framing and source integrity. All1728 candidate Base prompts still use an unmarked CURRENT QUESTION followed by Assistant:. Fixed assistant commitments recur: “I will check that person in the ledger.”72, “I will use the dated ledger for that person.”96, “I will check the requested date.”72 and “I will consult the ledger.”48. The development non-delivery result makes this a material transfer risk; it does not establish that those phrases caused the failure. The authorized format intervention did not itself repair delivery.

The existing288 AI VALID_WITH_LIMITATIONS judgments remain unconfirmed. Reference/evidence audit results are preserved; no new objective ground-truth error was found by this narrower framing check. All288 matched controls remain LENGTH_MATCHED_DIAGNOSTIC_CONTROL, not semantically neutral. Procedural reading/closing-folder narratives can prime discourse/style; equal tokens cannot remove that confound. E/V changes entity/value/lexical and date/value packages; E1V1 supplies answer-supporting information by design. H_none is shorter.

The existing [64-case/64-control stratified packet](P1d_stratified_scientific_review_guide_v1.md) remains the single targeted scientific-review route. Prioritize context follow-ups, entity confusion, integration tasks, leakage and procedural priming. Human fields remain blank. No new duplicate approval form is needed. If a reference-changing defect is found, version the corrected bank before any independent inference.

## Independence and precision

There are144 nominal speaker clusters and288 paired cases, but247 distinct question strings,16 abstract grammars and four common paraphrase ancestors. Name replacement does not generate linguistic independence. The existing [precision study](P1d_statistical_precision_assessment_v1.md) is retained, not rerun. Its illustrative144-speaker half-widths6.88/6.91/13.48pp and poor new-template coverage under hypothetical template slopes are assumptions-based simulations, not measured ICCs. Unknown-outcome identification cannot be repaired merely by adding speakers.

Before confirmatory freeze, state a fixed-template target or approve genuinely independent template diversification; retain speaker pairing and a prespecified template sensitivity. No outcome-driven case selection, independent-data relabeling or favorable endpoint switch is permitted.

## Independent measurement readiness

The new sixteen applicability records agree with the frozen nine-endpoint matrix. Separate evidence fields support factual claims, temporal selection, required components, delivery, relevance, coherence and fidelity. Missing, N/A, unsupported claims, interpretation uncertainty and unavailable boundaries remain distinct. A bounded reply lacking a completeness certificate is not necessarily boundary-unresolved.

The independent form omits AI scores and arm mapping. A real second reviewer should first score it without suggestions, then independently adjudicate raw boundaries in a separate pass. Use the existing prospective stratified sampling/adjudication plan, report category-specific agreement with uncertainty and do not count researcher adoption of AI proposals as independent human annotation. No independent reviewer or agreement statistic currently exists. Correct policy echoes with failed tasks must be included in rubric calibration; they expose why factual correctness alone is insufficient. No metric is dropped because of a floor or ceiling.

Main validation remains NO-GO because model/output adequacy, scoped material/control adoption, independent measurement evidence, template-generalization scope and final execution authorization are unresolved. The approved sample-size targets and S/F/H research direction are not reopened or replaced.
''')
    print(json.dumps({'engineering':engineering,'smoke_manifest_sha256':smokehash},indent=2))

if __name__=='__main__':main()
