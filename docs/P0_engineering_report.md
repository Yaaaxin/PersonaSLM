# P0 Engineering History and Acceptance

**Maintainer:** Yaxin ZHENG  
**Project:** PersonaSLM  
**Paper:** Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models  
**Research Protocol:** v1.1  
**Primary experimental language:** English  
**Research target:** Real-Speaker Persona Modeling with Small Language Models, approximately 0.8B–3B  
**Acceptance:** P0 PASS; Engineering and Methodological Infrastructure Validation Completed; P1 NOT STARTED

This report consolidates the preserved engineering history by development stage. It distinguishes implementation tests, real-model observations, human annotations and scientific acceptance. It introduces no new experiment, changes no frozen policy and does not replace original reports or raw records. Source documents remain authoritative for their exact command captures, original timestamps, run directories and per-case evidence. Missing historical information is identified explicitly.

The current evidence comprises 140 preserved real generations across 17 generation runs, 40 original matched-control pairs, 24 new matched development candidates, 40 completed original human reviews and 24 researcher-confirmed new candidate decisions. The detailed new annotation form remains incomplete despite completed decisions. The registration checkpoint passed334 tests and the bounded six-style closure passed348; the final scientific-closure suite passes365. An earlier bounded six-style revision produced five exact matches and one failed match. Subsequent researcher confirmation accepts the five unchanged texts; a separately authorized single Tessa correction now matches99/99 and has its own explicit ACCEPT_NARROW approval. The final closure repeats the full suite with365 passing tests and rechecks all25 historical journals without new generation. These counts refer to different inventories and must not be added together as a scientific sample size. The [final scientific assessment](P0_final_scientific_acceptance_report.md) documents the current adoption limits; the [decision registration report](P0_control_decision_registration_report.md) retains its earlier checkpoint; prior report bytes remain archived.

## 1. Infrastructure and environment setup

### Objective

Establish an isolated, writable and testable research workspace after command execution had failed with `helper_unknown_error: setup refresh had errors`. Keep local inference, synthetic data, private paths and researcher-managed Git operations separate from unrelated applications and external data.

### Implementation

Environment checks established that PowerShell commands, workspace file writes, Git inspection and the existing Python project were usable. Project components included `pyproject.toml`, `src/personaslm`, tests, configuration, protocol documents and the synthetic fixture inventory. The working project interpreter was Python 3.14.3 in `.venv`; dependency verification reported no broken requirements.

Runtime path validation resolves paths against the research root and rejects traversal, external paths, symlinks and junctions for managed inputs. Ignore rules exclude virtual environments, GGUF files, backend binaries, local configuration, raw result directories, private conversations and common credential files. The researcher exclusively manages commits and pushes; automated changes remain available for review.

### Technical decisions

Commands use the explicit project interpreter because the system WindowsApps `python` and `py` aliases did not work. The project was not repaired by changing a system-wide Python installation or PATH. Pytest uses the ignored `results/.pytest_cache` location. An unreadable preexisting cache was retained instead of changing its permissions or deleting it to manufacture a successful directory audit.

The first researcher-managed repository synchronization is identified by commit `4a538570c77666009a609c1218a435ac52a6187a`. Commit and push provenance are separate: the researcher confirmed the push; the commit record alone does not establish when a remote synchronization occurred.

### Experiments and validation

The environment baseline returned **34 passed, one warning**; the warning concerned the old pytest cache. The expanded offline engineering suite returned **113 passed** without a reported warning. `pip check`, synthetic validation, parser smoke checks and missing-model preflight were exercised. Sixteen representative ignored paths matched the intended Git exclusions. The original execution-helper failure did not recur in the recovered environment.

Recorded command forms include:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m personaslm validate
.\.venv\Scripts\python.exe -m personaslm smoke
.\.venv\Scripts\python.exe -m personaslm preflight
```

These commands are evidence of distinct checks, not equivalent success criteria. Exact historical invocations and shell wrappers remain in the [environment transcript](validation/P0_environment_transcript.txt) and [command results](validation/P0_command_results.json).

### Errors and attempted solutions

The global interpreter aliases failed; the project interpreter succeeded. The old cache produced `[WinError 5]` on directory inspection, so the full isolation traversal reported PARTIAL. Initial PowerShell wrappers obscured the application's incomplete-result exit code; explicit propagation of `$LASTEXITCODE` established exit 2. Both failed and corrected command records remain available. Missing model and server configuration caused truthful preflight and execution failures with zero generations.

### Final results

The workspace supports development, tests and the controlled CPU inference pipeline. The current documentation check records HEAD `e1da38723b310ff6a12b04e1164ac20bb12feb1f` with a dirty working tree. It does not attribute those uncommitted changes to a clean commit or perform a Git mutation.

### Remaining limitations

The original unreadable-directory finding remains part of the audit history. A successful scoped project check is not proof that every filesystem location is readable or that a universal secret scan has been performed. See the [environment and adapter report](P0_real_inference_report.md) for original failures and the [repository instructions](../AGENTS.md) for the continuing governance rules.

## 2. Model and inference backend configuration

### Objective

Bind inference and tokenization to an explicitly supplied model and executable, verify their binary identities and observe CPU execution without treating filenames or configured arguments as sufficient evidence.

### Implementation

`configuration.py`, `provenance.py` and `server.py` implement explicit runtime paths, streamed SHA-256 verification, GGUF checks, backend version capture and ownership of a newly started local server. The manager refuses an occupied port, removes `LLAMA_ARG_*` environment overrides, starts a hidden Windows child, records its process and launch arguments, and cleans up only the process it owns. `/props` must agree with the configured model path, context and declared backend revision; postflight checks retain the identity evidence.

| Component | Pinned identity |
|---|---|
| Model artifact | `Qwen3.5-2B-Base.Q4_K_M.gguf` |
| GGUF file size | 1,270,808,256 bytes |
| GGUF SHA-256 | `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` |
| Declared original developer/model | Qwen / `Qwen/Qwen3.5-2B-Base` |
| Third-party publisher | `aashish1904/Qwen3.5-2B-Base-GGUF` |
| Fixed publisher revision | `765d2baaa04dbb8d6df3e78af571e6beaa4373d7` |
| Backend | llama.cpp `0.6.0-dev`, build 11573, commit `0f701c882` |
| Server executable SHA-256 | `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |

### Technical decisions

The deployment uses four inference threads, four batch threads, context capacity 4096 and one slot. Launch arguments include `--n-gpu-layers 0`, `--device none`, `--no-kv-offload`, `--no-op-offload`, `--no-context-shift` and `--offline`. Detailed logging supports verification beyond those arguments. HTTP worker threads are separate from the inference thread pool.

Default generation uses seed 42, maximum 96 new tokens, temperature 0, top-p 1, no text stop strings, `cache_prompt=false` and `ignore_eos=false`. The [example runtime configuration](../configs/p0_runtime.example.json) deliberately leaves required paths and the model digest unset; the ignored local configuration supplies the actual files. Base transcript prompts go directly to native `/completion`; the GGUF chat template is not applied implicitly.

### Experiments and validation

Loading logs report GGUF V3, architecture `qwen35`, Base metadata, Q4_K Medium, 320 tensors and approximately 1.88 B parameters. The tensor inventory contains 133 f32, 152 q4_K, 18 q5_K and 17 q6_K tensors; the quantization label is a mixed configuration. The tokenizer metadata identifies BPE with `gpt2` type and `qwen35` pretokenization, not a GPT-2 inference model. Training-context metadata of 262144 does not increase the configured deployment capacity.

