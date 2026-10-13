# P1 Wave 1 Measurement Audit

Maintainer: Yaxin ZHENG. Target journal: PLOS ONE. Formal baseline: Research Protocol v1.1. This is an additive, post-generation measurement audit, not a new experiment or replacement evaluation. The revised v1.2 r1 document remains an unadopted proposal.

## Decision and scope

**Saved experimental execution and reconstruction: PASS. Semantic measurement coverage: PARTIAL. Human response review: OPEN (0/96). Further inference: not authorized by this audit.** The existing accepted P0 status is unchanged.

The 96 distinct factorial requests have 96 native responses, 96 preserved first-reply spans and 96 reproducible original evaluation records. They support an auditable structural description. They do not yet support a general factual-accuracy estimate, a four-axis semantic reliability comparison, or a scientific claim that persona conditioning helps or harms reliability. No new generation was performed, no observation was removed, and no original score was changed.

## Evidence and reconstruction

The authoritative preparation run is `20261013T065000-5b7eb2b7a3d64b29945f557bdf2abb59`; the generation run is `20261013T065228-971f93c4c1434254a5298dde72dd9061`, both under `results/p1_wave1/development_v1/runs/`.

The [structured audit](validation/p1/measurement_audit_v1.json) retains all 96 response partitions, original evaluation objects, source bindings, journal hashes and case-level contrasts. Verification covered both event chains (2,278 preparation events; 909 generation events), all 3,192 original run files, 720 preparation tokenizations, and 96 generation-time tokenizations/completions. Original HTTP response bytes, submitted token IDs, generation parameters, prompt hashes and saved parser spans agree. The original evaluation was recomputed from saved inputs twice per response with identical results; this verifies deterministic reconstruction, not independent human agreement.

Preparation has a terminal `run_finished` event, but no standalone `summary.json`; this is the journal's saved format, not a lost generation. Seven preparation health timeouts and 34 preparation/15 generation startup HTTP 503 responses precede readiness. All 96 completion responses are HTTP 200; there are no completion retries/errors. These startup diagnostics remain in the audit and original journals.

Model and executable bytes were rehashed during this audit:

| Artifact | Identity / SHA-256 |
|---|---|
| Model | Qwen3.5-2B-Base, Q4_K_M; `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` |
| Backend | llama.cpp b11573 / `0f701c882`; `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| Dataset | `p1_development_v1`; `4a59f4519cb6ade311737ce613446aaac1b9d78283949d7ebc818a4a3e25469d` |
| Actual-token wave manifest | `df27733f1267c859e8420397187ab6000d644c241c66dd5e0caa0346c32b88cb` |
| Original result file | `25ccd117baf2a2e5adb9e51d7211dc04a06cfd49133ca9202eca126e131f1dab` |
| Audit HEAD | `ded2ab28af9b9b7b5afd303221672424350c5106`; working tree dirty, including preexisting P1 work |

The original configuration is CPU-only, threads 4/4, context 4096, temperature 0, top_p 1, seed 42, output budget 96, no stop sequences, `cache_prompt=false`. Prompts contain 129–217 tokens. Native evaluated counts agree and no input truncation was reported. Native input arrays equal saved submitted IDs; the backend does **not** echo evaluated input-ID arrays, so equality of those unavailable arrays is not claimed. Output IDs are present for all 96 responses. Saved server/version records, rather than a new server launch, establish loaded-backend observations.

## Main measurements

| Measure | Actual result | Interpretation |
|---|---:|---|
| COMPLETE / TRUNCATED / CROSS_TURN / AMBIGUOUS | 0 / 17 / 78 / 1 | Original `response_status_v1`, unchanged |
| Native budget / EOS termination | 95 / 1 | Backend events, separate from semantic completeness |
| Empty raw outputs / missing outputs | 0 / 0 | No dropped observations |
| Mechanically identifiable first spans | 96/96 | Extraction coverage, not 96 certified complete answers |
| Visible role-boundary first replies | 78/96 | Continued transcript after the first span |
| Additional role-labelled spans | 467 | Syntactic spans; not 467 certified complete dialogue turns |
| Generated tokens | 9,148 | 95 × 96 plus one 28-token response |
| Factual labels among 72 eligible responses | 15 Correct; 0 Incorrect; 57 Unverifiable | 24 additional responses are predeclared Not Applicable |
| Conclusive automatic factual coverage | 15/72 = 20.83% | Not an accuracy estimate |
| Human semantic responses reviewed | 0/96 | All human fields remain blank |

All 72 factual-task first replies have a narrow, whole-span source-bound sentence form. Of the 57 original Unverifiable labels, 33 arise on dated current-city sentences outside the frozen grammar, and 24 on membership questions intentionally routed to human review. This diagnostic uses the complete subject/predicate/object/date form and source validity, not substring correctness. It does not replace those 57 labels with Correct or certify semantic completeness.

A concrete instrumentation limitation was found: native `stop_type="eos"` is not recognized as `"eog"` by the frozen boundary policy. A [separate compatibility diagnostic](validation/p1/native_stop_compatibility_diagnostic_v1.json) identifies the saved EOS token and tests the alias without changing original records. The affected response remains AMBIGUOUS without a human completeness judgment. The [structural analysis](P1_wave1_structural_analysis.md) gives the exact scope and correction to the earlier interpretation.

## Scientific interpretation

C1−C0 and C3−C0 each change CROSS_TURN prevalence by −1/12 (−8.33 percentage points), entirely in the same nonfactual case. A lower CROSS_TURN rate here can mean a budget-censored response, not better dialogue reliability. All factual-task responses are CROSS_TURN; excluding that category would discard every factually eligible observation.

The average S×H and F×H structural contrasts are zero, while S×F is −8.33 percentage points. Opposite S×H changes in two cases cancel. These are exact descriptions of this small, dependent set of observations, not evidence of no interactions or a population effect. Semantic interactions remain unmeasured. See the [case-level analysis](P1_wave1_structural_analysis.md) and [four-axis coverage report](P1_wave1_evaluation_coverage.md).

S/F/H routing and shared evidence are reconstructible. Nevertheless, wording, added context length and content are intervention packages. History relevance differs by task; style realization is nested in speaker; prompts describe a target speaker rather than enforcing first-person role simulation. Fidelity is unmeasured. The new 24 P1 controls remain unreviewed and were not generated as response conditions. No control-adjusted effect is available.

## Deliverables, tests and limits

The [96-item human packet](validation/p1/output_human_review_v1.csv), [schema](validation/p1/output_human_review_schema_v1.json) and [annotation guide](P1_wave1_human_annotation_guide.md) provide separate completeness, relevance, factual, temporal and coherence judgments. Treatment mapping is kept in the ignored local administration directory, not distributed with the packet. Output wording, visible structural labels and existing public artifacts can still reveal treatments; no successful blind review or independent human judgment is asserted.

The complete suite passed **433 tests in 21.76 seconds**, exit 0, with no warnings reported (capture process 22.354203 seconds). The audit itself exited 0. An intentional import of the blank packet failed with exit 1 and `Missing or invalid unit judgment`; no registration was created. The [final delivery verification](validation/p1/measurement_delivery_v1.json) records preservation checks and actual command captures. Local engineering captures are separate from immutable experimental journals.

The [next-experiment recommendation](P1_wave1_next_experiment_decision.md) prioritizes semantic review before further inference; the [compatibility assessment](P1_protocol_compatibility_assessment.md) lists prospective changes requiring approval. No Wave 2, alternative model arm or protocol adoption occurred. Negative, null and uncertain observations remain available. This pilot alone is not submission-ready evidence for PLOS ONE.
