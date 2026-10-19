# PersonaSLM P1d core alignment and next scientific decision packet v1

Maintainer: Yaxin ZHENG. AI-assisted scientific recommendations, not human adoption. This single packet closes the already authorized Instruct feasibility scope and proposes one bounded next inference. It does not reopen approved P1d design targets or adopt v1.2.

## Verified result and recommendation

Eight Instruct requests were **newly executed exactly once** after exact manifest/model/native-token/backend preflight: 8 successful, 0 failed, 7 native EOS, 1 budget termination. Mean latency 20.808s; observed process peak working set 2689376256 bytes. Raw run is `results/p1d_instruct_smoke/development_v1/runs/20261014T160641-ca4d1cf9e0fd433e81d9c9d2bed924b3`. Complete engineering and scientific reports are `P1d_instruct_feasibility_engineering_report_v1.md` and `P1d_instruct_feasibility_scientific_report_v1.md`.

AI proposals: five complete requested-answer forms, two nonanswers, one partial; two correct complete tasks; 8/14 requested components present and 3/14 supported. Seven finished utterances are not seven complete task answers. The registered strict eight-case gate fails. Cleo's role-denial factual scope has an explicit Incorrect/Unverifiable alternative; either choice leaves the feasibility decision unchanged. All eight judgments remain unconfirmed. Human review can use `docs/validation/p1d/instruct_smoke_v1/measurement_v1/independent_review_without_scores_v1.csv` without AI scores; adopting proposals would not constitute independent second-human annotation.

Original parser labels remain seven AMBIGUOUS and one TRUNCATED. Native `eos` versus expected `eog` is a separately documented compatibility issue, not a new structural reclassification or evidence of factual failure. Eight identifiable candidate spans are not independent boundary truth.

## Exact scientific status

| Readiness dimension | Status and required resolution |
| --- | --- |
| Instruct technical feasibility | PASS for the eight development prompts; local model/backend/template/tokenizer verified. Third-party source conversion lineage still partial |
| Model/task measurement adequacy | NO-GO: strict answer-completeness criterion fails. No universal model-family failure inferred |
| Core S/F/H | Alignment and exact proposed weights restored; no new full-factorial inference. H_none includes persona/style and is not C0 |
| Candidate stimulus/control validity | Existing 288 VALID_WITH_LIMITATIONS remain AI proposals; procedural controls diagnostic only. Reuse the existing 64-case/64-control stratified review packet |
| Independence/precision | 144 names, 288 cases, 247 question strings, 16 templates and four ancestors; conditional scope or prospective diversification needed. Existing simulations retained, not empirical ICC estimates |
| Fidelity/independent measurement | Three authored profiles, 12 counterexamples and blind forms prepared; no independent human validation or behavioral ratings yet |
| Scientific model policy | Original P1d allocation unchanged. A primary-model, output-policy or core-factorial amendment requires a concrete later decision; it is not adopted by this packet |
| Main inference authorization | NO-GO for 1,728 Base + 288 Instruct; none executed. Confirmatory materials are not frozen as validated data |

## One proposed next inference decision

**Recommended: AUTHORIZE_P5_ORACLE_8_WITH_LIMITATIONS**, or **DEFER_P5_ORACLE_8**.

Manifest: `docs/validation/p5/oracle_evidence_proposed_v1/oracle_evidence_manifest_proposed_v1.json`

SHA-256: `894b7f0604f1f4c6121c1aefa1e24ee25c59a12c9e5be687e6403d9066d3c08e`

Scope: exactly eight existing development cases, H_none, one generation per case, same completed Instruct model/template/seed/order/96-token configuration, CPU4/context4096, no retries/warmup, 45-minute ceiling. Maximum 768 new output tokens. The eight new prompts replace only the trusted-ledger block with its minimal answer-sufficient source chain. Full-ledger Instruct references are reused, never regenerated. Native tokenizer arrays match the official tokenizer, with 182–303 input tokens. No validation case, training, algorithm-effect comparison or additional generation is included. Model hash remains `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`; backend hash `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`.