Read-only hardware observations identify an AMD Ryzen 7 PRO 5850U with Radeon Graphics, eight physical cores, sixteen logical processors, 16 GiB installed RAM and Windows 10 Professionnel 10.0.19045, 64-bit. OS-visible physical memory was 12,698,714,112 bytes. Server logs report four inference and batch threads, context 4096 and **0/25 layers offloaded**, with CPU model, KV, recurrent-state and compute buffers.

The validation archive contains 96 successful memory observations from eight newly instrumented generation processes, available physical memory between 1,004,601,344 and 1,900,142,592 bytes, and a highest observed peak working set of 2,486,325,248 bytes. These observations are not backfilled into the less-instrumented original C0 run and are not a continuous resource benchmark.

### Errors and attempted solutions

Before independent files were provided, startup remained BLOCKED. Source verification also retained failed web access, a restricted direct request and a fixed-revision README HTTP 404. The successfully retrieved publisher API entry matched the file size and LFS digest; that success did not erase the README failure or change the enclosing failure record. No replacement model was downloaded to bypass a failed check.

### Final results

File integrity, GGUF metadata and published-artifact identification **PASS** their stated checks. Observed CPU inference agrees with the deployment configuration. The [model provenance report](P0_model_provenance_report.md) distinguishes those checks from upstream lineage; [real validation evidence](validation/P0_final_evidence.json) retains the underlying observations.

### Remaining limitations

Upstream quantization fidelity remains **PARTIAL**: the publisher's exact upstream revision, original-weight digests and complete conversion/quantization recipe were not independently reproduced. The executable's reproducible build and release signature were not certified. Path, file digest and owned-process observations do not independently hash every loaded tensor in memory. Claims remain about this exact third-party artifact and backend.

## 3. Dataset and prompt construction

### Objective

Provide controlled English synthetic inputs with identical trusted evidence and current questions across Track A comparisons, while keeping the long-term real-speaker objective distinct from a small engineering fixture set.

### Implementation

The historical fixture is [p0_cases.jsonl](../data/synthetic/p0_cases.jsonl), with SHA-256 `31b5242c2cc01411f524c2b922086de0ef216105920e723f1270560e0bc1f282`. It contains 20 invented current-city cases, temporally scoped facts, fixed recent context and pre-generation endpoint applicability. Schemas and prompt construction reside in [schemas.py](../src/personaslm/schemas.py), [fixtures.py](../src/personaslm/fixtures.py) and [conditioning.py](../src/personaslm/conditioning.py).

`transcript_base_v1` orders the instruction, trusted evidence, optional additional context, fixed recent conversation and current `User:` question followed by `Assistant:`. The factorial registry retains C0–C7 for S, F and H; P0 execution exercised C0, C1, N_style, C3 and N_history. Defining eight cells in source code is not executing the factorial pilot.

### Technical decisions

Evidence appears before the intervention in the same template location. Actual matched neutral overrides, rather than unused fixture defaults, define the historical experiments. In particular, matched N_style uses the `Speaker style profile:` wrapper; inspecting a fallback `Speaker context note:` value would misdescribe the executed prompt.

The [English scope addendum](research_protocol_v1.1_language_scope_addendum.md) establishes the primary language prospectively without translating or relabeling completed inputs. The [frozen protocol](research_protocol_v1.1.md) keeps Track A shared-evidence interference separate from Track B knowledge availability and keeps Persona Fidelity separate from Dialogue Reliability.

### Experiments and validation

Offline reconstruction recovered **100/100 historical prompts** for the twenty cases and five conditions, with identical trusted evidence, questions, prompt bytes and saved native token-ID arrays. Evidence-preservation checks reject missing or duplicated evidence. The [control reconstruction](validation/P0_control_reconstruction_v1.json) and [case audit](validation/P0_case_audit.json) identify the actual materials.

### Errors and attempted solutions

Inspection exposed limited stimulus variation: one Alice persona, one repeated target style, ten old/current-city combinations repeated twice, and two question forms. Ten questions say “the person” while historical dialogue names Alice, leaving referent binding implicit. These findings were documented rather than repaired inside the historical dataset. Separate development versions introduced named questions and new fictional speakers.

### Final results

Historical inputs are reconstructable and preserve the required Track A evidence. New development materials are separately versioned and use explicit speaker references. The engineering report does not treat those changes as retrospective corrections to original prompts.

### Remaining limitations

Twenty questions do not represent twenty independent people. Answering about Alice or another named speaker does not demonstrate responding as that real speaker. The synthetic city task does not establish general persona fidelity, broad conversational reliability or the full S/F/H design's identification. No private real-speaker data or confirmatory test set was introduced.

## 4. Tokenizer and neutral-control matching

### Objective

Match total final-prompt tokens using the loaded GGUF tokenizer, preserve exact attempts and failures, and prevent generation when the corresponding control fails the declared zero-tolerance rule.

### Implementation

The owned backend provides `POST /tokenize` with `add_special=true`, `parse_special=false` and explicit token IDs. Candidate-development requests also specify `with_pieces=false`. The adapter validates token types, binds `/tokenize` and `/completion` through the same server identity, and submits the returned ID arrays directly for generation. It checks input budget, evaluated token count and `truncated=false`.

`matching.py` searches bounded candidate inventories against complete C1 or C3 prompts. Token tolerance stays **0**. Evidence text, current question, wrapper and intervention position are checked separately; token equality does not imply semantic equivalence or equal attention allocation.

### Technical decisions

Counting characters or using a different tokenizer was rejected. All matching decisions depend on tokenizer results and a declared candidate order, never model-answer correctness. Failed alternatives remain in journals. Complete-prompt counting includes the actual wrapper and special-token behavior, so counts from different prompt versions are not interchangeable.

### Experiments and validation

| Historical matching method | N_style | N_history | Consequence |
|---|---|---|---|
| Cartesian enumeration | 0/20; best delta −3 at 256 attempts per case | 20/20 exact | No generation from failed style prompts |
| Interleaved sentence counts | 0/20; best delta −1 at the same bound | Successful matches retained | Failure preserved |
| Multiset enumeration | 20/20 exact, first exact match at attempt 169 | 20/20 exact | Forty validated pairs available |

The search repair reduced duplicate sentence permutations without increasing tolerance, candidate budget or the allowed sentence inventory. [Original matching evidence](validation/P0_control_matching.json) preserves each pair's hashes and counts.

Native probes returned `Hello` as `[9419]`; enabling special tokens did not insert a BOS. Literal `<|endoftext|>` produced ordinary pieces `[27,91,8426,703,419,91,29]` with `parse_special=false`, and token `[248044]` with it enabled. The tested C0 prompt retained 78 tokens across the four add/parse probe combinations. Production settings remained unchanged.

### Errors and attempted solutions

The original failures were candidate-coverage failures, not demonstrated tokenizer defects. Repeated short sentences eventually matched length but introduced semantic concerns addressed in stages 9–10. A separate candidate v1 also failed all three style matches because its sentence pool left length gaps; its best differences of +2, −3 and −3 remain recorded.

### Final results

The first closure cycle verified78 native tokenizations under the same GGUF tokenizer and final prompt wrapper. At that checkpoint five reference/candidate totals agreed; Tessa was99/100. Stage10 records the separately authorized99/99 correction. All72 alternatives and six references retain full ID arrays. The failed pool covers differences-2,+1,+2,+3,+4,-1,+1,+2,+4,+4,+5,+6; the earliest minimum-absolute-difference attempt is+1. The method records a candidate coverage failure without relaxing tolerance or alleging tokenizer malfunction.

