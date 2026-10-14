# P1d algorithmic development and prior art — v1

Maintainer: Yaxin ZHENG. Empirical research remains primary. No new inference, model training or independently validated algorithm is reported.

## 1. Observed Failure Modes

**Temporal/entity selection:** P1b/P1c contain dated/entity errors and semantic ambiguity; a wrong entity is not automatically a wrong interval. **History admission:** the current E/V materials vary source identity, value and interval, so they cannot identify a unique memory-selection failure. **Persona–evidence separation:** P1d has no outputs yet; the persona-fidelity tradeoff is unmeasured. **Answer components:** P1b contains supported partial answers; P1c does not empirically separate factual/task labels. **Boundaries:** P1c retains eight unresolved primary boundaries, including both EOS terminations. **Interaction-aware routing:** P1c contrasts are uncertain and boundary-sensitive, not replicated adaptive-conditioning evidence.

The new historical diagnostic exposed a separate engineering error: identical raw strings are not unique request identities. The corrected identity join restores existing counts. The scoring-contract review also prevents interpreting a verifier's abstention-associated false boolean as an official task Failure. Neither is a newly discovered model mechanism.

## 2. Existing Methods and Published Prior Art

The [ten-paper full-method comparison](related_work_novelty_matrix_monitor_v4.md) remains the detailed source record; the [focused update](validation/p1d/scientific_validation_v1/related_work_monitor_delta_v5.json) records this review's narrower checks.

- [LongMemEval](https://arxiv.org/html/2410.10813v2), Sections 5.4 and D, already evaluates timestamped indexing, query time-range extraction and filtering. Its smaller reader can fail at range extraction; a deterministic explicit-date join is a limited baseline, not a replacement or novel temporal algorithm.
- [When Personalization Misleads / FPPS](https://aclanthology.org/2026.findings-acl.395/) is published in Findings of ACL 2026. Its activation steering directly overlaps factuality-preserving personalization. An evidence-priority prompt is not FPPS replication; the current GGUF HTTP workflow does not supply the requisite steering/probing implementation.
- [What to Admit and How to Present](https://arxiv.org/html/2610.11188v1) is treated as a preprint. Factual and persona-consistency admission and controlled presentation overlap the proposed relevance-gating direction. Its adjudication cost and large-model assumptions must be accounted for in an SLM adaptation.
- [Chain-of-Verification](https://aclanthology.org/2024.findings-acl.212/) and [RARR](https://aclanthology.org/2023.acl-long.910/) already verify and revise generated claims. Extra generation, retrieval and revision budgets differ from a supplied-claim checker; no fair performance comparison has yet occurred.
- Native EOS, official conversation templates, deterministic stops/role parsing and structured decoding are established boundary techniques. Offline extraction cannot measure the generation effect of a chat template or stop sequence. Persistent Personas?, TwinVoice, Wiki-Talkie and Decoupling Logic from Persona remain covered by the existing matrix; their publication-status and scope qualifications are retained, not upgraded.

## 3. Potential Algorithmic Improvements

Temporal processing should first compare requested-time filtering with entity-plus-time selection and explicit asserted-time verification. History gating should compare all-history, removal, lexical selection and established admission approaches at matched budgets. Persona separation requires fidelity-preserving controls rather than simply deleting persona information. Component checking should distinguish delivered supported requirements from a factually correct fragment. Boundary processing should permit abstention/multiple spans instead of forcing every heading into a role transition. Interaction-aware routing remains deferred until a reproducible interaction warrants it.

The existing `p1d_verifier_date_scope.py` prototype separates asserted time from requested-time delivery on development-only structured fixtures. The new `p1d_metric_contracts.py` is an uncertainty-preserving measurement adaptation with independent evidence inputs. Both are **known-method engineering adaptations**. No gap against the strongest applicable published system has been demonstrated; a new method name or component combination would not establish originality.

## 4. Validation Feasibility

The earlier 13 authored verifier fixtures and ablations remain preserved (old checker 8/13 specification matches; corrected checker 13/13). The new eight construct-contract fixtures are additional software checks, not independent accuracy. No future candidate answers or outputs were used to tune these algorithms. Previously measured checker CPU excludes extraction, model calls and full process RAM; it cannot establish end-to-end efficiency.

Required next evidence is independently labeled free-text claims, date/entity attribution and boundary spans on development material, followed by a separate held-out evaluation. Compare damage to already correct answers, complete delivery, temporal/factual labels, narrow persona fidelity, abstention and CPU/RAM at equal candidate-generation budgets. For FPPS/CoVe/RARR or memory-admission adaptations, document omitted components and extra calls. A supplied structured claim is not a realistic free-text extraction benchmark. None of these generation studies is authorized now.

## 5. Publication Value

Current contributions are measurement safeguards and a controlled empirical plan, not an original algorithm. The most informative next algorithmic step is independent boundary/claim annotation followed by strong simple baseline evaluation; further rule tuning on the eight inspected P1c prefixes would overstate progress. If existing methods solve the failures, retain that negative novelty result. PLOS ONE relevance depends on valid scientific identification, independent evidence and transparent measurement; no acceptance or readiness claim follows from software tests.