Scientific purpose: RQ4/P5 oracle generation headroom before attempting a new selector. Removing distractor rows changes evidence length, positions and candidate content jointly; the result identifies an oracle evidence **package**, not a pure retrieval mechanism or persona effect. Source-line and reference equality are checked. The oracle uses known reference witnesses and is not a deployable algorithm. Partial third-party GGUF lineage must remain explicitly accepted for this bounded diagnostic only.

Prespecified strict gate: eight identifiable, complete task answers with no answer-losing cut; separately report factual/temporal support, components and fidelity opportunity. Failure retains NO-GO and motivates targeted model/task-policy reconsideration, not an automatic sweep. Success only supports a separately proposed selection/all-condition development study. It cannot authorize the full validation cohort or silently reduce evidence in the adopted Track A design.

Approval would authorize only this exact eight-request P5 manifest. Deferral leaves it unexecuted; offline measurement/baseline/manuscript work remains available. The mandatory gate follows the researcher's explicit exclusion of future-phase inference from the current eight-request authorization. No software-enum change or completed engineering stage creates a new gate.

## Bound files

| File/version | SHA-256 |
| --- | --- |
| `docs/validation/p1d/instruct_smoke_v1/frozen_manifest_v1.json` | `ba63c30a9868b94b47f8f79dd774ac0627d56113810ffd4db08eb63af0374b91` |
| `docs/validation/p1d/instruct_smoke_v1/researcher_authorization_v1.json` | `6003b6f24790c0c6373a78557aa39ae61b71935101e05a22f109d62b32715537` |
| `docs/validation/p1d/instruct_smoke_v1/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv` | `9bd8447edc39c417cd96edcd06e1adecc8b0b68b16ab705a91639b0feb032246` |
| `docs/validation/p1d/instruct_smoke_v1/measurement_v1/AI_proposals_UNCONFIRMED_v1.json` | `01628344bace70d1abf69564e30c50583f422cc96eb8a6b4b4c931ba2e21f7aa` |
| `docs/validation/p1d/instruct_smoke_v1/measurement_v1/boundary_alias_sensitivity_v1.json` | `a5f643a0f55f23940416df67ee1fc81623ac18723c38091fb3c2257980422068` |
| `docs/validation/p5/oracle_evidence_proposed_v1/oracle_evidence_manifest_proposed_v1.json` | `894b7f0604f1f4c6121c1aefa1e24ee25c59a12c9e5be687e6403d9066d3c08e` |
| `docs/PersonaSLM_research_programme_alignment_v1.md` | `322783947aeca5533de62eccbf1d52d25634713b9ad5eb0247b26d520bf4bf24` |
| `docs/PersonaSLM_persona_fidelity_measurement_v1.md` | `6890270eb6932872e51dd63e0a6198f22e9f9baa9042d8b0c6244032ee753e63` |
| `docs/ESCP_candidate_specification_v1.md` | `23439ab4dab7d0a9af28ca38f49c216d4737a54c5c4d35a82c040ad4cf93c2a1` |

The original Instruct approval is already registered and exhausted; do not ask for it again. Broad material adoption, independent annotation and confirmatory freezing are future substantive requirements, not approvals fabricated here. A conditional 64-request S/F/H development sketch exists in the alignment report but is neither execution-ready nor requested now.

## Algorithm and publication consequences

ESCP is a typed offline scaffold with 16 authored fixtures, four ablations and a simple equal-information reference. Both full methods match 16/16 expectations; the scaffold adds diagnostics and costs more CPU per typed check. No generated reliability or persona gain, originality, independent algorithm validation or publication readiness follows. The closest prior-art overlap is explicit in novelty matrix v7. The empirical paper path remains independent S/F/H evidence with reliable fidelity measurement, transparent uncertainty and useful null/adverse findings. PLOS ONE remains the first target.

Scoped regression results, raw source hashes, historical preservation and precise changed-file inventory are bound in `validation/p1d/instruct_smoke_v1/reproducibility_manifest_v1.json`; the file intentionally does not contain its own digest.
