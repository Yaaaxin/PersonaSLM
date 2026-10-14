# P1c Repaired Neutral Semantics — Review v1

Maintainer: Yaxin ZHENG. Status: **OPEN; 0/12 new control approvals**. AI-assisted analysis below is not human evaluation.

## Preserved repair and tokenizer evidence

The original finite candidate search failed all 12 neutral matches. The already versioned repair changed only `its two parts.` to `its two distinct parts.` in the selected procedural reply. The old selected realization was one token shorter than the active reference in each case; the repaired realization has zero difference. The original bank, all attempts, counts, failed checks and native logs remain untouched.

[Repair inventory](validation/p1c/scientific_review_v1/neutral_repair_inventory_v1.json) preserves full old/new texts, line differences, prompt hashes and counts. [Native evidence links](validation/p1c/scientific_review_v1/neutral_native_evidence_links_v1.json) supply original and repaired ID lists and original log hashes. A new vocabulary-only pass reproduced all 72 final prompt ID lists. The model/backend/tokenizer identities are in [native reverification](validation/p1c/scientific_review_v1/native_reverification_v1.json).

The common reply is:

> The record places this question before its reply. Both are retained together in the archive entry, which preserves the exchange as one item rather than separating its two distinct parts.

Each text has the original archive date, Archivist question and case-specific named speaker. Matching is 766–938 full prompt tokens depending on case. H_none is 65 tokens shorter for ten cases and 66 shorter for Greta Sable's two cases. No tolerance was relaxed and no model answer selected a control.

## Semantic risk assessment

| Criterion | Observable evidence | AI-assisted interpretation requiring confirmation |
|---|---|---|
| New personal facts | Reply describes record layout, with no residence, preference, assignment or personal interval claim | No explicit additional biography detected; procedural claims are still content |
| Time and history | Archive date remains; no active validity interval is repeated | Not temporally empty or equivalent to active temporal propositions |
| Topic priming | Repeats record, archive, question, reply and exchange | May encourage record reading or metadiscourse; not semantically inert |
| Style | Long formal procedural sentence plus repeated related vocabulary | No explicit style instruction, but stylistic cue and naturalness risk |
| Speaker/role | Same Archivist and named target, two turns | Structure controlled; person replying about record layout differs pragmatically from reporting a personal fact |
| Hidden answer clues | No required answer component or target property in reply | Direct leakage absent; no claim that all indirect priming is excluded |
| Coherence | Reply describes the entry in response to what the entry says | Interpretable metareply, but self-reference can sound artificial and less informative |
| Negation/contrast | Contains “rather than”; active replies are simple assertions | Contrastive wording is an uncontrolled lexical/pragmatic difference |

The modifier repair does not introduce a new personal attribute. It also does not resolve the existing metadiscourse, length or naturalness issues. “Distinct” emphasizes separation; its behavioral effect is unmeasured. All cases share this wording, so 12 approvals would not establish a broad population of neutral realizations.

## Allowed comparison if approved

Active−neutral can compare a dated personal auxiliary assertion with a coherent procedural archive reply under fixed token length, wrapper, named speaker, turn count and insertion position. It cannot isolate topic, temporal content, personal fact presence or prompt length individually. ACCEPT_NARROW would approve only this role, not complete semantic neutrality or equivalence to H_none.

Review the [12-control CSV](validation/p1c/scientific_review_v1/neutral_review_v1.csv), which is a convenience subset of the [60-text master](validation/p1c/scientific_review_v1/history_text_review_v1.csv). Do not count the duplicate subset as 12 additional independent judgments. Keep originals blank and save a completed copy; reconcile by item_id, never by row order. Detailed instructions are in the [guide](P1c_scientific_review_guide.md). No prior P0/P1 approval transfers.
