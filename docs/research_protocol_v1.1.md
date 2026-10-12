# Research Protocol v1.1 — Research Design Freeze

**Working title:** Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models

**Status (2026-10-12):** Research-design freeze only. This is **not** a confirmatory experiment pre-registration. The final model selection, sample size, primary endpoints/contrasts, adjudication thresholds, sampling, and locked-test inventory require a *Confirmatory Experiment Freeze* after P0 and the pilot. Amendments require a dated changelog entry and justification.

## Research scope and hypotheses

Primary task: model a target speaker's responses to new conversations based on speaker-specific linguistic behavior and past dialogue. Models: ~0.8B–3B. CPU-only inference is a **fixed deployment setting**, not a causal treatment. Do not interpret synthetic personas as evidence for real-speaker fidelity.

**RQ1:** How does persona conditioning change response relevance, factual consistency, temporal consistency, and conversational coherence?

**RQ2:** How do linguistic style (S), supplementary personal facts (F), and controlled history presentation (H), independently and jointly, affect those outcomes?

**RQ3:** How do effects vary with model size, post-training and available context budget?

**RQ4:** Where do *observable* failures arise in retrieval, generation, selection and post-processing, and what headroom is indicated by diagnostic oracle interventions? No unsupported causal attribution from pipeline logs alone.

**Separate construct:** Persona Fidelity. Measure linguistic and behavioral fidelity independently from all reliability dimensions. Never include fidelity in a composite reliability score by default.

## Tracks, sources and population

**Track A: interference under shared evidence.** Every treatment condition receives identical, correctly dated, task-sufficient trusted evidence. S/F/H introduce **additional** information, not missing answers. Include neutral, length-matched placebo controls (N_style and N_history) to probe context-length/format effects.

**Track B: knowledge utilization.** Explicitly manipulate information availability (no memory, correct, stale, conflicting, oracle). Analyze separately from Track A. Do not describe missing-evidence failures as persona interference.

**Controlled synthetic tier:** internally valid factor manipulation with invented speakers/facts and script-generated test items. **Naturalistic tier:** authorized real-speaker history, temporally split; independent evaluation and privacy safeguards. **Existing public benchmarks:** auxiliary external comparisons, not assumed equivalent to real-speaker modeling.

## Controlled treatments and estimands

For Track A the S/F/H factors each take values in {0,1}, yielding the eight factorial combinations:

| ID | S | F | H |
|---|---:|---:|---:|
| C0 | 0 | 0 | 0 |
| C1 | 1 | 0 | 0 |
| C2 | 0 | 1 | 0 |
| C3 | 0 | 0 | 1 |
| C4 | 1 | 1 | 0 |
| C5 | 1 | 0 | 1 |
| C6 | 0 | 1 | 1 |
| C7 | 1 | 1 | 1 |

Operationalize **H** as the presentation of controlled, date-stamped dialogue history rather than uncontrolled raw logs. History and linguistic style cannot be made perfectly orthogonal in natural data. Manipulation checks must document remaining residual differences. Match additional tokens *after the actual model tokenizer and final prompt template*, and document evidence location. No factorial interpretation when interventions inadvertently disclose different answers.

**Preliminary primary contrasts** (to finalize after pilot): C1–C0 (simple style effect with F=H=0); C3–C0 (simple history effect with S=F=0); C1–N_style (style against token-matched neutral text); C3–N_history (history against length/format-matched placebo). These are **simple contrasts** and do not estimate average factorial main effects.

The balanced, equal-cell-weight **style average main effect** is

\[\Delta_S=\tfrac14 \sum_{f,h\in\{0,1\}}\bigl(E[Y\mid S=1,F=f,H=h]-E[Y\mid S=0,F=f,H=h]\bigr).\]

Report F and H analogously and factorial interactions as secondary, explicitly different estimands. If imbalanced or missing cells, predeclare weighting and analysis before locked testing. Preselect primary outcomes, contrast family and multiplicity policy (e.g., Holm) by confirmatory freeze; do not retroactively declare significance.

## Outcome applicability and evaluation

Four separate reliability endpoints: **Response Relevance** (appropriate reply to the latest turn), **Factual Consistency** (supported by trusted facts valid at evaluation time), **Temporal Consistency** (correct before/after and updated facts), **Conversational Coherence** (plausible relation to the *fixed* preceding turns). Overlap between factual and temporal errors is permitted and must be explicitly counted, not assumed independent.

