# PersonaSLM Independent Synthetic S/F/H Replication — Scientific Report v1

Date: 2026-10-18  
Researcher: Yaxin ZHENG  
Protocol: PersonaSLM Research Protocol v1.1  
Evidence level: disjoint held-out synthetic stimulus replication; exploratory estimation  
Source branch: `research/autonomous-personaslm`  
Source HEAD: `c40667ad266082481b1850453f67784b593f3723`

## Claim boundary

This completed study is a prospective, disjoint-case synthetic replication of
Style/Facts/History (S/F/H) conditioning on twelve controlled next-turn choice
cases. It is not natural-conversation, real-speaker, human-rated, cross-model,
confirmatory, causal, or population-level validation. Its phrase-level style
measure is not a general measure of linguistic or behavioral Persona Fidelity.

The study produced a scientifically useful negative measurement result: the
registered content effects are not point-identifiable under the frozen strict
choice scorer because missingness depends strongly on History. Missing outcomes
are retained and logically bounded; they are never recoded as zero.

## Prospective design and execution

- Four explicitly synthetic personas and twelve new cases were used.
- The three history regimes were `ALIGNED_HELPFUL`, `OUTDATED_CONFLICTING`, and
  `IRRELEVANT`, with four cases per regime and balanced preferred A/B options.
- All eight C0–C7 cells of the 2^3 S/F/H factorial were executed once for every
  case: 96 frozen requests.
- The unmatched `N_STYLE` and `N_HISTORY` controls were prospectively deactivated
  before model output; each had zero attempts.
- The model was Qwen3.5-2B Q4_K_M through llama.cpp b11573 on CPU, with
  temperature 0, seed 42, 4096-token context, and a 96-token completion limit.
- There were no retries, hidden warmups, outcome-dependent stopping decisions,
  or p-values.

The first official preflight receipt failed before server launch because the
runner looked for the cumulative budget at an incorrect JSON nesting level. It
recorded zero tokenizer registrations, server launches, completions, and model
generations. A versioned repair changed only that lookup. The second official
preflight passed with 4,744,179,712 bytes of available physical RAM against the
registered 3,221,225,472-byte threshold.

The completed run attempted and archived 96/96 requests, received 96/96 raw
responses, and produced 96/96 derived results. All 96 offline native-tokenizer
registrations were reproduced by live server-side tokenization before completion
1. All 96 completions reported native EOS. No request was repeated.

## Registered condition-level results

“Resolved” below means that the frozen strict current-choice endpoint was
identifiable. “Preferred” is reported only among resolved responses.

| Condition | Resolved | Preferred among resolved | Missing content | Narrow style conjunction |
|---|---:|---:|---:|---:|
| C0 | 11/12 | 8/11 | 1/12 | 0/12 |
| C1 | 11/12 | 6/11 | 1/12 | 12/12 |
| C2 | 11/12 | 11/11 | 1/12 | 0/12 |
| C3 | 0/12 | not estimable | 12/12 | 1/12 |
| C4 | 11/12 | 8/11 | 1/12 | 10/12 |
| C5 | 1/12 | 1/1 | 11/12 | 12/12 |
| C6 | 0/12 | not estimable | 12/12 | 0/12 |
| C7 | 1/12 | 1/1 | 11/12 | 12/12 |

Only 46/96 content outcomes were resolved; 50/96 were missing. The missingness
was strongly treatment-related: 4/48 H=0 outcomes and 46/48 H=1 outcomes were
missing. Consequently, a null content effect cannot be inferred.

## Registered primary estimands

| Estimand | Complete cases | Point estimate | Logical bounds | LOPO point range |
|---|---:|---:|---:|---:|
| F main effect on current preference | 0/12 | not estimable | [-0.416667, 0.625000] | not estimable |
| H effect, aligned-helpful, on current preference | 0/4 | not estimable | [-0.750000, 0.250000] | not estimable |
| H effect, outdated-conflicting, on current preference | 0/4 | not estimable | [-0.625000, 0.375000] | not estimable |
| H effect, irrelevant, on current preference | 0/4 | not estimable | [-0.812500, 0.312500] | not estimable |
| F×H, outdated-conflicting, on current preference | 0/4 | not estimable | [-1.250000, 0.750000] | not estimable |
| S main effect on narrow surface-style uptake | 12/12 | +0.937500 | [0.937500, 0.937500] | [0.916667, 0.972222] |

The registered H effects on `history_target_selection` also lacked point
estimates. Their logical bounds were [0, 1] for aligned-helpful, [0, 1] for
outdated-conflicting, and [-0.25, 0.875] for irrelevant cases.

