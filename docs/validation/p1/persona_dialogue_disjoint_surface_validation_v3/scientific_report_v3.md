# Disjoint Synthetic History Semantics-by-Surface Validation v3

## Scientific status

**ACTUALLY EXECUTED — PROSPECTIVE INDEPENDENT-CASE SYNTHETIC VALIDATION.**
This study collected 168 new responses from Qwen3.5-2B Q4_K_M on 24 previously
unseen controlled dialogue-choice cases. The cases use 12 explicitly synthetic
personas and three task families. They are disjoint from the two bound development
banks by exact entity, exact template, and normalized entity-hash checks. The study
was frozen before tokenization or output, executed once with zero retries, and
analyzed with its registered estimands.

The evidential boundary is narrow. Style and Facts were held present in every arm;
the study compares no History with three History-semantics regimes and two History
surface forms. It is not a full S/F/H factorial experiment, real-speaker evidence,
population inference, human-validated Persona Fidelity, or algorithm validation.

## Prospective design and execution integrity

Each case was executed under seven within-case arms:

- `SF_NO_H`;
- aligned, conflicting, or decision-irrelevant History; and
- raw-recommendation or declarative-record rendering for each History regime.

The 24 x 7 allocation used a frozen near-Williams order. Every arm appeared 24
times, six times per run quartile, and three or four times at each within-case
position. Every directed non-self predecessor pair appeared three or four times.
The run used temperature 0, seed 42, a 4,096-token context, a 96-token completion
limit, four CPU threads, and the official non-thinking chat template.

Independent pre-execution scientific and code reviews returned GO. They are process
separation inside one autonomous research session, not independent researcher review.
The exact authorization permitted at most 168 generations, 168 native tokenizer
calls, 168 live tokenizer checks, zero retries, and zero hidden warmups.

- Prospective design SHA-256: `28caab146f9ff51ec5f09aee9f3a9da9f0ae82a511ac7c332bb8a9418dc0fbac`
- Case bank SHA-256: `b694f87ccc62d62960c61aeae81229e9eca7f37038c755d8e3ccf31f8567e3dd`
- Human-review protocol SHA-256: `e4db428b9c523a70c19781be22c1711839c3835fb8a863e3c7cf654ace986943`
- Material audit SHA-256: `9bc2a744c4f3fafee290fda862cfa12b8dc749cd7cfb173b2fdc2a44deef996b`
- Frozen controller SHA-256: `b461ec0d9f6f5b8256b75c444f3a00f1e31319f0fec86b190bfc86d123d57255`
- Execution authorization SHA-256: `da3e3c3ee332bc6472e75a9a515d720e11c5b8ebeec55c5ebda5d78816b1a70a`
- Frozen manifest SHA-256: `da559249c4ec4076de572b571b1746f70436dbe781bd51287e0ad36b52c6a3cb`
- Official preflight SHA-256: `20ee1e2ce9bc884ea1aede2b05de8f96e37674d87046dc5f4a6149048f2b919d`
- Execution audit SHA-256: `2d86ea152519bc2ac27ab122bd2c54cf738dd89b6f1050b712a13be9f60c2c3d`
- Registered analysis SHA-256: `0a2d4547a6501991d6b9f1855a4f4081ff885bba5e700f226757ace58d182a44`
- Source Git HEAD: `c40667ad266082481b1850453f67784b593f3723`

The model weight SHA-256 was
`0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`;
the llama.cpp backend SHA-256 was
`71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`;
and the chat-template SHA-256 was
`0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`.

The official preflight observed 3,581,276,160 bytes of available physical RAM
against the frozen 3,221,225,472-byte minimum. It verified the model, backend,
template, source closure, manifest, disk, and cumulative budget. The 168 native
token arrays covered 245–357 input tokens; all 168 live server arrays matched
before completion 1.

