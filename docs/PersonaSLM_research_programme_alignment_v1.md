# PersonaSLM research programme alignment v1

Maintainer: Yaxin ZHENG. AI-assisted prospective synthesis, not a new adopted protocol. Official paper title: **Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**. First submission target: PLOS ONE.

## Governing scope

Protocol v1.1 remains the frozen research-design baseline, explicitly distinct from a confirmatory experiment freeze. `PersonaSLM_Research_Protocol_v1.2_Proposed.md` remains proposed. The registered P1d Addendum v1 governs its scoped E/V plan, with 144 synthetic speakers, 288 paired cases, 1,728 Base and a matched-subset 288 Instruct targets. These targets are not execution authorization. This alignment neither replaces that plan nor retroactively changes any experiment.

Track A holds sufficient, valid, dated trusted evidence, question, reference answer and fixed context identical within each case. S/F/H add conditioning information. Track B (P2) independently varies evidence availability; it is never pooled with Track A. P5 oracle evidence is a headroom diagnostic outside the equal-evidence S/F/H contrast.

## Permanent work tree and evidence

| Branch | Question / scientific purpose | Current evidence and status | Missing requirement |
| --- | --- | --- | --- |
| P0 | Reproducible measurement infrastructure | PASS; historical evidence frozen | Maintain versioned contracts; new runtime aliases require separate compatibility validation |
| P1a | RQ1/2: initial S/F/H C0–C7 | Completed development exploration; prior eight-cell evidence retained | Independent replication and usable fidelity measurement |
| P1b | RQ1/2: complex tasks and answer delivery | 192 development generations, researcher-adopted AI-assisted ratings; supported intermediate facts can coexist with incomplete tasks | Independent task/template coverage; do not merge with P1c as independent units |
| P1c | RQ1/2/4: focused R/T/P diagnostics | 72 adopted annotations; 16 exploratory comparisons; boundary sensitivity retained | R/T estimates are package effects, small and uncertain; no pure mechanism |
| P1d | Independent empirical validation | Prospective E/V design adopted; 288 AI validity proposals, no confirmatory responses; **NO-GO** | Model/task adequacy, semantic/control review, fidelity, independent measurement, dependencies, final freeze and authorization |
| P2 | Track B knowledge utilization | No newly executed study; missing/correct/stale/conflicting/oracle evidence preparation only | Separate protocol, N/A rules and authorization; do not mislabel evidence absence as interference |
| P3 | RQ3: model/size/context configuration | Completed 144 Base budget, 16 Base format, now 8 Instruct development requests | Matched configuration study; quantization/template differences are not pure post-training |
| P4 | H5: real-speaker external validity | No real-speaker data collected here | Explicit lawful access, consent/permissions, minimization, temporal split, independent review and release plan |
| P5 | RQ4: retrieval/generation/selection/parser localization | Frozen raw/parsed comparisons; proposed eight-request oracle-evidence diagnostic, unexecuted | Authorize exact diagnostic; independent boundary truth; oracle headroom is not unique causal blame |
| P6 | Remedies, strong baselines, ablations | Existing retrieval/checking baselines plus new typed ESCP offline scaffold | Surviving residual gap, fair inference/cost/fidelity comparisons and independent data; no original method established |

The 144 budget requests did not change matched first replies. Sixteen Base format requests suppressed continuation without improving task delivery. Eight Instruct requests demonstrate some answer delivery but fail the registered strict feasibility gate. These are configuration-specific development findings, not universal Base or Instruct failure.

## RQ / hypothesis / estimand mapping

