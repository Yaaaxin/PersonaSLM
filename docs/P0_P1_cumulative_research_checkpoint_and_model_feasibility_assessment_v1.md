# PersonaSLM Retrospective P0-P1 Cumulative Checkpoint and Model-Feasibility Assessment v1

Project: PersonaSLM  
Researcher: Yaxin ZHENG  
Paper title: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*  
Record date: 2026-10-17  
Protocol baseline: Research Protocol v1.1 and approved addenda; Protocol v1.2 remains proposed

## 1. Checkpoint character and scope

This is a **retrospective cumulative Git archival checkpoint prepared after P1 Stage B**. It collects the currently completed public-safe P0-P1 research dependency closure in one checkpoint because the working tree accumulated multiple scientific milestones without intermediate commits. It is not a contemporaneous preregistration, a pre-unblinding commit, or evidence that these files were versioned before Stage B. Historical artifact timestamps, hashes, frozen manifests, authorizations, negative results, and the development log remain the evidence for when the underlying scientific actions occurred.

The checkpoint is prepared on the dedicated branch `research/autonomous-personaslm`, created from `main` at HEAD `c40667ad266082481b1850453f67784b593f3723`. Branch creation did not alter that HEAD or rewrite history. Its exact proposed public paths are recorded in `docs/validation/research_checkpoint_v1/public_git_allowlist_v1.txt`. That file is an allowlist, not an instruction to add its parent directories recursively.

The current repository `AGENTS.md` reserves commits and pushes to the human researcher. No file was staged, committed, or pushed by the automated research agent. Consequently, the model-feasibility design was fixed and SHA-bound before any challenger output, but it is not represented as a Git-anchored preregistration.

The public scope includes research code, tests, Protocol v1.1-era records and approved addenda already present in the repository, P0-P1 reports, frozen manifests, scoring definitions, reference and synthetic development data, tokenizer/provenance metadata, aggregate Stage B decision and execution evidence, and the cumulative research log. P5 remains a completed diagnostic and P6 remains paused; their records are retained only where they form historical dependency or negative-result context for P1. This checkpoint does not activate either phase or claim an ESCP advantage.

## 2. Public-safe Stage B result

The existing Stage B decision and execution records remain authoritative; this report does not create a competing decision record.

| Configuration | Researcher-audited task success | Original automatic success | Automatic/researcher agreement | Qualified |
| --- | ---: | ---: | ---: | --- |
| D0 | 1/8 | 1/8 | 7/8 | No |
| D1 | 5/8 | 5/8 | 8/8 | No |
| D2 | 5/8 | 5/8 | 8/8 | No |
| D3 | 5/8 | 5/8 | 8/8 | No |

No O/Q configuration met the frozen requirement of audited success at least 6/8 and agreement at least 7/8. Branch B therefore executed exactly eight frozen minimal-temporal C0 calibration requests. The frozen exact/alias endpoint scored 6/8 current-value adoptions and 2/8 outdated-value adoptions, below the registered 7/8 gate. The 80-request S/F/H factorial pilot was not executed. The historical ledger is 80/160 used and 80 remaining; the unused 80 requests remain blocked by the failed gate and are not reassigned here.

The executed configuration was the Qwen/Qwen3.5-2B instruction-capable GGUF from `lmstudio-community/Qwen3.5-2B-GGUF` revision `bb84e11355a036e28f080c7793fa6d22b7c4e344` (intended upstream revision `965dcc54bc9c0591873df0e9869c056a54d323d1`), Q4_K_M model SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`. It used CPU-only llama.cpp build `b11573-0f701c882`, backend SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`, four generation and batch threads, context 4096, greedy temperature 0/top-p 1, seed 42, and 96 maximum new tokens. The distributor did not supply complete source-weight conversion lineage; that limitation remains recorded.

These are developmental results. They are not confirmatory findings, independent validation, general evidence of model incapability, full Persona Fidelity measurement, algorithmic novelty, or publication readiness.

## 3. What the 6/8 calibration result supports

The two failed cases emitted frozen, trusted old values for the correct entity and attribute rather than the value valid on the requested date. Both outputs were nonempty, contained one identifiable answer unit, used native EOS, and exactly matched old-value aliases. The observed endpoint failures therefore are not explained by wrong-entity selection, missing output, or failure of the registered exact/alias matcher. The frozen evidence supplies explicit validity intervals, so no evidence ambiguity was identified by the automatic audit.

The narrow observed pattern is consistent with outdated-value selection or temporal attribution failure. It does not establish which internal mechanism caused the failures, and two cases cannot identify a dominant general failure mechanism. Structural status remains `AMBIGUOUS` and semantic completeness remains `UNCERTAIN`; native EOS is not treated as independent proof of completeness. Prompt-package sensitivity and broader reasoning limitations remain possible, while unrestricted prompt search, retries, case replacement, and threshold lowering remain scientifically disallowed.

## 4. Public/private reproducibility boundary

The public checkpoint supports inspection of the protocols, code, manifests, frozen policies, aggregate decisions, scores, tests, provenance hashes, and reported numerical summaries. It does **not** provide clone-only end-to-end reproduction of every result.

Private archive only:

- the restricted unblinding key;
- the complete researcher unblinding record;
- the researcher-filled review sheet, comment-bearing compatibility/import records, and the unapplied proposal sheet named in the exact ignore rules;
- raw model run directories and claims under ignored `results/` paths.

External or local-only execution dependencies:

- GGUF model weights under ignored `models/` paths;
- pinned backend binaries under ignored `bin/` paths;
- a machine satisfying the registered CPU and memory preflight.

Public manifests retain SHA-256 references to private or local-only artifacts where already recorded. A public clone can verify the distributed dependency closure and derived records, but independent rescoring of undistributed raw responses or exact inference replay requires controlled access to the private archive and separately obtained, hash-verified model/backend artifacts. No public download link or access guarantee is invented.

At Stage B closeout, the authoritative v2 reproducibility manifest indexed 485 hashes: 35 scientific artifacts, 441 run files, eight attempt records, and one execution claim; the recorded audit found zero missing and zero mismatched entries. The later retrospective checkpoint changes documentation and public-governance metadata, so that historical manifest remains a closeout snapshot rather than being silently rewritten to describe a later Git state.

## 5. Restricted-data and process controls

Exact-path `.gitignore` rules protect fifteen private human-review, linkage, protected-mapping, and unblinding artifacts from routine staging. They must also remain protected by private storage and explicit allowlist review; `.gitignore` is not a security boundary. The public allowlist excludes model weights, backend binaries, raw run archives, caches, temporary files, credentials, and those private records.

Two procedural events remain disclosed:

