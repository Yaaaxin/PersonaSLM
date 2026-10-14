# P1c Researcher Decision Registration and Execution Gate — v1

Maintainer: Yaxin ZHENG. First submission target: PLOS ONE. This is a decision-import workflow, not a new experimental design or an inference runner.

## Actual status

Current HEAD at entry: `ab588dd973dfbb3743279d15bf1f72b8909efa6b`; working tree was clean. All 77 rows of the original confirmation form, all 12 case forms, all 60 text forms and their 12-control subset have blank human fields. No completed researcher file was found among the current P1c files. **Zero real decisions have been registered.**

The [offline gate result](validation/p1c/decision_gate_v1/current_gate_status_v1.json) is NO_GO. Technical verification passes: 12 cases, 60 history/control texts, 72 original requests, unchanged order, prompt/reference/applicability reconstruction, all saved native token-ID arrays and current pinned model/backend/tokenizer/DLL hashes. This verification reuses actual earlier tokenizer logs; it does not run tokenization or generation anew. Previous broad audits and precision simulations were not repeated.

There are **72 unique item decisions outstanding**: 12 cases and 60 text records. Twelve text rows also require a diagnostic-control assessment; those are not twelve new observations. Five scientific policy decisions and a separate execution authorization remain outstanding.

## Restricted analysis metadata

The [analysis specification overlay](validation/p1c/decision_gate_v1/analysis_restrictions_v1.json) retains every original condition ID and all 16 registered contrast weights. R and T remain the original topic/attribute/color and validity-interval/value packages. Their contrasts do not isolate pure topical relevance, pure temporal validity, stale-answer competition or internal model mechanisms.

All 12 original `N_history` records receive separate analysis metadata:

`analysis_control_class = LENGTH_MATCHED_DIAGNOSTIC_CONTROL`

Their treatment IDs and old labels remain untouched. This classification implements the researcher's current interpretation rule; **it is not human approval of the twelve texts**. Comparisons against them remain length/format-matched diagnostic content replacements with unresolved semantic, temporal and stylistic differences. They are not fully controlled semantic-history effects. A claim of strict neutrality would need a different, explicitly supported review/version; this importer cannot upgrade them automatically.

Use the existing four reliability endpoints, plus separate task success, component coverage, semantic completeness and structural outcomes. Persona Fidelity remains N/A without its own ground truth. Correct, Incorrect, Unverifiable, Not Applicable and administrative Missing remain distinct. Retain 12 paired case units and six speaker clusters; no 72-independent-observation analysis or composite score is introduced. The frozen 96-token cap and response-boundary limitations remain in force.

## Three separate inputs

Create completed **copies** of these masters. Editing the masters would break their source hashes.

1. [Item decision CSV v2](validation/p1c/decision_gate_v1/researcher_item_decisions_v2.csv): 72 rows, exact original IDs and source-item hashes. It references existing full review materials without duplicating their stimulus text.
2. [Scientific approval JSON](validation/p1c/decision_gate_v1/scientific_approval_template_v1.json): researcher provenance and five policy decisions bound to exact source hashes.
3. [Execution authorization JSON](validation/p1c/decision_gate_v1/execution_authorization_template_v1.json): a separate explicit instruction, bound to both the frozen 72-request manifest and the eventual registered-decision snapshot.

The original 77-row v1 confirmation form remains intact. Its earlier vocabulary is not silently translated. The new v2 CSV uses the current requested decision vocabulary; old `ACCEPT_AS_DEVELOPMENT` or `ACCEPT_WITH_LIMITATIONS` values require explicit researcher clarification rather than automatic mapping. A completed old form by itself does not satisfy the new gate.

### Item decisions

Allowed `researcher_decision` values are:

- ACCEPT
- ACCEPT_WITH_RESTRICTED_ESTIMAND
- DIAGNOSTIC_ONLY
- REVISION_REQUIRED
- REJECT

ACCEPT validates the item within the global restricted design; it cannot enlarge the estimand. Every other value requires a specific `restriction_reason`. Preserve corrections or disagreements in `researcher_notes`; do not alter original text or AI proposals. A correction that requires stimulus changes must use REVISION_REQUIRED and a later version, not a silent edit.

