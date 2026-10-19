# Declarative-History Repair of the Synthetic S/F/H Replication v1

## Scientific status

**ACTUALLY EXECUTED — OUTPUT_INFORMED_SYNTHETIC_DEVELOPMENT.** This experiment is a simple, non-novel prompt baseline applied to the same 12 synthetic cases whose archived raw-history outputs motivated it. It is not independent validation, real-speaker evidence, confirmatory inference, a causal test of an internal memory mechanism, or algorithm validation.

The intervention changed only the archived assistant's first sentence from `I recommend the <archived target>.` to `My choice was <archived target>.` in the four `H=1` conditions (`C3`, `C5`, `C6`, and `C7`). The archived user turn, target, reason, second sentence, message roles, current notes, current question, and all S/F materials were preserved. The original 48 `H=0` observations (`C0`, `C1`, `C2`, and `C4`) were reused from their frozen event chain and were not regenerated. The original 48 raw-history `H=1` observations were retained as paired surface-normalization comparators but did not occupy the hybrid descriptive reconstruction.

## Prospective design and execution integrity

The candidate was frozen before any new tokenization or model output. A separate reviewing process in the same autonomous session initially returned NO-GO because the first declarative frame was ungrammatical, the registered outdated-value endpoint was absent from analysis, primary repair contrasts did not fully disclose cross-batch aliasing, and execution/reconstruction paths lacked focused tests. These issues were corrected prospectively. Final review returned GO after 15/15 targeted tests and 32/32 combined relevant tests passed. This process separation is not review by an independent researcher.

- Design SHA-256: `31fba764f949ffcdcc07fd348e334195878aeb82de24b1ff3e0e8cc88f919546`
- Case-transform SHA-256: `f1f1bb31d9e088cf7ffa5f9356a43323bd2217a1585826186fe4c3a13ee86c3b`
- Controller SHA-256: `6632607faaacd30c18709ab7c5e53625d02a97e1b3140f57c82383c5b5b0594f`
- Frozen pre-execution test SHA-256: `969e408fb0c6ffa9d854ea8dac1b4aecfafdef4def1dec5b997c04676d2c2785`
- Authorization SHA-256: `25fe4ba7dcfa27a518989a416991e856199247dc7140f774fae051af21383ac0`
- Frozen-manifest SHA-256: `4e7dc5bf4503018fbf9130f49025e4eb7bef31b4e9f9f6ca5ae9cc2987987de0`
- Preflight SHA-256: `87be4e7a97c7c9fa7faf29184830233510e49642bfa54a8e0b82caa3beb2eca6`
- Execution-audit SHA-256: `2d2583b763fc02501fc51b3920580c2898e52661c7fadc0c242ec26c3087a995`
- Analysis SHA-256: `8972902387ac485030dc1526a02c64dabfee63b39f6b9314c26e8ec111381ab0`
- Source Git HEAD: `c40667ad266082481b1850453f67784b593f3723`

The model was the development-only Qwen3.5-2B native-chat Q4_K_M artifact (weight SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`) through llama.cpp b11573 (backend SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`). Generation used temperature 0, seed 42, a 4,096-token context, a 96-token completion limit, and four CPU threads.

The official preflight observed 4,069,130,240 bytes of available physical RAM against the frozen 3,221,225,472-byte requirement. It verified the model, backend, template, source hashes, cumulative budget, exclusive allocation, and disk gate. Forty-eight native tokenizer records covered 285–460 input tokens. All 48 live server token arrays matched the registered arrays before completion 1.

The run directory is `results/p1_persona_dialogue_independent_replication_declarative_repair/v1/runs/20261018T195559-40418fba50ea405b97a2e955145c3c9f`. All 48 new requests were attempted once, and all returned a response and deterministic result. There were zero retries, hidden warmups, failed completions, or archived-H0 regenerations. The terminal status was `PASS`.

## Direct repair result

The complete-denominator automatic results were:

| Endpoint | Archived raw H=1 | New declarative H=1 | Declarative minus raw |
|---|---:|---:|---:|
| Frozen strict selection resolution | 2/48 | 42/48 | **+0.8333** |
| Raw `I recommend the ...` recurrence | 44/48 | 2/48 | **-0.8750** |
| Narrow surface-style uptake | — | — | -0.0208 |

The selection-resolution and raw-frame effects were stable in direction under leave-one-persona-out deletion: `[+0.7778, +0.8889]` and `[-0.9444, -0.8333]`, respectively. These ranges are sensitivity ranges, not confidence intervals.

The new declarative batch had lower registered raw-frame recurrence and higher frozen-selector applicability than the archived raw batch. These are coupled manifestations of a surface/measurement association, not two independent scientific effects: the selector itself rejects the article-bearing raw recommendation frame. It did not provide a paired point estimate for content choice: the raw-history member was unresolved in 46/48 pairs, so paired current-target, current-preference, and archived-target contrasts had only 2 complete pairs and logical bounds spanning both benefit and harm. Surface wording and execution batch are completely aliased, so this is not a causal wording effect or evidence of semantic/reliability repair.

