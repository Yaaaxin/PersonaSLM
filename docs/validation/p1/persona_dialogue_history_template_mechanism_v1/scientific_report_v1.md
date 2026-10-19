# PersonaSLM Native-History Recommendation-Frame Mechanism Study

Scientific report v1 — 2026-10-18  
Researcher: Yaxin ZHENG  
Protocol: PersonaSLM Research Protocol v1.1  
Evidence level: `DEVELOPMENT_MECHANISM`  
Source branch and HEAD: `research/autonomous-personaslm`, `c40667ad266082481b1850453f67784b593f3723`

## Result in one sentence

On six new synthetic paired cases, changing an archived assistant turn from the
recommendation frame `I recommend the <target>.` to the declarative frame
`<target> was my choice.` eliminated literal frame copying (6/6 to 0/6) and
restored strict no-article response formatting (0/6 to 5/6), but did not improve
current-target selection, exact historical-target intrusion, or the registered
task-success endpoint.

This is bounded evidence for an association between the bundled archived
wording/speech-act manipulation and the next response frame. Because the
declarative arm changes wording, tokenization, and speech-act semantics together,
it does not isolate lexical copying or anchoring as a cause. It is not evidence of
improved semantic reliability, an internal memory mechanism, an effective
algorithm, algorithmic novelty, broad Persona Fidelity, or independent validation.

## Prospective question and design

The preceding 96-request factorial replication showed that H-present conditions
often copied an archived assistant recommendation frame and became unscorable by
the strict current-choice contract. This output-informed study prospectively
tested whether that behavior was associated with the archived response surface,
current-content recency, or a format-only reminder.

Six new synthetic personas each supplied one new controlled-choice case. Two cases
were aligned-helpful, two outdated-conflicting, and two irrelevant; preferred A/B
options were balanced within every regime. Each case was run once in five paired
arms (30 requests total), with S=1 and F=1 throughout:

1. `SF_NO_H`: no archived turns.
2. `SFH_RAW_NATIVE`: native user/assistant history whose assistant begins
   `I recommend the <archived target>.`
3. `SFH_SURFACE_NEUTRAL`: identical native history role, target, reason, second
   sentence, and final user message; only the assistant first sentence changes to
   `<archived target> was my choice.`
4. `SFH_CURRENT_RESTATEMENT`: raw history followed by a final-user restatement of
   the current F block and current option notes.
5. `SFH_FORMAT_REMINDER`: raw history followed by a format-only reminder containing
   no option name, reason, preference value, or archived target.

The 30-request order was fixed before tokenization. Every arm occupied six
positions with identical position sum 87 and mean 14.5. The study used the frozen
Qwen3.5-2B Q4_K_M CPU configuration, temperature 0, seed 42, a 4096-token context,
96-token completion cap, no retries, and no hidden warmups.

## Registered measurement policy

The finite first-sentence grammar recognized exact current or archived targets in
three current-target forms: no article, optional `the`, or a correct `Option A/B —`
label. This grammar was kept separate from strict format adherence. Exact archived
target intrusion was scanned across the full reply.

The registered binary metrics were:

- current-target selection;
- exact historical-target intrusion;
- literal `i recommend the` frame copying;
- strict format adherence;
- current-preference task success, requiring strict format, selection of the
  preferred current option, at least one exact frozen cue for that option, and no
  exact cue for the other current option; and
- narrow surface-style uptake.

All 30 responses were assessable on these endpoints, so no registered paired
contrast required missing-outcome widening. The analysis was descriptive: no
p-values, confirmatory claim, population inference, or causal claim was registered.

All 30 automatic `response_status` records were `AMBIGUOUS` because there was no
certified semantic boundary or budget evidence, while all retained an identifiable
first reply, `raw_termination.truncated=false`, and automatic
`measurement_state=ASSESSED_IDENTIFIABLE_UNIT`. Native EOS and an identifiable
scoring unit do not establish semantic completion.

## Execution integrity and resources

The official preflight observed 4,317,827,072 bytes of available physical RAM
against the 3,221,225,472-byte gate and passed all model, backend, template,
manifest, disk, and cumulative-budget checks. Thirty native tokenizer calls were
archived at registration. Before completion 1, all 30 live server `/tokenize`
arrays exactly matched the frozen token arrays.

The single run completed 30/30 attempts, responses, and derived records with zero
failure, retry, or hidden warmup. All 30 completions ended at native EOS. The model
server exited after postflight verification.

| Resource | Observed value |
|---|---:|
| Generated tokens | 783 |
| Completion-inference time | 174.50069829999484 s |
| Batch wall time | 182.01441759999943 s |
| Server peak working set | 2,369,359,872 bytes |
| Minimum across dedicated server memory-observation events | 2,048,229,376 bytes |
| Lowest archived system observation, including in-context postflight | 2,045,513,728 bytes |
| Cumulative autonomous budget afterward | 232/1200 generations; 1361.7570141999922/72000 s |

## Registered arm results

All denominators are six. “Preferred category” is the registered category count,
not the stricter task-success endpoint.

