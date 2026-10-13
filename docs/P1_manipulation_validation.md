# P1 Manipulation Validation - Development Wave 1

Maintainer: Yaxin ZHENG. Research Protocol v1.1 remains unchanged. This report concerns English fictional stimuli and construction integrity, not completed human manipulation checks or model fidelity.

## Materials and frozen allocation

The [dataset](../data/synthetic/p1_development_v1.json) contains 12 fictional speakers and 48 cases, with all four families for every speaker. Six style categories each have two distinct realizations: brevity, formal register, conversational register, plain lexical preference, separated sentence rhythm and acknowledgment before the answer. Names, residence cities, reading groups and supplementary possessions are independently permuted with seed 713019. No style is deliberately attached to a preferred answer or city. The [plan](P1_experiment_plan.md) was frozen before generation.

Wave selection uses speaker index i=0..11 and family ABCD[i mod 4]. The 12 selected speakers each contribute one case; A/B/C/D each contribute three. Seed 713042 shuffles case blocks and condition order within each block. All eight cells are retained regardless of C0 correctness. The remaining 36 development cases were not executed. Selection is not a confirmatory sample-size justification.

| Family | Task | Factual eligibility per condition | Temporal eligibility per condition |
|---|---|---:|---:|
| A | Current residence after an update | 3; bounded city grammar | 3; human review |
| B | Stable reading-group membership | 3; human review | 0 |
| C | Friendly welcome without biographical claims | 0 | 0 |
| D | Current destination in fixed move-related follow-up | 3; bounded city grammar | 3; human review |

Every case has stable persona/case IDs, English language and fictional provenance labels, style, separate possession fact, two-turn dated residence history, current evidence, a validity-interval fact ledger, fixed question/context, expected answer where applicable and a predeclared applicability matrix. Relevance/coherence apply to all cases; fidelity lacks independent reference behavior and is not scored.

## Construction gates

[Machine validation](validation/p1/manipulation_v1.json) checks all 48 cases and 384 final factorial prompts. [The immutable wave manifest](validation/p1/wave1_manifest_v1.json) binds the selected 96 prompts and input token arrays.

| Check | Result | Evidence and scope |
|---|---|---|
| Correct C0-C7 S/F/H routing | PASS | Eight exact factor assignments for every case; no factor silently routed into another cell |
| Shared trusted evidence, question and fixed context | PASS | Exact strings and SHA-256 hashes; evidence begins at character offset 70 in every prompt |
| Speaker identity | PASS for construction | Stable ID/display-name mapping; history response uses that display name; profile wrapper remains the existing generic speaker wrapper |
| Genuine past versus current facts | PASS | Old city interval ends before current city begins; history date lies within the old interval; no simultaneous residence contradiction |
| Supplementary fact separation | PASS for authored scope | Possession fact is bound to the speaker and is not the expected city/membership answer |
| Answer leakage in S/F/H | PASS for explicit-answer checks | Expected city/membership string is absent from the additions; no claim that lexical checks prove all semantic independence |
| Style category expressed by authored text | PASS for construction; adoption unverified | Distinct intended category wording; no generated response was used to select or revise stimuli |
| Prompt/evaluation policy freeze | PASS | transcript_base_v1, response_status_v1, separate_axes_policy_v1 and p1_endpoint_routing_v1; hashes verified after execution |
| Context capacity | PASS | Selected factorial prompts 129-217 actual tokens; at most 313 with the 96-token budget, below 4096 |
| Independent semantic review | OPEN | No new P1 control or response judgments have been supplied |

S is a description of the named speaker under the existing wrapper; it is not an explicit first-person role-play instruction. Tasks ask an assistant about, or for a greeting to, the speaker. Style adoption and authentic speaker simulation are therefore unvalidated constructs in this wave. This is a declared interpretation limit, not a measured fidelity failure.

## Actual tokenizer matching

