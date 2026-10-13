# P0 Final Scientific Acceptance Report

Maintainer: Yaxin ZHENG. Paper: **Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**. Research Protocol v1.1 is unchanged. Primary experimental language: English.

**P0 = PASS. Engineering and Methodological Infrastructure Validation Completed.**

**P1 = NOT STARTED.** No P1 execution is authorized by this acceptance. The validated scope is pipeline, parser, measurement and explicitly qualified control infrastructure. P0 establishes no persona effect, general factual accuracy, real-speaker fidelity or research novelty.

## Final researcher decision and review integrity

The researcher explicitly approved the exact final addition:

> Speaker style profile: No speaker-specific style information appears in this profile.

Tessa = **ACCEPT_NARROW**, solely as an explicit absence-of-style control. The [separate approval](validation/P0_tessa_researcher_approval_v1.json) records reviewer_id `Yaxin_ZHENG`, review_type `researcher_verified_human_review`, decision_source `researcher` and final_decision_authority `researcher`. The candidate ID, prompt hashes and original tokenizer evidence bind the decision to this exact wording. Human review time was not supplied and remains null; registration time is recorded separately. Preliminary assessments were available, so the record retains assisted-review provenance and does not invent blind review, a second reviewer or agreement statistics.

Candidate prompt SHA-256: `93908ec82736f26131119c8d04ce518a0fe7f74f867c9c438e6fe043c9ed553c`. Reference prompt SHA-256: `420294b895b631db5b59f98bfbfeed0e4b5f37b9dc204fd12cd22b5c060289d3`. Native counts: **99 / 99, difference 0**. The preceding 100-token candidate and its REVISION_REQUIRED decision remain unchanged. The other five approved style texts have not been edited. No new single-axis annotation is inferred from the final overall decision.

The [selected-control manifest v2](validation/P0_final_selected_controls_v2.json) adds only this decision and its provenance to the preceding manifest. Its registration-time P0 field records that the audit was then pending; the authoritative subsequent [acceptance decision](validation/P0_acceptance_decision_v1.json) records the completed audit and PASS. Neither earlier PARTIAL manifests nor blank review masters were rewritten.

| Speaker | N_style reference / candidate | History A reference / candidate | Differences | Decision |
|---|---:|---:|---:|---|
| Riley | 101 / 101 | 118 / 118 | 0 / 0 | ACCEPT_NARROW in each declared scope |
| Samara | 101 / 101 | 120 / 120 | 0 / 0 | ACCEPT_NARROW in each declared scope |
| Devon | 99 / 99 | 119 / 119 | 0 / 0 | ACCEPT_NARROW in each declared scope |
| Tessa | 99 / 99 | 120 / 120 | 0 / 0 | ACCEPT_NARROW in each declared scope |
| Blair | 99 / 99 | 119 / 119 | 0 / 0 | ACCEPT_NARROW in each declared scope |
| Robin | 100 / 100 | 118 / 118 | 0 / 0 | ACCEPT_NARROW in each declared scope |


Six History A ACCEPT_NARROW decisions and **18 confirmed source associations** remain registered in the [researcher registration](validation/P0_scientific_review_registration_v1/registration.json). comparison_suitability=PASS applies only to the predefined length/format comparison. topic_alignment=FAIL, temporal_relationships=FAIL and conversational_coherence=UNCERTAIN remain exactly as supplied. Approval does not convert these into full semantic neutrality. History B remains **REJECT_AS_NEUTRAL (6)**; History C remains **DIAGNOSTIC_ONLY (6)**.

The original 40 reviews, prior 24 decisions, 336 individual judgments, 90 later source-style judgments, original source CSVs, conversions and evidence quotations remain preserved. Historical detailed-form deficiencies remain documented: the adopted A evidence/suitability confirmations have been separately resolved; missing or incompatible fields on superseded/excluded materials are not filled by inference. They do not add a requirement to rehabilitate rejected controls.