| Arm | Current target | History intrusion | Frame copy | Strict format | Task success | Narrow style | Preferred category |
|---|---:|---:|---:|---:|---:|---:|---:|
| NO_H | 6/6 | 0/6 | 1/6 | 5/6 | 2/6 | 6/6 | 5/6 |
| RAW_NATIVE | 5/6 | 1/6 | 6/6 | 0/6 | 0/6 | 6/6 | 2/6 |
| SURFACE_NEUTRAL | 5/6 | 1/6 | 0/6 | 5/6 | 0/6 | 6/6 | 1/6 |
| CURRENT_RESTATEMENT | 6/6 | 0/6 | 6/6 | 0/6 | 0/6 | 6/6 | 4/6 |
| FORMAT_REMINDER | 6/6 | 0/6 | 6/6 | 0/6 | 0/6 | 6/6 | 3/6 |

The exact registered selection-category distributions were:

- NO_H: five current-preferred and one current-nonpreferred;
- RAW_NATIVE: two current-preferred, three current-nonpreferred, and one archived
  target;
- SURFACE_NEUTRAL: one current-preferred, four current-nonpreferred, and one
  archived target;
- CURRENT_RESTATEMENT: four current-preferred and two current-nonpreferred; and
- FORMAT_REMINDER: three current-preferred and three current-nonpreferred.

## Registered paired effects

Effects are high arm minus low arm. Every estimate uses six complete within-case
pairs. LOPO is leave-one-persona-out, which is also leave-one-case-out because each
synthetic persona contributed exactly one case.

| Contrast | Current target | History intrusion | Frame copy | Strict format | Task success | Narrow style |
|---|---:|---:|---:|---:|---:|---:|
| RAW − NO_H | -1/6 | +1/6 | +5/6 | -5/6 | -2/6 | 0 |
| SURFACE_NEUTRAL − RAW | 0 | 0 | -6/6 | +5/6 | 0 | 0 |
| CURRENT_RESTATEMENT − RAW | +1/6 | -1/6 | 0 | 0 | 0 | 0 |
| FORMAT_REMINDER − RAW | +1/6 | -1/6 | 0 | 0 | 0 | 0 |
| CURRENT_RESTATEMENT − FORMAT_REMINDER | 0 | 0 | 0 | 0 | 0 | 0 |

For RAW − NO_H, the LOPO ranges were [-0.2, 0] for current-target selection,
[0, 0.2] for historical intrusion, [0.8, 1] for frame copying, [-1, -0.8]
for strict format, and [-0.4, -0.2] for task success. For
SURFACE_NEUTRAL − RAW, frame copying was -1 under every deletion and strict-format
LOPO ranged from +0.8 to +1. Current-target and intrusion LOPO ranges were both
[-0.2, +0.2]. Restatement and reminder effects on current-target selection and
intrusion also had LOPO ranges containing zero.

The bundled wording/speech-act comparison showed a robust response-frame
difference but merely moved the single exact archived-target output from one
aligned case to the other; it did not improve the registered content outcomes.

## Regime and latency descriptions

Each regime contains only two cases and cannot support a regime-level population
claim. Frame copying under SURFACE_NEUTRAL − RAW was -1 in all three regimes.
Strict-format effects were +0.5 for aligned-helpful and +1 for both irrelevant and
outdated-conflicting cases. Restatement and reminder changed current-target
selection (+0.5) and exact intrusion (-0.5) only in the aligned pair.

Mean completion latency was 4.8392 s for NO_H, 5.6656 s for RAW, 5.8112 s for
SURFACE_NEUTRAL, 6.7487 s for CURRENT_RESTATEMENT, and 6.0187 s for
FORMAT_REMINDER. Registered paired latency differences were +0.8264 s for
RAW − NO_H, +0.1456 s for NEUTRAL − RAW, +1.0830 s for RESTATEMENT − RAW,
+0.3531 s for REMINDER − RAW, and +0.7299 s for RESTATEMENT − REMINDER.
These are descriptive observations from one CPU batch, not general performance
effects.

The frozen analysis computes its RAM minimum from the dedicated
`memory_observation` events. The separately archived postflight preflight record,
captured before the server context exited, contains the slightly lower system
observation shown above. This scope distinction does not affect the pre-run 3 GiB
launch gate.

## Scientific interpretation

The data support a narrow association repeated across these archived batches: the archived recommendation
wording/speech act co-occurred with the same article-bearing response frame and a
broken exact output contract, whereas the declarative wording/speech act did not.
The lexical frame was present in all six raw-history outputs and absent from all
six surface-neutral outputs. This result is consistent with earlier disjoint
batches in which `I recommend the` and `My pick:` from native assistant history
also appeared in subsequent replies, but it does not by itself isolate a causal
lexical-copy mechanism.

The result does **not** show semantic repair. Surface neutralization left
current-target selection, exact historical-target intrusion, and task success
unchanged relative to raw history. Current restatement and the shorter-prompt,
lower-latency format-only reminder were identical on all six registered binary
metrics in this batch, and neither
improved registered task success. No intervention therefore established an
algorithmic advantage.