The run directory is
`results/p1_persona_dialogue_disjoint_surface_validation/v3/runs/20261018T214135-eb079a7d40da4ca1a1db9135718d6ad2`.
All 168 requests were attempted exactly once; all returned HTTP 200, a raw response,
a deterministic derived record, and native EOS. The append-only journal contains
1,557 hash-chained events. The execution audit verified all 168 planned slots,
HTTP bodies, raw records, derived records, and source bindings. No request was
retried or regenerated.

## Registered automatic results

The primary automatic endpoints inspect only the certified first response sentence.
`preferred` requires exactly the preferred current anchor; `any-current` requires
exactly one of the two current anchors. `NONE` and `MULTIPLE` are complete-denominator
zeros for an otherwise assessable response. These are constrained selection-format
endpoints, not semantic quality or broad Persona Fidelity.

| Arm | Preferred current anchor | Any current anchor |
|---|---:|---:|
| `SF_NO_H` | 23/24 | 24/24 |
| `SFH_ALIGNED_RAW` | 19/24 | 20/24 |
| `SFH_ALIGNED_DECLARATIVE` | 20/24 | 21/24 |
| `SFH_CONFLICT_RAW` | 19/24 | 20/24 |
| `SFH_CONFLICT_DECLARATIVE` | 19/24 | 21/24 |
| `SFH_IRRELEVANT_RAW` | 19/24 | 20/24 |
| `SFH_IRRELEVANT_DECLARATIVE` | 18/24 | 19/24 |

All registered contrasts had 24/24 complete case contributions and point-identical
logical bounds because no response was empty, truncated, or boundary-invalid. The
leave-one-persona-out (LOPO) ranges are sensitivity ranges, not confidence intervals.
No p-values were computed.

| Registered contrast | Preferred estimate (LOPO) | Any-current estimate (LOPO) |
|---|---:|---:|
| Aligned minus irrelevant, `theta_A` | +0.0417 `[0,+0.0682]` | +0.0417 `[0,+0.0682]` |
| Conflict minus irrelevant, `theta_C` | +0.0208 `[-0.0227,+0.0455]` | +0.0417 `[0,+0.0682]` |
| Mean declarative minus raw, `theta_surface` | 0.0000 `[-0.0303,+0.0152]` | +0.0139 `[-0.0152,+0.0303]` |
| Irrelevant H minus no H, `theta_generic_history` | -0.1875 `[-0.2045,-0.1136]` | -0.1875 `[-0.2045,-0.1136]` |
| Aligned minus conflict | +0.0208 `[0,+0.0227]` | 0.0000 `[0,0]` |
| Surface interaction: aligned minus irrelevant | +0.0833 `[+0.0455,+0.0909]` | +0.0833 `[+0.0455,+0.0909]` |
| Surface interaction: conflict minus irrelevant | +0.0417 `[0,+0.0909]` | +0.0833 `[+0.0455,+0.0909]` |

The pooled declarative-minus-raw estimate was approximately zero. Thus the large
same-bank surface/measurement association observed in the earlier development bank
did not reproduce as a stable pooled declarative advantage on these disjoint cases.
Aligned and conflicting History also differed by no more than one preferred success
out of 24 and did not separate on any-current selection.

Task-family strata were heterogeneous. The preferred pooled surface estimate was
+0.0833 for collaborative planning and -0.0417 for both routine negotiation and
supportive reply. `theta_A` and `theta_C` were each +0.1875 in planning, were nonpositive
in routine negotiation, and were mixed in supportive reply. The preferred aligned-minus-
conflict difference was 0 in planning, -0.0625 in routine negotiation, and +0.125 in
supportive reply. These eight-case strata do not support a uniform history-semantics effect.

## Post-hoc measurement-mechanism audit

The following audit is **POST_HOC EXPLORATORY**, deterministic, and separated from
the registered estimands. It was prompted by the observed automatic failures and must
not be represented as preregistered confirmation.

