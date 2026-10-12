# P0 Researcher Annotation Registration

2026-10-12. **Annotation completion PASS: 40/40. Control validity PARTIAL. Overall P0 PARTIAL.** This report supersedes earlier current-status statements saying no human annotations were supplied; those dated records remain historical.

The researcher explicitly confirmed personal review of all 40 records, then supplied `docs/validation/PersonaSLM_P0_Researcher_Reviewed_v3.csv`. Actual extension: `.csv`. SHA-256: `06629e8bc69684b3a276ec00a71558291c5762c64acc23dac619cc86d88bfb42`. The file has 40 unique case-condition keys (20 N_style, 20 N_history), complete six-dimensional judgments and two auxiliary judgments. All immutable materials match the original v3 master and frozen comparison prompts, allowing only CSV CRLF/LF representation differences. Original bytes are preserved.

The [latest registration](validation/P0_researcher_verified_annotation_v1_revision2.json) uses annotation version **`researcher_verified_annotation_v1`**, registration revision **2**, reviewer **`Yaxin_ZHENG`**, review type **`researcher_human_review`**. Revision 1 refers to the earlier received source and remains preserved; it is superseded for current reporting. This does not create two reviewers or two independent annotations per item.

The final review is **AI-assisted human review, not blind review**. Source metadata attests an independent initial judgment followed by consultation of preliminary AI assessments and researcher revisions. No separate first-pass record is available for independent verification. The distinction between an initial process claim and the observed final file is retained. No reviewer identity, human timestamp, second reviewer, agreement statistic or consensus was manufactured. Review times are null because not supplied; registration timestamps are real import times.

| Dimension | no | yes | uncertain |
|---|---:|---:|---:|
| Answer leakage | 40 | 0 | 0 |
| Additional factual information | 40 | 0 | 0 |
| Contradictory information | 40 | 0 | 0 |
| Temporal interference | 40 | 0 | 0 |
| Unintended linguistic style | 0 | 20 | 20 |
| Semantic neutrality | 0 | 0 | 40 |
| Speaker referent ambiguity (auxiliary) | 30 | 10 | 0 |

`uncertain` is a completed judgment, not a blank or a PASS. The source's overall `control_suitability` is **PASS 0 / PARTIAL 40 / FAILED 0**. The separate deterministic disposition is **PASS 0 / PARTIAL 20 / FAILED 20** because the 20 N_style records explicitly identify extra style. These two summaries answer different questions and must not be conflated. Source judgments are never rewritten to match the software disposition.

## Version preservation and actual differences

The [earlier received CSV](validation/P0_received_review_source_v1.csv), hash `f09a128f212a1405b9276ccc27ffd871c2365df5798d6e8feec6194dbca1733e`, was archived before the later file arrived. Its former untracked working-copy path disappeared during researcher delivery; the preserved bytes remain available. It had already been attested as researcher-verified. It is not represented as the untouched AI original.

The [full comparison](validation/P0_researcher_annotation_version_comparison_v1.json) records all changed cells. Between available versions: **0 judgment changes in six core plus two auxiliary fields; 0 records with changed judgments; 40 records with metadata/provenance changes**. Reviewer IDs are now consistently populated, source/type metadata is corrected or added, and declared prior hashes are retained. The declared `original_file_sha256` matches the preserved earlier bytes.

The additional declared intermediate source hash is `2fd4ea2a2817a9b3c8ed6266582825f32423ad2c33121aabd5c5162e7680b807`; its source file was not supplied. The untouched AI assessment and the initial independent human pass are also unavailable. Therefore **the number and identity of judgments changed from those earlier stages cannot be verified**. The researcher's report that some judgments were corrected is preserved; a zero difference between the available snapshots does not contradict it. No missing version is reconstructed or fabricated. Historical automated audit files remain unchanged and retain their non-human attribution.

## Import validation and future resolution

The new `personaslm.researcher_review` importer validates the versioned schema, exact item set, duplicates, all required labels, material hashes/locked fields, reference text, reviewer identity, declared source linkage, supplied timestamps and the submission-bound task attestation. It preserves raw CSV and rejects overwrite. The original strict v3 importer is unchanged; missing review time is explicitly supported by this separately versioned registration, without inventing time or weakening its old rules.

The [English follow-up guide](P0_neutral_control_resolution_guide.md) and blank [resolution form](validation/P0_neutral_resolution_form_v1.csv) support quoting and adjudicating outstanding issues or independent replication. These are follow-up materials, **not** evidence that the completed 40-item review is still absent. No follow-up ratings have been fabricated.

What still blocks scoped P0 acceptance is unresolved control validity, not failure to supply a human review. The existing N_style repetition/style cue and N_history topic/information/coherence imbalance have not been repaired or accepted under a researcher-approved revised interpretation. Upstream quantization uncertainty, backend ID-array limitations and bounded response/evaluation coverage remain documented scope limits. P1 still requires separate researcher authorization after acceptance.