The registered task-success measure is itself narrow. It jointly requires the
no-article strict frame and an exact frozen reason cue. Consequently, all raw,
restatement, and reminder outputs fail it because they copy `the`, while plausible
reason paraphrases can also score zero. Narrow style was 30/30 and therefore at
ceiling; it measures fixed prefixes, suffixes, punctuation, and sentence count,
not general Persona Fidelity.

Exact history intrusion misses paraphrases. Surface neutralization changes wording
and tokenization; restatement and reminder jointly change prompt length and
recency. The data use one quantized model, six synthetic personas, one case per
persona, and no human semantic judgments.

## Posthoc observation — not a registered contrast

Directly reducing the registered category labels to preferred-current selection
produces rates of 5/6 (NO_H), 2/6 (RAW), 1/6 (SURFACE_NEUTRAL), 4/6
(CURRENT_RESTATEMENT), and 3/6 (FORMAT_REMINDER). The corresponding unregistered
paired differences are -3/6, -1/6, +2/6, +1/6, and +1/6 respectively. These are
hypothesis-generating only because preferred-current selection was not frozen as
a paired binary estimand.

One surface-neutral output recommended the noisy option and stated that continuing
drum practice aligned with a low-noise preference. This observed semantic
contradiction illustrates why the narrow automatic endpoints cannot establish
reason correctness without a valid semantic instrument.

## Reproducibility

| Artifact | SHA-256 |
|---|---|
| Model weights | `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc` |
| Backend executable | `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| Native tokenizer executable | `e05dbdef761e577b3d56f3daea7b205a07f68e5d87242ea4e2544382ffdd358e` |
| Chat template | `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6` |
| Case bank | `f471a2a3cf54f2c3e72d83437822a16b6732fa4f03d98a62ad18e53e2d5bc98d` |
| Prospective design | `dcc70c37a19e7fa26de491d3d4311dc7b4573a78b1033d345b5b31c2db27d619` |
| Runner | `a220a522ee9691e7b12536f6271e568b0f85ad97f41a06785538b3f591a8a061` |
| Runner tests | `01e042c3dfd7b29a2670a8a2ec76623ef2b1415503988a37c1caee6f6090bc21` |
| Execution authorization | `7ad6d2e505b7321ae0b374efadb3266bb45d64ba73dbd6206be30a74147d7572` |
| Frozen manifest | `0b72b60fe1e10037beecb061372ce7b5a3834dce87c9087d1f5ebc75df1eb6ae` |
| Official preflight | `9c1bb110f6c012114038e2fef352efc99f2bce727f10627d62a933515944b6e7` |
| Run claim | `ffd8174dc510d834dda3b7dee118e3b7b52055fb6998f73f8cc8e468bb9a6152` |
| Run manifest | `9db594641a091a2b61b29490384f653cb9cd85c9e811f60232251c2bf42e24eb` |
| Run summary | `c27af8ed1ae798cb704d47ba0d030b574ad4228a2bf6860c79559ff9d0dc150a` |
| Terminal event chain/content hash | `94f57c3b199c60a00058d3c803a41ff51a84bad055433a50b36256b063e0c08a` |
| Terminal event file | `710651e29c295cf45c6877155212268b9b9e4d0a913336ad5b2fed13ed96d051` |
| Execution audit | `8c94cfcf14632eb6fa2adfa2231f43b748cab0f5d7f359b5462bc891bb1738f3` |
| Analysis | `c39848c8ba03840c066cb3581e4037743167f1d3ce31187537ed55dfc002b266` |
| Local reconstruction receipt | `53039a105daa72cf5c343aab9ad21c6b0dc87578104c590c624ab5bb4e27e2f0` |

The private raw run is
`results/p1_persona_dialogue_history_template_mechanism/v1/runs/20261018T182339-7d70edadcd4747088859dfc659650884`.
A separate read-only reconstruction in the same autonomous research session
verified all 305 hash-chained events and rebuilt 30 frozen requests, 30 native tokenizer records,
30 live tokenizer checks, 30 raw responses, 30 scores, all arm summaries, all
contrasts, latency, memory, audit, and analysis with zero differences and zero
model calls. The receipt is `analysis_reproduction_v1.json`.

The frozen runner and its source snapshot provide the executable replay logic, but
the receipt is not a standalone reproducer and the reconstruction was not performed
by an independent human researcher. Public-clone reproduction is partial because
the ignored raw run and model weights are not distributed here. This establishes
local analysis reproducibility, not independent experimental validation or
bit-identical generation reproduction across environments.

## Next falsifiable experiment

The next prospective study should use entirely new cases and orthogonally cross
history semantics (aligned versus conflicting) with history surface
(recommendation versus declarative), plus NO_H. Current-option identity and order
must be counterbalanced. Direct preferred-current selection, independent of the
format gate, should be a primary endpoint. Semantic reason correctness requires a
validated blinded human measure; template copying and strict format remain
mechanism endpoints. This design can distinguish lexical frame transfer, semantic
history interference, and their interaction before any algorithm is proposed.