In a post-hoc qualitative text inspection, not a blinded human rating, all six unresolved new responses appeared to contain current-choice language: two used `I recommend the <current target>.`, three used an option-label plus a current target, and one used an option label with current names in the second sentence. They remain missing under the frozen strict grammar. This observed coverage gap shows that strict selection resolution is partly a format endpoint rather than a complete semantic-choice measure.

## Hybrid cross-batch descriptive 2^3 S/F/H reconstruction

The combined descriptive dataset contains 48 frozen archived `H=0` rows and 48 new declarative `H=1` rows. No archived row was regenerated or edited. Consequently, H is exactly aliased with both execution batch and declarative-history rendering; the table permits bounded exploratory decomposition but is not an internally randomized causal factorial comparison.

| Condition | S | F | H | Strictly resolved | Preferred current choice among resolved | Exact archived-target choices | Raw frame | Narrow style uptake |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 | 0 | 0 | 0 | 11/12 | 8/11 | 0/11 | 0/12 | 0/12 |
| C1 | 1 | 0 | 0 | 11/12 | 6/11 | 0/11 | 0/12 | 12/12 |
| C2 | 0 | 1 | 0 | 11/12 | 11/11 | 0/11 | 0/12 | 0/12 |
| C3 | 0 | 0 | 1 | 10/12 | 7/10 | 0/10 | 0/12 | 0/12 |
| C4 | 1 | 1 | 0 | 11/12 | 8/11 | 0/11 | 0/12 | 10/12 |
| C5 | 1 | 0 | 1 | 11/12 | 6/11 | 0/11 | 1/12 | 12/12 |
| C6 | 0 | 1 | 1 | 10/12 | 7/10 | 0/10 | 0/12 | 0/12 |
| C7 | 1 | 1 | 1 | 11/12 | 6/11 | 0/11 | 1/12 | 12/12 |

### Registered current-preference effects

The table reports complete-case paired estimates, the number of complete cases out of 12, logical missing-outcome bounds, and leave-one-persona-out point-estimate ranges. No p-values were computed.

| Effect | Estimate | Complete cases | Logical bounds | LOPO range |
|---|---:|---:|---:|---:|
| F | +0.1250 | 10/12 | `[0.0000, +0.2083]` | `[+0.0357, +0.1563]` |
| H (declarative) | -0.1250 | 10/12 | `[-0.2292, -0.0208]` | `[-0.1563, -0.0938]` |
| S | -0.2250 | 10/12 | `[-0.2708, -0.0625]` | `[-0.2857, -0.1563]` |
| F x H | -0.2500 | 10/12 | `[-0.4167, 0.0000]` | `[-0.3125, -0.0714]` |
| S x F | -0.0500 | 10/12 | `[-0.2500, +0.1667]` | `[-0.0714, 0.0000]` |
| S x H | +0.0500 | 10/12 | `[-0.1250, +0.2917]` | `[-0.0714, +0.1875]` |
| S x F x H | +0.1000 | 10/12 | `[-0.3333, +0.5000]` | `[0.0000, +0.1429]` |

The F direction was positive but its logical lower bound reached zero. The H and S directions remained negative under the registered logical treatment of the two incomplete cases. Those two incomplete cases were both in the irrelevant-history regime (`REP_G_IRRELEVANT_TOUR` and `REP_I_IRRELEVANT_COUNTER`), so complete-case point estimates weight 4 aligned, 4 outdated, and only 2 irrelevant cases; the registered logical bounds should be prioritized. H is exactly aliased with execution batch and declarative-history rendering, and S is an explicit style-prompt package that also adds length and exact format exemplars, not broad speaker fidelity. Therefore these observations support a bounded development pattern, not causal factor effects in a speaker population or a validated fidelity-reliability trade-off.

The registered S effect on narrow surface-style uptake was **+0.9583**, with LOPO range `[+0.9444, +1.0000]`. This records near-ceiling uptake of the frozen surface contract, not linguistic or behavioral Persona Fidelity.

### History-regime and temporal diagnostics

For current-preference choice, the descriptive H contrasts were:

- aligned-helpful: `-0.2500`, 4/4 complete, LOPO `[-0.3333, -0.1667]`;
- outdated-conflicting: `-0.1250`, 4/4 complete, LOPO `[-0.1667, -0.0833]`; and
- irrelevant: `+0.1250`, 2/4 complete, logical bounds `[-0.3125, +0.3125]`.

These strata contain only four cases each. Aligned history performing worse in this bank does not establish that semantic alignment is generally harmful.