A per-case, per-endpoint *applicability matrix* must be frozen **before** any generation; use N/A instead of silently counting as right/wrong. Primary denominator: all pre-eligible locked cases, not cases chosen after inspecting C0. `P(C1 wrong | C0 correct)` may be reported as secondary paired description only. Automated factual checks must reject negation and conflicting extra answers; open-ended judgments require blinded adjudication.

Persona Fidelity: **linguistic** (lexical habits, rhythm, punctuation etc.) and **behavioral** (response patterns across situations). Use independent blind evaluation, not an in-house scorer trained from the same outputs alone. Report inter-annotator agreement.

**Multi-turn coherence:** main benchmark uses fixed, prewritten context histories identical across conditions. Free-running interactive conversations are a separate exploratory protocol, because their trajectories diverge after each model reply.

## Models and inference controls

CPU-only local GGUF inference via a separately started llama.cpp service; initially Qwen-family 0.8B/2B Base. Add post-trained and cross-family conditions later with correct model-specific templates. Record file SHA-256, engine revision, tokenizer, GGUF quantization, CPU, OS, threads, context capacity, actual prompt tokens, decoding parameters, seed, latency and memory. A fixed seed does **not** guarantee byte-identical outputs across platforms/backends; distinguish reproducible specifications from deterministic outputs.

**Every answer** logs raw model output, token IDs if endpoint supports them, termination/stop reason, parsed output and any subsequent filtering decision. A parser can produce emptiness that must not be attributed to the model. Forced stopping is an inference intervention and must be tracked.

## Error localization

Log evidence presence and temporal validity; candidate-level answer quality; selection index; parser transformations. Use **Oracle Retrieval** and **Oracle Selection** as *diagnostic intervention/headroom estimates*, not automatically causal allocations of blame. They alter evidence or selection distributions. Measure Evidence Recall@K, Candidate Coverage@K, Final Answer Accuracy, raw/parsed empty rates, and CPU end-to-end cost separately.

## Research execution and freeze schedule

- **P0 — Pipeline / Parser Validation:** schema, synthetic fixtures, evidence preservation, manipulation checks, correct tokenizer accounting, distinguish raw empty/EOS/stop truncation/parser deletion, unit tests and provenance. No research effect claims.
- **P1 — Controlled Factorial Pilot:** Track A S/F/H and neutral controls; refine stimuli using development data.
- **P2 — Knowledge Utilization:** Track B no / correct / stale / conflicting / oracle evidence.
- **P3 — Model & Context Sensitivity:** model scales, Base/post-trained, controlled context budgets and CPU metrics.
- **P4 — Naturalistic Validation:** legally authorized real-speaker conversations, chronological splits, independent annotations.
- **P5 — Pipeline Diagnostics:** oracle retrieval/selection and parsing audit with shared candidate pools.
- **P6 — Optional Method / LoRA:** only if earlier evidence identifies a target bottleneck; separately audit training labels, masks, EOS and train/inference formatting.

**Freeze #1 — Research Design (now):** title, RQs, scope, tracks, endpoints, fidelity separation, CPU constraint. **Freeze #2 — Confirmatory (after P0+pilot):** final data and models, test sets, intervention implementations, primary contrasts/endpoints, sample size, seeds, annotation procedures, statistical test and exclusions. Never tune against the locked test set.

## Statistics, privacy and research integrity

Use paired cases under identical conditions. Account for clustering by persona: many questions do not imply many independent people. Cluster-aware bootstrap or hierarchical approaches should be considered where speaker count supports them, with honest uncertainty for small numbers of speakers. Control multiplicity for declared confirmatory comparisons. Preserve null and mixed results.

Synthetic P0 uses no personal data. No commercial MimooPet files, models or code are imported or linked. The independent research root must have no junctions/symlinks outside its subtree and should not commit private data. Authorized naturalistic data requires a documented lawful basis/permissions, minimization, retention and dissemination plan. The protocol and factorial design alone are not novel scientific contributions; novelty requires robust findings, boundary conditions or validated evaluative methods.

## Changelog

- 2026-10-12 — v1.1: Explicit estimands; neutral matching; pre-generation metric applicability; fixed versus free-running multi-turn; parser audit moved to P0; two freeze checkpoints.

- 2026-10-12 — Prospective [English language-scope addendum](research_protocol_v1.1_language_scope_addendum.md), requested by the researcher. Protocol v1.1 objectives, factors and evaluation procedures are unchanged; completed P0 artifacts are not rewritten.