1. During the earlier recovery, a legacy test process parsed the restricted key after the researcher review had already been frozen. It printed no mappings, calculated no condition-level result, changed no bytes, and does not by itself establish reviewer contamination.
2. During the current safety audit, a generic byte-level NUL check called `ReadAllBytes` on two private files before the exact-path exclusions were installed. It did not parse or emit mappings or comments and changed nothing. This was unnecessary access; the new exact-path ignore guards and path-level allowlist checks prevent those files from entering the public staging proposal.

No restricted contents are reproduced here.

## 6. Prospectively bounded model-feasibility recovery

The first challenger was prospectively frozen in `docs/validation/p1/model_feasibility_recovery_v1/prospective_freeze_v1.json` as **HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF**, upstream commit `6a7e79393ef2957e087f11fce1e50476799e313c`, file `smollm2-1.7b-instruct-q4_k_m.gguf`, expected SHA-256 `decd2598bc2c8ed08c19adc3c8fdd461ee19ed5708679d1c54ef54a5a30d4f33`, reported size 1.06 GB, Apache-2.0. A second and final challenger, executable only after a complete valid nonqualifying first-candidate result, is **Qwen/Qwen2.5-3B-Instruct-GGUF**, commit `af75b7aaf5bb163ce4c5dab4e6b84d844e96265d`, file `qwen2.5-3b-instruct-q4_k_m.gguf`, expected SHA-256 `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`, 2,104,932,768 bytes, under the Qwen Research License. At prospective freeze time neither artifact was local. Candidate 1 has since been downloaded to ignored model storage and verified byte-for-byte; Candidate 2 remains absent and inactive. The first candidate retains the 3 GiB RAM floor; the larger candidate has a prospective 5 GiB floor.

The first batch is limited to the same eight already-observed fallback calibration cases and is explicitly `DEVELOPMENT_ONLY`. This reuses development material to assess measurement feasibility and cannot serve as independent confirmation. The task bank, frozen exact/alias scorer, 7/8 qualification threshold, greedy decoding (`temperature=0`, `top_p=1`, seed 42, 96 maximum new tokens), no-retry policy, existing pinned llama.cpp backend, 3 GiB available-RAM preflight, and 45-minute batch ceiling are specified before outputs. The model's native embedded chat template must be frozen after verified acquisition and before completions; it must not be hand-rewritten after observing results.

Primary endpoint: at least 7/8 current-value task successes. Secondary endpoints: current-value adoption, outdated-value adoption, wrong entity, unverifiable, contradictory, missing output, structural status, semantic completeness, and latency. The first complete qualifying candidate is selected in the frozen least-complex order; a qualifying first candidate prevents downloading or executing the second. Candidate 2 may run only after Candidate 1 completes all eight attempts with an integrity-valid score below 7/8. An integrity, runtime, incomplete-run, or resource failure stops screening rather than activating the next model. If neither candidate qualifies, screening stops without adding candidates or lowering thresholds. Any selected model still faces the separately frozen disjoint pilot C0 gate; the observed eight cases cannot be relabeled as independent validation.

The new autonomous authorization is maintained separately from the historical ledger: at most 1,200 local CPU generations and 72,000 seconds of actual inference, whichever is reached first. Current use at checkpoint preparation is zero. Initial screening is capped at eight attempts per candidate and 16 in total. Download or validation does not authorize inference unless all frozen provenance, safety, and execution checks pass.

## 7. Checkpoint safeguards and limitations

- The allowlist is path-exact and sorted; no `git add .` or `git add -A` is appropriate.
- The 2026-10-17 allowlist snapshot contains 880 non-ignored paths, is ordinal-sorted, and has SHA-256 `853fd4f45da2f6b2d45d7d41e4b52e0a0102b21796f84d36861261c84784026d`. Recovery found it no longer exactly matches the later working tree, so it is historical evidence rather than a current staging instruction.
- The checkpoint is not presently ready to stage from that stale allowlist. Repository `AGENTS.md` leaves staging, commits, and pushes to the human researcher; any future human checkpoint must regenerate and verify an explicit allowlist and confirm that no restricted or ignored path appears.
- Existing raw scientific outputs and frozen records are not modified by this preparation.
- The cumulative checkpoint preserves negative and failed-gate findings; it does not reinterpret them to pass a threshold.
- Task success, factual consistency, temporal consistency, response relevance, coherence, answer completeness, required-component coverage, outdated adoption, and Persona Fidelity remain distinct. Linguistic and behavioral Persona Fidelity are `NOT_APPLICABLE`, not zero, for the minimal single-answer calibration.
- P0 is frozen; P1 remains active at model-feasibility recovery; P2, P3, and P4 remain paused; P5 is diagnostic completed; P6 remains paused.

## 8. Candidate 1 preparation outcome and stopping condition

Candidate 1 download completed without inference: 1,055,609,536 bytes and SHA-256 `decd2598bc2c8ed08c19adc3c8fdd461ee19ed5708679d1c54ef54a5a30d4f33`, matching the frozen official artifact. The GGUF contains 218 tensors and 34 metadata keys. Its embedded native template SHA-256 is `872be49dbb638044ad01b60388f48d469ff2980e5f0dccdc22ec907db54d0788`. All eight frozen development requests were rendered through the existing byte-verified Jinja2 3.1.6/MarkupSafe 3.0.4 runtime and tokenized with the pinned llama.cpp native tokenizer. The resulting immutable materialized manifest SHA-256 is `7ab1a88fb4aa324173379da891f86f8468444a356576a8b3ad456fdf0a09c194`.

Two preparation failures were preserved rather than hidden: the initial GGUF reader evaluated an assignment right-hand side before its serialized key and therefore misread a key length as metadata type 20; after a focused regression fix, the next attempt correctly stopped because Jinja2 was not importable from the project virtual environment. Reuse of the already archived, byte-hashed project-local renderer resolved the latter without installing a new unpinned dependency or rewriting the native template. Both failed receipts report zero generations.

The registered inference preflight then failed. It observed 2,669,027,328 available physical bytes against the unchanged 3,221,225,472-byte requirement, a deficit of 552,198,144 bytes. The separately recorded memory observation moments later was 2,661,564,416 bytes. No process was terminated, no memory threshold was lowered, no model/backend/context setting was changed, and no completion endpoint was called. Candidate 1 therefore has no task-success result; Candidate 2 is not activated; the disjoint pilot and S/F/H factorial remain unexecuted. New-autonomous-budget use remains 0/1,200 generations and 0/72,000 inference seconds. Historical use remains 80/160 with its 80-request remainder separate and blocked.

