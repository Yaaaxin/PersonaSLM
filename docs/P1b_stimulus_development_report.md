# P1b Stimulus Development and Offline Validation — v1

Maintainer: Yaxin ZHENG. Official title: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Status: **PROPOSED DEVELOPMENT ONLY; empirical discrimination UNTESTED; human semantic review OPEN**. Zero new model generations and zero new tokenizer requests. No Wave2, model training or later phase was started.

## Scope and source preservation

Starting HEAD was `287b74381ddef95ec530817dff76c676a59dd5bc`, with a clean working tree. The current proposal retains Protocol v1.1 as formal and leaves v1.2 Revised Proposed r1 unchanged. Existing P0 acceptance, Wave1 stimuli, outputs, annotations, automatic scores and analytical results are historical evidence, not editable calibration material.

An initial baseline records313 tracked files and3,192 original P1 run files. The latter are byte-identical after the offline audit; both event chains verify (2,278 preparation events and909 generation events). The final [delivery record](validation/p1b/delivery_v1.json) identifies the exact allowed configuration/log edits and preserved source inventory. This is not a new audit of every ignored P0 run directory; tracked P0 evidence is protected by the baseline, and earlier P0 raw audits remain unchanged.

The new [dataset](../data/synthetic/p1b_development_proposed_v1.json) has SHA-256:

`feea8880314bea78e8b74aebbdbeb3439237551df56d7bd8b34a019ebeabd49a`.

The [design manifest](validation/p1b/design_manifest_v1.json) records actual creation metadata, Git SHA/dirty state, source hashes and output hashes. The [offline validation](validation/p1b/offline_validation_v1.json) records every evidence, question, context, answer and eight-condition prompt hash. Rebuilding from the saved generator reconstructs the exact JSON and all192 prompt hashes. No token count is approximated or fabricated.

## Implementation decisions

The independent `personaslm.p1b` module builds a deliberately small bank and a deterministic **source-query oracle**. It does not call a model, alter production response policies, or grade English outputs. The CLI `tools/p1b_design.py` either creates a fresh package or verifies an existing one without replacing it. All builds are local, deterministic and refuse existing versioned destinations.

There are twelve fictional speakers and24 cases, two per speaker, covering eight families and three designed complexity levels per family. The second allocation block shifts speaker IDs to avoid a single complexity level being constant within speaker. This is not full orthogonal counterbalancing: family/level cells have one prototype and style realization remains nested in identity. Future larger allocations need more independent realizations; the bank is not a confirmatory sample.

Source facts use explicit unique IDs and inclusive validity intervals. Queries specify unique selections/joins, temporal filters and, where necessary, a verbatim context binding. The English question and symbolic query are both saved so a human can inspect their agreement. New fact-ledger formatting differs from Wave1 prose; old/new differences would combine task and presentation changes, not isolate difficulty.

The same trusted evidence, question, reference and recent context occur in all eight cells of each case. The evidence begins in the same common prefix. S/F/H additions remain independently switched and in the same block order. Character position is verified; actual token positions/context capacity await the future real-tokenizer preflight. Answers occur in the common source or are derived from it, never supplied accidentally by the additional style, possession or residence-history blocks under the construction checks.

## Actual validation results

| Check | Result | Scope / limitation |
|---|---|---|
| Dataset schema/allocation |24 unique cases;12 speakers;8 families ×3 levels | Fictional development material, not a sample-size claim |
| Symbolic support |24/24 unique oracle answers | Human question-to-oracle agreement still OPEN |
| Necessary-evidence deletion |46/46 removal checks refused unsupported resolution | Internal oracle necessity, not a model performance measurement |
| Key-evidence change |24/24 changed the oracle answer | Controlled in-memory source variants only; no altered historical evidence or generated output |
| Factorial prompts |192 reconstructed; common inputs preserved | Full S/F/H grid; no matched neutral prompts for new cases |
| Applicability |24 factual;11 temporal;24 relevance/coherence;0 fidelity | New proposed matrix saved per case; historical matrix unchanged |
| Independent regression examples |Temporal boundaries, four-fact chain failure, wrong entity, ambiguous role, missing context, leakage, contradictory intervals, unsupported keys | Tests are meaningful source/measurement safeguards, not human semantic ratings |
| Old real tokenizer evidence |24 exact matches;720 native records reconciled | Existing Wave1 prompts only; no new tokenization |
| Old model/backend |Both actual file hashes match saved design | No new inference; upstream quantization equivalence is not inferred |
| Historical response integrity |96 raw/first-span hash pairs and applicability match;972 contrast rows inspected | Frozen structural labels and original human provenance retained |
| Full current test suite |**510 passed,0 failed,14.55seconds,exit0; no warnings reported** | Test process15.291056seconds; no new real-model generation |