After JSON decoding, 24/144 History-conditioned raw responses contained the literal
case-sensitive placeholder `<exact A anchor>` or `<exact B anchor>` in
`event.data.response.content`; the no-H arm contained 0/24. Of those 24 responses,
23 had registered category `NONE` and one `CURRENT_PREFERRED`. Every one of the 23
`NONE` responses nevertheless named the exact canonical preferred current option in
its first sentence; none named the nonpreferred current option. All 24 placeholder
responses named the preferred option and none named the nonpreferred option.

This is direct evidence of a response-realization and measurement failure: additional
History context was associated with literal copying of the system prompt's abstract
format placeholder, and the frozen anchor scorer necessarily counted those otherwise
preferred-name responses as zero. It prevents interpreting the registered -0.1875
generic-H contrast as a demonstrated semantic persona-choice loss. No-H versus H also
bundles context length and additional entities, so even the formatting association is
configuration-specific rather than a pure population-causal History effect.

All 168 responses failed the stricter exact label-anchor-name sentence diagnostic.
Eight current-nonpreferred anchor selections were concentrated entirely in synthetic
persona `DSV_P02` (five in case 002 and three in case 010); qualitative inspection found
that the selected first-sentence option conflicted with the accompanying reason. That
concentration is not a registered persona effect and requires blinded human adjudication.
No exact archived target name occurred in an output, but exact-name absence cannot
replace semantic History-intrusion or conflict-resolution review.

## Human semantic and Persona Fidelity status

No human label was created. Stage A is a 168-record current-only pointwise review of
relevance, current-evidence consistency, coherence, behavioral and linguistic Persona
Fidelity, completeness, unverifiable claims, selected entity, and evidence spans. Stage B
contains 72 raw/declarative pairs and cannot be prepared until a valid Stage-A submission
is sealed.

The official empty Stage-A template is
`results/p1_persona_dialogue_disjoint_surface_validation/v3/human_review/stage_a_delivery/stage_a_current_only_REVIEW_TEMPLATE.csv`
(SHA-256 `1b125f7c17eebb262dbbc2ad1ecbbf8ca265fb92feff6458fa41fe6ab4c41d47`).
The instructions SHA-256 is
`33ff59daa42ddf57fea84ae2f4973cc7930b6141e441b9cfa9d773bced878185`;
the package receipt SHA-256 is
`fb8262dad4118fde81ec8a286f48d1aca009911b06ac65a79a26ef95417895e6`.
All 16 editable fields in all 168 rows are blank. The protected mapping is not in the
delivery package and must not be shown to the reviewer.

The researcher must copy the official template and fill the copy, never edit the
official file in place. A private 21-field provenance record must truthfully report
project relationship, prior exposure, rubric involvement, AI assistance, UTC times,
and exact package/submission hashes. AI-generated judgments cannot substitute for this
review. A single principal-investigator review is genuine human evidence but not
independent validation or inter-rater reliability.

The frozen intake validates `prior_rubric_or_item_involvement` and the independence
field, but its current exposure-classification helper does not incorporate those two
fields. Therefore, if either field is `YES` or `UNCERTAIN`, a mechanically valid seal
must not by itself be described as clean or independent; the submitted provenance must
be reported directly and a prospective versioned clarification is required. The frozen
controller is not modified after output observation.

## Resource observations

- New generations: 168
- Generated tokens: 8,691
- Native EOS: 168/168
- Completion inference: 1,203.5250848 seconds
- Batch wall time: 1,242.3468222 seconds
- Mean completion time: 7.1638398 seconds
- Peak server working set: 3,591,196,672 bytes
- Minimum observed available physical RAM during execution: 289,243,136 bytes
- Cumulative autonomous budget: 508/1,200 generations and
  3,171.5446088/72,000 inference seconds

The very low minimum free physical RAM is a future stability warning even though this
run completed normally. It does not invalidate the recorded outputs, but any later
generation batch requires a new prospective resource plan and RAM preflight; the
threshold must not be lowered retrospectively.