The combined post-Stage-B, feasibility, and literature-monitoring regression selection completed with 92 passed, 0 failed, 0 skipped, and one pre-existing `cache_dir` configuration warning. This is an engineering stopping condition, not evidence that Candidate 1 lacks temporal task capability.

The daily literature workflow has a verified active local Windows schedule but is not remotely active on GitHub. The restored task completed a real scheduled collection on 2026-10-18 with result 0; its interactive-only boundary requires the workstation to be on and the researcher logged in. GitHub scheduled workflows run from the default branch; remote activation therefore requires researcher-controlled commit/default-branch integration and enabled Actions. No scheduled cloud execution is claimed.

## 9. Interrupted-session recovery addendum — 2026-10-18

Recovery confirmed that Candidate 1 had not generated any output and that both authorization ledgers remained unchanged. A second versioned registered preflight (`candidate1_preflight_attempt_v2.json`, SHA-256 `f60c98804ef3d495518374215d4ff04a3ee34a99310fc8a4fe63980b170e2222`) observed 2,828,460,032 available bytes against the unchanged 3,221,225,472-byte threshold and stopped before model inference. Later passive observations also remained below threshold. No unrelated user process was terminated, no runtime parameter changed, and no Candidate 2 activation, pilot, or factorial request occurred. The verified autonomous balance remains 0/1,200 generations and 0/72,000 inference seconds.

The two Stage B failures were reclassified only at the observable-output level: each selected a trusted old value for the correct entity and attribute. They are `OUTDATED_VALUE_ADOPTION`, not wrong-entity, empty-output, alias, or evidence-ambiguity failures. Two cases cannot identify an internal attention, reasoning, or prompt-interpretation mechanism; researcher semantic review of the eight Stage B outputs remains pending.

Daily literature persistence was repaired without an interactive-agent dependency. The versioned recovery evidence records the least-privilege task contract, a successful scheduled run at 2026-10-18T09:28:51Z, the 196-record private discovery snapshot, and one retained Crossref source failure. The structured primary-source ledger now contains fourteen records. The closest verified novelty collision, *Beyond similarity retrieval*, already combines persona-related governing facts, temporal revisions, supersession handling, local CPU inference, and small open-weight models. Additional reviewed work covers stale binding, adaptive handling of memory-induced unreliability, non-selective persona control, deterministic linguistic-fidelity measurement, and persona-consistency/reasoning-stability trade-offs.

These sources require a narrower prospective contribution: the complete paired shared-evidence `2^3` S/F/H factorial and its joint reliability, outdated-value, persona-fidelity, and CPU-cost endpoints may remain differentiating if actually measured and independently validated. Generic novelty claims about history-induced stale answers, temporal provenance, CPU-small-model memory tests, or fidelity-reliability trade-offs are not defensible. P6 remains paused; SCR-T-style supersession and evidence-grounded memory handling become required strong baselines for any later algorithm proposal.

The persistent state now also carries the requested A–M publication-readiness scorecard without an aggregate score. Research-question validity is supported; experimental control, novelty, reproducibility, ethics/data planning, and manuscript completeness are developing; construct validity, dataset independence, sample adequacy, evaluator reliability, statistical credibility, and generalization evidence are insufficient; baseline strength is blocked by the RAM preflight. This inventory is not a claim of publication readiness.

Suggested checkpoint message: `chore(research): checkpoint P0-P1 through Stage B and preserve failed calibration`.

## 10. Candidate 1 execution and Candidate 2 preparation addendum — 2026-10-18

This addendum records evidence created after the recovery state described above; it does not rewrite those earlier time-bounded observations. Candidate 1's second registered preflight remained blocked: `candidate1_preflight_attempt_v2.json` (SHA-256 `f60c98804ef3d495518374215d4ff04a3ee34a99310fc8a4fe63980b170e2222`) made its gate decision at 2,828,460,032 available physical bytes against the unchanged 3,221,225,472-byte requirement and issued no completion. A later, separately versioned preflight passed without changing that requirement, stopping policy, model, backend, context, or generation settings. `candidate1_preflight_attempt_v3.json` (SHA-256 `15cae497000444fcd207c11af1795f70e54508fb40ef0eff0f3664934c2e072c`) observed 3,838,619,648 available bytes and authorized only the frozen Candidate 1 batch.

Exactly one Candidate 1 run then executed the eight frozen development-screen requests, with no retries or replacement cases. All eight produced a result and native EOS. The frozen exact/alias endpoint classified one `CURRENT_VALUE_ADOPTION`, one `OUTDATED_VALUE_ADOPTION`, and six `UNVERIFIABLE_ANSWER` records, giving **1/8** automatic task successes against the unchanged **7/8** qualification threshold. `candidate1_run_receipt_v1.json` is byte-identical to the immutable run summary and has SHA-256 `541cabb568afe3be0ace249f4a9d24dc507c652f2624e62d6722f70ed8ff3485`. Replay audit `candidate1_audit_v1.json` (SHA-256 `d73d16cf9b8ab7b433f4f53ff2b7567d186d88003b3b7a119df5bd439d725921`) found eight attempts, eight completion HTTP records, eight replayed results, a complete terminal event, and `integrity_status: PASS`. The registered selection state is therefore `CANDIDATE_1_FAILED_CANDIDATE_2_PENDING`; Candidate 1 did not qualify and no model has been selected.

A disclosed post-output AI-only semantic reinspection judged that four responses contained the current requested value: cases 00, 06, 13, and 15. Three of those responses used sentence or evidence-line wrappers that the frozen exact/alias endpoint did not accept. It judged cases 03, 05, and 09 to select the correct entity and attribute but the outdated value, and case 11 to end at native EOS after naming the relevant record/entity without supplying the requested value. No wrong-entity answer or token-budget truncation was observed. Thus the diagnostic taxonomy is four current-value answers, three outdated-value selections, and one incomplete answer. This **4/8 post hoc AI assessment is not an independent annotation, a researcher-confirmed score, a registered secondary endpoint, or a replacement for the frozen 1/8 gate result**. It cannot activate the pilot, alter aliases retrospectively, or support a claim that Candidate 1 passed. Instead, the discrepancy is developmental evidence that output-form sensitivity and semantic task competence require separate validation before either model incapability or scorer validity is claimed. All eight automatic structural statuses remain `AMBIGUOUS`, and semantic completeness was not independently adjudicated.

The run consumed eight generations and 65.87628550000954 seconds of recorded completion inference. The separate autonomous balance is consequently 8/1,200 generations and 65.87628550000954/72,000 seconds used, leaving 1,192 generations and 71,934.12371449999 seconds under the hard ceilings. There are no unresolved in-flight requests. The historical P1 ledger remains independently unchanged at 80/160 attempts; its 80-request remainder was neither consumed nor transferred.

