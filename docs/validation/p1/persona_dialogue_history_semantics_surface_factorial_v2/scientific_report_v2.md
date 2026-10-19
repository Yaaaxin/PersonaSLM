# Position-Balanced History Semantics by Surface Development Mechanism Replication v2

## Scientific status

**ACTUALLY EXECUTED — DEVELOPMENT_MECHANISM_REPLICATION.** This was a prospectively frozen, position-balanced synthetic development experiment. It is not independent validation, real-speaker evidence, confirmatory inference, or algorithm validation.

The completed experiment asked whether two properties of an archived dialogue turn have separable associations with a model's current choice:

1. archived choice semantics: aligned with versus conflicting with the current preferred choice; and
2. assistant surface form: a raw recommendation frame versus a declarative statement.

Style and facts were held present (`S=1`, `F=1`). Twelve synthetic personas supplied one matched case each. Every case appeared in five arms, for 60 frozen requests:

- `SF_NO_H`;
- `SFH_ALIGNED_RAW`;
- `SFH_ALIGNED_DECLARATIVE`;
- `SFH_CONFLICT_RAW`; and
- `SFH_CONFLICT_DECLARATIVE`.

The current-preferred position by aligned-archived-target position matrix was exactly balanced at 3/3/3/3. Aligned and conflicting archived targets each appeared first in 6 cases and second in 6 cases. The inherited absolute current-order by archived-order table remained 4/2/2/4 and is a disclosed secondary limitation.

## Prospective integrity correction

The registered but unexecuted v1 design was scientifically withdrawn before preflight or generation because aligned archived position was exactly confounded with current preferred position. Its frozen evidence was preserved. V2 changed only the archived option order in six cases, then received an independent pre-execution review before authorization. V1 contributed zero model generations.

## Execution and provenance

- Run: `results/p1_persona_dialogue_history_semantics_surface_factorial/v2/runs/20261018T192639-5e91d9f5e0c84ad2ae29d495544fa92f`
- Created: `2026-10-18T19:26:39.376212+00:00`
- Source Git HEAD: `c40667ad266082481b1850453f67784b593f3723` (dirty research worktree was recorded in the run manifest)
- Model: Qwen3.5-2B native chat, Q4_K_M third-party development artifact
- Model SHA-256: `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`
- Backend SHA-256: `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`
- Context: 4096; maximum new tokens: 96; seed: 42; CPU threads: 4
- Prompt template: `explicit_official_nonthinking_token_ids_v1`
- Case-bank SHA-256: `8e849a0f272d3551fe414516c72daceb65743f56420832507e5d346f7ef65a9e`
- Prospective-design SHA-256: `ff48daf11c0c439e1631db1898b3029a6ea1d765a0f8193e662e622f9616f5fc`
- Authorization SHA-256: `ea4fddb9d6973840f0fb03810b0d587d8dff4098ecfe990a7312b64a92711caf`
- Frozen-manifest SHA-256: `13f3baa26a8a0a1f341feb35045e88f007ef8cc65ac7dd2bbbec751bc059386a`
- Preflight SHA-256: `5e875cf60ba1640c559981c00c3c8b84994c11036bf2c75a3bf23d01320bdb0c`
- Execution-audit SHA-256: `0c90ddcd96208c85e845b30458ed6cabedcd77492ee2ab0774acfd8fe6c0d54e`
- Registered analysis SHA-256: `b1afd391e9f3fedeb4a1dc920d5b8de242847869203ea52d097ceb4219270104`

The official preflight passed with 4,139,778,048 bytes of available physical RAM against this experiment's prospectively registered 3 GiB requirement. This requirement is specific to this configuration and does not amend the historical Candidate 2 threshold.