The registered outdated-value-adoption endpoint was **0/4 resolved and 4/4
missing** in both C6 and C7. This is not “0/4 adoption.” C7−C6 has no point
estimate and only the logical interval [-1, 1].

## Registered exploratory seven-effect matrix

All content columns below have 0/12 complete case contributions. Their entries
are logical bounds, not point estimates.

| Effect | Current named selection | Current preference | History target | Narrow style estimate; LOPO |
|---|---:|---:|---:|---:|
| S | [-0.5000, 0.5417] | [-0.6042, 0.4375] | [-0.5417, 0.5000] | +0.9375; [0.9167, 0.9722] |
| F | [-0.5208, 0.5208] | [-0.4167, 0.6250] | [-0.5208, 0.5208] | -0.0625; [-0.0833, -0.0278] |
| H | [-0.9583, 0.0833] | [-0.7292, 0.3125] | [-0.0833, 0.9583] | +0.0625; [0.0278, 0.0833] |
| S×F | [-1.0417, 1.0417] | [-1.0833, 1.0000] | [-1.0417, 1.0417] | -0.0417; [-0.1111, 0.0556] |
| S×H | [-1.0000, 1.0833] | [-0.7917, 1.2917] | [-1.0833, 1.0000] | +0.0417; [-0.0556, 0.1111] |
| F×H | [-1.0417, 1.0417] | [-1.2500, 0.8333] | [-1.0417, 1.0417] | +0.0417; [-0.0556, 0.1111] |
| S×F×H | [-2.0833, 2.0833] | [-2.0000, 2.1667] | [-2.0833, 2.0833] | +0.2500; [0.1111, 0.3333] |

The +0.25 three-way narrow-style interaction is descriptively driven by one
unexpected C3 style pass and two C4 style failures. It is not evidence of a
general three-way Persona Fidelity interaction.

## Measurement validity

All 96 outputs had exactly two sentences, no semicolon, and no exclamation mark.
The exact second-sentence prefix passed in 52/96 outputs and the exact suffix in
48/96. Nine case-level S contributions were +1 and three were +0.75. Therefore,
the +0.9375 S estimate primarily measures compliance with explicit prefix/suffix
phrase templates, not broad linguistic resemblance.

The secondary exact-cue endpoint classified 16 outputs as `SUPPORTED`, four as
`CONTRADICTED`, and 26 as `UNRESOLVED`; 50 were not applicable because the
strict content unit was missing. The four `CONTRADICTED` labels are artifacts of
the literal cue rule in semantically plausible paraphrases and must not be
reported as four factual errors without genuine semantic review.

No human semantic ratings were collected. Response relevance, conversational
coherence, broad linguistic Persona Fidelity, behavioral Persona Fidelity,
semantic completeness, and real-speaker validity remain unmeasured.

## Posthoc mechanism audit — not a registered endpoint

Inspection after the frozen analysis established that all twelve archived
assistant messages begin with `I recommend the <historical target>.` The
following descriptive audit was output-informed and cannot replace the
registered analysis.

| Group | Strict resolved | Strict unresolved | `I recommend the ...` | `I recommend Option ...` |
|---|---:|---:|---:|---:|
| H=0 | 44/48 | 4/48 | 0/48 | 4/48 |
| H=1 | 2/48 | 46/48 | 44/48 | 2/48 |

Across the 48 paired H comparisons, 42 changed from resolved to unresolved, two
remained resolved, four remained unresolved, and none changed from unresolved to
resolved. The paired increase in unresolved rate was 42/48 = +0.875.

A separate posthoc lexical reading of the first sentence found that all 48 H=0
outputs selected a unique current option and 37 selected the preferred current
option. Under H=1, 38 selected a current option, nine named an exact archived
target, and one paraphrased an archived target; 26 selected the preferred current
option. Preferred-current transitions were 23 correct→correct, 14 correct→wrong,
three wrong→correct, and eight wrong→wrong, a net difference of -11/48.

Within outdated-conflicting H cases, exact stale-target mentions occurred in 4/8
cases without F (C3/C5) and 0/8 with F (C6/C7). This is hypothesis-generating
only: the lexical recode was posthoc, and the registered content effects remained
unidentified.

Together with a prior disjoint development batch in which the history phrase
`My pick:` entered model outputs, these observations support a reproducible
candidate mechanism: the surface frame and entity of a native assistant-history
turn can anchor the next reply and interfere with the current exact-selection
contract. They do not isolate an internal memory mechanism because H jointly
changes historical content, target, discourse form, and temporal provenance.

## Resource accounting