Two positive-criterion fields are mandatory for every item:

| Field | YES | NO / UNCERTAIN |
|---|---|---|
| `reference_answer_valid` | The common evidence still supports the unchanged reference under the requested interpretation | Material validity concern remains; no GO |
| `no_material_answer_leakage` | No material unintended answer leakage is identified | Leakage/uncertainty remains; no GO |

These fields do not certify absence of all shortcuts or pure mechanism identification. They address the mandatory reference/leakage gate only. Missing values are rejected. Acceptance alongside NO or UNCERTAIN is contradictory and rejected; a corresponding REVISION_REQUIRED or REJECT is preserved as a valid negative decision that blocks GO.

For the twelve rows marked `is_matched_control=YES`, also enter `control_assessment_decision` and `control_assessment_reason`. Allowed dispositions are DIAGNOSTIC_ONLY, REVISION_REQUIRED or REJECT. A diagnostic acceptance needs a reason acknowledging its restricted scientific role. Contradictory text/control dispositions are rejected. Non-control rows must leave both control fields blank. The same twelve source IDs link text and control assessment, so no duplicate record is imported.

### Scientific approval and provenance

The completed JSON must identify `Yaxin_ZHENG`, `RESEARCHER_CONFIRMED`, decision source `researcher`, and the actual method `Researcher review of AI-assisted scientific proposals`. It requires an explicit confirmation statement and decisions on:

1. Restricted package-level estimands.
2. Diagnostic-only control policy.
3. Evaluation policy and frozen applicability.
4. Statistical analysis policy.
5. P1c-specific prospective protocol addendum.

Each policy uses APPROVE, DECLINE or DEFER and a specific scope/reason. DECLINE/DEFER are preserved, not converted to approval; either blocks GO. This separates the prior combined evaluation/statistics decision into explicit checks without adding a new scientific requirement.

`review_timestamp` may remain null. Do not fill it with import time. The importer records its own actual registration time separately. It retains source CSV/JSON bytes, AI source hashes, researcher corrections, current Git state and importer hash. It does not claim independent blinded annotation, a second human reviewer or agreement statistics. File metadata validates consistency and traceability, not a cryptographic proof of the researcher's identity; registration must be based on an actual researcher-supplied or explicitly confirmed record.

### Separate authorization

After registration, copy its SHA-256 from `registration_receipt_v1.json` into the authorization file. Explicit authorization requires `AUTHORIZE_72_REQUESTS`, integer request count 72, `Yaxin_ZHENG`, decision source `researcher`, and the researcher's actual authority statement. The statement must refer to this bounded experiment. No timestamp is invented; it can remain null.

The file binds to manifest SHA-256:

`b0cf330d9dd5f7b59a186dc298c477a97bd86e06a29209805989a9f399fde02b`

A filled item form, policy approval, original global authorization row, file existence, or an AI recommendation is **not** substituted for this separate explicit authorization. DECLINE/DEFER and missing or mismatched authorization retain NO_GO.

## Validated commands

Run from the repository root. Paths below refer to completed copies to be supplied later; these commands were not used to register nonexistent human decisions.

```powershell
.venv\Scripts\python.exe tools/p1c_decisions.py validate --items completed_item_decisions.csv --approval completed_scientific_approval.json

.venv\Scripts\python.exe tools/p1c_decisions.py register --items completed_item_decisions.csv --approval completed_scientific_approval.json --output docs/validation/p1c/decision_registrations/v1

.venv\Scripts\python.exe tools/p1c_decisions.py gate --registration docs/validation/p1c/decision_registrations/v1/registration_v1.json --authorization completed_execution_authorization.json --output docs/validation/p1c/decision_gate_v1/authorized_gate_v1.json
```

Registration validates the complete set before creating an output directory. Valid negative decisions may be registered but block GO. A malformed or incomplete set is rejected as a whole, with exact item/field errors. Existing output destinations cannot be overwritten. If an interrupted import leaves an incomplete directory, preserve it and use a new version; the gate cannot accept a partial registration without its validated receipt. An amended decision requires a new preserved registration and new authorization binding.

