# P1c Annotation Reliability Plan — Proposed v1

Maintainer: Yaxin ZHENG. No human labels, reviewer identities, review times or agreement measurements are created by this plan. Historical AI-assisted researcher-confirmed annotations remain unchanged.

## Independent outcomes and response units

Stage A presents question, identical trusted evidence, requested/evaluation dates, answer components, fixed context and the frozen first-reply span. Hide treatment IDs, factor assignments, token counts, native stops, automated suggestions and structural labels. Use independently shuffled anonymous IDs, proposed seed 715005, with a separately protected mapping. Responses may themselves reveal cues; masking columns is not perfect blinding.

Rate relevance and coherence on the established 1–5 scales. Label factual and temporal consistency Correct / Incorrect / Unverifiable / Not Applicable under the fixed applicability matrix. Record each false or unsupported claim with the exact response quotation and relevant fact IDs/intervals. Unsupported claims and missing final answers are not demonstrably false claims. Score every required component separately; record full/partial/no final answer and semantic completeness independently. Do not infer reasoning success from a correct intermediate fact.

Stage B reveals full raw continuation, native termination, frozen `response_status_v1`, first-span offsets/hash and excluded continuation. Review unit extraction, extra turns, truncation and ambiguity without changing the frozen structural status. If Stage B motivates a revised semantic judgment, retain the original Stage A version and record the reason in a new version. Never replace the first reply with a later correct turn. An unidentifiable unit remains unscorable under the conservative analysis; any adopted-span sensitivity must be separate.

## Reliability subset selected prospectively

For the proposed 72-response development bank, seek an independent second human review of **36 responses**: one preselected case per speaker, all six cells, alternating current/historical query mode within each two-speaker task family. Thus all six speakers, three families, both requested-date strata and all treatments are covered without selecting outcomes. Record the selection before inference; the analyst keeps its masked treatment map. This is a calibration reliability check, not a precise population agreement estimate. If resources permit, review all 72 independently.

Before scoring study responses, reviewers calibrate the rubric using separate illustrative examples excluded from the experiment. Discuss definitions, then independently lock initial labels with no access to the other's decisions or AI suggestions. Preserve both original sets before adjudication. The first review may use assistance only if its provenance is disclosed; a claimed independent human subset must actually be independently rated. The researcher may act as adjudicator but must not be represented as a third independent rater.

After labels are locked, provide disagreements and source evidence for adjudication. Save each original label, uncertainty reason, adjudicated label and rationale. Do not replace unknowns by consensus-looking PASS values. Do not manufacture an agreement denominator from AI versus human adoption.

## Statistics and limitations

Report raw agreement, full confusion matrices and Cohen's kappa for nominal factual/temporal categories, separately from missingness. Treat Unverifiable as a genuine category; exclude only true inapplicability with counts. For ordinal relevance/coherence use prespecified linear-weighted kappa and agreement within one category, with full distributions. For component decisions report item-wise agreement and denominator. Bootstrap whole speaker clusters for uncertainty; six clusters and category imbalance make intervals unstable. Kappa can be undefined under a constant marginal distribution; report this rather than zero. No coefficient exists until actual independent ratings are supplied.

For an independent validation wave, select the reliability subset by speaker, task family and query-time stratum before outcomes, retaining every assigned cell. Choose its size to obtain useful uncertainty for disagreements, not an arbitrary universal percentage. Rare-error supplemental audits may be added with their outcome-based selection disclosed, and must not be pooled into representative agreement estimates.

If no second reviewer is available, retain single-researcher provenance, request a masked repeat after a separation interval when feasible, and report intra-rater rather than inter-rater consistency. Keep alternative plausible labels and boundary units in sensitivity analyses, including category bounds and leave-one-speaker-out results. Such sensitivity does not replace independent annotation reliability. This is a publication limitation to resolve or explicitly qualify, not permission to invent another reviewer.

## Import and freeze

Reuse the existing versioned import principles: exact response-ID set; immutable question/evidence/span hashes; unchanged applicability; valid labels/ranges; explicit missingness reasons; actual source provenance and researcher approval. A P1c-specific schema must be frozen before future outputs, without rewriting the P1b importer or labels. Hash the confirmed snapshot before unblinding. Exclusive-create output paths and a manifest prevent silent replacement; preserve corrections as a new annotation version. There is no P1c outcome dataset to import now.
