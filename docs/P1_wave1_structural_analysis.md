# P1 Wave 1 Structural Analysis

Maintainer: Yaxin ZHENG. Baseline: Protocol v1.1. Diagnostic version: `p1_measurement_audit_v1`. All original `response_status_v1` records remain immutable.

## Response units and backend events

The raw continuation, original first-span start/end offsets, removed prefix, excluded continuation, parser operations, native termination, output tokens and source hashes are retained for each of the 96 rows in the [audit JSON](validation/p1/measurement_audit_v1.json). Concatenating removed prefix + first span + excluded tail reconstructs every original raw response exactly. Prefix removal occurred in zero rows. Additional role-labelled spans retain their raw offsets and text; the final span can itself be cut by the budget.

There are 78 visible role transitions and 467 additional role-labelled spans across those outputs. Seventeen first spans run to the 96-token budget without an observed reply boundary. All 17 contain an opening `<think>` without a closing marker; quotations or prospective greetings inside that unfinished text are not extracted as final answers. One output has a native EOS. Every first span is mechanically identifiable, but semantic completeness has no human judgments (0/96).

The native completion budget applies to the **whole continuation**. Therefore 95 length stops do not imply 95 truncated first replies. CROSS_TURN is a structural property and does not imply a wrong first answer. Conversely a sentence ending in punctuation is not independently certified complete. The frozen COMPLETE category explicitly requires a separately supplied, hash-bound semantic judgment: zero COMPLETE must not be described as zero potentially complete first replies.

## Native EOS compatibility finding

Request `p1_speaker_11_C__C1` returned 28 tokens, `stop_type="eos"`, and terminal output token 248044. The original saved server log identifies 248044 as `<|endoftext|>` and an EOS/EOG token (lines 133 and 143). Its first span is the full raw output, beginning “Here is a friendly welcome greeting for Ellis”.

The frozen classifier recognizes `eog`, not this native `eos` enum. Its original reason is `no_certified_boundary_or_budget_evidence`, with `observed_boundary=null`; it is insufficient to describe this solely as semantic uncertainty. The additive [native-stop diagnostic](validation/p1/native_stop_compatibility_diagnostic_v1.json), version `p1_native_stop_compatibility_diagnostic_v1`, tests an eos→eog copy of the backend field. The diagnostic observes a native boundary and changes the reason to `bounded_reply_semantics_not_certified`, while the status remains AMBIGUOUS. All 96 original status labels and first spans remain unchanged; no replacement score is emitted.

Independent tests check missing semantic evidence, conflicting stop flags, role transitions and unchanged non-eos enums. A future production fix requires a new adapter/policy version and prospective documentation. This audit does not patch the frozen function or infer semantic completeness from EOS.

## Distribution and concentration

| Scope | N | COMPLETE | TRUNCATED | CROSS_TURN | AMBIGUOUS |
|---|---:|---:|---:|---:|---:|
| All responses | 96 | 0 | 17 | 78 | 1 |
| A: current state | 24 | 0 | 0 | 24 | 0 |
| B: stable facts | 24 | 0 | 0 | 24 | 0 |
| C: nonfactual greeting | 24 | 0 | 17 | 6 | 1 |
| D: temporal follow-up | 24 | 0 | 0 | 24 | 0 |

Overall proportions are 81.25% CROSS_TURN, 17.71% TRUNCATED and 1.04% AMBIGUOUS. These aggregate different response behaviors. No baseline-correctness filter or structural exclusion was applied.

| Condition | N | CROSS_TURN | TRUNCATED | AMBIGUOUS |
|---|---:|---:|---:|---:|
| C0 | 12 | 10 | 2 | 0 |
| C1 | 12 | 9 | 2 | 1 |
| C2 | 12 | 10 | 2 | 0 |
| C3 | 12 | 9 | 3 | 0 |
| C4 | 12 | 10 | 2 | 0 |
| C5 | 12 | 10 | 2 | 0 |
| C6 | 12 | 11 | 1 | 0 |
| C7 | 12 | 9 | 3 | 0 |

In the following complete case inventory, X=CROSS_TURN, T=TRUNCATED, A=AMBIGUOUS. Δ is the within-case difference in the CROSS_TURN indicator.

| Case | C0 | C1 | C2 | C3 | C4 | C5 | C6 | C7 | Δ C1−C0 | Δ C3−C0 |
|---|---|---|---|---|---|---|---|---|---:|---:|
| p1_speaker_01_A | X | X | X | X | X | X | X | X | 0 | 0 |
| p1_speaker_02_B | X | X | X | X | X | X | X | X | 0 | 0 |
| p1_speaker_03_C | T | T | T | T | T | T | X | T | 0 | 0 |
| p1_speaker_04_D | X | X | X | X | X | X | X | X | 0 | 0 |
| p1_speaker_05_A | X | X | X | X | X | X | X | X | 0 | 0 |
| p1_speaker_06_B | X | X | X | X | X | X | X | X | 0 | 0 |
| p1_speaker_07_C | T | T | T | T | T | T | T | T | 0 | 0 |
| p1_speaker_08_D | X | X | X | X | X | X | X | X | 0 | 0 |
| p1_speaker_09_A | X | X | X | X | X | X | X | X | 0 | 0 |
| p1_speaker_10_B | X | X | X | X | X | X | X | X | 0 | 0 |
| p1_speaker_11_C | X | A | X | T | X | X | X | T | −1 | −1 |
| p1_speaker_12_D | X | X | X | X | X | X | X | X | 0 | 0 |

## Factorial descriptions and uncertainty

Let Y be the CROSS_TURN indicator. A main effect averages the four within-case on−off differences over the other two factors. A pairwise interaction is the difference-in-differences averaged over the remaining factor; it is not the simple C1−C0 or C3−C0 contrast. All 12 cases contain all eight cells, but responses within a case are dependent.

| Contrast | Mean difference (percentage points) | Cases with nonzero difference |
|---|---:|---|
| C1−C0 | −8.33 | 11_C only |
| C3−C0 | −8.33 | 11_C only |
| Average S | −4.17 | 03_C, 11_C |
| Average F | +4.17 | 03_C, 11_C |
| Average H | 0.00 | 03_C, 11_C cancel |
| S×H, averaged over F | 0.00 | 03_C: −0.5; 11_C: +0.5 |
| S×F, averaged over H | −8.33 | 03_C: −0.5; 11_C: −0.5 |
| F×H, averaged over S | 0.00 | 03_C: +0.5; 11_C: −0.5 |

All remaining case-level interaction values are zero; full category-specific contrasts are retained in the audit JSON. The complete factual-task CROSS_TURN saturation prevents discrimination on that indicator. Zero average interactions can conceal opposing observations. Neither significance tests nor a precision/equivalence claim are justified by these descriptive results. There are 12 speaker-case clusters, not 96 independent speakers, and only three speakers per family. Family, persona, wording and content differences cannot be separated cleanly here.

Native EOS compatibility does not alter these structural contrasts. Future semantic annotation might show evaluable first replies despite transcript continuation, or different first-span/full-continuation judgments. Both are hypotheses to evaluate, not completed findings. The proposed v1.2 fixed-F interaction differs from the frozen wave's averaged interaction and is not substituted retrospectively.