Candidate 1's complete, integrity-valid nonqualifying result prospectively activated Candidate 2 preparation. The first Candidate 2 download operation was blocked by a Windows socket-permission error and is preserved in `candidate2_download_receipt_v1.json`; it made zero generation requests and is an engineering failure with evidence, not a model result. The authorized retry produced `candidate2_download_receipt_v2.json`, verifying the 2,104,932,768-byte Qwen2.5-3B-Instruct Q4_K_M artifact at SHA-256 `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`. Offline materialization then rendered and native-tokenized all eight unchanged requests without a completion. Its canonical manifest and receipt have SHA-256 `591dadd21a2b893a6c327d4d8737da3159a380a5f921049f9d5364a5bc849c43`; the embedded native-template SHA-256 is `d5495a1e5db0611132a97e46a65dbb64a642a499421228b9c8b93229097fa9a4`.

Candidate 2's first formal registered preflight is preserved as `candidate2_preflight_attempt_v1.json` (SHA-256 `51047252c9cfc194c882dbe2804b65a9ec710097865bf8e04cf91aa2a9d4c1ed`). Its gate decision observed 4,746,973,184 available physical bytes against the unchanged 5,368,709,120-byte requirement, a 621,735,936-byte deficit; the failure handler's separate observation moments later was 4,737,028,096 bytes. The action stopped before model load or completion and made zero generation attempts. It may execute only after a materially new resource state and a fresh, versioned full preflight observe at least the registered threshold and all other frozen checks pass; the threshold must not be lowered and unrelated user processes must not be terminated to manufacture eligibility. The bounded two-candidate feasibility screen is therefore **blocked and unresolved**, not complete, not a bounded negative model finding, and not evidence that Candidate 2 lacks task capability. The disjoint pilot C0 gate and the S/F/H factorial remain unexecuted.

Finally, each challenger is scientifically defined as an exact **model-plus-native-template configuration**. Candidate 1 used model SHA-256 `decd2598bc2c8ed08c19adc3c8fdd461ee19ed5708679d1c54ef54a5a30d4f33` with embedded-template SHA-256 `872be49dbb638044ad01b60388f48d469ff2980e5f0dccdc22ec907db54d0788`; Candidate 2 uses the model and template hashes recorded above. Candidate-specific embedded templates are the prospectively disclosed compatibility adjustment, not a controlled pure-weight manipulation. Any later difference between the two screens must therefore be interpreted at the configuration level and cannot, by itself, be attributed solely to parameter count, architecture, weights, instruction tuning, or temporal reasoning ability.

## 11. Resource-aware evaluator-validity milestone — 2026-10-18

Candidate 2 remains resource-blocked. A passive observation at 2026-10-18T10:40:29.080477Z found 4,997,967,872 available physical bytes, still 370,741,248 bytes below the unchanged 5 GiB requirement. This observation was not promoted to a versioned preflight, no model was loaded, and no completion was requested. Process inspection found no Python, llama.cpp, Ollama, or other identifiable PersonaSLM inference process to stop. One nearly idle hidden PowerShell process could not be safely attributed to the project and was left intact rather than risking an unrelated user process. Candidate 2 therefore remains `BLOCKED_RESOURCE`, with zero requests and no performance result.

Offline work produced a reproducible aggregate-only evaluator-validity result without reading the restricted key, unblinding record, researcher comments, raw responses, or record-level model text. The O/Q audit has 31/32 exact-category agreement (96.875%; descriptive record-level Wilson 95% interval 84.26%–99.45%) and equal automatic/researcher success totals of 16/32. These aggregate marginals cannot identify a full confusion matrix, sensitivity, specificity, kappa, independent factual/temporal validity, or inter-rater reliability. Wave 1 automatic factual coverage was 15/72 (20.83%), and its broader labels were researcher-confirmed AI-assisted coding rather than an independent second rating. Structural status is not a semantic proxy: Wave 1 contained 78/78 semantically complete `CROSS_TURN` first replies, while the independent P1b aggregate contained 142/186 semantically complete `CROSS_TURN` outputs.

Candidate 1 further exposes a format-coverage problem. The frozen alias endpoint recognized a current or outdated value in 2/8 outputs, and only 2/7 outputs judged semantically classifiable by the disclosed post-hoc AI-only diagnostic. This **2/7 is descriptive cross-source coverage, not accuracy**. It neither upgrades the AI diagnostic to human evidence nor changes the frozen 1/8 success score or 7/8 threshold. Because Style may alter answer wrappers, this endpoint cannot be the sole semantic outcome in a future S/F/H comparison without risking differential misclassification. The deterministic artifact is `docs/validation/p1/model_feasibility_recovery_v1/evaluator_validity_v1.json`, SHA-256 `66ef42aaf58b18993eeb168d88f54d7354d7c7dc9ad3d12375906e5c39676ab9`; eight focused tests reproduce it exactly from six public-safe aggregate sources.

Current evidence does not justify P6. All eight feasibility cases are C0, only case 09 showed outdated-value selection across both tested configurations, and model, native template and output form changed together. History-conditioning causality is therefore not identified. Any prospective mechanism study must separately vary target relevance and current-versus-outdated history while matching format, length and evidence order, then compare at least full context, history removal, recency/entity-time rules, SCR-T-style supersession and evidence-grounded memory baselines before proposing a new algorithm.

An independent-validation boundary was also estimated without generation. A candidate minimum is 48 entirely new speakers × two ancestry-disjoint cases × ten conditions (C0–C7, N_style and N_history), or 960 generations. Under central paired-binary assumptions, approximate primary C3−C0 outdated-adoption 95% half-width is 12.0–17.3 percentage points; high-variance interactions may remain wider than 20 points. This is neither a frozen cohort nor authorization to execute. It remains `BLOCKED_SCIENTIFIC` until a configuration passes the frozen model and disjoint-C0 gates, the development factorial is interpretable, and a prospective crossed speaker/template simulation and blinded semantic-review plan pass their acceptance criteria.

## 12. Candidate 2 preflight v2 and independent analysis reproduction — 2026-10-18

After the researcher reported additional memory availability, one new versioned official
Candidate 2 preflight was executed. `candidate2_preflight_attempt_v2.json` (SHA-256
`686f92690681b69911643840ff5a30b8b7b07015bc55a293cc0b283b1908d5d9`)
observed 4,595,142,656 available physical bytes against the unchanged 5,368,709,120-byte
gate, a 773,566,464-byte deficit. The later failure-handler observation was 4,584,386,560
bytes. The action stopped before model load and made zero completion requests. Candidate 2
therefore remains `BLOCKED_RESOURCE` and scientifically unevaluated; the autonomous ledger
remains 8/1,200 generations and 65.87628550000954/72,000 seconds, with no unresolved
request, while the historical ledger remains 80/160.