The original forty pairs match exactly. All 100 main-run tokenizer arrays equal prepared and submitted IDs; evaluated counts agree and no input-context truncation was reported. The new candidate version adds 24 exact development pairs, described separately below.

### Remaining limitations

The backend does **not** return independently evaluated input-ID arrays. Count equality, submitted IDs and decoded prompt checks are supported evidence; elementwise verification of an unreturned internal array is unavailable. Output IDs are separate data and cannot substitute for missing input IDs. This qualified interface limitation is not a requirement to invent an unsupported endpoint.

## 5. Real-model inference validation

### Objective

Demonstrate the complete CPU request-to-record pipeline on real model outputs, identify every response independently and distinguish execution success from factual or methodological success.

### Implementation

`runner.py` combines preflight, managed server, frozen prompts, native tokenization, raw HTTP recording, parsing and evaluation. Each run has a unique immutable directory. Raw responses are retained before parsing or scoring. Request and response identifiers link case ID, condition, prompt hash, token arrays, generation parameters, termination information and errors.

### Technical decisions

The researcher's successful C0 run was audited in place without rerunning or overwriting it. Its 271 events and server log identified twenty distinct cases; a later inventory verified all 273 files including the manifest. New condition execution followed successful prompt validation. Historical score labels were preserved even when subsequent methodology audits identified limitations.

The actual researcher command was:

```powershell
.\.venv\Scripts\python.exe -m personaslm run-local --config configs/p0_runtime.local.json --condition C0
```

### Experiments and validation

| Main P0 condition | Independent responses | Nonempty raw / empty | Parser preserved / failure | Legacy correct / incorrect / unknown |
|---|---:|---:|---:|---:|
| C0 | 20 | 20 / 0 | 20 / 0 | 20 / 0 / 0 |
| C1 | 20 | 20 / 0 | 20 / 0 | 20 / 0 / 0 |
| N_style | 20 | 20 / 0 | 20 / 0 | 20 / 0 / 0 |
| C3 | 20 | 20 / 0 | 20 / 0 | 6 / 14 / 0 |
| N_history | 20 | 20 / 0 | 20 / 0 | 20 / 0 / 0 |

These are legacy rule outputs, not human-confirmed factual counts or a comparative reliability result. All 100 requests returned 96 output tokens, native `limit` termination and matching output-ID counts. There were no completion HTTP failures, evaluated-count mismatches or input truncations in this inventory.

The engineering inventory subsequently added 18 budget-diagnostic responses, 16 boundary-development responses and six policy-validation responses: **100 + 18 + 16 + 6 = 140**, across **17 generation runs**. Tokenizer-only control development added no generations. [Per-case evidence](validation/P0_case_audit.json), [budget evidence](validation/P0_budget_diagnostic.json), [boundary evidence](validation/P0_response_termination_evidence.json) and [real policy holdout](validation/P0_response_policy_real_holdout_v1.json) preserve those separate populations.

### Errors and attempted solutions

Reaching the numerical cap in every main response prompted a controlled budget diagnostic. The first three synthetic IDs under C0/C3 were selected by a fixed rule, with budgets 96, 192 and 256 and all other settings held constant. All 18 responses reached their assigned limit, with **zero EOS/EOG** and nonempty preserved raw output. The six prompt/condition pairs kept the same hashes and input IDs across budgets; each shorter output was an exact prefix of its longer counterparts in this observation.

Increasing the budget prolonged transcript continuation rather than establishing termination. This negative result was retained; no higher-cap result was reclassified as a complete dialogue turn merely because it contained a useful first sentence.

### Final results

Real CPU adapter execution and raw-record linkage **PASS**. The saved outputs show the model can continue invented dialogue after a plausible initial answer. The pipeline captures that behavior without reporting it as a crash or hiding later text.

### Remaining limitations

The observations do not identify a Persona effect, a Base-versus-Instruct effect or general factual accuracy. Request costs and resource observations remain in the original records, but were not collected as a controlled performance comparison. The original C0 manifest lacks some provenance and memory fields added to later runs; those fields were not fabricated retrospectively.

## 6. Response boundary and parsing

### Objective

Define a reproducible response unit under finite token budgets, preserve valid multiline content and extra generated turns, and distinguish backend termination from semantic completeness.

### Implementation

The historical parser records transformations, raw and parsed hashes, and classifications such as `direct_eos`, `stop_without_visible_text`, `newline_truncation`, `parsing_or_filter_removed` and `preserved`. The main real inventory observed 100 preserved responses and none of the four other mechanisms. Synthetic tests exercise mechanisms that were not observed in those outputs.

The separate frozen [response policy](P0_response_status_policy_v1.md), `response_status_v1`, records exact first-reply offsets, optional leading prefix, excluded tail, backend stop data and uncertainty reasons. Concatenating the stored spans reconstructs the original raw text. Line-start role recognition handles capitalization and horizontal whitespace; ordinary newlines remain part of valid responses.

### Technical decisions

| Research status | Operational interpretation |
|---|---|
| COMPLETE | Identifiable nonempty reply, supported boundary and separately supplied completeness judgment bound to the raw hash |
| TRUNCATED | Maximum-token termination without an earlier certified boundary; factual wrongness is not implied |
| CROSS_TURN | Visible continuation into another recognized turn or past the declared marker; the first reply may still be assessable |
| AMBIGUOUS | Conflicting evidence, delimiter hazards, empty unit or insufficient boundary/completeness support |

A text stop is an inference intervention, not proof of natural EOS or semantic completeness. Literal, quoted, fenced, inline and unknown-role hazards route conservatively to ambiguity. No completeness judgment is invented for real outputs. A separate review contract verifies the supplied judgment's structure and hash binding, not the reviewer's independence.

### Experiments and validation

Four independent boundary-development tasks compared the original transcript with and without role stops, and an explicit end-marker format with and without its stop. Sixteen requests used unchanged token budget and decoding settings. Role stops were `\nUser:` and `\nAssistant:`; the explicit marker stop was `\n<END_OF_REPLY>`.

Original transcript outputs all reached 96 tokens; role-stopped outputs generated 9, 23, 9 and 11 tokens with native `word` stops. Both explicit-marker variants reached 96 tokens in every case. None reported EOS/EOG. Supplemental inspection accepted two of four original/role-stop cases structurally and none of the explicit-marker cases. All variants and original classifications remain preserved in the [boundary diagnostic](P0_response_termination_diagnostics.md).

The final policy used sixteen additional software development examples, then a frozen implementation and a separate sealed holdout. The software holdout produced **24/24 status matches and 24/24 span matches**; six were AMBIGUOUS, giving **75% decided coverage**. These are authored software-contract expectations, not human semantic accuracy. The six real holdout responses yielded **five CROSS_TURN and one AMBIGUOUS**, all with a separately recorded 96-token cap and zero EOS/EOG. Independent real-output classification accuracy is unavailable.

### Errors and attempted solutions

The initial case-sensitive rule missed uppercase `USER:`. Literal role text conflicted with delimiter assumptions, and a first-newline shortcut would have removed valid bullet content. The explicit end marker was not generated within the tested budget. These failures motivated a new measurement-policy version rather than repeated prompt optimization on the same four examples.

