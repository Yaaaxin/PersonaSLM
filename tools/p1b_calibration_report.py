"""Render append-only English calibration reports from audited observations."""
import json
from pathlib import Path

from personaslm import p1b_calibration as core
from personaslm.journal import atomic_json, utc_now

PUBLIC=Path('docs/validation/p1b/calibration_v1')
ANALYSIS=PUBLIC/'analysis_v1'
LOCAL=Path('results/p1b_execution/v1')


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
                     ['| '+' | '.join(str(x).replace('\n',' ') for x in row)+' |' for row in rows])


def write(name,text):
    path=Path('docs')/name
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(text.strip()+'\n')


def main():
    s=core.load(ANALYSIS/'analysis_v1.json')
    test=core.load(LOCAL/'engineering/full_tests_final_01.json')
    if test['exit_code']!=0:
        raise ValueError('Do not render successful validation while the final test suite fails')
    run=Path(s['run_directory'])
    manifest=core.load(run/'manifest.json')
    captures={p.name:core.load(p) for p in sorted((LOCAL/'engineering').glob('*.json'))}
    prefix='Maintainer: Yaxin ZHENG. Version 1. Formal Protocol v1.1; proposed v1.2 r1 remains unchanged and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE.'
    source='[Machine-readable analysis](validation/p1b/calibration_v1/analysis_v1/analysis_v1.json), [request measurements](validation/p1b/calibration_v1/analysis_v1/request_measurements_v1.csv), [native transport reconciliation](validation/p1b/calibration_v1/analysis_v1/transport_integrity_v1.json), and [hash inventory](validation/p1b/calibration_v1/analysis_v1/execution_inventory_v1.json).'
    statuses=', '.join(f'{key}: {s["status_counts"].get(key,0)}' for key in ('COMPLETE','TRUNCATED','CROSS_TURN','AMBIGUOUS'))
    limitations='''- H_L1/H_L2 are simple follow-up baselines; context necessity is not demonstrated. H_L3 retains consecutive User turns, with possible Base continuation effects.
- Unique terminal entities, explicit identity cues and repeated answer patterns allow shortcuts. Designed levels are not validated difficulty rankings or evidence of internal multi-step reasoning.
- Style is partially nested in 12 synthetic speakers. Two cases per speaker are not independent speaker replications. F uses a limited supplementary-fact realization.
- Task family, history relevance and temporal content are not disentangled. Eight cells estimate intervention packages, not isolated history mechanisms.
- S/F/H additions also change context length and inserted content. Without reviewed matched controls, these eight-cell estimates do not isolate effects independent of length, wrapper or semantic content.
- The fixed 96-token budget can censor longer answers. Censorship, first-reply completeness, relevance and factual support remain distinct.
- No independent confirmatory set, model-configuration replication, authentic-speaker validation or neutral-adjusted effect is established. No case is removed based on C0 performance.'''
    checks=table(['Check','Result','Evidence / limit'],[
        ['Researcher stimulus review','PASS','24 cases; 312 preserved positive-criterion judgments; explicit message confirmation of AI-assisted assessment'],
        ['Frozen data / manifest','PASS','Exact byte hashes; no assignments or input edits'],
        ['Pinned files / native backend','PASS','Model/executable hashes before and after; owned b11573-0f701c882 process'],
        ['Live GGUF tokenization','PASS','192 actual /tokenize responses; exact input IDs match freeze before first completion'],
        ['Input capacity','PASS','150–434 tokens; plus 96 output tokens = at most 530, below 4096'],
        ['Native requests and decoding','PASS','192 serial requests in frozen order; temperature 0, seed 42, cache_prompt false'],
        ['Executed / raw / parsed results','PASS','192 unique request IDs; no retry or additional generation'],
        ['Response policy','PASS','response_status_v1 and separate_axes_policy_v1 preserved'],
        ['Semantic outcome review','PENDING','Stimulus acceptance does not label generated outputs'],
        ['Neutral comparisons','OPEN / NOT EXECUTED','The 24 prior Wave 1 candidates remain unreviewed; no transfer to P1b']])
    execution=f'''# P1b Calibration Execution Report

{prefix}

## Execution decision and result

The explicitly authorized bounded calibration completed **192/192 real local CPU requests**, with **192 responses, 192 persisted results and zero failed requests**. No extra wave, model switch, answer retry or neutral-control generation occurred. This is adapter execution PASS, not acceptance of scientific hypotheses or publication readiness. Human semantic output review remains pending.

Run ID: `{s['run_id']}`. Local raw journal: `{s['run_directory']}`. Original events and timestamps remain immutable. The run started from Git `{manifest['git']['sha']}` with dirty state `{manifest['git']['dirty']}` because the new approval records and registration helper were uncommitted. Frozen inference source hashes matched the mandatory preflight.

{checks}

## Researcher approval provenance

[Registration](validation/p1b/calibration_v1/researcher_review_registration_v1.json) records `reviewer_id=Yaxin_ZHENG`, `review_status=RESEARCHER_CONFIRMED`, `final_decision_authority=researcher`, and `review_method=Researcher confirmation of AI-assisted case-level assessment`. The original 24-row proposal, 312 judgments, master CSV, source quotations and limitations remain unchanged. The completed source copy and official 41-column import are separate artifacts. Approval came from the actual researcher message, not independently hand-entered CSV values or a blinded outcome questionnaire. No review timestamp, second reviewer or agreement statistic was invented; registration times are actual logging times.

The preparation-time `authorized=false`, `executed=false` and pending review flags in frozen inputs were not rewritten. The separate hash-bound authorization, write-ahead events, native responses and result events establish the actual current state. A copied plan flag in a raw result is not evidence that a request was unexecuted.

## Fixed configuration and identities

- Qwen3.5-2B-Base Q4_K_M; llama.cpp `b11573-0f701c882`.
- Model SHA-256: `{core.MODEL_SHA}`.
- Backend executable SHA-256: `{core.BACKEND_SHA}`.
- Dataset SHA-256: `{core.DATA_SHA}`.
- Frozen manifest SHA-256: `{core.MANIFEST_SHA}`.
- Base prompt `p1b_transcript_proposed_v1`; condition order seed 714001; decoding seed 42; temperature 0; top_p 1; output budget 96; no declared stop strings; return_tokens true; cache_prompt false.
- CPU threads 4 / batch threads 4; one server slot; context 4096. Native log reports `offloaded 0/25 layers to GPU`, qwen35 architecture and a 2B model. File identity does not independently prove fidelity of upstream third-party quantization.
- The live native endpoint receives integer input IDs. Input evaluated counts agree, all reported cache_n values are zero, and no context truncation occurred. Output IDs were returned and retained. A separate backend array of evaluated input IDs is unavailable; no such observation is invented.

The optional CIM hardware query returned access-denied errors despite PowerShell exit code 0. Its empty CPU/RAM/OS values are **unavailable**, not valid observations. Previous Ryzen hardware attribution remains historical; current thread/offload/slot observations come from this run's server log. Per-request process-memory observations remain in the local journal. Concurrency with lightweight read-only development checks means latency is not an isolated hardware benchmark.

## Logging, interruption and reconstruction

An exclusive claim and writer lock bind the wave to one authorization. Each attempt is journaled before transmission; raw HTTP bytes precede parsing. Failed or uncertain sends are never silently retried. This run required no interruption or resume. The documented resume adapter remains available for a separately authorized continuation of unattempted IDs, not re-generation of successful outputs.

{source}

The [command register](validation/p1b/calibration_v1/command_register_v1.json) points to full local captures. Full final suite: `{test['stdout'].strip().splitlines()[-1]}`; exit code {test['exit_code']}; process duration {test['duration_seconds']:.3f} seconds. The original pre-generation suite passed 631 tests; 13 new offline accounting tests were added. Final preservation checks are recorded separately in the [integrity report](validation/p1b/calibration_v1/final_integrity_v1.json).

## Errors and retained limitations

An initial inspection helper passed a string to a Path API and raised AttributeError before mandatory preflight. Correcting that helper did not change any experimental source or configuration. The failure record is retained. Mandatory preflight and execution had no failures. One optional literature fetch returned a cache miss; it was not repeatedly retried. The optional denied hardware query remains an explicit observation gap.

{limitations}

## Algorithmic Opportunity Assessment

Execution integrity demonstrates instrumentation, not a new algorithm. Structural observations and pending semantic coverage are assessed separately in [the algorithmic report](P1b_calibration_algorithmic_opportunity.md). No algorithm, model training or extra generation was initiated.
'''
    write('P1b_calibration_execution_report.md',execution)
    coverage=table(['Outcome','Eligible','N/A','Automatically scored','Human scored','Pending'],[
        [a,c['eligible'],c['inapplicable'],c['automatically_scored'],c['human_scored'],c['pending']] for a,c in s['coverage'].items()])
    measurement=f'''# P1b Calibration Measurement Report

{prefix}

## Coverage and scientific status

All 192 continuations are available. There are **zero human outcome annotations** and no approved automatic semantic scorer for this bank. Therefore factual accuracy, temporal accuracy, semantic completeness rates and semantic S/F/H effects are **not yet estimated**. Zero scored Unverifiable labels means no semantic assessment has been imported, not that every output is verifiable.

{coverage}

Structural labels: **{statuses}**. The frozen parser identifies a unit in {s['unit_identifiable']}/192 outputs; {s['first_reply_empty']} extracted first replies are empty and {s['raw_empty']} raw continuations are empty. Identifiability and visible text do not establish semantic completeness. Each record retains native termination, full raw continuation, first span, removed prefix, excluded tail and token counts.

## Evaluation contract and masked packet

Use [the 192-row outcome form](validation/p1b/calibration_v1/analysis_v1/output_human_review_v1.csv) and [review guide](P1b_calibration_output_review_guide.md). All human fields are blank. The separate local treatment mapping was frozen before observing outputs. Generated text and prior researcher knowledge may compromise perfect masking; record actual access and assistance rather than claiming independent blinded annotation.

Factual and temporal outcomes use Correct, Incorrect, Unverifiable and predeclared Not Applicable. A supported partial statement can be Correct while the requested answer remains incomplete. Unsupported attribution is not automatically a verified contradiction. Relevance and coherence retain separate 1–5 ratings. Every eligible missing/unscorable output stays in its denominator with its reason. Neither CROSS_TURN nor TRUNCATED is a factual error rule. Do not use the P0 city checker, substring occurrence or the source oracle as a free-text scorer.

The first request, `P1B-CAL1-001`, is retained as an execution-order-selected illustration: its first reply names “Maple Counter”, whereas the frozen April 5 reference component is “Birch Counter”. This source/output discrepancy is a review target, not a registered human judgment or an estimated error rate. It does not identify a persona mechanism. No stimulus or generation setting was changed after seeing it.

## Ceiling effects and Wave 1 comparison

Wave 1's researcher-confirmed 72/72 factual and 48/48 temporal Correct results remain unchanged. This calibration's ceiling status is **unresolved until valid semantic scoring**. A few conspicuous discrepancies cannot demonstrate bank-level discrimination, while syntactically smooth replies do not prove a remaining ceiling. Different task content, global date exposure and prompt realization prevent attributing a between-wave difference solely to difficulty.

Family and designed-level structural tables are in [the structural report](P1b_calibration_structural_analysis.md). They describe output form, not empirical cognitive difficulty. Future analysis must separate factual support from component completion, temporal date selection, relevance and extraction agreement. Keep 24 paired cases and 12 speaker clusters; no C0-correct filtering.

## Scientific limitations and Algorithmic Opportunity Assessment

{limitations}

The immediate information gain comes from reviewing existing responses. No corrective verifier is justified merely by lack of automated coverage. The [algorithmic assessment](P1b_calibration_algorithmic_opportunity.md) separates an instrumentation problem from a demonstrated semantic failure. {source}
'''
    write('P1b_calibration_measurement_report.md',measurement)
    group_tables=[]
    for dim,title in [('condition','Factorial condition'),('family','Task family'),('designed_complexity_level','Designed level')]:
        group_tables.append('## '+title+'\n\n'+table([title,'Requests','COMPLETE','TRUNCATED','CROSS_TURN','AMBIGUOUS'],[
            [k,v['requests']]+[v['status_counts'].get(x,0) for x in ('COMPLETE','TRUNCATED','CROSS_TURN','AMBIGUOUS')] for k,v in s['groups'][dim].items()]))
    contrast_table=table(['Contrast','CROSS_TURN difference (pp)','Nonzero cases','Leave-one-speaker-out range (pp)'],[
        [r['contrast'],f"{100*r['estimate']:.3f}",r['nonzero_cases'],f"[{100*r['leave_one_speaker_out_min']:.3f}, {100*r['leave_one_speaker_out_max']:.3f}]"] for r in s['contrasts'] if r['outcome']=='CROSS_TURN'])
    structure=f'''# P1b Calibration Structural Analysis

{prefix}

## Observed output structure

**{statuses}** across 192 real requests. Native termination counts: `{json.dumps(s['stop_counts'],sort_keys=True)}`. Generated tokens: {s['generated_tokens']['min']}–{s['generated_tokens']['max']} per response, {s['generated_tokens']['total']} total. Latency: median {s['latency_seconds']['median']:.3f}s, range {s['latency_seconds']['min']:.3f}–{s['latency_seconds']['max']:.3f}s; summed request latency {s['latency_seconds']['sum']:.3f}s. These are recorded execution observations, not a controlled hardware comparison.

Native output-budget termination applies to the full continuation. `response_status_v1` independently identifies first-reply structure; a continuation containing another role can be CROSS_TURN even though the backend stops at the budget. Frozen labels and excluded text are preserved. Semantic first-reply completeness remains unknown pending review.

Under this frozen policy, COMPLETE additionally requires a separate hash-bound completeness judgment. No such judgment was supplied during generation. Consequently, a zero COMPLETE count is not evidence that every first reply is semantically incomplete; do not reinterpret the policy's certification requirement as a model-performance statistic. Later human completeness labels remain separate from these frozen original statuses.

{chr(10).join(group_tables)}

Families A–H retain their frozen labels: retrieval, multi-fact integration, validity intervals, relational chains, relevant historical distractors, entity disambiguation, current/past distinction and context follow-up. L1–L3 are designed levels, not observed difficulty. Each family has three cases; style/persona and task/history associations limit causal interpretation of differences between families.

## Concentration and boundary inspection

All five TRUNCATED records are in family G: G_L1/C2 (`P1B-CAL1-113`) and G_L3/C3/C5/C6/C7 (`143`, `141`, `139`, `144` respectively, with the same request prefix). The four G_L3 continuations visibly start with a `<think>` block and end mid-continuation at 96 tokens. This is an observed text/termination pattern, not a human factuality score. These four H-present cells belong to one case, so they do not provide four independent replications of a general history effect.

The single AMBIGUOUS result is B_L3/C0 (`P1B-CAL1-036`): it reaches EOG after 71 tokens, but its extracted span includes an unrecognized `Factual question:` label and generated question before another Assistant turn. It requires extraction adjudication; retain the frozen span and status. G_L1/C1 (`P1B-CAL1-120`) also reaches EOG, after 77 tokens, with an additional generated user/assistant exchange and is CROSS_TURN. EOG therefore neither guarantees one turn nor resolves semantic completeness.

C1−C0's CROSS_TURN increase is entirely B_L3's AMBIGUOUS-to-CROSS_TURN transition. C3−C0's net zero combines the B_L3 increase with G_L3's CROSS_TURN-to-TRUNCATED change. A lower CROSS_TURN rate is not automatically an improvement: it can represent unfinished continuation without an observed next-turn boundary. These sparse transitions are why raw paired values and separate semantic measurements matter.

## Paired exploratory contrasts

{contrast_table}

Every contrast above uses 24 case-level paired units, nested in 12 synthetic speakers. Exact case-level values, including zeros, are in [the contrast CSV](validation/p1b/calibration_v1/analysis_v1/structural_case_contrasts_v1.csv); summaries for all four structural outcomes and weights are in the analysis JSON. C1−C0 and C3−C0 are simple package contrasts. Main effects average four matched differences across the other factors. Two-way interactions are difference-in-differences averaged over the third factor; the three-way contrast differences those interactions. These scales are deliberately distinct and can have different numerical ranges.

The interval shown is **leave-one-speaker-out descriptive sensitivity**, not a confidence interval. No p value, population causal claim, significant effect or independent 192-observation inference is made. Finite-bank equality is not proof of a population null. Analysis code was prepared during execution after early raw responses were inspected; the weights came from the existing prospective precision plan, but these summaries are exploratory rather than confirmatory preregistration.

## Interpretation and Algorithmic Opportunity Assessment

Structural variation may affect measurement coverage, but cannot establish corresponding factual or temporal effects without semantic review. The existing Wave 1 labels (78 CROSS_TURN, 17 TRUNCATED, 1 AMBIGUOUS, 0 COMPLETE) remain historical; the banks and prompt configurations differ. Raw continuation rates alone do not establish a novel failure mode. A separately controlled boundary/template comparison may later test usable first-reply coverage, with false-cut and latency assessment, if review demonstrates a concrete need. No such comparison is executed here.

{source}
'''
    write('P1b_calibration_structural_analysis.md',structure)
    next_report=f'''# P1b Calibration Next Experiment Decision

{prefix}

## Current recommendation

**Complete condition-masked semantic review of the existing 192 outputs before authorizing more inference.** Execution is complete; semantic effect estimation and whether the Wave 1 ceiling was reduced remain pending. This decision does not reopen stimulus approval or require perfect model performance. It uses the information already purchased by the bounded CPU run.

| Option | Information value and trigger | Remaining confounds | Cost / decision |
|---|---|---|---|
| Score existing calibration | Establish factual/temporal discrimination, first-reply completeness and scorer coverage | Assisted/experienced single-researcher review must be disclosed; extraction uncertainty retained | Zero new generations; reviewer effort unmeasured. Recommended now |
| Expand Base on independent cases | Useful precision and replication only after coverage and variance are known | Speaker/style nesting, task templates and unchanged termination may persist | Eight calls per new case. No size or latency extrapolation asserted; not authorized |
| Separate Instruct arm | Could assess whether a different operational configuration improves usable dialogue measurement | Post-training, artifact provenance and native template may change together; not a pure post-training effect | A full 24-case eight-cell arm would require 192 new calls, with unknown per-call CPU cost. Later authorization and hashes required |
| Narrow boundary diagnostic | Valuable if complete first replies are obscured or false cuts materially distort contrasts | Stop strings alter generation opportunity; template differences need independent material | Bounded new allocation must be prospectively justified; no repeated tuning on these answers |
| Independent discriminative material / history R–T diagnostic | Useful if review reveals a specific ceiling or conditional history question | Relevance/time/task family are not separated here; new factors need explicit approval | No new candidate bank or calls now; use independent evidence and retain null/negative outcomes |

The immediate prerequisite is valid outcome measurement, not an algorithm or another model. Once reviewed, report complete denominators, case-paired estimates, speaker uncertainty, negative/null patterns and substantive unresolved ambiguity. The researcher decides the next arm. Neutral-control review remains OPEN; the prior 24 candidates are Wave 1 materials and do not authorize P1b matched comparisons.

## Novelty and publication relevance

The [existing novelty matrix](related_work_novelty_matrix.md) documents direct overlap in persona sensitivity, history-aligned factual distortion, memory selection and structural failures. A new cache-miss fetch does not invalidate or reverify an old literature record. Current primary-record checks are retained in [the access register](validation/p1b/calibration_v1/literature_access_v1.json).

*Principled Personas* already evaluates intended persona effects and sensitivity to irrelevant attributes; persona cues alone are not novel. [Primary record](https://aclanthology.org/2025.emnlp-main.1364/). *When Personalization Misleads* directly studies personalized factual distortion; its claimed mechanism is not proven by our package contrasts. [Primary record](https://aclanthology.org/2026.findings-acl.395/). A possible additional contribution would require reproducible evidence that separating structure from semantic support changes an S/F/H interpretation on independent material. This remains a falsifiable prospective claim, not a discovery from the current unscored bank.

PLOS ONE requires rigorous methods, supported conclusions and sufficient reproducibility, considers negative/null results, and asks close replications to provide a scientific rationale. Successful execution alone does not meet those conditions. [Journal criteria](https://journals.plos.org/plosone/s/criteria-for-publication). This calibration supplies auditable development evidence; independent validation, precision and contribution assessment remain necessary before a publication claim.

## Algorithmic Opportunity Assessment

The separate [assessment](P1b_calibration_algorithmic_opportunity.md) considers selection, temporal validity, style/evidence separation, response boundaries and verification. It recommends no algorithm implementation now. Natural continuation is observable; factual failure mechanisms and the benefit of a correction remain unestablished without review and identifying comparisons.
'''
    write('P1b_calibration_next_experiment_decision.md',next_report)
    algorithm=f'''# P1b Calibration Algorithmic Opportunity Assessment

{prefix}

## Observed Failure Modes

The observed structural distribution is **{statuses}**. Native termination is `{json.dumps(s['stop_counts'],sort_keys=True)}`. These observations support examining continuation and first-reply extraction; they do not establish factual errors or semantic incompleteness. The initial source/output discrepancy documented in [measurement](P1b_calibration_measurement_report.md) is a review target, not a validated causal mechanism. Human semantic outcome coverage is currently zero. The empirical research remains primary.

## Existing Methods

The repository already provides frozen role-transition extraction and separate semantic applicability. Prior work covers persona robustness and personalized factual distortion. Memory selection and presentation are explicitly separated in *What to Admit and How to Present*, which also reports personalization trade-offs; this is direct overlap, not a new decomposition invented here. [Primary abstract](https://arxiv.org/abs/2610.11188v1). LongMemEval already includes temporal reasoning and knowledge-update evaluation in long-term conversational memory. [Primary record](https://arxiv.org/abs/2410.10813).

The earlier [algorithmic assessment](P1b_algorithmic_opportunity_assessment.md) records additional overlap with Decoupling Logic from Persona and AlignScore. The attempted new fetch of Decoupling v2 returned a browser cache miss; no fresh verification or reproduction is claimed. All literature checks here are record/abstract scope, not a systematic full-text review.

## Potential Algorithmic Improvements

| Direction | Actual support and unresolved question | Necessary baselines and validation | Cost / publication value |
|---|---|---|---|
| Historical evidence selection | History is an operational factor; relevance is entangled with task family. No reviewed harmful-history effect yet | All-history, no-history, equal-budget random and relevance selection; preserve trusted evidence and independently measure memory utility | Rules are cheap; neural retrieval costs unmeasured. No novel selector justified now |
| Temporal validity handling | Tasks expose explicit intervals; the first observed reference mismatch motivates review, not a causal diagnosis | Date-aware lookup versus supplied-ledger baseline, paired date/reference controls, independent cases | Offline rules versus new generation arms have different costs; useful only if reviewed temporal failures reproduce |
| Style/evidence separation | No valid semantic S or S×H estimate yet; repeated style/persona realizations constrain scope | Single-pass sectioning, no style, matched-compute multi-pass baselines and independent fidelity evaluation | Extra passes cost additional inference. Architecture alone has strong prior overlap |
| Response boundary control | Repeated cross-turn continuation is directly observed | Frozen no-stop transcript, post-extraction, predeclared stop rules and a separately pinned native Instruct configuration; test false cuts and complete-answer retention | Offline parsing is cheap; new arms need authorization. Measurement validity is a plausible contribution, not a claimed new algorithm |
| Evidence-grounded verification | General semantic scoring is deliberately unimplemented; source queries are not free-text judges | Human-referenced claim-level evaluation, exact-match-with-abstention and suitable existing factuality metrics on held-out answers | Rules cheap, learned verification adds unmeasured compute. Do not fit a scorer to these outputs and report held-out accuracy on the same items |

## Validation Feasibility

First annotate and integrity-register the existing packet. Distinguish unsupported assertions, verified contradictions, incomplete answers, date confusion, speaker ambiguity and extraction errors. A prospective method becomes justified only if it targets a reproducible unresolved pattern and is compared on independent material with appropriate compute, evidence and fidelity controls. No algorithm code, new model, extra prompt arm or training is executed in this task.

## Publication Value

The strongest current deliverable is auditable measurement infrastructure and a bounded development observation set. Increased error counts would not themselves establish novelty. Supported conditional effects or changed conclusions under valid structural/semantic measurement could motivate a contribution, but must survive independent validation and direct prior-work comparison. Exact tokenization, CPU deployment, a factorial table and a larger generation count are insufficient originality claims.
'''
    write('P1b_calibration_algorithmic_opportunity.md',algorithm)
    # Exact commands and timing are carried in structured records, not invented narrative dates.
    register={'version':'p1b_calibration_command_register_v1','created_utc':utc_now(),
              'captures':{name:{k:v for k,v in value.items() if k in ('argv','started_utc','finished_utc','exit_code','duration_seconds','scope')} for name,value in captures.items()},
              'full_local_capture_directory':(LOCAL/'engineering').as_posix(),
              'inspection_helper_error':core.load(LOCAL/'inspection_helper_error.json'),
              'scope':'Captured engineering/execution commands; exploratory read-only shell inspection and apply_patch file edits are described in the development log, not fabricated as captured process commands.'}
    atomic_json(PUBLIC/'command_register_v1.json',register)
    log=f'''\n\n## {utc_now()} — P1b authorized development calibration and offline measurement preparation

Maintainer/researcher: Yaxin ZHENG. Formal Protocol v1.1 unchanged; v1.2 remains a proposal. Objective: register explicit researcher stimulus approval, execute exactly the frozen 192-request Base calibration and preserve valid measurement denominators. This entry supplements all earlier preparation records without rewriting their pending states.

**Approval and inputs.** Registered 24 cases and 312 judgments as researcher confirmation of AI-assisted assessment, with actual user-message authority; no invented review timestamp or blinded outcome review. Dataset `{core.DATA_SHA}`, manifest `{core.MANIFEST_SHA}`, model `{core.MODEL_SHA}`, backend `{core.BACKEND_SHA}`. Git HEAD `{manifest['git']['sha']}`, dirty at execution because of new uncommitted registration materials. No Git write operation was performed.

**Executed commands and evidence.** Exact child argv, timestamps, exits and durations are in [the command register](validation/p1b/calibration_v1/command_register_v1.json), with full stdout/stderr under `{LOCAL.as_posix()}/engineering/`. Executed approval transcription/import, mandatory static preflight, authorization binding, the real run, offline analysis/reconstruction and tests. Read-only inspection used PowerShell Get-Content/Get-ChildItem, rg, Git status/rev-parse and inline Python JSON/CSV/hash checks; repository file edits used the patch tool. These inspection/edit operations are not represented as invented subprocess capture files. Browser primary-source accesses and a cache miss are separately registered.

**Actual execution.** Run `{s['run_id']}`: 192 attempted, 192 raw responses, 192 results, zero failed requests, no retries or additional waves. All 192 live native tokenizations matched frozen IDs before completion; input range150–434, context4096, output96, temperature0, seed42, order seed714001, CPU4/batch4, GPU offload0/25. Same evidence/question/context/reference and native decoding retained. Source snapshots, request order, raw HTTP bytes, output IDs, native termination, parser spans and source hashes are preserved. No new inference source implementation was needed.

**Measurements.** {statuses}. Four semantic axes remain PENDING under frozen manual routing: factual192, temporal88, relevance192, coherence192 eligible. No human output label or automatic correctness score invented. Prepared a condition-masked192-row packet with separate local mapping; structural contrasts use24 paired cases and12 speaker clusters, with descriptive leave-one-speaker-out sensitivity and no significance claim. New offline code was written during execution, after initial raw inspection; this is disclosed as exploratory analysis.

**Errors and correction.** The initial inspection-only helper used str where Path was required, raised AttributeError, and was corrected before official mandatory preflight. Its error is preserved. Optional CIM access was denied; PowerShell returned0 with null fields and stderr, so hardware fields are marked unavailable rather than verified. Optional Decoupling v2 browser fetch returned cache miss. Mandatory static/live preflight and execution passed without changed settings. No failed mandatory preflight was bypassed.

**Validation.** Pre-generation full suite631passed; new offline accounting tests13passed; final suite `{test['stdout'].strip().splitlines()[-1]}`, exit0. Native transport, prompt/input, output-byte/parser reconstruction, JSON/CSV and historical preservation evidence are linked from [execution](P1b_calibration_execution_report.md). The separate final integrity record retains all old failed/interrupted journal statuses rather than relabelling them as successful experiments.

**Files.** Added registration/analysis/report/verification tools, offline accounting tests, the `calibration_v1` approval/analysis artifacts, outcome review guide, and five calibration reports. Only this historical development log is appended; earlier experiment sources and documents remain unchanged. All changes remain uncommitted for researcher review.

**Limitations and decision.** No semantic ceiling conclusion, factual/temporal effect, pure history mechanism, independent style effect, algorithmic originality or publication readiness is established. H_L1/L2 context shortcuts, H_L3 User/User format, relational/entity shortcuts, style/persona nesting, task/history confounding and96-token censoring remain visible. Prior Wave1 neutral controls remain OPEN and do not transfer to P1b. Recommended next action is semantic review of existing outputs, not additional inference. No later phase, training, unrelated project access or extra wave occurred.
'''
    with Path('docs/research_development_log.md').open('a',encoding='utf8',newline='\n') as f:
        f.write(log)
    print(json.dumps({'reports_created':5,'development_log':'appended','semantic_outcome_review':'PENDING','new_generation_requests':0}))


if __name__=='__main__':
    main()