The new analysis-reproduction entry point then replayed Candidate 1 from the local private
journal/raw-output archive: eight attempts, eight completion records and eight reconstructed
results passed integrity, preserving the frozen 1/8 score and 7/8 threshold. In a separate
temporary directory, a new interpreter process launched with `-I -B` copied only eight
explicitly allowlisted aggregate/code files and reconstructed `evaluator_validity_v1.json`
exactly. The receipt is `analysis_reproduction_v1.json` (SHA-256
`4d0570e78106abf1b19113fe616c5b11e4fb59cc87868c646951e22e65bad352`).
The scoped regression suite passed 43 tests with one pre-existing unknown `cache_dir`
warning. This execution made zero model generations and zero network calls.

The reproduction boundary is deliberately limited. Local private-archive analysis and the
public-safe aggregate reconstruction pass. Public clone-only full reproduction is partial
because the raw Candidate 1 run and model weights are not public-tracked inputs. Generation
reproduction was not attempted and cannot be inferred from analysis replay; exact bytes are
not promised across hardware or backend changes.

The same receipt exposes a downstream safety dependency. The existing conditional controller
and both 80-request manifests bind the historical Qwen3.5 model and historical authorization;
the two manifests also have different request sequences. Consequently, even a future 7/8
Candidate 2 screen cannot call the old controller or select C0 by an unverified positional
slice. A new Candidate-2-native manifest, namespace, ledger binding, and controller must be
prospectively validated before any pilot request. The semantic endpoint-validity gate remains
separate and still blocks the remaining 72 requests even if the disjoint C0 execution gate
eventually passes.

## 13. Updated literature collision and mechanism-design consequence — 2026-10-18

Full-text primary-source review added Wiki-Talkie, ReTurn, and Memory Echo/FPA as a
versioned structured delta. Wiki-Talkie already compares raw persona history with explicit
profiles and behavioral summaries. ReTurn supplies matched direct/conversational references
and separates history-required from history-interfering tasks. Memory Echo's
Family-Provenance-Authority method already implements source-family grouping,
correction-conditioned stale-record eligibility, and authority-guided answering.

These studies do not eliminate the controlled CPU-small-model S/F/H empirical question,
but they invalidate broad priority claims about history-versus-profile comparisons, history
help/harm, or provenance-guided conditional stale-memory suppression. FPA is now a direct P6
competitor and strong baseline. P6 remains paused: a new method would first need a replicated
residual failure that is not merely trace multiplication or task-rebinding ambiguity, then
incremental evidence over simple restatement, explicit temporal filtering, authority-only,
and FPA-like baselines while preserving Persona Fidelity and CPU cost.

## 14. Post-restart Candidate 2 v3 block and offline scientific progress — 2026-10-18

The planned restart recovery verified the supplied checkpoint hashes, branch
`research/autonomous-personaslm`, HEAD `c40667ad266082481b1850453f67784b593f3723`, zero
staged paths, all 28 frozen reference hashes, Candidate 1's complete 8/8 archive with the
frozen 1/8 score, and both unchanged authorization ledgers. No Candidate 2 v3, run, audit,
or selection receipt existed, and its attempt count remained zero.

Exactly one official Candidate 2 v3 preflight then ran. The preserved receipt
`candidate2_preflight_attempt_v3.json` has SHA-256
`1b8b1c144cbfb4c330171a0e297ae497154230fff0feef4f096993caffaff8dd`.
Its gate measurement observed 4,901,916,672 available physical bytes against the unchanged
5,368,709,120-byte threshold, a 466,792,448-byte deficit; the failure-handler observation
was 4,883,410,944 bytes. It made zero generation requests and did not load the model.
Candidate 2 remains `BLOCKED_RESOURCE`, not a model failure. Autonomous use remains
8/1,200 generations and 65.87628550000954/72,000 inference seconds; historical P1 use
remains separately 80/160. No retry, threshold change, process termination, or frozen-input
change occurred.