An enclosing diagnostic command also exited 1 after successful generation because its auditor incorrectly required HTTP 200 from startup health checks. Fourteen loading responses with HTTP 503 were retained. The auditor was corrected to distinguish health from inference requests, regression-tested and rerun offline twice without regenerating outputs.

### Final results

The frozen boundary instrument passes its scoped software checks, preserves raw text and exposes uncertainty. It establishes a usable measurement contract; it does **not** establish that every real response terminates naturally or is semantically complete. Freeze, holdout and results remain separate [policy evidence](validation/P0_response_policy_freeze_v1.json), [seal](validation/P0_response_holdout_seal_v1.json) and [software results](validation/P0_response_status_holdout_v1.json).

### Remaining limitations

Unknown speaker conventions and open-ended quoted content remain outside automatic certification. Future rule changes require a new version and independent holdout. Independent completeness labels are still needed where semantic completion is a scientific endpoint; neither stop strings nor software accuracy can replace them.

## 7. Evaluation methodology

### Objective

Avoid conflating unsupported assertions, false assertions, temporal interpretation, response boundaries and relevance. Preserve historical labels while defining an explicit policy for subsequent scientific use.

### Implementation

The legacy evaluator and its results remain intact. Additive residence audits introduced v2 and `english_residence_claim_audit_v3`. The frozen [evaluation policy](P0_evaluation_policy_v1.md), `separate_axes_policy_v1`, applies the bounded factual rule to the identifiable first reply or observed prefix and stores excluded continuation separately.

The output axes are factual support, response completeness, relevance, temporal consistency and conversational coherence. Relevance and coherence retain their existing 1–5 annotation scales; pending annotations remain null. Temporal consistency has its own judgment and reason. Persona Fidelity is not folded into any reliability score.

### Technical decisions

Factual outcomes are **Correct**, **Incorrect**, **Unverifiable** and **Not Applicable**. A supported recognized residence claim can be Correct within the synthetic unique-city schema. A verified contradiction is Incorrect. Unsupported grammar, unidentified subjects, missing evidence, unfinished claims or unsupported additional facts remain Unverifiable. Not Applicable requires predeclared endpoint inapplicability.

The accounting population retains all pre-eligible cases. Uncertainty, truncation and ambiguity are not silently excluded or converted into success/failure. A verified contradiction retains priority while other uncertain claims and reasons remain visible. The ordinary legacy runner is not silently switched to a new evaluator; versioned sidecars identify the new scoring unit and policy explicitly.

### Experiments and validation

Auditing the fourteen C3 outputs originally labeled incorrect produced **two bounded contradictions, eleven Unverifiable outputs and one supported output** at whole-output scope. This did not overwrite the fourteen historical labels. Some initial replies were supported while later generated turns introduced unsupported statements. Recognizing a past city is not itself a contradiction with a current city.

A separate Morgan residence fixture tested affirmation, negation, contradictions, past validity, conflicting assertions, unidentified subjects and unverifiable material. Twenty-two text examples plus inapplicability and conflicting-source checks gave **24 passing contract checks**. Six examples exposed v2 limitations, including negation, wrong subject, proximity rather than residence and unfinished temporal clauses. See [v3 validity evidence](validation/P0_evaluation_validity_v3.json).

The six real policy-holdout replies yielded **one Correct, zero Incorrect, five Unverifiable and zero Not Applicable**. All six remain in eligible accounting. Unsupported wording explains abstention; this distribution is not a model accuracy estimate.

### Errors and attempted solutions

Legacy city substring matching could treat an appropriately historical city mention as a current contradiction and did not safely distinguish all negations or extra claims. The repair added conservative subject/predicate/temporal checks in a new version with independent regression cases. No old output was rewritten and no uncertain answer was promoted merely to improve a score.

### Final results

Measurement axes, response unit, evaluator version and category handling are explicit and pass scoped implementation tests. Historical scores remain inspectable through the [v2 audit](P0_evaluation_audit_v2.md), [v3 validity report](P0_evaluation_validity_v3.md) and [policy acceptance report](P0_policy_acceptance_report.md).

### Remaining limitations

The rule is restricted to canonical English synthetic residence claims. It does not validate open-domain facts, arbitrary aliases, complex temporal reference, coherence or real-speaker fidelity. Open-ended research still requires the protocol's independent annotation and adjudication procedures. Instrument validation does not require every model output to be correct, but future experiments must invoke and log the declared evaluation policy.

## 8. Reproducibility and logging

### Objective

Allow reconstruction of exact saved inputs, transformations and evaluation without rerunning successful inference, while retaining actual failures and distinguishing reproducible specifications from deterministic model outputs.

### Implementation

The narrow closure freezes source/tool/configuration hashes, Git commit and dirty status before native tokenization. It retains a new294-event journal and reconciles78 raw HTTP request/response bodies offline with published IDs. Generation parameters are explicitly null. Engineering captures and the model-backed journal are separate. The [closure delivery record](validation/P0_control_closure_delivery_v1.json) verifies the original23 journal inventories and adds the new tokenizer-only record.

Each run retains a manifest, ordered event JSON and a server log when a process started. HTTP bytes are saved as base64 before decoding; raw generations precede parser and evaluator operations. Atomic publication and fsync protect completed events, and a manifest-bound hash chain detects inconsistent edits. Source/dataset snapshots, effective configuration, prompt text and hashes, input/output IDs when available, seeds, backend settings and errors accompany the record.

Engineering command captures are separate from experiment journals. New runs record read-only Git HEAD and dirty status along with exact source bytes; a commit alone cannot reconstruct uncommitted code. Public derived evidence references the local original archive rather than claiming the repository contains every raw file.

### Technical decisions

Audit and replay are offline operations. `audit-run` validates saved evidence; `replay-run` reconstructs prompts and parser/evaluator results into a new output. Replay does not request another model response. Existing paths refuse overwrite. No automatic generation retries, multiwriter recovery or silent continuation of an interrupted run are assumed.

These are parameterized reproduction examples, not claims that the placeholder commands were executed literally:

```powershell
.\.venv\Scripts\python.exe -m personaslm audit-run --run-dir results/p0/YOUR_RUN_ID
.\.venv\Scripts\python.exe -m personaslm replay-run --run-dir results/p0/YOUR_RUN_ID --output results/NEW_UNIQUE_REPLAY.json
```

Actual expanded arguments and their outcomes remain in the linked [final validation command index](validation/P0_final_commands.json), [methodology command index](validation/P0_methodology_commands.json) and [control-development command index](validation/P0_control_development_commands_v2.json).

### Experiments and validation

The initial real-validation inventory reconstructed nine generation runs consistently in two offline passes. The budget extension reconstructed fifteen; the boundary and policy additions brought the preserved generation inventory to seventeen. Further tokenizer-only development brought the full journal inventory to **23**. The final control review reconciled **444 native tokenizer request/response pairs**, comprising 420 candidate prompts and 24 references, against original bodies and IDs.

The final-control delivery verified **163 protected existing files** and **23 unchanged historical journal inventories**. Those are preserved results of that audit, not a claim that this documentation task re-executed every historical chain. The present task separately hashes the existing repository-visible materials to detect unintended changes.

Relevant Git provenance includes budget-manifest HEAD `8ffe1fdeb64ccc85182d2ff983b514940ecb6f70`, policy-manifest HEAD `1c9bfc3791f7f5cb4b4bda78cd02e2580f0429da` and candidate-v2 run HEAD `4d00ee1adbe538d24175d5c3e83c318bff8365a3`. Dirty state and source snapshots accompany those runs. A concurrent external Git update exposed HEAD `e1da38723b310ff6a12b04e1164ac20bb12feb1f`; the experimental manifests retained their actual earlier identities.