## Experimental identification

| Contrast | What is measured | Held constant | Remaining confounds / prohibited interpretation |
|---|---|---|---|
| C1 - C0 | Operationalized style-conditioning prompt package, F=H=0 | Speaker, trusted evidence, current question, fixed recent context, inference/evaluation policy | Style wording, heading, length and positions co-vary. Not an isolated style mechanism or an average factorial main effect. |
| C3 - C0 | Operationalized dated historical-dialogue package, S=F=0 | Speaker, shared current evidence/question, recent context and inference/evaluation policy | History format, length, topic, facts and time information co-vary. Not a pure format or temporal-conflict effect. |
| C1 - N_style | Specific style information versus explicit absence of style information | Wrapper, position, exact final-prompt length, identity, evidence and question | Lexical content, absence priming and declarative/profile cues differ. Not behavioral equivalence with C0 or complete semantic neutrality. |
| C3 - N_history (History A) | Residence history versus unrelated coherent dated dialogue | Role/turn format, dated header, speaker identity, position, exact length, shared evidence/question | Topic relevance, historical factual content and temporal factual information differ. Not isolated temporal conflict, pure historical format or semantic equivalence. |


These are qualified simple contrasts under the protocol, not demonstrated causal findings or perfectly orthogonal mechanisms. Exact tokens control measured input length, not attention allocation or semantics. This supports a defensible future development pilot with its inputs and applicability frozen before generation; it does not authorize that pilot or remove the later confirmatory freeze. Persona Fidelity remains separate from Dialogue Reliability. See the [full identification assessment](P0_final_identification_assessment.md).

## Mandatory acceptance checklist

| Mandatory P0 requirement | Status | Evidence / scope |
|---|---|---|
| 1. Reliable CPU inference infrastructure | PASS | Historical real CPU execution and observed four-thread, 4096-context, zero-offload server logs remain byte-identical. No new generation. |
| 2. Verified model and backend identity | PASS | Pinned GGUF and executable rehashed; build 11573/0f701c882 confirmed with --version. Metadata/loading evidence preserved; no upstream-equivalence claim. |
| 3. Actual-tokenizer accounting | PASS | All 12 selected final prompts have exact length equality. 524 original native request/response pairs reconstructed twice; no approximated counts. |
| 4. Trusted evidence and questions preserved | PASS | Both arms retain the exact shared evidence and question; prompt hashes and IDs checked against native records. |
| 5. Reproducible prompt construction | PASS | transcript_base_v1, dataset hashes and frozen source/tool hashes verified. No prompt or policy changed during closure. |
| 6. S/F/H intervention construction | PASS | Existing software routing/manipulation checks cover 160 original-fixture factorial prompts. Development controls do not establish perfectly orthogonal semantics or a completed factorial study. |
| 7. Explicit response boundary policy | PASS | Frozen response_status_v1 and its development/holdout evidence retained; stop cause is separate from semantic completeness. |
| 8. Separate COMPLETE/TRUNCATED/CROSS_TURN/AMBIGUOUS statuses | PASS | Existing instrumentation and tests preserve uncertainty and raw spans. Natural EOS is not required for every model answer. |
| 9. Consistent evaluation units and predeclared applicability | PASS | separate_axes_policy_v1 retains Correct/Incorrect/Unverifiable/Not Applicable and separate completeness, support, relevance and temporal axes; first-reply/prefix policy unchanged. |
| 10. Raw output and parser traceability | PASS | Historical raw responses, parser traces and earlier evaluations are unchanged. No retrospective replacement by a newer score. |
| 11. Required researcher reviews | PASS | Six selected style decisions and six History A decisions are ACCEPT_NARROW; 18 History A evidence links confirmed. Final Tessa approval is explicit and hash-bound; missing review time remains null. |
| 12. Defensible selected-control comparisons | PASS | Style compares information against explicit absence; History A compares residence history against unrelated coherent dialogue at matched length/format. Residual lexical, topic and temporal confounds are explicit. |
| 13. Reproducibility and provenance | PASS | 25 journals / 32919 original files rehashed; all hash chains recomputed. Original annotations, source snapshots, inputs and failures retained. |
| 14. Passed engineering validation | PASS | 365 tests passed, 0 failed, 0 warnings reported, exit code 0. No source functionality or test threshold changed. |
| 15. Documented scientific limitations | PASS | Bounded synthetic-city evaluation, assisted single-researcher review, limited stimuli, unsupported backend arrays and unverified upstream quantization equivalence remain disclosed. |