All 60 requests were attempted exactly once. The run received 60 responses, produced 60 deterministic result records, used zero retries and zero hidden warmups, and ended `PASS`. All 60 native completions stopped at EOS. The batch produced 1,631 tokens in 339.3382625 completion-inference seconds and 352.0313928 wall seconds. Server peak working set was 2,586,701,824 bytes; minimum observed available physical RAM was 1,579,372,544 bytes.

All 60 version-bound response-status records remained `AMBIGUOUS`, with semantic completeness `UNCERTAIN`, despite native EOS. The registered finite-text endpoints are still deterministically measurable, but native stopping does not establish semantic completeness or conversational coherence.

## Observed arm results

All proportions below use 12 returned responses per arm. The reason-cue endpoint is a secondary exact-phrase diagnostic, not semantic reason correctness.

| Arm | Current preferred | Any current target | Archived-target intrusion | Raw frame | Strict format | Finite grammar | Surface style |
|---|---:|---:|---:|---:|---:|---:|---:|
| `SF_NO_H` | 11/12 | 12/12 | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 |
| `SFH_ALIGNED_RAW` | 6/12 | 9/12 | 3/12 | 12/12 | 0/12 | 12/12 | 11/12 |
| `SFH_ALIGNED_DECLARATIVE` | 8/12 | 10/12 | 1/12 | 0/12 | 9/12 | 10/12 | 11/12 |
| `SFH_CONFLICT_RAW` | 7/12 | 10/12 | 2/12 | 12/12 | 0/12 | 12/12 | 12/12 |
| `SFH_CONFLICT_DECLARATIVE` | 9/12 | 12/12 | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 |

## Registered descriptive contrasts

Contrasts are matched case-level estimates. The bracketed ranges are leave-one-persona-out point-estimate ranges, not confidence intervals.

### Declarative minus raw history surface

- current-preferred selection: **+0.1667** `[+0.0909, +0.2727]`;
- any current-target selection: **+0.1250** `[+0.0455, +0.1364]`;
- exact archived-target intrusion: **-0.1667** `[-0.1818, -0.0909]`;
- raw recommendation-frame occurrence: **-1.0000** `[-1.0000, -1.0000]`;
- strict-format adherence: **+0.8750** `[+0.8636, +0.9091]`; and
- surface-style uptake: **0.0000** `[-0.0455, +0.0455]`.

The surface manipulation therefore reproduced a large and perfectly observed effect on the registered raw-frame diagnostic and a large accompanying format effect. These two endpoints are structurally overlapping rather than independent: strict format explicitly excludes the article-bearing `I recommend the ...` frame. The manipulation also produced smaller descriptive improvements in current-choice reliability.

### Aligned minus conflicting archived semantics

- current-preferred selection: **-0.0833** `[-0.1364, 0.0000]`;
- any current-target selection: **-0.1250** `[-0.1818, -0.0455]`;
- exact archived-target intrusion: **+0.0833** `[0.0000, +0.1364]`;
- raw recommendation-frame occurrence: **0.0000** `[0.0000, 0.0000]`; and
- strict-format adherence: **-0.1250** `[-0.1364, -0.0909]`.

Within these 12 synthetic cases, aligned history did not improve either registered selection endpoint relative to conflicting history. The direction was descriptively worse. This is a negative development result, not evidence that semantic alignment is generally harmful.

### Semantics-by-surface interaction

- current-preferred selection: **0.0000** `[-0.0909, +0.0909]`;
- any current-target selection: **-0.0833** `[-0.0909, 0.0000]`;
- exact archived-target intrusion: **0.0000** `[-0.0909, +0.0909]`;
- raw recommendation-frame occurrence: **0.0000** `[0.0000, 0.0000]`; and
- strict-format adherence: **-0.2500** `[-0.2727, -0.1818]`.

The primary choice endpoint showed no observed interaction. The strict-format interaction reflects incomplete declarative-format recovery in the aligned cell and must not be interpreted as an internal semantic mechanism.

### Factorial history mean minus no history