### Errors and attempted solutions

The final scientific delivery scanner encountered a separate escaped-JSON false positive in a frozen source dictionary expression. Historical-file and native-token checks had already completed. Decoding JSON values before checking drive prefixes resolves the scanner error. The original failed capture and checker version remain preserved; completed checks are explicitly reused in corrected delivery. No frozen input is rewritten.

The narrow closure delivery checker initially misidentified escaped newlines after uppercase prompt headings as absolute drive paths. All prior historical-file and chain checks had completed; the later heuristic failed. The initial script and failure are preserved. Requiring a standalone drive prefix fixes the false positive; corrected delivery rehashes old files and explicitly reuses the completed chain checks. No prompt, source policy or experimental record is changed by this checking correction.

Startup HTTP 503 responses were separated from failed inference rather than deleted. A reporting check also falsely matched its own private-path diagnostic string and retained historical document paths. Its correction restricted scanning to new content and independently checked preservation of historical bodies; the failed capture remained. Test-fixture path isolation and schema serialization fixes are documented in stage 10.

Attribution wording was made vendor-neutral without claiming that implementation was exclusively manual. The [attribution audit](validation/P0_vendor_neutral_attribution_audit.json) records the limited changes and archived originals; measurements and frozen objectives were not rewritten.

### Final results

New records identify HEAD `e1da38723b310ff6a12b04e1164ac20bb12feb1f`, dirty true, dataset SHA-256 `2469c88daeddd5f91882ccdd670a18ed0a7c7b2e55926feba9f4b7bd8dfe1453` and freeze SHA-256 `33faca83ef75dbc164c76d8730b9d546f764cebbd1f85dbed3e3d39cf696bd90`. The original data, reviews, journals and frozen policies remain unchanged; original narrative bytes are archived separately before updating this maintained report.

Saved experimental inputs and scoped parser/evaluation results are reconstructable. Current journal and offline token reconciliation checks pass their stated contracts. The [reproducibility report](P0_reproducibility_report.md) and [final-control delivery evidence](validation/P0_final_control_delivery_v3.json) link source snapshots, inventories, commands and preserved errors.

### Remaining limitations

A hash chain is not signed, tamper-proof storage and cannot preserve a response that was never completely written. Original C0 lacks some contemporaneous fields; later observations do not fill that gap. A fixed seed does not guarantee cross-platform output identity. Full independent dissemination requires the retained raw archive as well as public derived files. This report consolidates records; it does not certify missing evidence or independently repeat all historical audits.

## 9. Human annotation and semantic validation

### Objective

Evaluate whether exact-length controls are suitable experimental interventions, distinguish human judgments from automated preliminary analysis, and keep review completion separate from semantic acceptance.

### Implementation

The researcher supplied two renamed CSVs, containing six style records and eighteen history-source records. Every source field is retained; the blank human-entry cells are not backfilled. Explicit conversation confirmation and subsequent agreement supply researcher authority in a separate attestation, with reviewer_id Yaxin_ZHENG, review_type researcher_verified_human_review and decision_source/final_decision_authority researcher.

The [History A evidence table](P0_history_a_evidence_verification.md) extracts18 associations from the unchanged master. Both arms carry verbatim excerpts, source hashes and character offsets. Topic differences, date-versus-past-fact differences and question-answer adjacency remain visible. These are proposed associations, not invented supporting human quotes or new judgments.

Yaxin ZHENG's supplied final file was registered as `researcher_verified_annotation_v1`, registration revision 2, reviewer `Yaxin_ZHENG`, review type `researcher_human_review`. Forty unique records contain 240 completed core judgments. The [registration](validation/P0_researcher_verified_annotation_v1_revision2.json) retains source text, provenance, counts and the available version comparison.

The final researcher CSV has SHA-256 `06629e8bc69684b3a276ec00a71558291c5762c64acc23dac619cc86d88bfb42`. The separately preserved preceding received source has SHA-256 `f09a128f212a1405b9276ccc27ffd871c2365df5798d6e8feec6194dbca1733e`. The latter was already described as researcher-corrected and is not relabeled as an untouched automated assessment.

### Technical decisions

Preliminary AI-prefixed judgments and interpretations remain visible. A request for blind-review wording does not establish a blinded procedure; the registered provenance stays assisted and non-blind. This is not a new P0 gate. Unavailable human review times remain null; registration times are separate. No second reviewer or agreement statistic is invented.

Final review is **AI-assisted human review, not blind review**. The researcher reported an initial independent pass followed by consultation and revision, but an independently saved first-pass artifact is unavailable. No second reviewer, agreement statistic or missing review timestamp is invented. Actual registration metadata remains in the original record.

Review labels only apply to the exact materials reviewed. Revised controls require new token evidence and new human judgments. Automated dimension routing is reported separately from the researcher's overall suitability decisions.

### Experiments and validation

| Original review measure | Recorded result |
|---|---|
| Completed human-reviewed controls | 40/40 |
| Researcher overall suitability | PASS 0 / PARTIAL 40 / FAILED 0 |
| Answer leakage, added personal facts, contradictions, temporal interference | No for each of the forty records |
| Unintended style | Yes for twenty N_style; uncertain for twenty N_history |
| Semantic neutrality | Uncertain for all forty |
| Auxiliary speaker-reference ambiguity | Yes for ten history records; no for thirty others |
| Separate deterministic dimension routing | PASS 0 / PARTIAL 20 / FAILED 20 |

The two available submitted versions have **zero changes across the six core and two auxiliary judgment fields**, with metadata/provenance changes across forty rows. This is a comparison of those two files only. The number of earlier researcher corrections is unknown because the untouched preliminary source and intermediate versions are not all available.

### Errors and attempted solutions

The original N_style controls repeat document-format descriptions under a style-profile heading, introducing style cues despite exact length. N_history uses unrelated document dialogue in place of residence history. Some speaker references are implicit. These substantive findings were not resolved by completing the form. Import and provenance handling preserved missing metadata explicitly instead of backfilling review information.

### Final results

Five unchanged absence-of-style candidates are ACCEPT_NARROW; the prior Tessa candidate remains REVISION_REQUIRED. Ninety source style-axis judgments remain unchanged, including semantic-neutrality uncertainty. History A has six narrow approvals, eighteen confirmed quotation associations and six explicitly supplied comparison_suitability PASS labels within scope. Its topic/temporal FAIL and coherence UNCERTAIN labels remain intact. The latest exact Tessa replacement now has a separate explicit ACCEPT_NARROW decision from the researcher, bound to its full prompt hash. The old revision decision is not changed.

The [integrity audit](P0_annotation_integrity_audit.md) reproduces18 empty suitability labels,6 incompatible style coherence N/A values and81 missing required quotes. Of the quotes,18 relate to adopted A and63 to superseded or excluded alternatives;279 other empty quote fields are optional. Six historical A PASS values were identified as conversion-derived and required categorical confirmation; the current researcher instruction now explicitly supplies PASS within the narrow scope. The [short form](validation/P0_closure_correction_form_v1.csv) asks only for those six fields;18 evidence confirmations are in their own table. At the first closure checkpoint, style review was0/6, A evidence confirmation0/18 and categorical clarification0/6. Current registration resolves those historical questions; the subsequent Tessa sentence is separately approved in the [final approval](validation/P0_tessa_researcher_approval_v1.json).

