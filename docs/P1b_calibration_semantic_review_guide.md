# P1b Calibration Semantic Review Guide — v2

Maintainer: Yaxin ZHENG. Formal experimental baseline: Protocol v1.1. Protocol v1.2 Revised Proposed r1 remains prospective and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Development evidence only; no new inference.

## Start with the semantic view

Use [semantic_scoring_view_v2.csv](validation/p1b/measurement_audit_v1/semantic_scoring_view_v2.csv), containing all 192 records, stable BR001–BR192 response IDs and BC case aliases. Presentation was independently shuffled with seed **714003**, distinct from execution order 714001 and original alias shuffle 714002. This new order was chosen during the post-generation audit; it is not a claim of pre-generation blinding. Do not sort by case before the first pass.

The first view includes the question, sufficient trusted evidence, question/reference date, fixed context, reference answer components, case-level historical source, first-reply text, hashes and frozen applicability. It excludes conditions, factors, request/execution identifiers, automatic predictions, structural categories, stop reasons, token counts and full continuation. Expected components are references for human evaluation, not labels on model outputs.

Save a completed copy. **All supplied human fields are blank.** Do not open this audit's treatment analyses or assistance file before initial scoring if minimizing anchoring is desired. Evidence IDs, recognizable speakers, repeated answers, style and model-generated content may reveal cues. Prior researcher knowledge cannot be erased. This is condition-label masking, not a guarantee of perfect blinding or independent annotation.

## Two-stage unit verification

1. Record initial semantic judgments on the unchanged extracted span. If its attribution or meaning is unclear, use UNCERTAIN completeness and an explicit missing-metric reason; do not force a factual label. Save this initial version before the next step.
2. Open [structural_review_view_v2.csv](validation/p1b/measurement_audit_v1/structural_review_view_v2.csv). It has the same response IDs/order, full original continuation, exact parser spans/tail, frozen status and native termination. Confirm the reply unit as PASS / FAIL / UNCERTAIN and quote boundary issues. Do not modify text, offsets, hashes or labels.
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

[Optional AI-assisted observations](validation/p1b/measurement_audit_v1/optional_AI_assisted_observations_v1.csv) provide source quotations and questions, without suggested correctness labels. Use only after the initial pass if wanted; disclose access. It is not human annotation. Enter actual reviewer identity, assistance and prior access; record a review time only when actually known. No second reviewer, agreement statistic or consensus is presumed.

Validate a completed semantic copy with:

```powershell
.\.venv\Scripts\python.exe tools/p1b_measurement_audit.py validate-review --master docs/validation/p1b/measurement_audit_v1/semantic_scoring_view_v2.csv --completed PATH_TO_COMPLETED_COPY.csv
```

Use the same command with the structural master to validate its completed copy. The command checks IDs, every immutable field, labels, applicability, provenance and explicitly explained missingness; it does not certify semantic truth, import judgments, invent dates, or unblind results. Explicitly missing judgments are reported as missing even when the file passes schema validation. Keep both initial and corrected versions; register only after the researcher confirms them and boundary dispositions are reconciled.

The treatment mapping is stored separately under local ignored `results/p1b_measurement_audit/v1/protected/`; its digest is in the audit summary. Local separation is not encryption or filesystem access control. Share only the intended stage's CSV and this guide, not the analyst artifacts. A later genuinely independent reviewer may receive a separately masked, prospectively stratified subset; retain both originals before adjudication and calculate agreement only from actual paired human labels.

## Algorithmic Opportunity Assessment

This packet is measurement preparation. It neither implements a new answer-selection algorithm nor approves one. Boundary disagreement and semantic error patterns must first be measured before considering mitigation; see [the assessment](P1b_calibration_algorithmic_opportunity.md).
