# PersonaSLM — P1c targeted semantic and boundary audit (AI-assisted; UNCONFIRMED)

Maintainer of the research project: Yaxin ZHENG. Audit prepared for researcher review. **Not a human-independent annotation, not a frozen official rating, and not a confirmatory analysis.**

## Source integrity

- 72 primary proposal records, each with a unique anonymous response ID and 12 case IDs (6 outputs per case).
- 8 secondary boundary records, with immutable AMBIGUOUS source status.
- Source SHA-256 (primary CSV): `0b86587c9d09a4cc976f3bbcce05f1307dc79ec4065f32ab12118f46efa2bdc8`.
- Source SHA-256 (secondary CSV): `f0f5189f395b665ae5602367674a5912c700360b8adecae33112be61c3ea6ded`.
- Source SHA-256 (decision package): `62123ed0141c5c1b71d008dc1a1d2a77f0cb1b94fd2dd98bf5df7894a97c1586`.
- UTF-8 hashes of all 72 `raw_first_reply` fields match their stored `first_reply_sha256`; all 8 raw, original-candidate and proposed-prefix hashes match. All eight proposed prefixes are exactly contained at the specified leading spans. All 72 quoted trusted-evidence strings occur in the included trusted evidence. **These checks establish source integrity, not semantic truth.**
- All researcher/human score and confirmation fields were empty in the source. No researcher's approval has been inferred.

## Score distributions and denominator caveat

Primary Factual Consistency: Correct 43; Incorrect 20; Unverifiable 9. Primary Temporal Consistency: Correct 43; Incorrect 15; Unverifiable 14. Primary Task Success: 43 success; 20 failure; 9 unknown. Coverage: 44 at 1.0, 20 at 0.0, 8 unknown. Relevance/Coherence: 59 at 5, 5 at 4 and 8 unscorable each. Semantic completeness: 64 YES, 8 UNCERTAIN.

**Critical distinction:** 8 of 9 primary factual Unverifiable entries correspond to `AI_primary_unit_status=UNRESOLVED`, so they are *structural reply-unit uncertainty*, not eight supported examples of unverifiable model facts. Among the 64 provisionally evaluable first replies, factual results are 43 Correct, 20 Incorrect, 1 Unverifiable. On this same subgroup temporal results are 43 Correct, 15 Incorrect, 6 Unverifiable. Do not silently reclassify the frozen labels. Register `boundary_unresolved` in parallel and report denominators and identification/sensitivity bounds.

The eight secondary prefixes, if accepted **solely for sensitivity**, give four additional factual Correct and four additional Incorrect (therefore 47 Correct, 24 Incorrect, 1 remaining Unverifiable on the 72-row denominator). Secondary temporal outcomes include 4 Correct, 1 Incorrect and 3 Unverifiable, giving 47 Correct, 16 Incorrect and 9 Unverifiable; these are alternative analyses, not the primary view.

## Specific scientific questions

1. **PC004:** The reference says destination room **Cobalt**, while the output calls it *Cobalt collection desk*. `Correct` is defensible for the requested value only if the wording is a harmless alias; otherwise an unsupported attribute claim needs separate coding. Obtain an explicit researcher wording interpretation.
2. **PC006:** The output states *on Thursday, 2042-12-15*; the schedule's **service day** is Thursday, but the Gregorian calendar day for **2042-12-15 is Monday**. Treat the service-day reading and literal-weekday reading as competing interpretations. Freeze admissible interpretation rules before official analysis; do not silently convert this to Correct or Incorrect.
3. **PC011, PC027, PC030, PC035, PC040:** All assert Laurel for Idris Fern when the trusted destination is Silver. Factual Incorrect is well supported. Whether Temporal Consistency is Unverifiable or Incorrect depends on a consistent rule for wrong-entity/attribute substitution; it must not be settled to favor a treatment effect.
4. **Eight AMBIGUOUS** (PC010, PC023, PC033, PC039, PC042, PC044, PC054, PC063): original reply-unit boundaries remain unresolved. The earlier generated prefix is a *plausible* evaluable unit, not a certified primary boundary. PC023 has the same weekday/service-day ambiguity. Three other cases (PC033/039/042) contain incorrect or partly incorrect response components; PC054 asserts an outdated/wrong room. Secondary treatment must preserve original structural status and excluded tails.
5. **Score independence:** Factual Correct and Task Success coincide for all 63 explicitly decided records, as do Relevance and Conversational Coherence for all 64 scored records. Different narrative explanations appear for relevance/coherence, so literal column copying is not established. Yet these axes have no observed discriminant power in this 12-case sample. Do not claim empirically independent dimensions or inflate evidence by treating these as independent signals. `component_coverage` follows the documented fraction of *correctly supported required components*, not mere presence of filled answer slots. The duplicate distributions can emerge from task design and rubric, but need a reproducible rubric-implementation check.
6. **Design scope:** 12 paired cases from only six speakers. Task outcomes often cluster by case; significance or new mechanisms cannot be inferred here. R/T are package replacements and are not pure isolated temporal/relevance mechanisms. The fixed 16 registered contrasts must be computed after real human confirmation, with unknown bounds and whole-speaker uncertainty.
7. **Blinding:** The primary CSV lacks treatment and structural labels, but repeats the same case six times, and contents/wording may reveal treatment; this is condition-masked, not a demonstrated independent human blind review.

## Recommended decisions

- Treat the 57 routine rows as **AI proposals consistent with the source under this targeted check**; they still require genuine researcher adoption.
- Prioritize explicit review of the 15 records identified as `HIGH` in the accompanying 72-row audit file (seven semantic/temporal interpretation issues and eight boundary-primary issues).
- Retain original primary proposal CSV and the boundary CSV unchanged. If wording/temporal ratings are corrected, append a versioned correction table rather than overwrite prior proposals.
- Preferred boundary plan: original primary (with clear `boundary_unresolved` status) plus independently recorded **eight-prefix sensitivity-only** evaluation. Do not promote prefixes to primary observations simply to reduce unknown counts.
- After *genuine researcher confirmation* of all 72 primary proposals or corrections and the boundary policy, freeze the confirmed snapshot and perform the 16 registered exploratory package-level contrasts. Do not relabel this as independent human blind annotation or add a second fictitious reviewer.
- After the development analysis, prioritize a real independent human second-review subset for measurement reliability and new held-out speakers/tasks for empirical confirmation. A second reviewer of existing outputs is not equivalent to independent experimental replication.

## Generated review aids

- `PersonaSLM_P1c_72_item_secondary_AI_audit_UNCONFIRMED_v1.csv` — all IDs, proposals, reason-coded issues and blank researcher decision fields.
- `PersonaSLM_P1c_8_boundary_secondary_AI_audit_UNCONFIRMED_v1.csv` — exact secondary prefixes, alternative scores and blank researcher fields.

No inference, repository modification, Git commit or Git push was performed by this audit.