| Quantity | Observation |
|---|---:|
| Generations | 96 |
| Generated tokens | 2,617 |
| Completion-inference time | 518.5032313999945 s |
| Mean completion time | 5.4010753270832765 s |
| Batch wall time | 534.6503611000007 s |
| Server peak working set | 2,900,316,160 bytes |
| Minimum observed available physical RAM | 1,899,884,544 bytes |
| Native EOS | 96/96 |
| Cumulative autonomous budget afterward | 202/1200 generations; 1187.2563158999974/72000 s |

## Supported and unsupported conclusions

Supported:

- strong complete-case uptake of explicitly prescribed phrase-level style cues
  on the new synthetic cases;
- a large, reproducible H-associated collapse in strict response-format
  identifiability;
- raw lexical evidence consistent with assistant-history surface-template copying
  and target anchoring; and
- a negative measurement finding: the frozen scorer cannot identify the content
  factorial effects under treatment-related missingness.

Not supported:

- a null F or H content effect;
- a registered outdated-value-adoption rate;
- broad linguistic or behavioral Persona Fidelity;
- semantic relevance, coherence, factual completeness, or temporal correctness;
- natural-dialogue, real-speaker, cross-model, or population generalization;
- confirmatory significance or causal internal-memory claims; or
- an effective or novel algorithm.

Native EOS establishes only the backend stopping state, not semantic completion.

## Reproducibility evidence

| Artifact | SHA-256 |
|---|---|
| Case bank | `a93cd629c0d152e9eb2325399235882beaebf510d4b6e32b24724975554fab8c` |
| Design v2 | `628bedc18b8aa549cb165fbfb3f33ffbb889b5ad3090d7ef86f58112476c156c` |
| Design amendment v3 | `9cd70fceca8b1fb806bd6b3c3bcb4deccfd974830d2a5e762c1e75a45120d937` |
| Wording clarification v4 | `4cce2737b31022426a58cb7a0ef1e145c8096494dd67deb0b6ad00ad81f1c218` |
| Analysis amendment v5 | `867aac85c5cc0962a657fa6befc4b05c1b11d877d46cfc901a8a43bb0a8751a3` |
| Preflight repair amendment v6 | `f95ae3030deac01863ef64409d30c54a2eb904d428ec8e108113df37ca6749b1` |
| Frozen manifest | `55673bc8f9a802fe22f9d4234cd0bea32e806a4d9f3386cd0e483fa1cc716485` |
| Execution authorization | `79997cd2e021f92cfa77192311677f0b429ef34c496892d6875c068b02df2c62` |
| Repair authorization | `d6f523b3810ed1f0a0f9631e2a8c20af561a4182158ae7c4d03ab420120d22ea` |
| Failed preflight v1 | `2de0d11f9d7d9ec2062fd39c4df0cb690a1ee1dfd5fc277f873be79a7160c031` |
| Passing preflight v2 | `1d0a27b9357095c6efba78d46d91228682ace1601907d18c768b797a58a365b2` |
| Model weights | `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc` |
| Backend executable | `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| Tokenizer executable | `e05dbdef761e577b3d56f3daea7b205a07f68e5d87242ea4e2544382ffdd358e` |
| Chat template | `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6` |
| Original runner | `0f1d52c64845e70e9abc33782847c5a46c86dd47d205df52df85aed24993edec` |
| Repair wrapper | `e73d33fb152cf2e90036421909db56e8401a9454a98dcc0371e6461f39a604d5` |
| Run manifest | `265cc8aa596a96bd1a4f30deb033d0dac938d2f15c8ad33258adbc7b690cf07e` |
| Run claim | `b61373a6581d07a6e00dac44e139aef3def19d5b74c26ea41502c16ec4246dd5` |
| Run summary | `455d389fe252c1f4938f0a57994a3994b4631f3d2a6e9088ebc15dcd2cea4773` |
| Execution audit | `ed74b2f0b11c3c4a7233d290bf8ca8121b065e311765419fbc3166e9d4afb118` |
| Analysis | `8d50119d7e91f07a039649a85e4ffd11d007295901130db7b5603ba910776ddf` |
| Terminal journal event | `d8aa31c82fc0114c3ce20bd5399ab563fc366ddf754b5902b4992bfd5f4bff6c` |

The run contains 899 hash-chained journal events. The archived manifest records
the dirty working tree and a source snapshot, exact prompt and request hashes,
raw HTTP responses, native token records, stopping reasons, timing, memory, and
derived scorer records. Audit and analysis each performed zero new generations.

## Next prospective action

The next bounded study should manipulate the native assistant-history surface
frame independently of the archived target and compare it with no-history,
current-content-restatement, and format-reminder baselines on entirely new cases.
This can test the candidate template-copy mechanism without modifying the
completed factorial evidence. Any positive result remains developmental until
it is replicated on independent cases, another model, and valid human-rated
Persona Fidelity outcomes.
