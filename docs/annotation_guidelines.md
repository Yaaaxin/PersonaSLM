# Annotation Guidelines — Draft for P0 and Pilot

**Status:** Draft. These criteria must be trained, piloted, revised, then locked before confirmatory testing. Do not decide applicability by looking at model outputs.

## Applicability matrix (pre-generation)

Each `case` has `applicability` with `response_relevance`, `factual_consistency`, `temporal_consistency`, `conversational_coherence`, `linguistic_fidelity`, `behavioral_fidelity`: true/false. False = N/A and excluded from that endpoint's denominator. Example: a greeting without temporal assertions is N/A for temporal consistency; a fixed two-turn question is eligible for context coherence; behavioral fidelity requires defined speaker behavior and a matched scenario.

## Reliability — four independent endpoints

- **Response Relevance:** Does the output address the user's request/communicative intent? Rating 1: non-responsive/irrelevant; 3: partial; 5: adequately responsive. Answers can be short if the context warrants them.
- **Factual Consistency:** Compare against the pre-attested facts *valid at the evaluation time*. Mark `correct`, `incorrect`, `unknown/abstains`, `unverifiable`, or `N/A`; explicitly recognize negation, contradiction and multiple incompatible claims. Do not count mere keyword overlap as correct.
- **Temporal Consistency:** Explicitly distinguish older facts, updates, current valid state and event order. Same categorical outputs; factual and temporal failures may overlap.
- **Conversational Coherence:** With a *fixed pre-specified* multi-turn context, rate anaphora, topic continuity and whether the last turn is appropriately integrated (1–5). Free-interaction trajectories are an exploratory task, never pooled with fixed-context results.

## Persona Fidelity — separate endpoints

- **Linguistic Fidelity (1–5):** Lexical choice, syntactic brevity, sentence rhythm, punctuation/emoticons, consistent natural use of signature phrases; discourage repetitive caricature.
- **Behavioral Fidelity (1–5):** Response strategy to invitations, apologies, disagreement, complaints, humor, follow-ups, uncertainty. Requires reference examples and known speaker-specific tendencies across matched situations. Do not infer from a single catchphrase.

Annotators review the same context/evidence/target-speaker reference pack. Condition and model identity are hidden. Split annotation and metric development from the locked test. Use independent annotators for a subset (preferably all important comparisons) and report agreement and adjudication policies.

## P0 deterministic fact evaluator: limited scope

Automated city-fact checker is **not** a universal semantic judge. It only supports synthetic `current_city` claims: recognizes city names, clear English/Chinese negations and incompatible city mentions. It returns `unknown` or `unverifiable` when facts cannot be reliably determined. It must not be used as evidence of general dialogue reasoning ability.

Examples for the locked *unit tests*:

- Trusted Paris; `Alice currently lives in Paris.` -> `correct`.
- Trusted Paris; `She lives in Lyon.` -> `incorrect`.
- Trusted Paris; `Not Paris, Lyon.` -> `incorrect`.
- Trusted Paris; `Not Lyon, she lives in Paris.` -> `correct`.
- Trusted Paris; `Paris and Lyon are both her current home.` -> `incorrect`.
- Trusted Paris; `I don't know.` -> `unknown`.
- Trusted Paris; `She used to live in Lyon but now lives in Paris.` -> `correct`.

For each scored result, preserve `reason`, `reference_fact_id`, question ID, scope and metric applicability.

## Important distinction

An *output* cannot decide whether an endpoint was applicable. No filtering to C0-correct cases for the primary comparison. A conditioned transition statistic can be added separately and transparently reported as descriptive.

## 2026-10-12 language scope and P0 review addendum

Primary experimental and annotation materials are English under the [Protocol v1.1 language-scope addendum](research_protocol_v1.1_language_scope_addendum.md). Historical multilingual software-rule support above is not authorization to add non-English dialogue to the primary benchmark. Completed P0 artifacts remain unchanged.

The [independent neutral-control review instructions](P0_neutral_review_instructions.md) and 40-item blank forms operationalize the existing semantic-control checks. The supplemental `english_city_temporal_audit_v2` rule audit is separately versioned and does not replace historical scores, endpoint applicability, annotation procedures or human judgments.