The deletion/change checks are **analytical evidence-dependence checks**, not proof that a language model will find these tasks difficult. More linked facts, competing entities and date boundaries create distinct operations; genuine empirical discrimination remains unmeasured. A supported partial reply can still receive factual Correct under the existing policy; retain completeness/relevance separately rather than changing the rule to manufacture errors.

## Review materials and precise status

The blank [stimulus form](validation/p1b/stimulus_review_v1.csv) includes each case's evidence, question, context, answer components/proof IDs, interventions, eligibility and human judgment fields. Suggested labels are PASS/FAIL/UNCERTAIN for the six checks; a FAIL/UNCERTAIN needs quoted source and a correction rationale. Reviewers should independently trace the English task before comparing it with the proposed key. No reviewer identity, time or judgment is filled. This form is **not** the old control import schema; retain any completed copy separately and validate IDs/immutable materials before a later registration.

The [control index](validation/p1b/control_review_index_v1.csv) presents the unchanged24 old matched controls, with the original complete form and validated importer linked from the [control guide](P1b_control_review_preparation.md). Human review remains0/24 OPEN. Exact old token matches do not transfer to new questions/templates or establish neutrality. New P1b stimuli have no approved controls and no actual token counts; those are explicit gates before any intended matched-control run.

## Actual commands, errors and corrections

The following meaningful commands were executed using the project virtual environment. Captures are immutable under `results/p1b_design/v1/engineering/`; they retain actual timestamps, stdout/stderr, exit codes and process durations. Commands in the future review/calibration instructions are proposals and were not executed.

| Capture | Actual subprocess command | Result |
|---|---|---|
| targeted_tests.json | `.\.venv\Scripts\python.exe -m pytest -q tests/test_p1b.py` |31 passed in0.17seconds;exit0 |
| build.json | `.\.venv\Scripts\python.exe tools/p1b_design.py build` |24 cases,192 prompt checks,24 old matches;exit0 |
| verify.json | `.\.venv\Scripts\python.exe tools/p1b_design.py verify` |Exact reconstruction;3,192 run files unchanged;exit0 |
| full_tests.json | `.\.venv\Scripts\python.exe -m pytest -q` |Collection error;pytest exit2, no completed suite |
| full_tests_corrected.json | `.\.venv\Scripts\python.exe -m pytest -q` |510 passed;exit0 |

Each was wrapped by `.\.venv\Scripts\python.exe tools/p0_capture.py --output <capture> -- <command>`. Read-only Git/PowerShell/Python inspections and primary-source web access are recorded separately; unavailable per-inspection start times are not fabricated.

Two failures were preserved. First, default `git ls-files` quotes non-ASCII filenames, causing the initial inventory script to treat an escaped quoted PDF name as a path (exit1). Using `git ls-files -z`, UTF-8 decoding and NUL splitting fixed enumeration without changing any file. Second, default pytest recursive discovery entered `results/p1_human_analysis/v1/source_final_snapshot/test_human_factorial.py`, whose original relative fixture path is invalid inside an archive. No archived file was moved/deleted. A tracked-file inspection confirmed every formal test is in `tests/`; adding `testpaths = ["tests"]` in `pyproject.toml` scopes discovery to the real suite. All479 earlier formal tests plus31 new tests pass; no assertion was weakened or test skipped to obtain a pass.

Only a narrow `.gitignore` exception was added for the named fictional dataset; private data, binaries, local models and results remain ignored. The development log is append-only. New source snapshots and full local captures remain separate from experimental archives; public reports use repository-relative paths.

## Remaining gates and information priority

The [task design](P1b_discriminative_task_design.md) proposes review of this fixed bank, then only if separately authorized one192-request Base calibration. Its empirical purpose is to test discrimination and coverage, not effects in a preferred direction. No larger allocation, Instruct arm, R/T/P intervention, budget change, semantic-control acceptance or confirmatory set is approved by software validation. The [precision plan](P1b_sample_size_and_precision_plan.md) shows why many more generations can still yield inadequate clustered precision. The researcher must choose a meaningful interval width and the narrow scientific claim before expansion.
