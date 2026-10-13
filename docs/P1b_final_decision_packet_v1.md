# P1b Final Researcher Decision Packet — v1

Maintainer: Yaxin ZHENG. **Unfilled; AI assistance disclosed.** Dataset `p1b_development_proposed_v2`, SHA-256 `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6`. Protocol v1.1 remains formal; no prospective protocol adoption.

## What is already resolved

All 192 frozen prompts expose the fictional evaluation date; all shared-input and factor-routing checks pass. H_L3 has explicit User / Assistant / User / User / Assistant-stub boundaries. The pinned GGUF tokenizer returned 150–434 input tokens; all 192 fit 4096 context with the 96-token output budget. No answer was generated. Original review fields, source files, stimuli and historical records are unchanged. See the [full scientific review](P1b_final_scientific_review.md).

No new dataset revision is recommended solely to make easy items harder or impose alternating roles on the native transcript. The supplied AI suggestions are still not human decisions.

## Only unresolved scientific confirmations

The same two questions are available in a [short decision CSV](validation/p1b/final_review_v1/decisions_pending_v1.csv). Its human decision and provenance fields are blank. It supplements the existing case-level form and does not replace its required judgments.

| ID | Question for the researcher | Recommendation, not a human judgment | Researcher decision | Case IDs / notes |
|---|---|---|---|---|
| Q1 | After inspecting the existing 24 cases, source quotations and references, are the evidence, answers, temporal/entity interpretations and frozen applicability valid for bounded development calibration? | Complete the existing case-level review, preserving all original fields. Report any concrete failed case rather than accepting AI labels automatically. | | |
| Q2 | May the unchanged bank be retained with the explicit limitations below, without claiming genuine multi-hop/context necessity, isolated history mechanisms, or guaranteed 96-token completeness? | Retain easy anchors and the explicit H_L3 same-user follow-up; preserve all cases and the 96-token setting. | | |

For Q1, use the [unchanged 41-column, 24-row review copy](validation/p1b/final_review_v1/researcher_review_v2.csv) and [existing positive-criterion guide](P1b_researcher_review_guide.md). Do not fill a second set of duplicate per-case judgments in the resolution notes. Save the completed form separately. A general checkbox here does not mechanically populate missing individual labels.

For Q2, review these specific boundaries together:

- A_L1–L3 and F_L1 are legitimate easy retrieval/identity anchors. H_L1/H_L2 do not require context to choose among competing answers. Their value is calibration, not proof of advanced reasoning.
- D has unique terminal targets; F has recurring role/name mappings. Successful answers do not establish the intended reasoning path.
- H_L3's two successive User messages are explicitly labelled and select Parcel 111. Retaining them does not assert equivalence with an alternating transcript or prove that the Base model will respect the boundary.
- B requests 2/3/4 components. Keep factual support separate from omitted components, semantic completeness and structural termination. Actual input fit does not guarantee output-budget adequacy. No primary scoring policy changes are proposed.
- Style is nested in speaker; the bookmark supplement is uniform; residence-history relevance varies with family. Interpret S/F/H as operational packages. No neutral-adjusted result or isolated temporal mechanism is justified.

Suggested decision labels for this short packet: `ACCEPT_FOR_CALIBRATION`, `REVISION_REQUIRED`, `UNCERTAIN`. If revision is required, identify the exact case, source passage and concrete validity problem. Do not select changes based on model output quality. Evidence-based easy baselines need not be discarded simply for being easy.

Reviewer ID: ____________________

Review method / assistance actually seen: ____________________

Date, only if actually recorded: ____________________

Completed case-review filename: ____________________

No blind-review claim, second reviewer, consensus or review timestamp is inferred. All decisions remain blank until supplied by the researcher.

## Import and execution gate

Future command for a completed copy; **not executed in this task**:

```powershell
.\.venv\Scripts\python.exe tools/p1b_readiness.py import-review --csv docs/validation/p1b/P1b_stimulus_completed.csv --output docs/validation/p1b/researcher_stimulus_registration_v1
```

The existing importer validates the original 41-column contract, IDs, immutable fields, all required labels and provenance. The unchanged review copy is compatible with that master. Source or label mismatches must be reported, not silently repaired. Case acceptance does not authorize execution.

Current recommendation: **NO-GO to launch now; technical tokenizer preflight PASS; human semantic review OPEN.** Once Q1/Q2 and the existing per-case review are resolved, request explicit authorization for the fixed192-request development run and use a reviewed manifest-consuming generation adapter with manual task scoring. Do not rerun tokenization merely to obtain different counts; reuse its saved evidence unless inputs/artifacts change.

The 24 original Wave 1 neutral controls remain OPEN. They are not included in these192 requests and do not block a factorial-only calibration. No new algorithm, Instruct arm, larger sample, confirmatory set or P2–P6 phase is requested here.