Original human-review completeness **PASS**; original semantic-control validity **PARTIAL**. The [researcher annotation report](P0_researcher_annotation_report.md) and [neutral-control diagnostic](P0_neutral_control_diagnostic.md) retain judgments, source limitations and comparison interpretations.

### Remaining limitations

Single-researcher assisted review is not independent multi-annotator consensus. The annotations identify methodological issues; they do not establish all controls as valid. The new candidates now have24 researcher-confirmed decisions, with detailed schema gaps preserved as described in stage10. The original forty reviews were not transferred to the new wording.

## 10. Neutral-control improvements

### Objective

Develop more coherent, explicitly scoped control alternatives without altering the original forty controls, choosing by model-answer quality or treating one control as capable of isolating every historical-information mechanism.

### Implementation

The final authorized repair changes only Tessa: is provided becomes appears in the absence-of-style-information sentence. A single candidate and single original reference were frozen before tokenizer access under tessa_minimal_repair_v1. The other five strings, historical candidate versions, original reference, trusted evidence, question, persona identity, active style and transcript_base_v1 wrapper remain unchanged.

Version `neutral_style_closure_v1_dev` revises only the six rejected-for-revision style additions. Twelve unique, declarative absence-of-profile-information alternatives were frozen per case. The original six development cases and `transcript_base_v1` wrapper remain fixed. No generic history, B/C, trusted evidence, question or historical reference is revised.

Candidate v1 used three separate development scenarios, 36 style and eight history candidates per case. Its tokenizer-only run included 100 historical rechecks, 132 candidate prompts and six references: **238 tokenizations, zero completions**. History matched 3/3; style matched 0/3. V1's `control_candidate_prompt_v1_dev` used a different heading, which is retained as an explicit version difference.

Candidate `neutral_control_candidate_v2_dev` restores the original `transcript_base_v1` wrapper and covers six invented speakers: Riley, Samara, Devon, Tessa, Blair and Robin. The first three reuse v1 scenarios for declared development repair; the others expand development coverage. None is a held-out scientific test case. The fixed pool contains 32 natural single-sentence style candidates, sixteen history-format exchanges, twelve topic-clarification replies and ten generalized-residence replies per case.

### Technical decisions

The predeclared ceiling is72 candidate requests plus six references. Every alternative is evaluated once; earliest exact match wins. Without an exact match, earliest minimum absolute difference is reported FAILED and no automatic expansion occurs. The retained local max_match_candidates256 does not govern this separate fixed pool. Candidate selection never invokes answer generation or uses answer quality. Style vocabulary, declarative register and the retained profile heading remain explicit semantic risks.

The entire pool was frozen before tokenization. Selection is the first exact match in fixed order; unsuccessful alternatives remain recorded. There was no adaptive expansion after observing counts, no generation for these candidates and no outcome-based control choice. All 420 candidate prompts preserve trusted evidence, current question and outer wrapper.

| Family | Intended replacement contrast | Material limitation |
|---|---|---|
| N_style / `style_generic` | Specific style profile versus generic discourse under the same heading and total length | Generic concise/formal prose and the heading may themselves cue style |
| History A / `history_format` | Residence dialogue versus unrelated but format- and length-matched dialogue | Topic, factual content and internal past reference change together; historical format is held fixed, not isolated as an effect |
| History B / `history_topic` | Past-residence answer versus clarification of the same residence question | Speech act, uncertainty and answer-avoidance cues change; half add an address-versus-city distinction |
| History C / `history_stale_generalized` | Named old city versus unspecified past-city residence | Diagnostic specificity ablation, not a neutral placebo; vague personal history remains |

C removes York, Bath, Exeter, Hull, Carlisle and Gloucester from the respective replies while retaining the city category and past-residence relation. Half also replace `at the time` with `back then`. A pure temporal-validity effect is therefore not identified. Explicit speaker names fix the earlier referent ambiguity only within the new inputs.

### Experiments and validation

Actual final counts are99/99, difference0, from two native tokenizer requests and zero answer requests. Model/backend hashes match the stage2 pinned artifacts before and after execution. The new prompt SHA-256 is `93908ec82736f26131119c8d04ce518a0fe7f74f867c9c438e6fe043c9ed553c`. The new journal has83 events. All selected style6/6 and History A6/6 counts now match exactly; prior failures are not deleted. The single candidate was not selected by answer quality.

Actual command forms, captured separately:

```powershell
.\.venv\Scripts\python.exe tools/p0_scientific_closure.py register
.\.venv\Scripts\python.exe tools/p0_scientific_closure.py freeze
.\.venv\Scripts\python.exe tools/p0_scientific_closure.py tokenize
.\.venv\Scripts\python.exe -m pytest -q tests/test_scientific_closure.py
.\.venv\Scripts\python.exe -m pytest -q
```

Targeted tests17 passed; full suite365 passed. The original strict65-column forms are unchanged; explicit researcher attestations remain separate rather than fabricating missing CSV cells.

The closure reference/revised totals are Riley101/101, Samara101/101, Devon99/99, Tessa99/100, Blair99/99 and Robin100/100. Model and executable hashes match the identities in stage2 before and after execution. Native requests use add_special=true, parse_special=false and with_pieces=false. The raw server log independently reports four inference/batch threads, context4096 and0/25 offloaded layers. This validates tokenizer execution, not new generation behavior. Twenty-four startup health responses returned503 while loading, followed by one healthy response; all78 tokenizer responses returned200. These transient startup responses remain in the raw record.