CSV schemas, duplicate/unknown IDs, immutable metadata, positive criteria, duplicate JSON keys, reviewer identity, optional timestamps, policy bindings, control contradictions, registration tampering and request counts are checked. Legacy labels are not guessed. All source originals remain untouched.

The gate's exit code 0 means GO; code 2 means NO_GO or rejected input. The capture wrapper reports a nonzero child result for the intentionally pending gate. This is not an inference or automated-test failure. Even GO only writes a report: this module has no generation, server, training or algorithm entry point.

## Exact execution conditions

GO requires all mandatory technical checks, accepted cases/texts, twelve explicitly reviewed diagnostic-control uses, no unresolved reference/leakage defect, five approved policies and explicit authorization tied to the exact registration/manifest. Failed or missing conditions remain listed individually. Keep all 72 requests, the original six conditions, Qwen3.5-2B-Base Q4_K_M, llama.cpp b11573, CPU threads 4, context 4096, output cap 96, decoding seed 42 and order seed 715001.

Any substantive change requires a new version and renewed approval. At a later authorized execution, disk/logging/resume/runtime preflight must still pass; this offline decision report is not a running service or a replacement for launch checks. No authorization has been provided in this task.

## Algorithmic opportunities retained

The existing [six-part prior-art assessment](P1c_algorithmic_opportunity_assessment.md#final-review-opportunity-assessment) remains the analysis authority; no new broad literature review or algorithm development is needed to register these decisions.

| Direction | Existing evidence and methods | Unresolved gap and candidate improvement | Validation/publication requirement |
|---|---|---|---|
| Temporal memory admission | P1b temporal errors; LongMemEval time-aware retrieval and interval filtering | Requested-date handling beyond availability/value cues remains unresolved; a selector is only a candidate | Independent current/historical cases, interval/newest/oracle baselines; no novel-method claim |
| Relevance retrieval | H package differences; published memory admission and query-relevance selection | Relevance versus exclusion/length remains confounded; topic/answer-support gate is hypothetical | Full/no-history, equal-count random and relevance baselines; measure helpful-memory loss |
| Persona/evidence separation | S/F/H heterogeneity; AO-DA and FPPS overlap | Adaptive separation beyond static/equal-compute methods is untested | Independent S/F/H cases and separate fidelity assessment |
| Evidence priority | Errors despite sufficient evidence; source-priority engineering and FPPS | No isolated authority-routing failure; provenance routing remains a hypothesis | Instruction/rule/steering baselines where feasible; disclose infrastructure differences |
| Component verification | Supported claims exceed complete answers; CoVe and RARR already verify/revise | Coverage beyond claim verification is unproven | Checklist/schema/published verifier baselines, independent components and compute controls |
| Response boundaries | Cross-turn outputs coexist with valid first replies; templates/stops/parsers are established | Unit-selection bias not quantified independently | Human-span validation, fixed parser/template/stop baselines; preserve raw outputs |

The previous source verification and its limitations remain visible in the linked assessment. No originality claim is added. The empirical study remains primary; independent validation, measurement reliability and useful precision matter for PLOS ONE. An algorithm is optional and not a new approval gate.

## Validation evidence

Necessary non-generation tests: **105 passed in 2.42s** across the new importer/gate tests and existing final/scientific-review regression suites. This includes 60 new test cases using artificial temporary fixtures; those are explicitly not registered research annotations. The complete historical suite was not rerun for this narrow workflow. Its earlier 796-pass result remains historical, not a claim about this run.

See [source bindings](validation/p1c/decision_gate_v1/source_pins_v1.json), [technical/gate report](validation/p1c/decision_gate_v1/current_gate_status_v1.json) and [reproducibility record](validation/p1c/decision_gate_v1/reproducibility_manifest_v1.json) for actual commands, tests, hashes and working-tree preservation. No protocol, historical output, original review form, manifest or control text was changed; no commit or push was executed.
