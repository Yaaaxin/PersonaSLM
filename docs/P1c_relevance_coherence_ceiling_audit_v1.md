# P1c relevance coherence ceiling audit v1

Maintainer: Yaxin ZHENG. Status: AI-assisted review; researcher confirmation pending.

## Rubrics and procedural dependence

Relevance asks whether a reply addresses the requested communicative intent. Coherence asks whether it integrates with the fixed preceding dialogue, including topic continuity and reference resolution. Neither is simply factual correctness. The original script assigned the two ordinal values together and produced generic explanations from that score. Thus 72/72 equality, including eight nulls, cannot establish independently evaluated dimensions. Historical proposals remain available verbatim.

The fixed context is generic: a user has the dated schedule ready, and the assistant asks which assignment to check. The 64 identifiable replies all continue with named assignment answers. Incorrect assignments remain factually wrong but do not necessarily create a discourse discontinuity.

## Specific pending recommendations

| Response | Metric | Original | Recommended |
| --- | --- | --- | --- |
| PC004 | conversational_coherence | 4 | 5 |
| PC006 | response_relevance | 4 | 5 |
| PC006 | conversational_coherence | 4 | 5 |
| PC011 | conversational_coherence | 4 | 5 |
| PC027 | conversational_coherence | 4 | 5 |
| PC030 | conversational_coherence | 4 | 5 |

PC004/011/027/030 explicitly use collection-desk wording for destination-room questions; retaining relevance 4 is a defensible attribute-alignment judgment, with 5 as a recorded alias-reading alternative. Their declarative replies nevertheless integrate with the schedule-checking dialogue, supporting coherence 5. PC006 directly attempts both requested fields: a calendar-versus-service-day ambiguity belongs to factual/temporal adjudication and does not by itself justify relevance/coherence deductions. Its two 4s are proposed as 5s. In the separate alternative-prefix view, PC023's service-day phrase similarly motivates two additional 4-to-5 recommendations.

Every row contains separate question/context/reply quotations, reasons, a plausible alternative score and qualitative confidence. These are AI explanations, not human notes. Ambiguous primary units remain unscorable. No score is changed merely to create variation, and these recommendations are not official labels.

## Measurement resolution

Original primary R/C: 59 score 5 and 5 score 4 among 64 (92.19% at the maximum). Reviewed primary R: 60/64 at 5 (93.75%); coherence: 64/64 at 5. Secondary reviewed R: 68/72 at 5; coherence: 72/72 at 5. The reinspection increases the ceiling rather than manufacturing variance. Constant observed coherence cannot sensitively measure small conditioning differences here; it does not establish a zero population effect or validate interval-scale assumptions.

Keep full ordinal distributions, missing units and threshold/sign sensitivities. Means, if later reported, are descriptive. Use independent rubric calibration examples that separate relevance, context integration and truth; do not retroactively rewrite this task bank to improve scale resolution.
