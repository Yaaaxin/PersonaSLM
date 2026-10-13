"""Create the versioned offline measurement report package without replacing history."""
from collections import Counter
import json
from pathlib import Path

from personaslm.journal import atomic_json, utc_now
from p1b_measurement_audit import OUT, LOCAL, OLD, core, digest, write_csv, RISKS

HEADER = ('Maintainer: Yaxin ZHENG. Formal experimental baseline: Protocol v1.1. '
          'Protocol v1.2 Revised Proposed r1 remains prospective and unadopted. '
          'Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. '
          'First submission target: PLOS ONE. Development evidence only; no new inference.\n\n')
LINK = 'validation/p1b/measurement_audit_v1/'


def table(headers, rows):
    def cell(x):
        return str(x).replace('|', '\\|').replace('\n', '<br>')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                     ['| ' + ' | '.join(cell(x) for x in r) + ' |' for r in rows]) + '\n\n'


def put(name, title, content):
    with (Path('docs') / name).open('x', encoding='utf-8', newline='\n') as f:
        f.write('# ' + title + '\n\n' + HEADER + content)


def main():
    stats = core.load(OUT / 'audit_summary_v1.json')
    previous = core.load(OLD / 'analysis_v1.json')
    rows = core.csv_records(OUT / 'response_boundary_audit_v1.csv')
    tasks = core.csv_records(OUT / 'task_discrimination_inventory_v1.csv')
    cases = {c['case_id']: c for c in core.load(core.DATA)['cases']}
    source = core.csv_records(OLD / 'output_human_review_v1.csv')
    mapping = core.load(LOCAL / 'protected/treatment_mapping_v1.json')
    by_request = {r['request_id']: r for r in rows}
    by_alias = {r['anonymous_response_id']: r for r in source}
    assistance = []
    for m in mapping['responses']:
        r, original = by_request[m['request_id']], by_alias[m['anonymous_response_id']]
        case = cases[r['case_id']]
        notes = [RISKS[case['family']],
                 'Assess each delivered proposition and each required component separately; no correctness prediction supplied.']
        if r['first_reply'].lstrip().startswith('I will check'):
            notes.append('Literal prospective-action opening. Determine whether this wording actually supplies the requested answer; do not use the phrase alone as a semantic classifier.')
        if r['structural_status'] == 'TRUNCATED':
            notes.append('Full 96-token continuation retained with no excluded tail. Text ends mid-continuation; no parser-deleted final answer is visible. Completeness and factual support still require distinct human judgments.')
        if r['explicit_think_open_unclosed'] == 'True':
            notes.append('Visible unclosed <think> block; no separately delimited final answer follows it. Assess any assertions without inventing a final answer.')
        if r['unit_identifiable'] == 'False':
            notes.append('Frozen extraction is unconfirmed: span contains Factual question: before a later Assistant label. Retain the span; do not score the later speaker as the original answer. Explicit unit adjudication required.')
        assistance.append({'assistance_version':'p1b_review_assistance_observations_v1',
            'anonymous_response_id':m['anonymous_response_id'], 'authorship':'Automated extraction and AI-assisted analytical guidance; not human annotation',
            'verbatim_first_reply':r['first_reply'], 'verbatim_trusted_evidence':case['trusted_evidence'],
            'required_answer_components':json.dumps(case['expected_answer']['components'],sort_keys=True),
            'analytical_notes':' '.join(notes), 'suggested_factual_label':'', 'suggested_temporal_label':'',
            'human_confirmation':'', 'use':'Optional after initial scoring; record actual access. No automatic registration.'})
    write_csv(OUT / 'optional_AI_assisted_observations_v1.csv', assistance)
    promises = [r for r in rows if r['first_reply'].lstrip().startswith('I will check')]
    atomic_json(OUT / 'diagnostic_observations_v1.json', {
        'version':'post_output_text_observations_v1', 'created_utc':utc_now(),
        'selection':'Every response inspected; text-pattern flags and all structural exceptions retained. No cases excluded.',
        'prospective_check_opening_count':len(promises), 'prospective_check_opening_requests':[r['request_id'] for r in promises],
        'pattern':'first_reply.lstrip().startswith("I will check")',
        'interpretation':'Literal surface pattern, not 17 human-confirmed missing answers; embedded answer references need adjudication.',
        'truncated_requests':[r['request_id'] for r in rows if r['structural_status']=='TRUNCATED'],
        'ambiguous_requests':[r['request_id'] for r in rows if r['structural_status']=='AMBIGUOUS'],
        'automated_semantic_labels':0})
    atomic_json(OUT / 'future_semantic_analysis_contract_v1.json', {
        'version':'p1b_semantic_analysis_pre_review_v1', 'created_utc':utc_now(),
        'timing':'After generation and raw inspection, before human scoring; exploratory, not preregistration',
        'formal_policies':['response_status_v1','separate_axes_policy_v1','p1b_manual_semantic_routing_proposed_v1'],
        'weights':__import__('personaslm.p1b_readiness',fromlist=['contrast_weights']).contrast_weights(),
        'eligible':{a:previous['coverage'][a]['eligible'] for a in core.AXES},
        'units':{'cases':24,'speaker_clusters':12,'temporal_cases':11,'temporal_speaker_clusters':9},
        'categorical_outcomes':['Correct','Incorrect','Unverifiable','Not Applicable'],
        'ordinal_scale':[1,2,3,4,5], 'human_answer_delivery_role':'Additional diagnostic only, not replacement of four primary metrics',
        'denominators':'All pre-eligible rows; no C0-correct filter. Show every category, missing and assessed-only descriptions separately.',
        'unknowns':'Unverifiable/explicitly missing remain unknown; propagate case-wise min/max bounds under each contrast weight, then aggregate.',
        'sampling':'Whole-speaker resampling retains every case and condition; purposive templates and small clusters limit generalization.',
        'boundary_disagreement':'Preserve original span and stage-1 record; document adjudication separately before primary scoring. Alternative spans are a named sensitivity version.',
        'multiplicity':'No significance claims; intervals exploratory, not simultaneous. Future confirmation needs a chosen endpoint hierarchy and multiplicity plan.',
        'neutral_adjusted_effects':'NOT_PERMITTED: controls OPEN', 'semantic_effects_computed':False})

    put('P1b_calibration_semantic_review_guide.md', 'P1b Calibration Semantic Review Guide — v2', f'''## Start with the semantic view

Use [semantic_scoring_view_v2.csv]({LINK}semantic_scoring_view_v2.csv), containing all 192 records, stable BR001–BR192 response IDs and BC case aliases. Presentation was independently shuffled with seed **714003**, distinct from execution order 714001 and original alias shuffle 714002. This new order was chosen during the post-generation audit; it is not a claim of pre-generation blinding. Do not sort by case before the first pass.

The first view includes the question, sufficient trusted evidence, question/reference date, fixed context, reference answer components, case-level historical source, first-reply text, hashes and frozen applicability. It excludes conditions, factors, request/execution identifiers, automatic predictions, structural categories, stop reasons, token counts and full continuation. Expected components are references for human evaluation, not labels on model outputs.

Save a completed copy. **All supplied human fields are blank.** Do not open this audit's treatment analyses or assistance file before initial scoring if minimizing anchoring is desired. Evidence IDs, recognizable speakers, repeated answers, style and model-generated content may reveal cues. Prior researcher knowledge cannot be erased. This is condition-label masking, not a guarantee of perfect blinding or independent annotation.

## Two-stage unit verification

1. Record initial semantic judgments on the unchanged extracted span. If its attribution or meaning is unclear, use UNCERTAIN completeness and an explicit missing-metric reason; do not force a factual label. Save this initial version before the next step.
2. Open [structural_review_view_v2.csv]({LINK}structural_review_view_v2.csv). It has the same response IDs/order, full original continuation, exact parser spans/tail, frozen status and native termination. Confirm the reply unit as PASS / FAIL / UNCERTAIN and quote boundary issues. Do not modify text, offsets, hashes or labels.
3. Preserve initial scores, then save any researcher-confirmed corrections as a separate version with a reason. A disputed unit remains in all eligible denominators. The one AMBIGUOUS span needs explicit adjudication; there is no fabricated replacement reply. An alternative span requires a named sensitivity record, never a silent rewrite of response_status_v1.

The full continuation is secondary evidence for attribution, not permission to credit a later generated Assistant answer to the first reply. Generated later questions/answers can be wrong even if the first reply is correct, or vice versa. Do not silently combine those units.

## Frozen meanings and allowed labels

The [annotation guidelines](annotation_guidelines.md), [routing](validation/p1b/final_v1/evaluation_routing_v1.json) and [original guide](P1b_calibration_output_review_guide.md) retain authority. This split presentation changes no primary metric definitions.

| Field | Meaning / allowed values |
|---|---|
| human_semantic_completeness | COMPLETE / INCOMPLETE / UNCERTAIN: whether the requested first reply is delivered, separately from factual support |
| human_factual_consistency | Correct / Incorrect / Unverifiable / Not Applicable; evaluate delivered propositions against evidence, including contradictions, negation and attribution |
| human_temporal_consistency | Same categories; apply each proposition/question date and inclusive intervals, not automatically the global date |
| human_response_relevance_1_to_5 | Existing 1–5 scale: 1 non-responsive, 3 partially responsive, 5 adequately responsive; preserve intermediate ratings |
| human_conversational_coherence_1_to_5 | Existing 1–5 scale: continuity and reference use within the fixed dialogue context |
| human_answer_delivery | DELIVERED / PARTIAL / NOT_DELIVERED / UNCERTAIN; separately versioned diagnostic of requested answer delivery, not a new primary score |
| human_required_components_notes | Quote which requested components were supplied or missing; a component list is not a substring-scoring rule |
| human_missing_metric_reason | Name any eligible metric left unscored and explain why; blank remains missing, never zero or retrospective N/A |

A verified false final assertion supports Incorrect. A claim without evidence or resolvable attribution supports Unverifiable, not necessarily Incorrect. An unfinished reply with supported assertions may be factually Correct but INCOMPLETE; a promise to check with no assessable factual answer may be Unverifiable. Do not infer support from an answer name appearing somewhere in text. Consider all delivered propositions and date/entity relations. A complete but irrelevant answer can receive low relevance independently of factuality. Correct first answer plus generated dialogue is not automatically a factual failure.

Factual eligibility is 192, temporal 88, relevance/coherence 192 each; temporal N/A is 104. No output is excluded because of structure or C0 correctness. Persona Fidelity is neither rated nor combined with these endpoints. PENDING describes workflow, not a fifth factual category. Missing human scores and semantic Unverifiable are different counts.

## Assistance, provenance and validation

[Optional AI-assisted observations]({LINK}optional_AI_assisted_observations_v1.csv) provide source quotations and questions, without suggested correctness labels. Use only after the initial pass if wanted; disclose access. It is not human annotation. Enter actual reviewer identity, assistance and prior access; record a review time only when actually known. No second reviewer, agreement statistic or consensus is presumed.

Validate a completed semantic copy with:

```powershell
.\\.venv\\Scripts\\python.exe tools/p1b_measurement_audit.py validate-review --master docs/validation/p1b/measurement_audit_v1/semantic_scoring_view_v2.csv --completed PATH_TO_COMPLETED_COPY.csv
```

Use the same command with the structural master to validate its completed copy. The command checks IDs, every immutable field, labels, applicability, provenance and explicitly explained missingness; it does not certify semantic truth, import judgments, invent dates, or unblind results. Explicitly missing judgments are reported as missing even when the file passes schema validation. Keep both initial and corrected versions; register only after the researcher confirms them and boundary dispositions are reconciled.

The treatment mapping is stored separately under local ignored `results/p1b_measurement_audit/v1/protected/`; its digest is in the audit summary. Local separation is not encryption or filesystem access control. Share only the intended stage's CSV and this guide, not the analyst artifacts. A later genuinely independent reviewer may receive a separately masked, prospectively stratified subset; retain both originals before adjudication and calculate agreement only from actual paired human labels.

## Algorithmic Opportunity Assessment

This packet is measurement preparation. It neither implements a new answer-selection algorithm nor approves one. Boundary disagreement and semantic error patterns must first be measured before considering mitigation; see [the assessment](P1b_calibration_algorithmic_opportunity.md).
''')

    ci=core.load(OUT/'structural_uncertainty_v1.json')['results']
    cross=[r for r in ci if r['outcome']=='CROSS_TURN']
    coverage_table=table(['Outcome','Eligible','Automatic semantic scores','Human scores','Pending','Frozen N/A'],
        [[a,v['eligible'],0,0,v['pending'],v['inapplicable']] for a,v in stats['semantic_coverage'].items()])
    contrast_table=table(['Contrast','CROSS_TURN change (pp)','Exploratory cluster percentile interval (pp)'],
        [[r['contrast'],f"{r['estimate']*100:.3f}",f"[{r['lower_percentile_95']*100:.3f}, {r['upper_percentile_95']*100:.3f}]"] for r in cross])
    put('P1b_calibration_measurement_audit.md','P1b Calibration Scientific Measurement Audit — v1',f'''## Audit result and scope

**Instrumentation PASS; semantic measurement OPEN.** Replayed all **192 attempted / 192 completed / 0 failed** requests from run `{stats['run_id']}`. No responses were regenerated or changed. All saved HTTP response bytes, raw text hashes, prompt/ID/count associations, first spans and parser operations were reconciled; all 192 original review records reconstruct exactly. Current audit baseline Git HEAD is `{stats['git_sha']}`; it was clean at the initial inspection. New work is uncommitted. Historical execution Git state remains in its manifest.

The journal has {stats['journal_events']} events and terminal hash `{stats['journal_terminal_hash']}`. [Native transport re-audit]({LINK}native_transport_reaudit_v1.json), [identity re-audit]({LINK}offline_identity_reaudit_v1.json), [summary]({LINK}audit_summary_v1.json) and [all-response audit]({LINK}response_boundary_audit_v1.csv) contain the evidence. The dataset and frozen manifest hashes remain `{core.DATA_SHA}` and `{core.MANIFEST_SHA}`.

Model hash `{core.MODEL_SHA}` and backend hash `{core.BACKEND_SHA}` were recalculated from the actual local files. The recorded backend is llama.cpp b11573, commit 0f701c882. Native tokenizer response IDs, submitted IDs and evaluated counts match for all 192 prompts. The backend did not return a separate evaluated-input-ID array; this limitation remains explicit. Output IDs are retained. This task replays original real-tokenizer evidence; it does not claim a new live tokenizer observation. Configuration remains CPU 4 threads, context 4096, temperature 0, seed 42, 96-token budget, order seed 714001; inputs 150–434 tokens and no context truncation.

## What boundary inspection adds

Frozen distribution: COMPLETE **0**, TRUNCATED **5**, CROSS_TURN **186**, AMBIGUOUS **1**. Identifiable first spans: **191/192**. Raw and first-span empty counts: **0**. Native stops: length **190**, EOS/EOG **2**. The 186 role-crossing continuations contain multiple visible role markers; marker counts are textual diagnostics, not independently verified discourse turns. Every removed prefix, first span and excluded tail reconstructs the raw text exactly.

COMPLETE under response_status_v1 requires an independent completeness certification that was not supplied during generation. Its zero count does not say all replies failed semantically. Budget termination concerns the full continuation, which may spend most tokens after a completed first reply. EOS likewise does not certify a single response.

| Request / case | Direct observation | Measurement disposition |
|---|---|---|
| 113 / G_L1 C2 | Ends `so it is valid on 2027` at 96 tokens; no excluded tail. Earlier date comparisons and Harbor Lodge are visible | Unfinished date/final clause; assess supported partial content separately. No evidence that the parser removed a completed answer |
| 139 / G_L3 C6 | Unclosed `<think>`; ends `Since March 20` | Reasoning continuation without a separately delivered final answer; human judgment pending |
| 141 / G_L3 C5 | Unclosed `<think>`; ends `The third is for ` | Missing final completion; also inspect the visible date/site assertions independently |
| 143 and 144 / G_L3 C3,C7 | Identical raw prefixes end `2027-03-3`; unclosed `<think>` | Preserve both paired cells, not two independent confirmations; no inferred next tokens |
| 036 / B_L3 C0 | 71-token EOS; first span contains `Factual question:` and a generated question, followed by another Assistant answer in the tail | **Required boundary adjudication.** Frozen AMBIGUOUS / unit_identifiable=false remains. No alternative first reply fabricated |
| 120 / G_L1 C1 | 77-token EOS with another User/Assistant exchange | EOS and CROSS_TURN coexist; judge the first response separately |

All five truncations end at the actual output limit; all retain their complete raw visible prefix with empty excluded tail. Four are the H-present cells of **one** G_L3 case. This supports an observed association in this bank, not a causal claim that history induces reasoning or that a larger budget would solve it. No controlled budget/template comparison was run.

There are **17 first spans literally starting `I will check`**, across B_L2, F_L1, G_L2, H_L1 and H_L2. Some mention a candidate location; do not equate the pattern with 17 confirmed missing answers. D-family first replies often give a crate/locker statement where the question requests a room/building. These observations show why grammatical or factually supported text can still fail to deliver the requested answer. [Diagnostic observations]({LINK}diagnostic_observations_v1.json) retain the complete ID list. No semantic scores were inserted.

## Semantic coverage and denominator policy

{coverage_table}
No assessed Unverifiable count or factual/temporal accuracy can yet be estimated. Missing judgments are 192/88/192/192 as appropriate; they are not failed answers. One unit needs boundary adjudication, five raw prefixes are structurally censored, and human completeness for all 192 is pending. The incomplete/ambiguous units remain eligible. Automatic scorer coverage is zero by design: the city scorer is not used outside its scope.

The split [review guide](P1b_calibration_semantic_review_guide.md) and two review views are ready. Preserve partial factual support independently of answer delivery, temporal attribution, relevance and coherence. False assertions differ from unsupported assertions; missing answers differ from false answers; extra turns differ from first-reply content. Ceiling reduction remains **unverified** until review.

## Structural pairing and uncertainty

{contrast_table}
Each contrast uses all 24 cases nested in 12 speakers. Weights remain the frozen simple/average-main/averaged-interaction definitions; [paired values]({LINK}structural_case_contrasts_v1.csv) retain zeros and failures. C1−C0's +4.167pp comes from B_L3's ambiguous-to-cross-turn transition alone. C3−C0's zero nets that transition against G_L3's cross-turn-to-truncated transition. Neither is a semantic effect or proof of a population null.

Intervals are a **new, post-output exploratory sensitivity analysis**, seed 714004, 10,000 whole-speaker resamples, with all of each sampled speaker's cases/cells. They are percentile intervals for resampling this purposive bank, not guaranteed population confidence, simultaneous intervals or significance tests. Sparse/zero outcomes can produce misleadingly narrow or degenerate intervals. The prior leave-one-speaker-out analysis remains unchanged. The full four-status results are in [the uncertainty file]({LINK}structural_uncertainty_v1.json).

For eventual semantic analysis, [the pre-review contract]({LINK}future_semantic_analysis_contract_v1.json) retains 24 factual paired cases/12 clusters, 11 temporal cases/9 clusters, each condition's factual24/temporal11 denominators, four distinct endpoints, and no C0-correct filtering. Show Correct/Incorrect/Unverifiable/missing/N/A separately. Unknown-outcome bounds propagate within-case signed weights before aggregation; assessed-only descriptions cannot replace the eligible denominator. Ordinal distributions and paired changes accompany descriptive means. No final semantic contrasts are computed now.

## Remaining gates and Algorithmic Opportunity Assessment

Human semantic scoring, unit adjudication and truthful review provenance are required before outcome claims. Neutral controls remain OPEN and no neutral-adjusted comparison is available. Statistical precision, independent material and model/generalization checks remain publication work, not reasons to regenerate this bank. The strongest immediate action is to score existing outputs; [publication readiness](P1b_calibration_publication_readiness.md) and [algorithmic assessment](P1b_calibration_algorithmic_opportunity.md) explain the next gates.

Reproducibility commands, test results, preservation checks and file hashes are retained in [delivery evidence]({LINK}delivery_v1.json). The audit code is [p1b_measurement_audit.py](../tools/p1b_measurement_audit.py). The complete original run remains local; public derivatives alone are not a substitute for archiving native journals and the protected mapping for controlled later unblinding.
''')

    task_table=table(['Case','Components','Facts / query steps','Temporal','Identifiable / 8','Truncated / 8'],
        [[r['case_id'],r['required_components'],r['source_facts']+' / '+r['query_steps'],r['temporal_eligible'],r['identifiable'],r['truncated']] for r in tasks])
    family_table=table(['Family','Intended demand','Identifiable / 24','Interpretation limit'],[
        [f, next(c['task_family'] for c in cases.values() if c['family']==f),
         sum(int(t['identifiable']) for t in tasks if t['family']==f), RISKS[f]] for f in 'ABCDEFGH'])
    put('P1b_calibration_task_discrimination.md','P1b Calibration Task Discrimination Audit — v1',f'''## Capacity versus demonstrated discrimination

The bank provides differing evidence operations and measurable candidate omissions/date mismatches. **It has not yet demonstrated a lower factual ceiling or an empirical difficulty ordering.** All 24 cases and all eight cells remain; no selection depends on C0 or a desired S/F/H direction. Source/query validation establishes answerability, not correctness of model replies or their internal reasoning process.

{family_table}
## Every case retained

{task_table}
The [24-case inventory]({LINK}task_discrimination_inventory_v1.csv) includes component references, evidence/question/context hashes, proof length, history relevance and structural coverage. Facts and steps are source counts, not complexity scores. Temporal applicability is 11 cases: C/E/G (three each) and H_L2/H_L3. Other facts carry validity metadata, but the predeclared task metric is not retrospectively changed.

## Evidence dependency and shortcuts

A is a valid easy direct-retrieval baseline; more distractors need not make it difficult. B adds required answer components, making brevity/96-token demand a competing explanation for incomplete answers. D's source path has two to four steps but a unique terminal entity permits shortcut selection; a correct building name cannot prove multi-hop reasoning. F often has explicit IDs or a unique archivist and terminal shelf. Keep these as measured lookup tasks rather than claim difficult ambiguity resolution.

C and G require selecting validity intervals at question-specific dates; explicit date tables reduce reasoning demands. C_L3 asks for a preceding-day value, while G_L3 asks two sites. E adds a relevant old residence, but relevance, domain and temporal task demands are not independently crossed. H_L1/H_L2 remain simple follow-up baselines with no demonstrated necessity for context; H_L3 retains consecutive User turns, so a format influence cannot be excluded. No source was edited in this audit.

## Observable review targets, not registered ratings

- The first execution request (C_L1) names Maple Counter whereas its April 5 reference is Birch Counter. This longstanding execution-order example motivates date-sensitive review; it is not a human error count.
- Some B replies omit a requested role; D replies may state crate assignment when a room or building is requested. Supported intermediate facts and complete answers must not share one label by default.
- All eight H_L2 first spans start with a promise to check rather than a declarative desk answer. F_L1 promises sometimes name a shelf, so the literal pattern alone cannot score delivery.
- The five G truncations and one B boundary ambiguity constrain unit coverage; other 186 CROSS_TURN replies still require semantic inspection.

Require source quotations and component-level notes to determine whether date selection, missing requested content or an unsupported statement caused low coverage. Extra gendered pronouns or incidental personal assertions, where unsupported, should be inspected rather than silently treated as attested speaker attributes. Do not award correctness for expected-word occurrence in later turns.

## Identification and next use

Within a case, evidence, question, fixed context, evaluation reference and model settings are identical across C0–C7. S/F/H add intervention packages that also alter length and content. Style is partly nested within speaker, F uses limited fact realization, and history relevance is partly nested within task family. No pure length-independent style, history-presentation or temporal-conflict mechanism is identified. P1 matched controls remain unreviewed; old approvals do not transfer.

Designed L1/L2/L3 outputs show 1/0/4 TRUNCATED responses respectively and one L3 ambiguity. These small, confounded counts do not establish monotonic difficulty. All cases remain development material; future independent tasks need orthogonalized templates/entities/date positions and untouched evaluation examples after an explicit design decision, not selection to manufacture persona effects.

## Algorithmic Opportunity Assessment

The current opportunity is improved measurement of supported-but-undelivered answers. A new reasoning algorithm is unjustified before reviewed errors reproduce. Retrieval or temporal-selection methods would need separate evidence-controlled baselines and independent material; no algorithm or new stimulus is implemented here.
''')

    put('P1b_calibration_wave_comparison.md','P1 Wave 1 versus P1b — Measurement Comparison',f'''## Verified descriptive comparison

Wave 1 confirmed labels and all immutable review fields were checked against its original masked master and saved SHA-256. P1b was reconstructed from its native journal. [Wave 1 comparison inputs]({LINK}wave1_verified_comparison_inputs_v1.json) retain the checks; historical annotations and automatic scores are untouched.

| Dimension | P1 Wave 1 | P1b calibration |
|---|---:|---:|
| Real responses / paired cases / speakers | 96 / 12 / 12 | 192 / 24 / 12 |
| COMPLETE / TRUNCATED / CROSS_TURN / AMBIGUOUS | 0 / 17 / 78 / 1 | 0 / 5 / 186 / 1 |
| CROSS_TURN rate | 81.25% | 96.875% |
| TRUNCATED rate | 17.708% | 2.604% |
| Frozen identifiable first units | 96/96 (including ambiguous MR069) | 191/192 |
| Human completeness | 79 COMPLETE, 17 INCOMPLETE | All 192 pending |
| Factual eligible / human scored | 72 / 72 | 192 / 0 |
| Temporal eligible / human scored | 48 / 48 | 88 / 0 |
| Relevance and coherence human scored | 96 each | 0 each |
| Confirmed factual / temporal Correct | 72/72 and 48/48 | Not estimated |
| Budget termination / EOS | **95 / 1** | **190 / 2** |
| Budget termination proportion | 98.958% | 98.958% |
| Task families | Four, including nonfactual greeting | Eight evidence-grounded families |

Wave 1 MR069 was AMBIGUOUS despite unit_identifiable=true and a subsequently confirmed complete reply. P1b's B_L3 ambiguity instead has unit_identifiable=false. These flags have different meanings; ambiguous counts alone cannot measure extraction coverage. Wave 1's 28-token EOS response prevents an inaccurate statement that all 96 outputs exhausted their budget.

The +15.625pp CROSS_TURN and −15.104pp TRUNCATED differences are descriptive across different banks. They cannot show improved or worsened semantic reliability. No comparable P1b human completeness or correctness rate exists yet. Historical Wave 1 automatic factual coding (15 Correct/57 Unverifiable) is scorer coverage under its limited grammar, not evidence to subtract from P1b's pending annotations.

## Why this is not a difficulty experiment

Task content, applicability, component counts, persona assignments, prompt construction and explicit fictional evaluation-date exposure differ. Both arms use the same Base model/backend and 96-token budget, but one changes task demands as a package. Relevance/history, evidence length and fixed context are not equal across waves. There are two P1b cases per synthetic speaker, versus one Wave 1 case; treating the extra responses as independent would overstate precision.

A future controlled test would hold speaker/style realization, S/F/H content, answerable evidence, template/date exposure, question family, inference and scoring unit constant, while prospectively manipulating one justified demand. Difficulty and answer length must be disentangled where possible. Independently constructed examples, all paired cells, explicit budget treatment and unit adjudication are needed. That proposal is not executed or silently added to Protocol v1.1.

## Algorithmic Opportunity Assessment

Equal budget-saturation proportions across different banks do not prove an invariant model mechanism. Persistent continuation motivates an operational model/template comparison, while confirmed first-reply annotations are needed to establish what it would improve. No boundary algorithm or extra generation is required to complete the current review.
''')

    put('P1b_calibration_instruct_arm_proposal.md','Prospective P1b Instruct Configuration Arm',f'''## Decision

**Scientifically plausible, not authorized or launched. First finish the current semantic review.** Persistent transcript continuation and 190/192 budget stops justify asking whether a native dialogue configuration yields more usable first replies. They do not establish semantic failure on all those outputs. No new model artifact was downloaded, tokenized or executed.

## Candidate and provenance gate

Candidate: the official **Qwen/Qwen3.5-2B** post-trained model, not an invented `-Instruct` repository name. The official card describes 2B language-model parameters and a post-trained checkpoint, with non-thinking mode the default. [Official model card](https://huggingface.co/Qwen/Qwen3.5-2B).

Use its official `chat_template.jinja`, which renders role delimiters and handles thinking configuration; the inspected template inserts a closed empty thinking block by default when adding the assistant generation prefix. [Official template](https://huggingface.co/Qwen/Qwen3.5-2B/blob/main/chat_template.jinja). This source was inspected on a moving main branch for planning; **no arm revision, converted GGUF hash or tokenizer hash is frozen yet**.

Before approval, pin upstream model/config/tokenizer/template revisions, selected quantized artifact publisher and conversion provenance, GGUF SHA-256 and metadata, executable/build hashes, native chat rendering and special-token behavior. Verify text-only operation, CPU/context support on the chosen backend; do not silently upgrade b11573 if unsupported. Quantization identity does not prove upstream training equivalence. Missing provenance is a preparation gate, not filled with the Base model's hash.

## Prospective comparison contract

Preserve all 24 case contents, evidence/questions/reference dates, S/F/H routing, predeclared metric applicability, seeds and within-arm randomized order. Evaluate every C0–C7 cell. Neutral controls remain excluded while semantic review is OPEN. Compare the same cases across configurations with paired, speaker-clustered reporting and masked review using the same four axes and separate answer-delivery/structure measures.

Proposed resource-matched starting point: 4 CPU threads, context4096, temperature0, seed42, output96. The candidate's native non-thinking configuration is explicit; Base has no equivalent guaranteed switch. Native template, special tokens and checkpoint/post-training differ jointly. This is an **operational configuration-sensitivity comparison**, not identification of a pure post-training effect. Temperature0 is a deliberate comparability proposal, not a claim that it is the vendor's recommended benchmark setting. A different budget/decoding regime needs a separately approved arm; do not change it after viewing results.

Native chat stop/EOG markers must be logged separately from semantic completeness. Preserve response_status_v1 results as historical measurements; validate any chat-specific delimiter adapter on independent fixtures and version any additional structural diagnostic. Do not force rendered chat output through a transcript interpretation without checking false cuts and excluded text.

## Scientific value, cost and limits

Measure semantic scoring coverage, first-reply completeness, instruction relevance, factual/temporal category distributions and structural continuations independently. Support for the feasibility hypothesis would be improved usable-answer coverage without hiding unknowns, backed by unit verification; unchanged or worse coverage would weaken it. Correctness improvement is not a required or assumed direction. Shared-case findings are developmental; independent material is still necessary for confirmation.

A full paired arm would require 192 additional calls **only after authorization**. Observed Base summed request latency was {previous['latency_seconds']['sum']:.3f}s, mean {previous['latency_seconds']['sum']/192:.3f}s/request, about {previous['latency_seconds']['sum']/60:.2f}minutes. A planning range of 1–3 times that cost is roughly35–105minutes, excluding setup, artifact preparation, failures and annotation; it is not measured Instruct performance. Quantization, tokenization and actual reply lengths can change cost. Do not expand case counts to spend a budget.

If current review instead finds that first replies already support reliable semantic measurement, prioritize independent discriminative cases and precision over a new model. If extraction errors dominate, a small independently designed boundary diagnostic may provide more information than all192 new calls. The researcher selects the next experiment after review; no automatic launch is permitted.

## Algorithmic Opportunity Assessment

Native template/EOG handling is an established configuration baseline. Demonstrating that it changes an S/F/H interpretation could support a measurement study; using it is not an algorithmic novelty. No new architecture, training, response selection or post-processing optimization is proposed for immediate implementation.
''')

    put('P1b_calibration_novelty_assessment.md','P1b Measurement Evidence and Novelty Assessment',f'''## Evidence level

Current findings establish preserved outputs, transcript continuation, sparse structural transitions and a need to distinguish supported assertions from delivered answers. Human semantic effects remain unknown. The existing [novelty matrix](related_work_novelty_matrix.md) is preserved. This update uses primary records/abstracts and an official template, not an exhaustive systematic review or replication. Newly accessed pages and the failed retrieval are listed in [source access evidence]({LINK}literature_access_v1.json).

| Prior work | Direct overlap | What P1b does and does not add |
|---|---|---|
| [Principled Personas: Defining and Measuring the Intended Effects of Persona Prompting on Task Performance](https://aclanthology.org/2025.emnlp-main.1364/), de Araujo et al., EMNLP2025 | Persona advantage, robustness to irrelevant attributes and fidelity are already evaluated | A shared-evidence S/F/H bank with explicit measurement units is a design choice, not new evidence of generic persona sensitivity |
| [When Personalization Misleads: Understanding and Mitigating Hallucinations in Personalized LLMs](https://aclanthology.org/2026.findings-acl.395/), Sun et al., Findings ACL2026 | Studies history-aligned factual distortion and proposes FPPS/PFQABench | Date/content review may reveal a scoped pattern, but cannot identify representational entanglement or claim first discovery of personalization hallucinations |
| [One Persona, Many Cues, Different Results](https://aclanthology.org/2026.acl-long.2079/), Weeber et al., ACL2026 | Compares persona cues and shows sensitivity of conclusions | Single style realizations and wrapper choices require replication; prompt sensitivity itself is established |
| [What to Admit and How to Present](https://arxiv.org/abs/2610.11188v1), Liu and Ding, preprint2026 | Separates memory admission from presentation and reports trade-offs | Current H packages confound these dimensions; no isolated temporal/relevance mechanism is demonstrated |
| [LongMemEval](https://arxiv.org/abs/2410.10813v2), Wu et al., ICLR2025 | Temporal reasoning, updates and memory-use evaluation already exist | Sufficient common evidence can rule out missing-evidence explanations, but not all selection or utilization alternatives |
| [Wiki-Talkie](https://arxiv.org/abs/2610.08513v1), Fucci et al., preprint2026 | Real discussion next-turn persona conditioning and behavioral distribution evaluation | Our fictional English bank has no demonstrated authentic-speaker external validity; no private dataset was imported |
| [TwinVoice](https://aclanthology.org/2026.findings-acl.981/), Du et al., Findings ACL2026 | Multiple real-world persona dimensions and separate capabilities | Separating fidelity, reasoning and memory is already established; our current measurements do not establish real-speaker fidelity |
| [Persistent Personas?](https://aclanthology.org/2026.eacl-long.246/), EACL2026 | Extended role-playing and instruction-following evaluation | A high role-transition rate is not itself novel; meaningful first-reply consequences require outcome review |
| [Decoupling Logic from Persona](https://arxiv.org/abs/2610.09772v2) | Repository's earlier literature audit records direct decomposition overlap | Fresh retrieval returned an internal error; do not claim fresh full-text verification or borrow a mechanism as a current finding |

## Falsifiable contribution tests

| Prospective claim | Additional evidence needed | Result that would weaken it | Novelty risk |
|---|---|---|---|
| S×H changes reliability under identical sufficient evidence | Valid separate semantic labels, paired interactions, independent persona/task realizations and useful clustered precision | Stable near-zero interaction within a prospectively useful equivalence margin, or effects explained by unresolved package differences | High: factorial design alone is established |
| Structural-versus-semantic measurement changes interpretation of persona effects | Human-confirmed first units, all denominators, versioned full-output sensitivity with separately defined unit, independent replication | Same supported conclusions across valid units and sufficient coverage | Plausible scoped contribution; generic parser failures are not new |
| Historical relevance/temporal validity explains a conditional pattern | An explicitly approved relevance×temporal-status diagnostic holding presentation/evidence constant | No precise conditional differences or disappearance after content/position controls | High overlap with temporal memory and admission work |
| Operational Base/native-chat configuration changes measurement feasibility | Pinned separate checkpoint/template arm and same-case blinded semantic coverage comparison | No useful coverage gain, or apparent improvement caused by excluding uncertain outputs | Model sensitivity is established; contribution requires interpretable boundary evidence |
| Findings generalize beyond synthetic cases | Authorized independent English real-speaker material, provenance and separate fidelity assessment | Failure to replicate under external material, reported as a scope limit | Strong existing persona-simulation overlap |

No claim above is accepted by completing192 generations. CPU deployment, parameter size, higher error counts and an eight-cell design are not originality evidence. Zero contrasts and negative or mixed outcomes remain reportable. A precise independent boundary or qualified replication could be useful to PLOS ONE even without a new algorithm; there is no promise of publication.

## Algorithmic Opportunity Assessment

Existing retrieval, temporal filtering, native chat formatting and factual verification are necessary baselines. Current evidence supports measuring failure types before choosing mitigation; it does not justify algorithm implementation. See [the assessment](P1b_calibration_algorithmic_opportunity.md) for decision conditions.
''')

    put('P1b_calibration_publication_readiness.md','P1b Calibration Publication Readiness',f'''## Current decision

**Not ready for a substantive publication claim; ready for researcher semantic measurement.** Engineering reproducibility is strong, but P1b has zero registered outcome judgments. The task now is to use the existing192 outputs, not maximize generations. P0 acceptance and the completed Wave1 findings remain unchanged.

PLOS ONE emphasizes technical rigor, evidence-supported conclusions, intelligible methods and appropriate reporting; null/negative findings and justified replications can be considered. This is not a requirement for a new algorithm or guaranteed positive effect. [Journal publication criteria](https://journals.plos.org/plosone/s/criteria-for-publication).

| Requirement | Current evidence | Remaining action |
|---|---|---|
| Measurement validity | Native/parsed audit192; first-unit191; frozen policies and four axes | Complete semantic review, adjudicate the ambiguous unit, retain initial/corrected annotations and unknowns |
| Annotation reliability | Blank masked package and explicit assistance/provenance fields | Record real reviewer access; if a second independent reviewer is available, freeze a stratified subset and genuine separate ratings before agreement/adjudication |
| Task discrimination | Different evidence operations and concrete candidate delivery/date problems | Verify labels and coverage before claiming a reduced ceiling or empirical difficulty hierarchy |
| Statistical precision | 24 paired cases,12 purposive clusters; temporal11/9; exact paired structural values | Use eligible counts, unknown bounds, cluster-aware intervals and independent material; do not treat192 as independent |
| Identification | Same within-case evidence/question/context/configuration | Style/speaker nesting, history/task relevance, length and semantic content confounds remain; no pure mechanism claim |
| Generalization | One Base model, one quantized configuration, fictional English cases | Select a justified operational model sensitivity arm and later independent cases; authentic-speaker validation is unexecuted |
| Neutral controls | Existing24 token-matched P1 candidates, semantic review OPEN | No control-adjusted claims until actual review; do not transfer P0 approval |
| Reproducibility and availability | Hashes, raw journals, source snapshots, ordered requests and versioned public derivatives | Archive synthetic data/code, raw journals and eventual mappings/annotations appropriately for release; local ignored results are not yet a public deposit |
| Scientific contribution | Testable measurement/conditional-effect hypotheses and direct literature overlap | Narrow a supported empirical claim; no novelty or population-null declaration from this pilot |

## Statistical reporting contract

For each of relevance, factuality, temporality and coherence, report total eligible, assessed, missing, Unverifiable and N/A separately, by condition and task family. Distinguish unknown factual state from absent human annotation. All cases, including structural failures, stay in the denominator. Semantically incomplete but assessable outputs are not automatically missing. Future plots should distinguish factual support from complete answer delivery, not combine them into a single reliability/fidelity score.

Use case-paired C1−C0 and C3−C0, averaged S/F/H effects and averaged interactions with their correct scales. Whole-speaker resampling preserves two cases per speaker and all conditions. Twelve clusters and purposive task templates make inference fragile; temporal coverage is only nine clusters. Current bootstrap intervals are post-output descriptive sensitivity, not confirmatory tests. Preserve the old leave-one-speaker-out results as a different sensitivity diagnostic.

The existing [precision plan](P1b_sample_size_and_precision_plan.md) supplies assumption-based scenarios, not measured P1b semantic variance. Do not extrapolate zero variance from Wave1's ceiling. After review, quantify useful uncertainty and condition-dependent unscorability, then choose a prospectively justified independent sample and primary contrast/endpoint hierarchy. Do not expand until a desired result appears.

## Ranked next decision

1. **Now:** complete the two-stage192-record review and provenance registration. Resolve B_L3's unit and distinguish supported partial answers, action promises and contradictions. No extra inference is needed.
2. **Conditional next experiment:** a separately pinned native-chat Qwen3.5-2B arm has high information value if usable-answer coverage remains poor. The [proposal](P1b_calibration_instruct_arm_proposal.md) defines provenance, comparability, cost and confounds. Researcher authorization is required.
3. **Alternative:** if first replies are already semantically measurable, independent task realizations/precision are more useful than rerunning these cases. If boundary disagreement dominates, use a narrow independent boundary diagnostic before a full model arm.
4. **Later targeted mechanism:** relevance/temporal-status manipulation only after a reviewed pattern and appropriate controls justify it. Presentation, model size, real-speaker transfer and a new algorithm are not automatic scope expansions.

Expansion of the same Base bank is currently lower value than reviewing its outputs. No new run, Wave2, training or later phase was started. A review that finds a continuing ceiling, no condition difference or widespread ambiguity is a valid outcome to preserve.

## Algorithmic Opportunity Assessment

Observed continuation is reproducible, but no reviewed benefit of a corrective algorithm exists. Native-template and frozen parser baselines should precede invented mechanisms; all methods need separate development and independent evaluation. The [assessment](P1b_calibration_algorithmic_opportunity.md) remains a proposal boundary, not an implementation plan.
''')

    appendix='''\n\n## Measurement-audit addendum — v2 (original v1 retained)

### Observed Failure Modes

The [192-response measurement audit](P1b_calibration_measurement_audit.md) reproduces every native output and frozen parser result. Beyond the earlier execution summary, it distinguishes four unclosed thinking blocks, one unfinished date clause with no parser-deleted tail, one unrecognized-label ambiguity, and17 literal prospective-check openings. The latter are text-pattern observations, not17 human-confirmed missing answers. Supported intermediate facts can fail to answer a requested room/building question. All semantic judgments remain pending.

### Existing Methods

Role-transition extraction already exists in this repository; the official post-trained Qwen template supplies native turn delimiters. LongMemEval covers temporal retrieval/updates; memory admission/presentation and factual personalization mitigation already appear in the [novelty assessment](P1b_calibration_novelty_assessment.md). A date filter, prompt section or response verifier is not inherently novel. No existing algorithm has been rerun or claimed reproduced in this audit.

### Potential Algorithmic Improvements

| Candidate | Current support / unresolved problem | Required baselines and independent validation | Cost and publication value |
|---|---|---|---|
| Evidence-aware response selection | Intermediate-fact and promise openings show answer-delivery review targets; no validated selector target yet | No selection, first-unit extraction, evidence-aware selection; human true-unit/claim annotations and false-selection rate on independent outputs | Offline rules inexpensive; extra sampled generations cost new inference. Useful only if valid units improve without cherry-picking |
| Temporal-aware historical retrieval | Concrete date/site discrepancies require confirmation; all trusted facts were already supplied | All-history/no-history, date filtering, relevance filtering, matched-budget random selection; crossed relevance/time and preserved evidence | Retrieval rules cheap; causal generation tests new cost. Strong prior overlap; no current method claim |
| Persona/evidence separation | S/F/H packages and length differ; no semantic interaction estimated | Existing sectioned prompt, native chat, compute-matched multi-stage baseline and independent fidelity review | Extra stages add calls. Cannot infer representational entanglement from these outputs |
| Response boundary management |186 cross-turns and one ambiguous boundary are observed; five prefixes end at96tokens | Frozen parser, native chat/EOG, predeclared stop strings; complete-answer retention, false cuts and full raw preservation on independent examples | Offline audit cheap, controlled new arms require approval. Instrument validity is more immediate than algorithm novelty |
| Structured factual verification | Source oracle validates stimuli but is not a free-text semantic judge | Exact-match with abstention, existing factuality/NLI tools, human claim-level references; negation/date/multiple-claim tests and held-out validation | Learned scoring cost unmeasured. Do not train/test on this same reviewed bank and claim independent accuracy |

### Validation Feasibility

First score the existing bank and quantify boundary agreement, missing answer delivery, contradictions, uncertainty and temporal misattribution. Retain unscorable cases and protected assignments until review is frozen. A new method is justified only if a reproducible unresolved failure persists beyond established baselines and a separate development/evaluation allocation can test it. No algorithm implementation, new inference or training is authorized by this assessment.

### Publication Value

Current value is a truthful measurement package. A replicated difference between raw-structure conclusions and valid semantic-unit conclusions could support an empirical contribution; a high continuation count or more errors alone cannot. Independent validation, useful precision and literature comparison remain necessary. This addendum preserves every earlier observation and does not retroactively change the empirical study's primary track.
'''
    with Path('docs/P1b_calibration_algorithmic_opportunity.md').open('a',encoding='utf-8',newline='\n') as f:
        f.write(appendix)
    print(json.dumps({'new_reports':7,'existing_report_append_only':1,'review_assistance_records':len(assistance),
                      'human_judgments_created':0,'new_generations':0}))


if __name__ == '__main__':
    main()