Freeze 36 single-sentence absence-of-style alternatives and 16 two-turn unrelated-dialogue alternatives per selected case. This is 624 candidate prompts, plus 96 factorial prompts: 720 preparation tokenizations. Preserve every attempt, then select the first exact match in the predeclared order. No pool expansion, character-based token estimate, repeated sentence padding or model-answer selection occurred. Generation separately rechecked all 96 selected factorial token arrays against the same pinned loaded backend.

| Selected case | C1 / N_style tokens | Difference | C3 / N_history tokens | Difference |
|---|---:|---:|---:|---:|
| p1_speaker_01_A | 152 / 152 | 0 | 174 / 174 | 0 |
| p1_speaker_02_B | 156 / 156 | 0 | 177 / 177 | 0 |
| p1_speaker_03_C | 164 / 164 | 0 | 182 / 182 | 0 |
| p1_speaker_04_D | 168 / 168 | 0 | 188 / 188 | 0 |
| p1_speaker_05_A | 155 / 155 | 0 | 175 / 175 | 0 |
| p1_speaker_06_B | 165 / 165 | 0 | 186 / 186 | 0 |
| p1_speaker_07_C | 165 / 165 | 0 | 186 / 186 | 0 |
| p1_speaker_08_D | 166 / 166 | 0 | 187 / 187 | 0 |
| p1_speaker_09_A | 152 / 152 | 0 | 173 / 173 | 0 |
| p1_speaker_10_B | 157 / 157 | 0 | 175 / 175 | 0 |
| p1_speaker_11_C | 161 / 161 | 0 | 182 / 182 | 0 |
| p1_speaker_12_D | 168 / 168 | 0 | 187 / 187 | 0 |

[Matching evidence](validation/p1/control_matching_v1.json) retains full prompts, IDs, hashes, differences, failed alternatives and the chosen index. Actual endpoint: the locally loaded GGUF's `/tokenize`, add_special=true, parse_special=false, with_pieces=false. No GGUF or tokenizer was substituted. Exact full-prompt length does not establish semantic equality.

## Identification and review boundaries

| Contrast | What is controlled | Interpretation and unresolved differences |
|---|---|---|
| C1-C0 | Evidence, question/context, model, decoding, endpoint policies | Total style-context package. Length, heading, wording and downstream positions differ |
| C3-C0 | Same shared case and runtime inputs | Total dated-residence-history package. Length, format, topic, personal facts and temporal content differ |
| C1-N_style | Intended wrapper/location and exact total tokens, pending review | Style information versus explicit absence information. Absence priming and wording remain; not C0 equivalence |
| C3-N_history | Intended two-turn format, date format, speaker and exact total tokens, pending review | Residence history versus unrelated coherent conversation definition. Topic relevance, factual content and temporal factual relationships differ |
| S/F/H average effects and interactions | Within-case eight-cell structure | Operationalized package effects; not purified psychological mechanisms or isolated relevance/time/presentation effects |

Matched length does not guarantee identical absolute token offsets for every downstream boundary, even when wrapper and insertion position match. History relevance differs by family: A/D ask residence questions; B/C do not. Family, speaker and style realization are partly confounded in the 12-case wave. The C request itself asks for friendliness, a constant task cue that can interact with style. All four families use limited template diversity and explicit answer-bearing trusted evidence. H chronology is genuine past information, not an independently manipulated temporal-conflict factor.

The new [24-item control packet](validation/p1/control_review_v1.csv) contains exact texts, active comparisons, source evidence, questions, contexts, token counts, hashes and blank human fields. Follow the [annotation guide](P1_annotation_guide.md); validated import rejects missing labels, changed materials, duplicate records, inconsistent decisions and missing provenance. The blank master was deliberately submitted once as a negative check and rejected. No human decision was invented. Semantic validity remains OPEN; no matched-control generation or control-adjusted effect is reported. Historical P0 controls and their approvals remain unchanged.