The post-restart daily collector first preserved a 13/13-source network-sandbox failure,
then succeeded outside that sandbox for all 13 frozen metadata requests. The successful
ignored snapshot contains 217 unreviewed records and 26 stable IDs not in the earlier
same-day snapshot. Full-text review of the important new candidate
[PersEvalBench](https://arxiv.org/abs/2610.19314v1) found direct overlap with evaluator-side
persona-use validation, directional under/over errors, and stale/superseded-use errors.
The paper reports limited LLM-judge reliability, a human-reference advantage, and much
easier pairwise than independent directional judgment. The review is AI-assisted and was
not independently reproduced. It prospectively requires PersonaSLM to retain blinded human
pointwise judgments, error direction, false alarms, and abstention/coverage; LLM-judge and
pairwise results can be secondary only. The old 14-record ledger and prior addendum remain
byte-unchanged; the delta is `primary_source_review_addendum_2026-10-18_v2.json`.

Offline planning then completed the previously missing crossed speaker/template simulation
for the candidate independent cohort. The deterministic design uses 48 speakers, two cases
per speaker, eight balanced new template ancestors, and ten conditions (960 planned but
unexecuted requests). Before the full run it declared that the central scenario must have a
median two-way clustered 95% half-width no wider than 15 points and conditional-template
coverage of at least 93%. Across 2,000 replicates, the central median half-width was 11.89
points with 95.95% coverage; the higher-template-dependence sensitivity was 13.11 points
with 97.15% coverage. The central planning rule therefore passed under its assumptions.

That pass is not a cohort freeze or execution authorization. Every dependence and
missingness parameter is assumed rather than fitted, eight templates cannot identify a
broad template population, and only C3−C0 outdated-value adoption was simulated. In the
outcome-dependent missingness sensitivity, median complete-pair availability fell to
88.54%, complete-pair bias was −2.48 points, coverage fell to 92.5%, and logical bounds
averaged 11.89 points wide. Missingness policy and genuine blinded semantic review remain
hard gates. The reproducible artifact is `independent_validation_precision_v1.json`
(SHA-256 `8a2f7145ff263893127e4607b33b448e71f8e6de81ab972eb65a5edf12b6d96b`);
its source SHA-256 is `94865bd06299964d2f45031ea91ef8fe1af70d2d624cf4792ef6e663663ed334`.

## 15. Blinded semantic-review package preparation — 2026-10-18

A local, pointwise-blinded review package was prepared from the eight completed Stage B
outputs and the eight completed Candidate 1 outputs. The generator revalidated all 16 raw
output hashes, both frozen request bindings, the source manifest, and the two immutable run
summaries before writing anything. It then assigned deterministic anonymous response IDs
in randomized order. The review CSV contains only the complete evaluation material, raw
response, and blank semantic-review fields; model/run/case identities, automatic labels,
condition labels, and prior AI interpretations remain in a separate local mapping.

The public hash-only receipt is `semantic_review_package_v1.json` (SHA-256
`dedd19f6383b44f44a9e91fc67e6e652bf7cae4a9dca043c262a628db3542dbd`). It records 16
responses, four hash-bound local package files, and zero completed human labels. The local
package is ignored rather than added to public-tracked evidence because it contains raw model
text. Its overwrite guard preserves the initial randomized template and mapping.

This preparation makes the next researcher task executable but supplies no semantic result.
One researcher review will not establish independent inter-rater reliability, and no review
has yet occurred. The frozen Stage B 6/8 and Candidate 1 1/8 gates remain unchanged;
Candidate 2 remains resource-blocked with zero attempts. No generation, model load,
inference time, budget transfer, unblinding, or historical-evidence rewrite occurred.

A separate offline intake validator is ready but has not been applied to the real package.
After a genuine completed review, it will require exact template/raw-text preservation,
complete allowed labels, consistent reviewer identity, explicit masking and prior-exposure
provenance, matching review-file hashes, and a one-to-one eight-case/two-arm mapping. Its
public aggregate omits evidence, raw responses, rationale text, and answer spans while
retaining their hashes, arm-level categorical counts, and paired current-value discordance.
It refuses to overwrite an existing integration output and explicitly preserves both frozen
gates. Tests use synthetic labels only; the real reviewer mapping remains unopened.

## 16. Prospective independent-validation missing-outcome policy — 2026-10-18

The crossed-cohort planning audit identified condition-dependent missingness as an unresolved
scientific gate. A deterministic policy candidate now binds the existing registered S/F/H
contrast weights to the already tested signed-bound engine rather than introducing another
estimator. It covers all nine registered simple/factorial contrasts, retains every frozen
eligible request in its denominator, preserves original weights, and produces logical bounds
from the endpoint range and the sign of each unknown cell.

The policy distinguishes a valid completed empty/nonanswer response, semantic `UNCERTAIN`,
infrastructure failure without a completion, hash-invalid raw evidence, missing review, and
prospectively frozen `Not Applicable`. None is silently relabeled as failure or success.
Full semantic category distributions remain on the eligible denominator. Current- and
outdated-value binary indicators treat genuine `UNCERTAIN` or absent semantic review as
unknown. Complete-pair estimates and crossed-cluster intervals are secondary selected-subset
sensitivities; all-eligible bounds remain primary whenever a required cell is unknown.

Artifact `independent_validation_missingness_policy_v1.json` has SHA-256
`75de14a4d62d023bd6c232ee81ec8480a1cb495e3a0d8868afec40175aa7c653`.
Four focused tests verify the existing registry, zero constant contrasts, zero-weight-cell
handling, deterministic reproduction, and signed bounds against every binary completion of
each single-unknown active cell. The artifact is a proposal pending researcher adoption: it
does not amend Protocol v1.1, authorize the 960-request cohort, choose a technical retry
allowance, resolve endpoint multiplicity, or supply any human/model outcome.

## 17. Candidate 2 disjoint-pilot native materialization — 2026-10-18

The downstream safety audit confirmed that the frozen 80-request minimal-temporal source is
case-grouped: its first eight rows are C0 through C7, not the eight C0 cases. Reusing the
historical controller's positional `[0:8]` slice for Candidate 2 would therefore execute the
wrong gate. The historical Qwen3.5 manifest, controller, authorization and 80-request ledger
remain unchanged and prohibited for Candidate 2.

A new zero-inference materialization preserves all 80 source messages, references,
applicability states and scientific hashes while rendering each with Candidate 2's verified
GGUF-native template and tokenizer. It writes the eight actual C0 requests first and, more
importantly, records their exact request IDs separately from the 72 continuation IDs. The
new namespace `P1_AUTONOMOUS_CANDIDATE2_DISJOINT_PILOT_V1` has an embedded 8+72 autonomous
sub-ledger and consumes zero of the historical 160-request authorization.

The artifact `materialized_candidate2_disjoint_pilot_v1.json` has SHA-256
`44f6f1991c03c8fae23e743099cafe5b8ceb1fd95f50b942878679e90f3b47cf`.
All 80 native tokenizer records report zero generation requests. Candidate 2 still has zero
attempts, total autonomous use remains 8 generations, and the historical ledger remains
untouched. This materialization does not select Candidate 2 or authorize inference. A new
validated C0-only controller is still required after a qualifying feasibility result; the
remaining 72 must additionally remain blocked until genuine semantic review and an endpoint-
validity decision are registered.

## 18. Candidate 2 disjoint C0 controller readiness — 2026-10-18

An additive controller now covers only the eight explicitly registered C0 request IDs. It
does not use request position, does not expose an action for the remaining 72 requests, and
pins the complete materialization SHA-256
`44f6f1991c03c8fae23e743099cafe5b8ceb1fd95f50b942878679e90f3b47cf`.
Runtime entry remains conditional on a complete, integrity-valid Candidate 2 feasibility
screen with at least 7/8 frozen successes and selected Candidate 2, followed by a fresh
preflight meeting the unchanged 5,368,709,120-byte available-physical-RAM requirement.

The controller writes an immutable claim before any completion, records an attempt before
each request, retains raw HTTP events and per-request results, reconstructs combined usage
across the screening and pilot namespaces, and provides a replay audit. Its C0 automatic
gate is the registered 6/8 current-value-adoption rule. Even a pass leaves the continuation
blocked for genuine semantic review, endpoint-validity resolution, and a separate validated
controller.

The non-executing readiness artifact `candidate2_c0_controller_readiness_v1.json` has
SHA-256 `f826f25c49b5b0721528a2e526088a996707ee9cd53ba343fd82e9f8425346af`.
It reports status
`READY_CODE_AND_MATERIALS_BLOCKED_UNTIL_CANDIDATE2_QUALIFIES_AND_RAM_PASSES`, eight explicit
C0 IDs, zero pilot attempts, and no run directory. The scoped regression suite passed 88/88;
receipt `candidate2_c0_controller_regression_v1.json` has SHA-256
`ff36aa574f8b0e764deaf428c59cefcc99f112b7d803bed70726ff9356f3a21a`.
No preflight retry, server start, model load, completion, inference time, semantic judgment,
or authorization consumption occurred.

## 19. Prospective endpoint hierarchy and multiplicity candidate — 2026-10-18

An audit of Protocol v1.1 against the current analysis registry found a planning mismatch.
The protocol lists four preliminary simple contrasts: C1−C0, C3−C0, C1−N_style, and
C3−N_history. The existing nine-contrast code registry contains the first two plus the
balanced S/F/H main effects and interactions, but not either neutral-control contrast. The
two missing contrasts must not be silently dropped or described as already registered.

A prospective candidate therefore defines one 11-hypothesis family on blinded-human
outdated-value adoption: the four protocol simple contrasts plus S, F, H, S×F, S×H, F×H,
and S×F×H. C3−C0 remains the lead planning and reporting contrast, but receives no
privileged unadjusted alpha. The candidate uses two-sided Holm step-down family-wise error
control at alpha 0.05. A hypothesis lacking a prospectively valid marginal test remains in
the family as an untestable non-rejection rather than being removed to shrink the denominator.
Current-value adoption, full semantic categories, the four reliability dimensions,
completeness, fidelity, and resource measures remain estimation/reporting outcomes unless a
later confirmatory freeze explicitly allocates alpha to them.

This is not an adopted policy. C1−N_style and C3−N_history can enter a confirmatory family
only after genuine semantic adoption of their exact controls and a missingness-policy
extension. The small-template two-way marginal tests also require prospective calibration;
Holm does not repair invalid marginal p-values. The cohort, model, prompts, applicability,
annotation plan, and technical retry policy remain unfrozen and unauthorized.

Artifact `independent_validation_multiplicity_candidate_v1.json` has SHA-256
`be40a8102c8b1b1c1310def44e5c4a2d6159538804905944dcfd8eb2232836a4`.
Eleven focused tests and a 99-test combined suite passed. Regression receipt
`independent_validation_multiplicity_regression_v1.json` has SHA-256
`0eee7d078e5d01ce5d66cf8beafa7914d5047049982a23e0a981f0f86a0479a6`.
No observed or simulated PersonaSLM outcome, human label, generation, or execution
authorization was introduced.

## 20. Independent-validation test calibration and bounds extension — 2026-10-18

The proposed 11-member Holm family was evaluated under prospectively coded synthetic
global-null rules before any independent cohort exists. These simulations contain no model
outputs and fit no PersonaSLM effect. The first candidate combined the existing
speaker-plus-template-minus-case sandwich variance with a two-sided t(7) reference. Across
three 3,000-replicate null scenarios, its worst Holm family-wise false-positive fraction was
7.7%; the corresponding Wilson upper limit was 8.71%, above the declared 6% ceiling.
Marginal type-I and nonpositive-variance criteria also formed part of the indivisible gate.
The candidate therefore failed and is not available for confirmatory use.

A separate v2 candidate narrowed the estimand to the finite, prospectively frozen set of
eight template ancestors and used speaker-cluster variance with t(47). It added a fourth
global-null scenario with condition-by-template heterogeneity while equalizing every
condition's expected mean over the exact 96-case allocation. Its Holm FWER criterion passed
in all scenarios (worst Wilson upper 5.77%) and nonpositive variance was negligible, but the
maximum marginal type-I Wilson upper limit was 6.98%, above the predeclared 6.5% ceiling.
Because every criterion was mandatory, v2 also failed. The thresholds were not relaxed, the
passing components were not cherry-picked, and no third method was searched merely to obtain
a pass.

The current inferential status is therefore
`NO_CALIBRATED_CONFIRMATORY_TEST_IDENTIFIED`. This does not invalidate effect estimates,
full categorical distributions, missingness accounting, or logical identification bounds;
it prevents dichotomous confirmatory claims from the tested procedures. A later freeze must
either justify and prospectively calibrate a different method or explicitly adopt an
estimation-first design whose uncertainty language does not imply validated hypothesis tests.

The v1 and v2 calibration artifacts have SHA-256
`e54ca677e770469c6c22fcc39ed1ba947321c213056f77a51d2b0d181d05a135` and
`3964f3eaaf82083d11d8c77bd000df8dbc96157e37fec1ccd1e82e73371c44c5`.
Both reproduce exactly from their recorded seeds. Missingness policy v2 extends signed
all-eligible bounds to all 11 candidate contrasts, including C1−N_style and C3−N_history,
without activating the neutral controls or authorizing execution. Its SHA-256 is
`b46067578c16d312e7b445e28a59829b65f7bb42141074bf63746d2cb59e1730`.
The 113-test regression receipt has SHA-256
`41bdcf19bd6d1bc588f6ec3b18f5dcbeb807acc1ec34d2f9b08e1754b7c171bf`.

## 21. Prospective estimation-first analysis candidate — 2026-10-18

Because both retained confirmatory-test candidates failed their indivisible calibration
rules, no third procedure was searched merely to obtain a passing result. Instead, an
outcome-blind estimation-first candidate now specifies what could be reported if the
researcher later adopts it before any independent-cohort output or label is inspected. It
is not a Protocol v1.1 amendment, confirmatory freeze, cohort authorization, or claim that
the independent cohort already exists.

The candidate retains all 11 contrast definitions. C3−C0 is the designated lead reporting
estimand but receives no privileged test or decision rule; both neutral-control contrasts
remain inactive without prospective semantic adoption. Its conditional target is only the
eventual realized, prospectively frozen 96-case cohort: 48 purposively selected speakers,
two cases per speaker, and eight fixed template ancestors. It makes no broad speaker or
new-template population claim.

The hash-bound reference implementation applies signed contrast points or logical bounds at
the eligible-case level, averages both cases within speaker without deleting unknown cases,
and then weights all 48 speakers equally. It fails closed when a whole speaker or case is
missing. Every active contrast must retain complete denominators, missingness reasons, full
semantic-category distributions, and direction and magnitude. Complete-pair estimates and
template leave-one-ancestor-out ranges may be labeled only as sensitivities. No p-value,
rejection, significance, equivalence, no-effect decision, calibrated confidence interval,
or unspecified interval-like procedure is authorized.

Artifact `independent_validation_estimation_candidate_v1.json` has SHA-256
`f8ea664882304c7a5ef9c5690e4374bd34f2764a3d8958a1d395f171b735a9ee`.
Six focused tests cover the fixed family, fail-closed calibration dependency, missing-cell
bounds, equal-speaker aggregation, whole-speaker omission, exclusive creation, and exact
archived reproduction. The source and test SHA-256 values are
`1cf817238f7041e276c55484ea49b4d1f7187cae85e375967e17b5e97f1ddfb4` and
`c8e479d923fec3796677b8eede1d4816edfa38fd2734d38b591426156206cff9`.
No generation, inference, annotation, gate, ledger, or frozen historical evidence changed.

## 22. Two-human semantic calibration readiness — 2026-10-18

The existing 16-response pointwise package was designed for one reviewer and cannot
establish inter-rater agreement. An additive calibration package now creates two local,
Git-ignored reviewer deliveries from the same immutable blank instrument. R1 and R2 receive
the same anonymous response set in two separately seeded fixed orders. Neither delivery
contains the protected mapping, model/condition identities, automatic or AI labels, or the
other reviewer's labels. Both remain unassigned with zero completed labels.

The prospective contract distinguishes unavailable human review from a completed semantic
`UNCERTAIN` judgment, requires answer spans for value-bearing states, and binds reviewer
provenance. Analysis requires two distinct external humans who attest that they did not
create the items or rubric, had no prior output or mapping exposure, saw no other-rater or
adjudication material before lock, and used no generative-AI assistance. Initial reviews are
hash-locked before any unblinding and are never overwritten by later adjudication.

The public hash-only preparation plan has SHA-256
`b6881b1ba7e8f730836ad83c0060457cce308cfff5c523f6eb4b4c9cb425a7e0`.
It exposes no response text, anonymous IDs, mapping IDs, rationale, reviewer identity, or
label. Preparation source and test SHA-256 values are
`4caa3f8ba4a79866ad76d0dfd17adecea08fa1ab994a079d17ac208d52bdbeca`
and `17e0437b94d08527b3ce471cae6bb67d00fe01d9c352f98eaaab09d0dcaafcf5`.

A separate aggregate-only analyzer is ready but has not been run on human input. It first
revalidates both immutable deliveries, completed files and provenance records, then reports
coverage, fixed 7×7 answer-state and 3×3 completeness matrices, raw exact agreement,
nominal Cohen kappa with explicit undefined states, and descriptive eligible-span exact
agreement. It publishes no record text, label rows, IDs, spans, rationales or reviewer
identities and has no acceptance threshold. The zero-result readiness receipt has SHA-256
`f3e099d0bc49bdbd8639494ea3fe714a856782ee4d1841cf0ed7a01df80959dd`;
analyzer source and test hashes are
`e112defd9feccd36f3bdc76b6c65d8a305d41f83fc2ec0a47a881bfd4318fd3e`
and `9658402be9dacacc989fbf5071641176e4e661c030b1ae725cebd6f2d9ffce57`.
The four-file semantic slice passed 15/15 tests.

This is development-instrument calibration only. No humans were recruited, no label or
agreement result exists, and 16 sparse categorical items may produce unstable or undefined
kappa. It does not validate the four reliability axes, Persona Fidelity, neutral controls,
independent replication, or any frozen model gate.

## 23. Candidate 2 execution and bounded-screen result — 2026-10-18

Three passive observations after the research-priority amendment measured 5,651,648,512,
5,643,354,112 and 5,644,156,928 available physical bytes. This crossed the unchanged
5,368,709,120-byte Candidate 2 threshold and supplied a material-change reason for exactly
one new official preflight. No user application was terminated. Versioned preflight v4 then
revalidated the frozen Qwen2.5-3B-Instruct Q4_K_M model, GGUF SHA-256
`626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`, native
tokenizer, llama.cpp backend, prompt materialization, generation settings, authorization
ledger and source hashes. Its gate observation was 5,675,884,544 available bytes, and it
passed the unchanged 5 GiB requirement. The preflight receipt SHA-256 is
`ca96e25002d5c78f9bf3f15ea6ad0412032bc2ebb3df9adc5b62723417cc9c2d`.

Exactly one frozen Candidate 2 batch then executed all eight requests. There were eight
attempts, eight completed results, no retries and no unresolved in-flight request. The
frozen automatic endpoint classified two `CURRENT_VALUE_ADOPTION`, three
`OUTDATED_VALUE_ADOPTION` and three `UNVERIFIABLE_ANSWER` records. Candidate 2 therefore
scored **2/8** against the unchanged **7/8** qualification threshold. The byte-preserved run
receipt has SHA-256
`f9140b58adfcf68e57543cc2452798fc7ac5e9499946fe62f2aeb2a0dc5523e7`.
It records 94.08076140000139 seconds of Candidate 2 completion inference.

Replay audit verified eight immutable attempt files, eight raw HTTP completions, eight
result files, prompt/order bindings, raw-output hashes, automatic rescoring, postflight and
source snapshots. Its status is `PASS`, its decision is `proceed: false`, and its SHA-256 is
`e1d2718bd1c5fdd1395329d736ea581c7c03cfdd00d1de8b63bd5a5d771f0984`.
Applying the prospectively frozen two-candidate rule produced
`BOUNDED_SCREEN_NEGATIVE` with no selected candidate; selection receipt SHA-256 is
`362fcac650cc8fe286ac5ade0c5a35fab7ef6d862c0214724b439d0bd8848b7e`.

Autonomous use is now 16/1,200 generations and 159.95704690001094/72,000 recorded
completion-inference seconds, leaving 1,184 generations and 71,840.04295309998 seconds.
The historical P1 ledger remains separately 80/160 and untouched. Because no candidate
qualified, the disjoint C0 pilot and its 72-request continuation are not authorized and no
S/F/H effect is estimable. The 2/8 result is an actual negative development-screen finding
for this exact model-plus-native-template configuration under the frozen automatic endpoint;
it is not independent validation, a broad model-capability claim, a Persona Fidelity result,
or evidence about factorial Style/Facts/History causality. Genuine blinded semantic review
remains necessary to characterize endpoint coverage, but cannot retroactively change the
registered 2/8 gate.

An additive analysis-reproduction workflow replayed both ignored local run journals without
network access, model loading, or generation. It independently reconstructed 8/8 attempts,
HTTP completions and results for each candidate, the 1/8 and 2/8 frozen scores, the bounded
negative selection, both authorization ledgers, and the 159.95704690001094-second aggregate.
The public-safe aggregate receipt is
`analysis_reproduction_v2.json` (SHA-256
`e76cead21a92cc3fa67175f09624c9b401429713a19078144a16bf960967cdbe`);
full reproduction by a public clone remains partial because model weights and raw journals
are not embedded. The additive current-state checkpoint is
`post_candidate2_research_state_v1.json` (SHA-256
`1489732ce936860d46fa0001bf1edc2328b65c3f7b5cde386563644558fbba65`).
The earlier state and restart handoff remain byte-identical. The final focused evidence,
historical-snapshot, semantic-readiness, evaluator-validity and literature checks passed
82/82; the regression receipt SHA-256 is
`0cb3d586d6761b7f04ef511c32f62a73357547aa2cf72c9aaa271aa68a31a17b`.