## Reproducibility

The frozen manifest binds request order, messages, prompt hashes, native token arrays,
model/backend/template identities, generation parameters, source hashes, and the
cumulative authorization baseline. The run journal preserves request payloads, HTTP
bodies, raw completions, derived scores, timestamps, stop reasons, latency, memory,
server defaults, and terminal state. Analysis reproduction is distinct from generation
reproduction; bit-identical generation across environments is not promised.

An independent local script that does not import the v3 controller and does not call its
`analyze()` function reconstructed the 1,557-event hash chain, all 168 slot bindings,
all 168 automatic scores, all 14 registered endpoint estimates, task-family strata,
LOPO ranges, resource totals, and budget accounting with zero differences and zero model
calls. Its first append-only receipt is `analysis_reproduction_v1.json` (SHA-256
`8b521427849353497869c0626c946f5e4716f7c7abe1d5f661233dc4f8641cfb`).
The post-hoc placeholder subset is separately versioned because its first receipt's
23/23 statistic described the no-H preferred-anchor subset rather than the intended
History-placeholder `NONE` subset; the first receipt remains preserved and is not
silently overwritten. The append-only corrected receipt is
`analysis_reproduction_v2.json` (SHA-256
`e0c234d6194019c62d4fc019da6c4a057825ec8648d04face8fdf3b696807d4e`). It binds
the decoded RAW field, exact regex and denominator and independently reproduces the
24/144 placeholder count, the `NONE=23`/`CURRENT_PREFERRED=1` split, and preferred
canonical-name occurrence in 23/23 scorer-`NONE` rows with nonpreferred occurrence
in 0/23. This correction changes no registered estimate, score, resource total, or
budget value.

## Scientific conclusion

On new disjoint synthetic cases, the registered pooled declarative-history advantage
was essentially zero, so the earlier large same-bank declarative association did not
generalize as a stable surface benefit. Registered semantic-regime contrasts were small
and task-family-dependent. The apparent -18.75 percentage-point automatic penalty for
decision-irrelevant History cannot be interpreted as semantic reliability loss: a
post-hoc raw-output audit showed that the scorer's zeroes were substantially driven by
literal placeholder copying despite explicit preferred-option names.

The supported mechanism is therefore a configuration-specific interaction between added
History context, exact response-format compliance, and a narrow anchor-based evaluator.
This is a reproducible measurement/realization failure, not evidence that History caused
general persona unreliability. Genuine blinded semantic review is required to determine
whether History affected current choice, reason support, coherence, conflict handling, or
Persona Fidelity.

No novel algorithm is established. Declarative rendering is a simple prompting baseline
and did not show a stable pooled advantage. Automatically inserting anchors would merely
optimize the frozen metric and would not repair semantic decisions. A later method study
should proceed only after human review distinguishes semantic selection from realization;
then a new, ancestry-disjoint bank may compare no intervention, ordinary prompting,
structured choice, constrained realization, and relevant retrieval/filter baselines under
equal information and CPU budgets. Real-speaker validation remains blocked until lawful,
governed speaker-derived material is available.

## Literature and next action

The Europe/Paris 2026-10-19 metadata collection succeeded for 13/13 requests and
returned 217 records. Relative to the prior successful snapshot, item-level new IDs,
removals, field updates, and publication transitions were all zero. No new paper is
claimed; the 2026-10-18 primary-source novelty boundary remains in force. The delta is
recorded in `docs/validation/literature_monitor_v1/daily_delta_2026-10-19_v1.json`.

The next scientifically necessary action is genuine Stage-A human review of the 168
current-only records, followed by provenance validation and sealing. Only then may the
72 Stage-B pairs be constructed and reviewed. Human results must be integrated without
changing the registered automatic estimates or the append-only raw evidence. Cross-model
replication or algorithm evaluation before resolving this construct-validity question
would risk reproducing the same measurement failure at larger scale.