Outdated-value adoption became mechanically classifiable in the declarative outdated-conflicting cells: C6 was 2/4 and C7 was 2/4. In both conditions all four cases selected current Option A; the archived preference mapped to A in two cases and B in two. The 2/4 incidence is therefore equally compatible with an Option-A/position bias and must not be attributed to history. The paired C7-minus-C6 estimate was exactly 0 over all four cases, but this is only the S contrast at F=H=1, not an H or repair effect. The archived raw-history counterparts remained 0/4 resolved in each condition, so raw-versus-declarative outdated-adoption benefit has no point estimate and logical bounds `[-0.5, +0.5]`.

## Measurement and response validity

All 48 new completions ended with native EOS and all 48 automatic units were identifiable. Nevertheless, all 48 response-status records remained `AMBIGUOUS` and semantic completeness remained `UNCERTAIN`, because no certified independent semantic boundary or completeness judgment was supplied. Native EOS is not semantic completion.

No genuine human label was created. Response relevance, semantic factual support, temporal interpretation beyond the finite outdated endpoint, answer completeness, conversational coherence, broad linguistic Persona Fidelity, and behavioral Persona Fidelity remain pending blinded human evaluation. The secondary exact-cue endpoint can label a semantically supported comparative answer as `CONTRADICTED` when it also accurately quotes the unselected option's note: `REP_G_CONFLICTING_CLASS__C6` selected Kestrel Workshop and stated its free-modification property, but also accurately noted that the unselected alternative was non-refundable. The cue endpoint is not a semantic factual-consistency endpoint, and no conclusion relies on it.

## Resource observations

- New generations: 48
- Generated tokens: 1,329
- Native EOS: 48/48
- Completion-inference time: 266.9242473 seconds
- Batch wall time: 276.7579974 seconds
- Mean completion time: 5.5609218 seconds
- Server peak working set: 2,634,989,568 bytes
- Minimum observed available physical RAM during the batch: 1,508,548,608 bytes
- Cumulative autonomous budget after execution: 340/1,200 generations and 1,968.0195240/72,000 inference seconds

## Scientific conclusion

On this fixed synthetic bank and model, the new declarative batch showed a large same-bank cross-batch surface/measurement association: registered raw-frame recurrence was 44/48 in archived raw H=1 and 2/48 in new declarative H=1, while strict selection resolution was 2/48 and 42/48. Because the selector rejects the raw frame and wording is aliased with batch, this is not a semantic reliability effect. In the complete-case descriptive reconstruction, the explicit current-preference fact block had a positive point estimate on the frozen current-preference-choice endpoint (+0.1250; logical bounds `[0.0000, +0.2083]`), whereas declarative-H/batch (-0.1250) and the explicit style-prompt package (-0.2250) were associated with lower values of that endpoint. The style package simultaneously produced near-ceiling uptake of the narrow surface contract. These are real model observations with preserved negative and missing outcomes, but they are output-informed, same-bank, cross-batch, single-model development evidence. They do not establish that wording generally dominates semantic history effects.

No novel algorithm has been established. The declarative rewrite is a simple surface-normalization baseline; its content benefit is unidentified. Any later algorithm must compare against it under comparable information and cost. The next valid step is a fully disjoint, prospectively frozen validation bank with a length-matched neutral-history control, complete counterbalancing, surface-independent target/entity diagnostics frozen before output, and genuine blinded semantic and Persona Fidelity judgments. A separately frozen cross-model replication should follow without tuning on that validation bank. Real-speaker claims remain blocked until lawful, governed speaker-derived material exists.

## Reproducibility boundary

The frozen manifest binds all 48 prompts, native tokenizer outputs, prompt hashes, request order, model/backend/template identities, runtime parameters, source hashes, and cumulative authorization. The 469-event append-only run journal contains the source snapshot, live token checks, request/response bodies, raw generations, deterministic results, memory observations, timestamps, and terminal summary. The post-run audit verified all 48 HTTP bodies and results and required a valid replay of the parent execution evidence before combined analysis. Generation reproduction can reconstruct the configuration, but bit-identical output is not guaranteed across environments.

A separate read-only analysis process in the same autonomous session reconstructed the 469-event child journal, 899-event parent journal, 48 child and 96 parent score objects, all condition/effect summaries, and resource accounting from frozen evidence with zero differences and zero model calls. Its receipt is `analysis_reproduction_v1.json` (SHA-256 `cc7d43a42381b9c2952ac29433e18552f9cf3b65eab17891b503bb7a1fa91dcd`). This is analysis reproduction, not an independent researcher, independent sample, semantic validation, or generation repeatability result. The successful preflight preserves the disk-gate pass and threshold, but not the exact contemporaneous free-disk byte count.

After completion, the prospective test that had permanently asserted absence of authorization/run artifacts was made phase-aware: it now verifies the frozen authorization, manifest, preflight, and claim hashes when those completed artifacts exist. This maintenance edit occurred after all model outputs and did not alter frozen execution code or evidence. The post-run test SHA-256 is `2ad0ada896a592936000d4c6803085930838568d2442fbe4d97853f5812a898d`; the updated combined related suite passed 32/32.
