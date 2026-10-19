# RealPersonaChat Development Style-Signal Diagnostic v1

Status: **observed development evidence with independent analysis
reproduction; not human-reviewed or independently experimentally validated;
no model generation**.

## Question and prospective design

Before computing outcomes, `registration_v1.json` froze a surface/stylometric
diagnostic on the RealPersonaChat v1.0.0 development partition.
Each eligible pseudonymous speaker contributes a deterministic source profile
and target profile, each aggregating two dialogues. For 74/76 profiles their
order is directly timestamp-verifiable; two targets contain a `NaT`-only
record. The four dialogues use four different partners. Controls are all other
eligible target profiles whose
selected partners do not overlap the focal speaker's selected partners.

The frozen vector contains turn-length dispersion, punctuation and sentence
ending rates, explicit laughter and Japanese politeness markers, and Unicode
script/category rates. It contains no word n-grams, persona facts, demographic
attributes, personality scales, speaker IDs, or review labels. Because the
laughter and politeness features use lexical or morphological forms, the vector
must not be called nonlexical. The primary estimand is the
mean standardized-L1 margin:

`median distance to eligible other speakers - distance to the same speaker`.

A positive margin means the later cross-partner profile is closer to the same
speaker. The registration hash is
`6cf206f3ffbf72a1ac080276c7ee136c49a9e303001b8018ca55e506d2d3ed7d`.

## Observed result

All 76 prospectively eligible development speakers resolved; none was missing.

| Quantity | Observed value |
|---|---:|
| Mean same-speaker distance | 0.736162 |
| Mean other-speaker median distance | 0.936639 |
| Mean margin | +0.200476 |
| Median margin | +0.188482 |
| Margin interquartile range | +0.059667 to +0.369073 |
| Same speaker closer than other-speaker median | 60/76 (78.947%) |
| Mean rank against eligible controls | 0.744524 |
| Leave-one-speaker-out mean-margin range | +0.193029 to +0.205084 |

The leave-one-speaker-out range is an influence diagnostic, not a confidence
interval or calibrated population-inference procedure. No p-value or
confirmatory claim is registered.

## Interpretation

The result supports a narrow conclusion: this real-speaker development corpus
contains a cross-profile, cross-partner signal in the frozen mixed
surface/stylometric features. The positive mean is not driven by any single
speaker under the stated leave-one-out diagnostic. This makes the feature set a
plausible *secondary* linguistic-style measurement for a future model pilot.

It does **not** establish:

- model Persona Fidelity or an S/F/H conditioning effect;
- semantic, behavioral, factual, or temporal fidelity;
- identification or faithful imitation of any individual;
- independence across networked dialogues or population generalization;
- a validated replacement for condition-blinded human review;
- an algorithmic improvement or novelty claim.

Partner accommodation, topic, chronology, and interaction-network dependence
may remain even after requiring four distinct partners and disjoint-partner
controls. The hand-built feature set captures only surface realization. The
analysis uses the development split only; the exploratory-test and independent
validation reserve were not used.

## Reproducibility and privacy

The source is RealPersonaChat v1.0.0 at commit
`28d0b6b3865b29cabc26c230a2db37cdf315e937`. The intake receipt binds the exact
dialogue manifest and interlocutor file. The registration binds the analysis
controller, source HEAD, split, cohort/dialogue assignment, and intake receipt.
`analysis_v1.json` retains the estimates and a hash of the case-level values.
The controller recalculates every quantity from ignored local raw data.

No participant utterance, persona sentence, pseudonymous ID, row-level result,
demographic attribute, or personality score is emitted. Raw data stay under
`.local/` and must not be staged or published. Public claims remain aggregate
and non-impersonating.

## Next valid use

Before any real-speaker generation, freeze a Japanese-capable semantic rubric
and demonstrate its applicability. A small, finite development-only S/F/H pilot
may then use this feature vector as a secondary linguistic endpoint while
retaining genuine human judgments for relevance, coherence, behavioral Persona
Fidelity, and reliability. The independent validation reserve must remain
untouched until the design and measurement pipeline are frozen.

## Post-analysis audit correction

`interpretation_correction_v1.json` binds the frozen registration, analysis,
controller, imported intake controller, Python version, and Unicode-data
version. It corrects two over-broad phrases without changing the observed
numbers:

- “nonlexical” is replaced by **mixed surface/stylometric** because laughter and
  polite-ending features match explicit forms;
- “cross-time/chronological” is limited to **deterministic
  recorded-timestamp-key order** until the independent reproduction emits a
  selection-specific timestamp-validity aggregate.

The audit also records transductive development scaling, residual interaction-
network dependence, leave-one-out cohort/scaling changes, and the fact that the
loader opened public reserve files programmatically before discarding their
rows. Reserve content was not used in the estimates or displayed, but future
validation should use physically separated manifests. The correction preserves
the result only as a development measurement diagnostic.

## Independent analysis reproduction

An independently implemented raw-JSON recomputation, which imports neither
the original intake functions nor the original style-signal controller,
reproduced every frozen aggregate exactly. Its status is
`PASS_EXACT_REPRODUCTION_WITH_CHRONOLOGY_LIMITATION`; the reproduction receipt
is `analysis_reproduction_v1.json` (SHA-256
`d5fc409374e14fdac38fd318f37af9e1f04eaac5f7d9ac020f97f4b879f8cf78`).
The case-level values hash remains
`6c7081d747d4f39e05729578d262b1de3263e07aa52d1d3a6c949358ca55c4d8`.

The reproduction also audited all 304 selected speaker-dialogue records: 302
have parseable ISO chronology keys, while two target-side records are
`NaT`-only. Consequently, strict source-before-target chronology is directly
timestamp-verifiable for 74/76 profiles, not all 76. The two records remain in
the frozen estimate because the prospective selector placed its `NaT` sentinel
last. This does not alter the exact numerical reproduction, but it prevents an
unqualified longitudinal or later-profile interpretation. No 74-profile
sensitivity reanalysis was performed after observing this limitation.