Actual command forms for this cycle, with complete captures linked in [command evidence](validation/P0_control_closure_commands_v1.json):

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_control_closure.py
.\.venv\Scripts\python.exe tools/p0_control_closure.py freeze
.\.venv\Scripts\python.exe tools/p0_control_closure.py tokenize
.\.venv\Scripts\python.exe tools/p0_control_closure.py export
.\.venv\Scripts\python.exe -m pytest -q
```

| Development case | Style reference/candidate | History A | History B | History C |
|---|---:|---:|---:|---:|
| control_v2_dev_001 | 101/101 | 118/118 | 118/118 | 118/118 |
| control_v2_dev_002 | 101/101 | 120/120 | 120/120 | 120/120 |
| control_v2_dev_003 | 99/99 | 119/119 | 119/119 | 119/119 |
| control_v2_dev_004 | 99/99 | 120/120 | 120/120 | 120/120 |
| control_v2_dev_005 | 99/99 | 119/119 | 119/119 | 119/119 |
| control_v2_dev_006 | 100/100 | 118/118 | 118/118 | 118/118 |

Each family achieves **6/6 exact matches**, totaling **24/24** with tolerance zero. The v2 run contains **444 tokenizations, 1384 chained events and zero completion requests**. Twenty startup health HTTP 503 responses are retained separately from successful tokenizer responses. The subsequent offline reconciliation verifies every saved request/response pair; it does not claim a fresh model execution.

The final [English review CSV](validation/P0_final_control_review_v3.csv) contains **24 items and 65 columns**, with active and candidate interventions, trusted evidence, question, reference metadata, expected answer, full prompt hashes, exact counts, fifteen judgments and quotation/notes fields. Human fields remain blank. The [guide](P0_final_control_review_v3_guide.md) explains review and import. `control_final_review_v3` is a form version, not a new prompt version; the earlier masters are unchanged.

The form SHA-256 is `1db60baea0e1c0f352da592141c73081586a3f12b774d620af4e0cb3581b3b7c`. Packet ID is `d7cf1b903fe6dad382bc905f68b5e95ce9ba8bfaf3661a5dfa5a09fd76328eb6`. These identify the unfilled master; a completed submission must be saved separately.

The separately supplied researcher decision file has SHA-256 `fbfa50099e8d5c55083a531d23d7bb1db1a41b42739f9ad0fa3e58ccccd637d0`. All 24 IDs and overlapping materials match that master. The researcher explicitly confirmed positive-question mapping: yes to PASS, no to FAIL, uncertain to UNCERTAIN, and not_applicable to NOT_APPLICABLE. All 336 supplied checks and 24 global quotes are retained. The [converted65-column file](validation/P0_final_control_researcher_registration_v1/annotation_65_columns.csv), SHA-256 `550e9e140995ac10dc6578c65e0a17ec63fc3b3da1a5b7a7db20cf213f10c651`, leaves missing review times and per-axis quotations blank. Final review is AI-assisted and not blind; no second reviewer or agreement is inferred.

The historical converter assigned six comparison_suitability PASS cells from ACCEPT_NARROW. The closure audit identifies these as derived values, not directly supplied categorical judgments: narrow acceptance does not uniquely imply that separate label. The conversion was preserved and six explicit categorical confirmations were requested. Those confirmations are now supplied separately by the researcher; the original derived cells still do not become historical direct human scores. The other 18 scope-specific decisions have no unique categorical translation and remain separately registered with blank suitability fields. Six style coherence N/A values violate the unchanged official whitelist and remain visible. Eighty-one FAIL/UNCERTAIN fields lack required per-axis quote attribution; global quotes are not silently assigned. The [registration](validation/P0_final_control_researcher_registration_v1/registration.json) therefore passes 24-decision registration while declaring detailed-schema conformance PARTIAL. Original CSV bytes, masters and all older annotations are preserved.

### Errors and attempted solutions

The first closure fixed pool failed Tessa by one token. That failure was retained without within-cycle expansion, relaxed tolerance or case deletion. Fourteen added tests passed and that checkpoint passed348. The current single-candidate repair is separately researcher-authorized and versioned. Actual blank style and History A imports return exit1 with Incomplete human review:0/6 and Actual researcher confirmation and identifier required, respectively. These expected negative tests create no reviewed artifact.

V1's style pool left gaps in reachable full-prompt lengths. V2 broadened single-sentence constructions and restored the wrapper; it did not relax zero tolerance. One initial test failed because a test fixture modeled files outside the repository; the fixture root was corrected without weakening production path restrictions. Another targeted run produced **six failures and sixteen passes** because newly serialized facts remained tuples where the schema requires lists. Correcting the new serializer produced **22 passing targeted tests**, with the old schema intact.

The completed v2 suite passed **285 tests**; final-review importer additions brought it to **307**. Researcher-decision conversion adds 27 regression tests; that checkpoint passed334; the closure additions bring the full suite to348. An initial 26-pass/1-fail targeted result exposed an incorrect test assumption that sorted JSON key order equals CSV presentation order. The correction checks key identity, while the integration test still verifies exact 65-column CSV order. The unchanged strict importer correctly rejects the converted incomplete form with exit1 and no completed-review output. Both failures and corrected results are preserved. Import validation rejects missing/invalid labels, changed materials, duplicate records, version/hash mismatches and absent reviewer metadata. FAIL/UNCERTAIN requires evidence quotations. A deliberate attempt to import the blank master returned exit 1 with `Incomplete human review: 0/24` and created no result. This was a successful negative test, not a failed human submission or fabricated review.

### Final results

The preserved [six-item closure review master](validation/P0_style_closure_review_v1.csv) has65 columns and entirely blank human fields. It includes the historical failed best-observed Tessa row, ineligible for exact-match adoption; current decisions and the new exact repair are registered separately. The [closure report](P0_final_control_closure_report.md) preserves every candidate count and all semantic caveats. At that checkpoint tokenizer execution passed, complete-set matching was PARTIAL and review OPEN. Current exact matching is6/6; the new Tessa approval is now explicitly supplied and registered separately.

At the v2 checkpoint, engineering construction, actual-token matching and review-package preparation were **PASS**; the historical closure5/6 and current final6/6 results are assessed separately above. The initially blank package has now received **24/24 researcher-confirmed decisions** through a separately preserved34-column submission. Its 65-column conversion retains every supplied axis judgment; full detailed-schema completion remains PARTIAL. The [development report](P0_control_development_report_v2.md), [identification matrix](P0_control_identification_matrix_v3.md), [per-candidate evidence](validation/P0_final_control_analysis_v3.json) and [final control report](P0_final_neutral_control_validation_report.md) specify constants, manipulations, risks and admissible interpretations.

### Remaining limitations

The corrected Tessa sentence retains the profile heading, style vocabulary and an absence declaration. These limit its interpretation to the same explicit-absence comparison already approved for the other five. Exact matching does not itself supply semantic approval. The researcher subsequently approved the exact one-item wording and hashes, only as an explicit absence control. The blank request master remains unchanged. No additional pool or answer experiment was run.

The first closure cycle ended without new human decisions and stopped at its declared bound. Subsequent explicit researcher approval accepts five unchanged absence statements narrowly; one specifically authorized Tessa correction has exact matching and its own subsequently supplied narrow approval. None establishes behavioral equivalence with C0.

History A now has explicit human acceptance for its narrow unrelated-topic comparison only. N_style initially required revision; all six selected replacements are now approved narrowly, including the separately confirmed exact Tessa wording. B remains rejected as neutral and C diagnostic only. No model-level reliability effect has been demonstrated. A/B/C serve separate roles; pure format, topic, factual specificity and temporal-conflict mechanisms remain incompletely separated. The existing [novelty matrix](related_work_novelty_matrix.md) records direct overlap with prior persona/context research. Better controls are an engineering improvement, not evidence of unprecedented methodology. [Falsifiable hypotheses](P0_control_hypotheses_v3.md) and the [P1 proposal](P1_experimental_design_proposal.md) remain proposals, with no executed P1 or confirmatory dataset.

## 11. Remaining limitations and P0 acceptance

### Objective

Apply the unchanged protocol's engineering and methodological requirements without demanding perfect model performance, weakening thresholds or treating software success as complete research sign-off.

### Implementation

Acceptance separates working instrumentation, actual-token matching, response/evaluation policy, review completeness, semantic validity and reproducibility. The current [control acceptance report](P0_control_acceptance_report.md), [checklist](P0_acceptance_checklist.md) and [blocker record](P0_remaining_blockers.md) remain linked to original evidence. This consolidated report supplies a stage-organized interpretation without rewriting their historical status entries.

### Technical decisions

Protocol v1.1 defines P0 pipeline/parser/measurement checks rather than a completed mechanism-identification study. C1-C0 and C3-C0 are effects of operationalized prompt packages; their length and content change together. C1-N_style controls total length/wrapper while contrasting profile information with declared absence. C3-N_history controls length/format while bundling residence-topic, factual-content and temporal-semantic differences. No isolated temporal-conflict or pure-format effect is claimed. Narrowly defensible pilot comparisons are distinguished from future factorial main effects and decomposition work.

At the24-decision registration checkpoint, the unresolved gate concerned the exact interventions proposed for adoption. The researcher supplied: N_style REVISION_REQUIRED, History A ACCEPT_NARROW, History B REJECT_AS_NEUTRAL and History C DIAGNOSTIC_ONLY, each for six cases. The minimum work then was style revision/matching/review plus18 History A evidence associations and six categorical confirmations. The first bounded repair matched five of six and retained its failure. The current researcher-confirmed registration and single Tessa repair resolve those tasks; the subsequent explicit Tessa approval closes the final selected-control gate. B/C redesign and exhaustive correction of superseded materials are not additional P0 gates. A completed decision file does not erase substantive or documentation findings.

Natural EOS absence, conservative ambiguity, bounded city-rule coverage, unsupported evaluated-input arrays and unverified upstream quantization fidelity are documented scope limitations. They do not independently require impossible backend interfaces or universally correct model responses. Future open-ended evaluation still needs the human procedures already required by the protocol. Narrowing official estimands or changing the protocol requires explicit researcher approval.

### Experiments and validation

The final acceptance verification used the project environment; the preceding decision-registration command remains in its original structured capture:

```powershell
.\.venv\Scripts\python.exe tools/p0_capture.py --output results/p0_acceptance/closure_v1/engineering/full_tests.json -- .\.venv\Scripts\python.exe -m pytest -q
```

Current result: **365 passed, zero failed, zero warnings reported, exit0**; the earlier334-test checkpoint is preserved. An additive decision-registration/conversion module and 27 regression tests were added; historical inference, candidate versions, frozen evaluations and the strict v3 importer remain unchanged. The separate closure module adds fourteen tests and one frozen twelve-alternative style pool. The [current acceptance delivery](validation/P0_acceptance_delivery_v1.json) identifies this report version and365-test closure; the [preceding scientific delivery](validation/P0_final_scientific_delivery_v1.json) remains bound to its separately archived PARTIAL report; the [earlier closure delivery](validation/P0_control_closure_delivery_v1.json) remains bound to its separately archived narrative. The [earlier decision delivery](validation/P0_control_decision_delivery_v1.json) identifies its separately archived narrative version and command references. The [earlier documentation validation](validation/P0_engineering_report_validation_v1.json) remains valid evidence for its separately archived report version and 307-test checkpoint. Raw execution metadata stays outside this narrative.


Final closure commands, executed without answer generation:

```powershell
.\.venv\Scripts\python.exe results/p0_acceptance/closure_v1/close_p0.py baseline
.\.venv\Scripts\python.exe tools/p0_capture.py --output results/p0_acceptance/closure_v1/engineering/register.json -- .\.venv\Scripts\python.exe results/p0_acceptance/closure_v1/close_p0.py register
.\.venv\Scripts\python.exe tools/p0_capture.py --output results/p0_acceptance/closure_v1/engineering/verify.json -- .\.venv\Scripts\python.exe results/p0_acceptance/closure_v1/close_p0.py verify
```

The register operation preserves every old material and adds only the explicit researcher decision. The verify operation rehashes25 journals, checks32919 original files and recomputes all event chains. It reconstructs524 original native tokenizer request/response pairs twice, checks12 selected exact matches and revalidates pinned binaries plus the frozen dataset/source/config hashes. Actual backend version output, source snapshots, command captures and original report hashes are retained in the [acceptance verification](validation/P0_acceptance_verification_v1.json) and [delivery evidence](validation/P0_acceptance_delivery_v1.json). No new HTTP tokenizer or completion request is issued. Available backend interfaces are verified without inventing unsupported internal token arrays.

The previous raw failed commands and startup responses remain preserved. Final approval is direct researcher authority, not a conclusion inferred from test success. No per-axis rating, review timestamp, independent reviewer, blind procedure or scientific finding is added by the approval registration.

### Errors and attempted solutions

No new model run was used to improve the acceptance status. Earlier failures remain documented: unavailable configuration, cache permissions, matching gaps, health-audit misclassification, role-boundary errors, evaluator limitations and candidate serialization defects. Consolidation resolves scattered or superseded status descriptions by identifying each stage and its scope; it does not delete those descriptions or alter their measurements.

### Final results

The current decision is P0 PASS: Engineering and Methodological Infrastructure Validation Completed. The researcher has explicitly approved the exact Tessa sentence. Engineering checks and all required selected-control reviews have sufficient evidence; no new blanket requirement for natural EOS, perfect model answers, independently reproduced quantization, blind control review or future research phases is introduced. The [final assessment](P0_final_scientific_acceptance_report.md) contains all fifteen required checks, all PASS within scope, and no remaining mandatory blocker. P1 remains NOT STARTED and requires separate researcher authorization.

At the earlier closure checkpoint, the gate contained one unmatched style case, new-style review,18 A evidence associations and6 categorical confirmations. The current assessment above supersedes that task list while retaining its history; the final exact-wording approval is now registered, closing that task list.

| Requirement | Status | Evidence and acceptance boundary |
|---|---|---|
| Research identity, English scope and protocol preservation | PASS | Frozen objectives and protocol retained; no P1 execution |
| Local CPU execution and artifact identity | PASS | Real responses, observed loading/CPU logs, pinned model/backend hashes |
| Track A evidence and input reconstruction | PASS | One hundred original prompts reconstructed; frozen development inputs preserved |
| Supported native token accounting | PASS | Submitted IDs/counts retained, no observed input truncation; unavailable internal IDs disclosed |
| Exact control matching | PASS | Original40/40 and v2 development24/24 preserved; first closure5/6 retained; final selected style6/6 and History A6/6, tolerance0 |
| Raw logging and frozen boundary instrumentation | PASS within scope | Preserved raw spans, tested status policy and conservative ambiguity |
| Versioned evaluation and uncertainty handling | PASS within scope | Separate axes and four factual categories; legacy results unchanged |
| Original human-review completeness | PASS | 40/40 researcher-reviewed, explicitly assisted and non-blind |
| Original semantic-control validity | PARTIAL | All forty overall suitability judgments remain PARTIAL |
| New candidate researcher decisions | PASS |24/24 confirmed, assisted and non-blind; four distinct dispositions preserved |
| Detailed new annotation conformance | PARTIAL |18 missing suitability labels,6 disallowed coherence N/A values and 81 missing required per-axis quotes across the full archive |
| Adopted-control validity within declared scope | PASS | Six explicit absence-of-style and six History A comparisons accepted narrowly; original semantic uncertainties and topic/temporal differences retained |
| Reproducibility | PASS within audited scope | Saved inputs, hashes, immutable records and offline reconstruction; missing historical fields disclosed |
| Upstream quantization equivalence and broad semantic validity | PARTIAL | Qualified limitations; no unsupported certification |
| Automated tests | PASS |365 passed, zero failed, exit0 |
| Overall P0 infrastructure acceptance | PASS | All mandatory pipeline/parser/measurement gates have scoped evidence; no scientific-effect claim |
| P1 entry | NOT STARTED | P0 accepted; separate researcher authorization required before execution |

### Remaining limitations

The first bounded cycle ended with5/6 matches and retained its failure. Subsequent explicit researcher instructions authorized only Tessa repair and confirmed the other selected controls. One frozen verb-phrase replacement now gives99/99; its exact wording now has the explicit researcher decision ACCEPT_NARROW. History A evidence and scoped suitability confirmations are complete. The researcher need not repeat the already supplied decisions, and unused B/C diagnostics need not be repaired to close this gate. The final master remains unchanged; separate converted and confirmation files preserve missing values. No new human judgment, Persona effect, general accuracy, causal mechanism or novelty claim is inferred by the conversion. All source changes remain subject to Yaxin ZHENG's review and researcher-managed commits and pushes.
