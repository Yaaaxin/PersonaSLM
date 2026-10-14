# P1c Final Scientific Decision — Review v1

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First target: PLOS ONE. Protocol v1.1 and the unadopted v1.2 Revised Proposed r1 remain unchanged.

## Decision

**NO-GO for the 72-request calibration at present. GO for researcher review of the completed offline package.** Technical identification/token checks pass; scientific approval, neutral suitability and inference authorization remain absent. There is no new generation, output, human approval or empirically measured P1c effect.

The narrow operational question is potentially defensible: do different topically related/unrelated auxiliary records, valid/expired at the requested date, change outcomes under shared sufficient evidence? R and T are independently routed but do not isolate unique semantic mechanisms. Do not present this bank as stale-answer competition. No concrete answer/routing defect required a stimulus revision, so the existing bank was preserved rather than redesigned.

## Review and acceptance gates

| Gate | Current state | Minimum remaining action |
|---|---|---|
| Original 12 cases, six condition IDs and 72 ordered identities | PASS | Preserve pinned sources |
| Evidence, question, reference, dates, context and model equality | PASS | Retain checks at execution preflight |
| Native model/backend/tokenizer and full prompt IDs | PASS: all 72 retokenizations identical | Recheck identities at any later execution |
| Active/neutral token match and context capacity | PASS: 12/12 sets, zero difference; max 938+96 <4096 | No matching relaxation |
| Scientific interpretation | PENDING | Accept narrow package estimands and date/value/lexical limitations, or decline this diagnostic |
| Case and historical-text semantics | OPEN: 12 cases and 60 texts | Complete separate forms with actual researcher decisions |
| Neutral validity | OPEN: 12 controls within those 60 | Explicitly approve limited procedural replacement, revise or reject; no automatic neutrality |
| Outcome and analysis policy | PROPOSED | Approve requested-date scoring, first-unit/unknown handling, simple/average interaction interpretation and prospective hierarchy |
| Prospective protocol authority | NOT ADOPTED | Approve the standalone P1c addendum; neither v1.1 nor v1.2 is edited |
| Execution freeze and authorization | NOT GRANTED | Approve exact input/configuration hashes and a final logging/resume manifest; authorize the bounded run explicitly |

The [input snapshot](validation/p1c/scientific_review_v1/calibration_freeze_candidate_v1.json) freezes what is being reviewed, not permission to run it. It preserves the original order with seed 715001 and records that the source has case/condition identities rather than separately assigned request IDs. No new randomization or substantive configuration was introduced. An actual execution adapter must stop on mandatory preflight failure, preserve partial attempts, distinguish completed from uncertain requests and never silently replay an uncertain generation under a changed configuration. That runtime manifest is a later approved action, not an outcome of this offline task.

## Required researcher decisions

Review the [12-case and 60-text package](P1c_scientific_review_guide.md). Accept or reject the **non-answer auxiliary topical comparison** as useful; accept the retrospective historical-state interpretation; decide narrow control suitability; confirm the requested-date outcome rubric and reporting hierarchy; approve the prospective addendum and eventual bounded execution separately. These decisions do not require a broad candidate search. If the narrow question is not useful, pause this design and request only a separately scoped competition comparison.

The [addendum proposal](validation/p1c/scientific_review_v1/prospective_protocol_addendum_proposal_v1.json) adds prospective operational factors, time interpretation and governance outside unchanged C0–C7. A standalone plan alone should not silently alter the formal estimands. No wholesale v1.2 adoption is requested. Independent validation precision and optional algorithm/model ambitions are not new requirements for accepting this development review; they govern later claims.

## Important limitations and scientific value

P1b case-level recomputation retains H Correct-label differences of −11.46 pp factual, −18.18 pp temporal and −18.75 pp full task success under the adopted-span sensitivity. Evaluated-only H sensitivities are −5.56 pp factual (18/24 cases) and −12.50 pp temporal (8/11); all-eligible binary bounds are [−18.75,+3.13] and [−29.55,+2.27] pp. These are development package observations, not proof that stale history caused the errors. Temporal S×H averages zero while signed case contributions cancel.

P1c's matched inputs remove length/position differences among the five nonempty cells, but do not remove predicate/color/date, topic, speech-act or archive-framing differences. The six clusters and small template bank cannot establish useful population interaction precision. The [budget plan](P1c_output_budget_risk.md) is optional, not a demand for another experiment before review. Retain Base initially if this scoped study is approved; an Instruct arm would test configuration sensitivity, not pure post-training.

The [prior-art review](P1c_scientific_prior_art_review.md) documents direct overlap with memory admission, temporal retrieval, factual-personalization steering and logic/persona separation. The algorithm assessment remains prospective: none of the six candidate directions warrants implementation on this evidence. No method, mechanism, novelty or PLOS ONE readiness is established by offline checks.

For the intended paper, later evidence should include independently frozen speakers/templates, informative precision, validated semantic units, transparent AI-assistance provenance and feasible independent human review. Publishable data/code and scoped claims matter; an algorithm and positive effects are not mandatory. The [PLOS ONE criteria](https://journals.plos.org/plosone/s/criteria-for-publication) require sound methods, supported conclusions and reporting integrity; publication is not assured. Null results remain valid outcomes of a justified experiment.

## Verification and reproducibility

See [validation results](validation/p1c/scientific_review_v1/verification_v1.json), [command captures](validation/p1c/scientific_review_v1/engineering_logs/) and [reproducibility manifest](validation/p1c/scientific_review_v1/reproducibility_manifest_v1.json) for final test counts, hashes and working-tree status. Original failed matches, repairs, raw logs, annotations, protocol versions and P0/P1/P1b records are preserved. The consolidated reports use methodological sections; actual timestamps remain in engineering logs and the development log. No Git commit or push was executed.


### Completed automated validation

Full project suite: **781 passed in 31.91s**, zero failures, exit 0, no reported pytest warnings. The captured process duration was 32.482 seconds; this is a test measurement, not an experimental-generation duration. New tests cover reference dependency, R/T package changes, native-ID identity, original-order preservation, blank human fields, repair history, contrast algebra, unknown bounds and nonauthorization. Final hash/link checks are recorded separately; test success is not semantic approval.


Final source verification rerun: **781 passed in 30.27s**, exit 0, no reported pytest warnings. Both full-suite captures are preserved. Historical integrity: 5,798 run artifacts and 1,234 original tokenizer logs unchanged; 551 baseline tracked files checked with only the three documented append-only reports/log permitted to change. All 588 human-entry cells across the master forms and convenience subset remain blank.