| Hypothesis | Core RQ and branches | Estimand and existing evidence | Falsification, alternatives and independent requirement |
| --- | --- | --- | --- |
| H1 Style × History | RQ1/2; P1a/P1b, future core P1d | At F=0: `[Y(C5)-Y(C3)]-[Y(C1)-Y(C0)]`. Existing development factorial observations motivate testing, not existence | A precise independent near-zero contrast weakens a meaningful interaction claim; length, realization and boundary changes are alternatives. New speaker/template blocks and full S/F/H coverage needed |
| H2 history mechanisms | RQ2/4; P1c and E/V P1d, P5 | R/T/P and E/V implemented package contrasts; no pure relevance, time or competition mechanism | Compare variants holding proposition/value or presentation fixed when possible; persistent bundles restrict interpretation. FPPS, LongMemEval and admission methods overlap |
| H3 structural/semantic divergence | RQ1/4; P0/P1b/P1c/P3/P5 | Separate boundary status, native stop, supported claims, delivery and extraction sensitivity | Independent adjudicated boundaries and matched raw/parsed effects; rule agreement alone is not accuracy. Known structure/semantics literature precludes blanket novelty |
| H4 prompt realization | RQ2/3; future core P1d/P3 | Within-factor semantic-equivalent realizations, assigned in balanced speaker/template blocks | Null narrow intervals or realization robustness may falsify material sensitivity; changed evidence or persona content invalidates a pure realization claim |
| H5 generalization boundary | RQ1–4; P1d/P3/P4 | Independent speakers, task families, templates, models and authorized naturalistic tier | Failure to transfer bounds the claim; synthetic names do not create linguistic independence. Real-person fidelity is absent from current evidence |

Reliability outcomes are Response Relevance, Factual Consistency, Temporal Consistency and Conversational Coherence. Task Success, required-component presence/support, structural status, Unverifiable/empty/repetition rates are separate. Linguistic and Behavioral Fidelity are separate again; latency/RAM are efficiency outcomes. No composite reliability/fidelity score is introduced.

## Exact treatment and contrast distinctions

`validation/research_alignment_v1/core_estimand_registry_proposed_v1.json` gives exact weights and preserves v1.1 routing: C0=000, C1=100, C2=010, C3=001, C4=110, C5=101, C6=011, C7=111 in S/F/H order. Main effects average four paired differences (weights ±1/4). Two-factor interactions average two differences-in-differences (±1/2). The three-factor interaction has ±1 weights. H1 at F=0 has weights `[1,-1,0,-1,0,1,0,0]`; it is not the F-averaged S×H effect.

C1−C0 and C3−C0 are simple effects with other factors absent. C1−N_style and C3−N_history concern particular controls whose semantic validity is unresolved; length matching is insufficient. None is interchangeable with a main effect. E/V contrasts preserve the adopted separate 16-comparison registry; P1c R/T and presentation diagnostics are not renamed S/F/H effects.

**Current H_none is not C0:** it retains a fictional persona/style profile and fixed dialogue. The eight-request Instruct run cannot estimate any persona effect. The present P1d E/V design partly addresses RQ1/2 under fixed S/F and historical packages; it cannot identify independent S or F effects, any complete S/F/H interaction, linguistic/behavioral fidelity, or all model-by-factor interactions. Its limited Instruct subset supports matched subset configuration comparisons only.

## Efficient prospective restoration, not automatic replacement

First resolve generation headroom and independent measurement. If adequacy is demonstrated, prepare a **separately authorized** development-only eight-case × eight-cell S/F/H study (64 requests) with true C0, semantically validated S/F/H, identical sufficient evidence and predeclared fidelity applicability. This is a conditional design sketch, not an executable manifest or current authorization. It does not follow automatically from the present failed gate. Add no token-matched neutral arm until its semantic role is reviewed.

For independent validation, propose a separate core-factorial addendum rather than silently modifying E/V. Construct genuinely new cases spanning task families, requested dates and speaker-specific linguistic/behavioral opportunities; cross independently authored templates with speakers rather than nesting each linguistic ancestor in one condition. Assign two legitimate realizations through balanced blocks. Keep all eight cells within case; balance evidence order independently of S/F/H. Choose the final sample from precision simulations for the actual primary contrast family, including H1 if adopted, not from P1c effects or existing E/V sample counts.

Candidate primary family: the v1.1 simple style/history contrasts on factual Incorrect-label incidence and task Success, with H1 nominated explicitly if scientifically prioritized; four reliability dimensions remain fully reported. Exact family and multiplicity must be approved before confirmatory freeze. Full-eligible-case categorical incidence, assessable-case correctness and supported complete tasks remain different estimands. Whole-speaker resampling, template/ancestor sensitivity, family strata, boundary uncertainty and unknown-outcome bounds remain necessary. Do not silently renormalize incomplete factorial cells.

The current E/V candidate bank remains unchanged: 247 question strings, 16 abstract templates, four construction ancestors. A conditional inference claim for these templates may be possible after other gates; general linguistic population inference is not established. Existing precision simulations are retained without rerun; their speaker assumptions do not estimate template ICCs. Reweighting names cannot repair construction dependence.