**Mandatory P0 blockers remaining: none.** The only preceding blocker was approval of this exact Tessa wording; the researcher has now supplied it. No threshold, scientific objective, protocol requirement or historical evaluation was changed to obtain PASS. Acceptance covers the selected controls within their stated scope, not all archived controls or every field of superseded review packages.

## Verification and reproducibility

The [offline verification](validation/P0_acceptance_verification_v1.json) rehashed **25 journals / 32919 original files** and recomputed every event chain. It reconstructed **524 native tokenization request/response pairs twice** from the unchanged raw bodies and arrays: 444 candidate-v2, 78 bounded style-closure and 2 final Tessa. All 12 selected reference/control pairs match exactly; evidence, questions, hashes and IDs agree. This used saved actual-tokenizer evidence, not character estimates or new model requests. Historical failed/interrupted journals remain failures/interruption records, not newly relabeled successes.

Current model: **Qwen3.5-2B-Base Q4_K_M**, GGUF SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`. Backend: **llama.cpp b11573 / 0f701c882**, executable SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. Both local binaries were rehashed and the executable's version command checked. Loaded-model metadata and observed CPU execution are supported by preserved server evidence, not newly claimed hardware measurements. The third-party artifact's fixed publisher revision remains recorded; matching bytes do not independently prove upstream quantization equivalence.

The original dataset hash is `31b5242c2cc01411f524c2b922086de0ef216105920e723f1270560e0bc1f282`; source/tool hashes, development dataset and runtime config match the frozen Tessa snapshot. Git HEAD is `e1da38723b310ff6a12b04e1164ac20bb12feb1f`; the working tree is dirty. No new answer generation, tokenizer request, model selection or rule tuning was performed. Existing raw outputs and all prior evaluation versions remain unchanged.

Full command: `.\.venv\Scripts\python.exe -m pytest -q`. Result: **365 passed, 0 failed, 0 warnings reported; exit 0**. Pytest reports **17.00 s**; the wrapper records **17.694733 s**. Full stdout/stderr, actual commands and UTC execution metadata are retained in the [delivery evidence](validation/P0_acceptance_delivery_v1.json) and local structured captures. No test or research functionality was changed during this closure.

## Accepted limitations and future work boundaries

Base-model continuation, missing natural EOS and imperfect model answers remain observable outcomes. response_status_v1 separates structural status from stop cause; separate_axes_policy_v1 does not equate truncation or unverifiability with incorrectness. The city-specific scorer is bounded and open-ended judgments require the protocol's future human procedures. Unsupported internal evaluated-input token arrays remain unavailable, not invented.

Single-researcher assisted control review is not blind multi-annotator outcome evaluation. Narrow style and history comparisons retain the confounds above. Six development personas and historical synthetic diagnostics do not establish external validity. Independent/interacting S/F/H effects, relevance/status/presentation decomposition, structural versus semantic failures, model-size/post-training sensitivity and authorized English real-speaker validation remain future questions; no unprecedented novelty is claimed.

The [complete engineering report](P0_engineering_report.md) is organized by eleven technical development stages without a calendar timeline. Original report versions and raw timestamps are preserved separately. The [development log](research_development_log.md) records the actual closure actions. All changes remain uncommitted for researcher review; no commit or push was executed.