- current-preferred selection: **-0.2917** `[-0.3636, -0.2273]`;
- any current-target selection: **-0.1458** `[-0.1591, -0.1136]`;
- exact archived-target intrusion: **+0.1250** `[+0.0909, +0.1364]`;
- raw recommendation-frame occurrence: **+0.5000** `[+0.5000, +0.5000]`;
- strict-format adherence: **-0.5625** `[-0.5682, -0.5455]`; and
- surface-style uptake: **-0.0417** `[-0.0455, -0.0227]`.

Every history cell was slower than its paired no-history cell. Mean paired completion-latency differences ranged from +0.8801 to +1.0127 seconds.

## Scientific interpretation

The experiment supports a narrow reproducible development finding for this model, prompt family, and synthetic controlled-choice distribution: archived assistant wording can dominate output surface form and is associated with lower current-choice reliability, while a simple declarative rewrite removes the measured phrase recurrence and partially recovers selection and format behavior. The no-history arm nevertheless retained the highest current-preferred rate (11/12), so declarative rewriting is mitigation, not restoration of an advantage from history.

The experiment does **not** establish an internal copying mechanism, a universal history-contamination effect, broad dialogue reliability, real-speaker Persona Fidelity, semantic reason correctness, or population-level generalization. Aligned versus conflicting history changed target identity, reason semantics, and lexical overlap as a package. History versus no history additionally bundles context length, archived entities and reasons, and an assistant turn; there was no length-matched irrelevant-history control in this experiment. Exact canonical-name scoring does not detect paraphrased or hybrid target references that omit every frozen name. For example, one response used shortened `Umber entrance` rather than the full frozen `Umber Museum Entrance`, and another emitted the hybrid `Moss Rehearsal Room`; the deterministic full-name scorer did not recover these entity-component relations. No p-values or confirmatory thresholds were registered or computed.

Broad linguistic Persona Fidelity, behavioral Persona Fidelity, conversational coherence, and semantic reason correctness remain human-only endpoints and are pending genuine blinded review. The observed `surface_style_uptake` endpoint is narrow prompt-contract adherence and must not be presented as general Persona Fidelity.

## Algorithm and novelty status

No algorithm was introduced or validated. Declarative history rendering is a simple baseline and cannot be claimed as novel. These observations identify a bounded failure mechanism and a baseline mitigation worth testing on disjoint cases and models; they do not establish a differentiated algorithmic contribution.

## Reproducibility boundary

The frozen manifest contains exact prompts, prompt hashes, native tokenizer records, model and backend identities, runtime settings, request order, and source hashes. The run directory contains the append-only event journal, verified HTTP bodies, source snapshot, server log, and terminal summary. The post-run deterministic `execution_audit_v2.json` verifies journal integrity and all 60 responses. A separate read-only reconstruction in the same autonomous session subsequently rebuilt all frozen endpoints directly from raw response text, verified the 575-event hash chain and source snapshots, and found zero score or summary discrepancies; it is analysis reproduction, not an independent researcher or independent experiment. Its receipt is `analysis_reproduction_v2.json`, SHA-256 `569c866e89d70976e3e1d3417ad2df4f7fd9076cd6ae2a65f5581ab7e39eac24`. `analysis_v2.json` materializes every registered cell, arm summary, matched contrast, missing-outcome bound, leave-one-persona-out sensitivity, and resource observation from the frozen evidence.

Generation reproduction can reconstruct the configuration, but bit-identical output is not guaranteed across CPU, backend, or dependency changes. Public reproducibility is partial where the exact model artifact or local raw evidence is unavailable.

## Next scientifically justified action

Freeze a genuinely disjoint validation case bank before any new outputs, retain the same five-arm estimands and automatic endpoints, add blinded human semantic/persona judgments, and test whether the surface and history-reliability findings replicate. A later cross-model replication should use a separately frozen model configuration. Real-speaker validation remains contingent on lawful, appropriately governed speaker-derived material.
