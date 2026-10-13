# P1b Researcher-Confirmed Semantic Annotation Registration

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Target: PLOS ONE. Protocol v1.1 remains formal; v1.2 Revised Proposed r1 is unadopted. Exploratory development evidence only. No new inference.

## Registration and integrity

The researcher explicitly approved all 192 proposed records in the current instruction. The source retains its UNCONFIRMED filename and original bytes. A new masked [final annotation CSV](validation/p1b/researcher_confirmed_annotation_v1.csv) and [provenance register](validation/p1b/confirmed_analysis_v1/registration_v1.json) implement `p1b_confirmed_ai_adoption_v1`.

The final CSV preserves every original 48-column value, including original blank `human_*` fields, and appends authoritative `confirmed_*` decisions and `registration_*` provenance. Blank original fields mean the researcher did not originally enter scores into those fields, not that the appended decisions remain pending. The registration metadata uses reviewer_id Yaxin_ZHENG, review_status RESEARCHER_CONFIRMED, decision_source researcher_confirmation, annotation_origin AI_assisted_condition_masked_review, and final_decision_authority researcher. This non-destructive representation avoids rewriting analytical provenance or collapsing YES/PARTIAL/NO into an older binary completeness schema.

Process: condition-label-masked semantic material; AI-assisted categorical/numerical proposals; researcher verification and adoption of all 192 proposals. No per-record label was corrected during import. Source evidence quotations, explanations, uncertainties and priorities remain AI-assisted material adopted by the researcher, not independently written human notes. The instruction is the confirmation source; no review timestamp, signature, second rater or agreement statistic is invented. Registration time is an engineering timestamp. Prior knowledge and text cues limit blinding.

All 35 original master fields match in each of 192 unique responses. All 24 cases have eight cells; speaker mapping yields 12 speakers. Every supporting source quotation is verbatim in the supplied trusted evidence. Final file SHA-256: `db834321db44dd9a230d3a841f10e1b17b4acc21a74a8ed28010bd4c6550f1f1`. Frozen dataset SHA-256: `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6`. Frozen manifest SHA-256: `d73ceb403148b01f7b2c83a51a20165fdd625658e50c04a7ce0caa118ab22869`.

Saved tokenizer events, prompt/token hashes, original inference sources and local model/backend files were verified without starting a server. Model SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; backend `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`, Qwen3.5-2B-Base Q4_K_M / llama.cpp b11573. See [offline identity](validation/p1b/confirmed_analysis_v1/offline_identity_v1.json); its reused readiness labels refer to the historical preflight workflow, not withdrawal of the present authorization. All 1831 original calibration artifact hashes matched before registration.

## Adopted labels and evaluation coverage

| Dimension | Actual labels | Frozen eligible | Missing annotations |
| --- | --- | --- | --- |
| Factual consistency | {'Correct': 137, 'Incorrect': 34, 'Unverifiable': 21} | 192 | 0 |
| Temporal consistency | {'Correct': 40, 'Incorrect': 34, 'Not Applicable': 104, 'Unverifiable': 14} | 88 | 0 |
| Response relevance | {'1': 4, '2': 14, '3': 31, '5': 143} | 192 | 0 |
| Conversational coherence | {'2': 4, '3': 1, '4': 18, '5': 169} | 192 | 0 |
| Semantic completeness | {'NO': 21, 'PARTIAL': 28, 'YES': 143} | 192 | 0 |
| Answer delivery | {'FULL_ANSWER': 110, 'NO_FINAL_ANSWER': 21, 'PARTIAL_ANSWER': 27, 'PARTIAL_WITH_FALSE_CLAIM': 1, 'WRONG_ANSWER_DELIVERED': 33} | 192 | 0 |


The 104 temporal N/A records are outside temporal eligibility. Unverifiable is an entered semantic judgment, not missing annotation or Incorrect. Claim-level correctness here means an **output-level judgment about its delivered factual claims**; no atomic-claim enumeration/denominator was collected. Do not report 137 as a count of independently verified atomic claims.

## Boundary scope and analysis gate

BR168 remains AMBIGUOUS under response_status_v1 and retains its supplied span, including an extra generated factual question. Its adopted labels are Correct, FULL_ANSWER, YES, relevance 5/coherence 4. No new human structural PASS was supplied. The old two-stage importer is preserved; this separately versioned adapter registers the semantic set actually authorized, not invented Stage B entries. `boundary_conservative` retains that record but treats its numerical semantic value as unknown. `confirmed_span_sensitivity` uses all adopted labels on the exact supplied spans. The other 191 units use existing identifiable-span evidence, not fabricated human structural review.

Registration and specification were written before joining treatments in this analysis. Existing earlier structural analyses were already known, so this is not first-ever blinding or prospective preregistration. The separate [unblinded analysis dataset](validation/p1b/confirmed_analysis_v1/analysis_v1/unblinded_analysis_dataset_v1.json) binds the original protected mapping. Original review CSVs remain masked. Exclusive-create writes and hash checks reject replacement or tampering.

## Reproducibility and status

Commands: `python tools/p1b_confirmed_analysis.py register`, then `python tools/p1b_confirmed_analysis.py analyze --output NEW_DIRECTORY`, using the project virtual environment. Two independent reconstructions produced byte-identical numerical datasets/tables; runtime manifests naturally have separate timestamps. Full suite:712 passed,0 failed,0 reported warnings,40.41 s,exit 0. [Delivery evidence](validation/p1b/confirmed_analysis_v1/delivery_v1.json) preserves exact commands, Git state and original-history verification. Semantic registration PASS; evidence does not establish independent annotation reliability or publication readiness.

## Provenance metadata clarification

The registration preserves the original AI suggestions and the sole named researcher authority. The initial provenance JSON used the field `independent_human_annotators: 1` to count that researcher; the field name does not establish independent annotation. The append-only [provenance clarification](validation/p1b/confirmed_analysis_v1/annotation_provenance_clarification_v2.json) records one named human reviewer and independent annotation status as unestablished, superseding that field interpretation. No second human, blind independence or agreement statistic is asserted. The original registration bytes, labels and analysis inputs remain preserved. The nested packet audit's zero imported reviews describes the original blank master before registration; the final registered count is 192.
