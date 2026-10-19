# Evidence-State-Constrained Persona Conditioning — candidate v1

Maintainer: Yaxin ZHENG. Phase P6, with P5 failure localization; RQ2/4. **Research hypothesis and engineering scaffold, not a verified original algorithm.** No training or algorithm-generation experiment has been executed.

## Observed Failure Modes

The eight Instruct H_none outputs include correct complete answers, complete wrong-period answers, a false assertion that an in-year date is outside the ledger, a volunteer-role denial and an incomplete chained answer. These AI-assisted interpretations remain unconfirmed. They occur without additional historical quotations and therefore do not establish persona-history interference. Earlier development records distinguish supported intermediate facts from successful task delivery. The first unresolved question is whether sufficient retrieved evidence is usable by this model/configuration, not whether a new admission algorithm is needed.

## Existing Methods and Published Prior Art

The [v7 novelty matrix](related_work_novelty_matrix_monitor_v7.md) is part of this specification. Temporal typed provenance, conflict invalidation, memory admission, persona/evidence separation and component verification all have direct prior art. The closest structural precedents are Zep, Mem0 and FC/PS admission; FPPS, LongMemEval, CoVe and RARR are mandatory relevant comparators. Typed fields, deterministic gates or a new acronym do not establish novelty. The present code does not reproduce any of their full model-based pipelines.

## Formal candidate and Potential Algorithmic Improvements

Let `x=(q,E,S,F,H,tq,ta)` denote question, trusted evidence, style, personal facts, history, requested time and evidence-availability cutoff (when such a cutoff is part of the task). An evidence atom is

`a=(source, entity, attribute, value, [valid_from,valid_to], asserted_at, provenance, trust_priority, uncertainty, conflicts)`.

Requested time and assertion time are distinct. A later assertion can describe a valid historical interval; an explicitly specified knowledge-as-of task adds a separate assertion-time constraint. Source trust comes from the externally assigned channel, not from an untrusted history sentence claiming higher priority.

For component `k=(entity,attribute,tq)`, define `W_k(E)` as the trusted atoms matching entity/attribute whose validity interval contains tq (and availability cutoff when applicable). Empty support yields Unverifiable; incompatible supported values yield CONFLICT_UNRESOLVED, not an arbitrary newest-value choice. Conflicting trusted evidence is a P5/Track B stress test outside ordinary Track A sufficiency assumptions. Do not silently repair the trusted ledger.

Admission `G(q,E,S,F,H)` retains S and eligible behavioral preferences as distinct channels. History can be answer-supporting, dated non-authoritative archival content, quarantined conflict, or uncertain. Supplied unstructured personal facts remain pending scope checks; the prototype does not pretend to solve their semantic classification. Relevant historical facts outside tq are not globally false and need not be deleted from persona memory. Final factual support remains anchored to E.

Verification `V(E,K,C(y))` maps each structured candidate claim to support/contradiction/uncertainty and separately maps required components to present/supported. A promise, a correct intermediate step, an explicit refusal and a final answer are different speech acts. Claim extraction `C` is an unresolved input to the current scaffold; using author metadata is privileged and its cost/errors cannot be omitted from a deployable comparison. Explicit abstention remains an outcome, including unnecessary abstention when sufficient evidence exists.

For algorithm A, evaluate the vector

`(Relevance, FactualConsistency, TemporalConsistency, Coherence, LinguisticFidelity, BehavioralFidelity)`

and separately task success, component coverage, abstention, boundaries, latency and RAM. Seek Pareto improvements subject to `CPU(A) <= B`, with prospectively justified fidelity non-inferiority margins if used. No arbitrary weighted scalar is optimized. Filtering all persona information is a required trivial baseline, not an acceptable undocumented way to claim personalized improvement.

An unresolved candidate question is whether uncertainty-aware support certificates can preserve useful persona content while preventing unsupported answer components under a bounded CPU budget. A concrete future distinction would require a proved or independently demonstrated uncertainty/calibration or cost advantage beyond the same typed declarative rules and published admission policies. **No such distinction has been established here.**

## Validation Feasibility

`tools/escp_offline.py` implements typed intervals, trusted-channel ownership, conservative conflict handling, archive/admission channels and component-level witnesses. Sixteen authored adversarial fixtures cover entity/time errors, valid historical answers, conflicting E, unknown intervals, duplicates, negation, unsupported additions, promise-only delivery, partial tasks and abstention. They are development specifications, not independent ground truth. Four ablations remove entity, time, conflict or delivery checks. A separately written simple declarative reference receives identical structured information.

The full scaffold and declarative reference both match all 16 authored expectations. Entity/time/conflict/delivery ablations match 13/12/15/15 respectively. This is a **negative novelty result**: straightforward established rules suffice on these fixtures. Feature/channel retention is not measured generated Persona Fidelity. Initial timing includes coarse Windows CPU-clock zeros; those are below-resolution observations, not zero computational cost. Longer bounded batches (10,000 repetitions × 16 fixtures × 3 batches) give median process CPU time about 6.05 microseconds per scaffold check versus 1.07 microseconds for the boolean reference. The scaffold produces additional diagnostics, so output workloads differ; no speed advantage is demonstrated. Parsing, model inference and repair costs are excluded and must be included in later comparisons.

Fair baseline ladder: no persona; full history; history removal retaining S/F; seeded random admission; lexical overlap; BM25; entity/time filtering; evidence-priority prompting; structured component verification; faithful published methods or explicitly named adaptations. Existing same-cardinality BM25/time/entity development records are retained rather than rerun. Equal context/candidate budgets and full end-to-end cost are required. FPPS needs activation/probe infrastructure; CoVe/RARR need extra generations; no proxy is labeled a reproduction. The simple declarative checker is the strongest equal-information baseline for this offline typed-input task.

Next falsification: if ordinary retrieval plus checking matches every proposed reliability/fidelity/cost advantage, reject the new-method claim. If oracle evidence does not yield answer headroom, do not infer a memory-selector bottleneck. If improvement disappears under independently adjudicated boundaries, report measurement dependence. If filtering degrades linguistic/behavioral fidelity beyond the prospectively set margin, the multi-objective goal fails. All candidate tuning must use development material; independent cases remain unavailable for optimization.

## Publication Value

Current contribution level: engineering scaffold and exploratory configuration observations. No replicated mechanism, known-method inadequacy or independently supported algorithm exists. A useful empirical paper remains possible through independently validated S/F/H effects or informative nulls, measurement robustness and fidelity/cost tradeoffs. Algorithm superiority is neither a prerequisite for that paper nor supported by these authored tests.
