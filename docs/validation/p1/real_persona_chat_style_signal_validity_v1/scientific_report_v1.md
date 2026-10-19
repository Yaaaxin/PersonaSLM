# RealPersonaChat Style-Signal Validity Controls v1

Status: **observed post-outcome development diagnostic; no model generation;
not confirmatory, human-reviewed, or independently validated**.

## Registration and access boundary

The original positive 76-speaker style-signal result was known before this
work. The finite control plan was frozen prospectively for the *new control
outcomes* in `registration_v1.json` (SHA-256
`9526ce41fff3ffe6dd9a1491c1a8d8077770617ac387ca3cbd236a53160716b6`).
Consequently, these controls can diagnose sensitivity but cannot convert the
original development finding into confirmatory evidence.

The first execution attempt failed on a nested registration-key lookup before
manifest construction, participant-text parsing, or outcome computation. The
registration was not overwritten. `registration_amendment_v1_1.json` records
the prospective one-line implementation correction and binds both controller
versions.

The corrected loader scanned 13,583 files only through their structural
`utterances` key, assigned the frozen speaker split from interlocutor IDs, and
then fully parsed only the 3,636 dialogues whose two interlocutors were in the
development partition. The 9,947 remaining dialogue texts were excluded before
JSON text parsing. The recorded counts for exploratory-test, independent-
validation, and cross-split dialogue texts parsed are all zero. No participant
text, pseudonymous ID, or row-level value is present in the evidence artifact.

## Observed controls

The original frozen mean margin reproduced exactly: `+0.200476` with 60/76
positive speaker-level margins.

| Diagnostic | Mean margin | Positive speakers |
|---|---:|---:|
| Frozen full feature set | +0.200476 | 60/76 |
| Remove turn-length features | +0.179469 | 61/76 |
| Remove explicit laughter/politeness markers | +0.219087 | 64/76 |
| Remove both length and explicit markers | +0.193660 | 61/76 |
| Ten nearest target-length controls | +0.163770 | 60/76 |
| Ten nearest character-trigram-overlap controls | +0.146100 | 60/76 |
| Remove exact repeated normalized turns | +0.196961 | 60/76 |

The registered correlations between the frozen margin and available
development-dialogue count, selected turn/character amount, and source-target
length imbalance ranged from `-0.120` to `-0.068`. None reached the registered
absolute diagnostic flag of `0.30`. Frequency-tertile mean margins were
`+0.200785`, `+0.240928`, and `+0.161284`; these are descriptive and do not
establish equality across frequency groups.

Content-character trigram overlap was itself higher for the same speaker than
for eligible other speakers: mean own-minus-other-median overlap `+0.010641`,
with 64/76 positive. This is evidence that lexical/topic continuity exists in
the corpus and contributes a plausible confounding route. Matching other
targets on that overlap attenuated the style margin from `+0.200476` to
`+0.146100`, but did not eliminate the positive descriptive signal.

Sixteen of 76 profiles shared at least one exact normalized turn across source
and target. Nineteen distinct overlaps removed 21 source and 21 target turn
occurrences. The post-removal margin remained `+0.196961`. Source and target
dialogue IDs never overlapped, and every selected profile retained four
distinct partners. Thus exact-turn leakage is present but does not explain the
aggregate signal under this registered sensitivity; less-than-exact formulaic
or topical reuse remains possible.

For the immediate-partner negative control, the focal target was on average
`+0.099059` standardized-L1 units closer to its own source than to the aggregate
language of its two source-dialogue partners; 48/76 speaker profiles were
positive. This weakens a pure immediate-partner-copying explanation, but the
substantial 28/76 nonpositive cases and the dialogue network prevent a claim
that partner accommodation has been removed.

## Scientific interpretation

The minimum controls support retaining the frozen mixed surface/stylometric
vector as a **secondary exploratory development endpoint**. Its positive
speaker-level signal is not solely attributable to the two explicit length
features, the explicit laughter/politeness features, exact repeated turns, or
the registered amount/frequency correlations.

At the same time, the positive trigram negative control and attenuation after
trigram matching show that the result is not topic- or lexical-independent.
The instrument measures a mixture of surface realization, stable expression,
lexical/topic continuity, formulaic reuse, and possibly interactional
accommodation. It must not be described as a validated measure of linguistic
Persona Fidelity by itself.

These data do **not** establish:

- fidelity of model-generated dialogue;
- any Style, Facts, or History conditioning effect;
- stable speaker identity independent of topic and partners;
- semantic, behavioral, factual, or temporal Persona Fidelity;
- population generalization or independent validation.

A real-speaker model pilot may use this vector only as one secondary automatic
proxy. Relevance, coherence, factual/history consistency, and behavioral
Persona Fidelity still require construct-appropriate evaluation and genuine
human judgments where automatic measurement is invalid.

## Reproducibility

`analysis_v1.json` (SHA-256
`7778a7857ad9689be9deb3b17867fff92fe6b5f110ea103298ecc49b2b55f5da`)
binds the exact RealPersonaChat revision, intake and split hashes, the frozen
76-speaker cohort hash, aggregate outcomes, and a digest of case-level values.
The analysis used no inference model and consumed zero generations. Raw corpus
text remains ignored local data and is not suitable for staging or public
redistribution by this project.
