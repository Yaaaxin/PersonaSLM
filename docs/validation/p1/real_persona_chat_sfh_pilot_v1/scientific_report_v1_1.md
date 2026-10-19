# Real-speaker S/F/H developmental model pilot

Date: 2026-10-19. Evidence level: OBSERVED DEVELOPMENT EXPLORATORY.

The first controlled RealPersonaChat model pilot completed all 64 frozen requests:
eight development speakers, one dialogue context each, and all eight S/F/H
conditions. There were no retries, hidden warm-ups, failed completion calls, or
outcome-dependent stopping decisions. This is real speaker-derived dialogue
evidence, with automatic proxy outcomes; human semantic findings and independent
speaker validation remain unestablished.

## Design and provenance

The [prospective design](prospective_design_v1.json) selected eight speakers from
the previously frozen 76-speaker development cohort. Two earlier source dialogues
had distinct partners, separate from the later target partner. All selected
timestamps support source-before-target ordering. S supplied numeric surface-style
descriptors, F supplied ten participant-authored self-statements of unknown temporal
truth, and H supplied six preceding dialogue turns. The next actual human turn was
withheld from every prompt. The same query, system instruction, and section headers
were used across C0-C7. XOR Latin ordering balanced conditions across execution
position. H contains both content and style; the estimands concern incremental
prompt packages, not isolated psychological constructs.

The RealPersonaChat v1.0.0 revision is
`28d0b6b3865b29cabc26c230a2db37cdf315e937`; split hash is
`950b5c16e7b6eb77a350b7e3adc4fc1f5be63d11facbaa5ccc3f70081cf3e6f7`.
The 58 independent-validation speakers remain unused. Raw participant material,
identifiers, prompts, references, and row-level outputs remain local under `.local/`.
The [governance amendment](data_governance_amendment_v1.json) authorizes this finite
anonymous aggregate development experiment while retaining the original intake
evidence and its privacy restrictions.

The model was the previously verified third-party Qwen3.5-2B Q4_K_M artifact,
weight SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`.
The backend was llama.cpp b11573-0f701c882, CPU only, four threads, context 4096,
maximum 96 new tokens, temperature 0, top-p 1, seed 42, thinking disabled, and no
custom stops. Third-party conversion lineage remains partially verified. Native
registration performed exactly 64 tokenizer operations (127-426 input tokens),
and all 64 live tokenizer arrays matched before the first completion. Source HEAD
was `c40667ad266082481b1850453f67784b593f3723`; the actual uncommitted runtime
source files are hash-bound and copied into the private run snapshot.

## Observed results

The [frozen analysis](analysis_v1_1.json) contains every condition summary and all
seven Hadamard contrasts for each of 16 automatic metrics. The main effect is the
within-speaker factor-present minus factor-absent average. Table entries below are
means over complete speaker-context units for the relevant endpoint.

| Outcome | Speaker units | S effect | F effect | H effect |
|---|---:|---:|---:|---:|
| Generated tokens, all responses | 8 | -18.937500 | +9.437500 | -2.875000 |
| Completion latency, seconds | 8 | -0.293696 | +1.948556 | +0.753629 |
| Frozen structural flag | 8 | +0.062500 | -0.062500 | +0.062500 |
| Surface-style distance, lower is closer | 5 | -0.104083 | +0.035680 | +0.026409 |
| Character-trigram F1 with one human continuation | 5 | +0.048791 | +0.009045 | -0.016897 |
| Trigram overlap precision with latent H text | 5 | +0.125691 | +0.024837 | +0.034555 |

There were 1,614 generated tokens, 60 native `eos` stops, and four native `limit`
stops. C0, C2, C3, and C6 each had one limit stop. These four censored responses
belong to three speakers. All 64 raw responses remain in the archive; the frozen
scorer marks the four truncated responses structurally invalid and leaves their
text-derived outcomes missing. Text coverage is therefore 60/64, with condition
denominators 7,8,7,7,8,8,7,8. Only five speakers have all eight text outcomes.
Every one of the 60 text-assessable replies contains Japanese-script characters;
this demonstrates script compatibility, not Japanese semantic quality.

For the eight-speaker token effect, S's descriptive leave-one-speaker-out mean
range is -23.642857 to -16.107143 tokens. For latency, the corresponding F range is
+1.721093 to +2.140722 seconds and the H range is +0.455960 to +1.205048 seconds.
These ranges describe influence of individual speakers. They are not confidence
intervals, hypothesis tests, or evidence of population generalization. Latency
includes different input lengths and generated output lengths, so it is the cost
of the complete conditioning package rather than isolated retrieval overhead.

## What the style signal measures

The earlier [76-speaker validity controls](../real_persona_chat_style_signal_validity_v1/scientific_report_v1.md)
retained a positive corpus-level margin after length, lexical-marker, exact-repeat,
topic-overlap, and partner controls, while also finding lexical/topic contamination.
That corpus result does not validate a one-reply generation metric.

A separately archived [post-hoc coordinate decomposition](posthoc_style_coordinate_decomposition_v1.json)
shows that -0.082165 of the -0.104083 S effect comes from the length coordinate:
78.94% of its arithmetic change. The remaining five-marker distance has an S effect
of -0.026301 (descriptive leave-one-speaker-out range -0.031667 to -0.018710), on the
same five complete speakers. This diagnostic was added after observing the primary
results and does not replace any frozen endpoint. The percentage is neither causal
mediation nor variance explained. S explicitly supplies length and marker targets;
the evidence primarily supports descriptor compliance, with a smaller marker
conformity component. It does not distinguish speaker identity from generic
shortening or establish linguistic or behavioral Persona Fidelity.

H's positive overlap contrast is a surface-reuse observation. Its negative
reference-F1 contrast cannot establish worse relevance or reliability: a single
human continuation is not the unique correct response, and complete-case selection
can distort effects. No factual accuracy, temporal truth, unsupported-claim rate,
or reliability-fidelity trade-off has been established by these proxies.

## Preserved implementation and measurement findings

The original official [preflight](preflight_v1.json) failed before any model
operation because JSON list masks were compared with equal-valued Python tuples.
It measured 4,854,206,464 available bytes. The original controller, tests, manifest,
authorization, tokenizer evidence, and failed receipt were preserved byte-for-byte.
The [v1.1 integrity amendment](execution_integrity_amendment_v1_1.json), independently
audited and separately authorized before inference, fixes only that representation
comparison. It adds no tokenizer operations and changes no schedule, prompt,
scorer, threshold, or generation setting. The [fresh v1.1 preflight](preflight_v1_1.json)
passed; the run repeated its required prelaunch integrity/resource checks.

Post-run independent inspection found a second, unresolved compatibility issue:
the backend emits `stop_type=eos`, while the frozen shared boundary parser recognizes
`eog`. Consequently, all 60 native-EOS responses have parser status `AMBIGUOUS` and
reason `no_certified_boundary_or_budget_evidence`. The frozen structural flag still
accepts them because it checks identifiable nonempty text, absence of prompt labels,
and status other than `TRUNCATED`. It does not actually require parser certification,
despite the stronger wording in the registered scorer specification. Thus the
60/64 value must be described as the implemented structural flag, not certified
response boundaries or semantic completion. Frozen scores and parser evidence are
unchanged. Any parser/criterion repair must be separately versioned for future
work; numerical reproduction alone cannot validate this shared assumption.

## Resources and reproducibility

Completion inference consumed 342.59149519992934 seconds; batch wall time was
351.21225779999804 seconds. Peak observed server working set was 2,581,692,416 bytes;
minimum observed available physical RAM was 2,332,139,520 bytes. The controller's
3-GiB prelaunch, 1-GiB ready, and 512-MiB per-request gates were retained. No unrelated
application was terminated.

Cumulative authorized usage is now **572/1200 generations and
3514.1361039998983/72000 inference seconds**, leaving 628 generations and
68485.8638960001 seconds. Earlier negative screens and statistical calibrations
remain frozen. The optional synthetic v4 controller still binds the obsolete
508-generation baseline and must not execute unchanged after this batch; it needs
a prospective accounting amendment and its unresolved native-tokenization gates.

The [independent analysis receipt](independent_analysis_reproduction_v1.json)
recomputed 1,024 row metrics, 128 condition summaries, and 112 factorial summaries
from archived HTTP bodies using separately implemented arithmetic, with tolerance
1e-12. It verified the journal chain and resource arithmetic. The frozen boundary
parser is a disclosed shared dependency. This is independent local analysis code,
not independent people, speakers, experimental replication, or human validation.

Run terminal event hash:
`4a86610ce70bced30790e9b1699f9baec0d78f6a4601c04a2703a4ade0655eab`.
Analysis hash:
`2adca94fceb295e2a2d29266aaca9f60280c964a330d561b5dca12c3d59df914`.
The [execution audit](execution_audit_v1_1.json) also links the private analysis.
Generation reproduction was not run. A public clone without private raw data and
model artifacts provides only PARTIAL reproduction.

## Next scientific dependency

The [separate 64-record human protocol](human_review_protocol_v1.json) requires a
Japanese-competent human to assess relevance, coherence, linguistic resemblance,
self-statement/history consistency, unsupported personal claims, and completeness.
Its provenance records prior rubric/item involvement, prior output exposure,
condition exposure, and assistance. A single researcher supplies human judgments
but not inter-rater reliability or independent experimental validation. The earlier
168- and 16-record review requirements remain separate and pending.

The prepared working copy is
`.local/reviewer-packages/real_persona_chat_sfh_pilot_v1/stage_a_delivery/stage_a_WORKING_COPY.csv`.
It contains all 64 records, including the four limit stops, with zero human or AI
labels. Draft validation is `DRAFT_VALID`: zero errors and 64 unfinished-row
warnings. Read the colocated instructions, complete the human-only fields and
truthful exposure/language/assistance provenance, and save incrementally. Run
`python tools/real_persona_chat_sfh_review_v1.py validate-draft` for feedback.
Do not open the protected mapping. Final validation does not itself seal or unblind
the submission. The protocol was frozen before review, not before generation.

Before spending the reserved speakers, obtain those genuine judgments, resolve
the prospective boundary-criterion compatibility issue, and select an endpoint
that distinguishes speaker-related behavior from generic length compliance.
Any subsequent length-only or mismatched-profile control must use a new prospective
development allocation; no such experiment has been executed. No new algorithm or
novelty claim is supported.

The later [scheduled literature delta](../../literature_monitor_v1/daily_scheduled_delta_2026-10-19_v1.json)
contains 216 records and 13/13 successful source requests: four added stable IDs,
five absent IDs, one metadata-only change, and no established version or publication
transitions. This supersedes the earlier 217-record snapshot for current status,
without changing that historical snapshot. Newly observed works are not necessarily
newly published today. Primary-method review of the RoutePrism and MERA preprints
limits novelty claims for order-sensitive memory restoration and evidence-guided
retrieval; the formal ACL factual-consistency stress test supports surface-robustness
checks but does not validate this pilot's semantic measurements. No discovery
recrawl was performed. The working daily scheduler runs metadata collection from
arXiv, Crossref, and OpenAlex, not daily AI deep review or direct queries to every
requested source; comprehensive recall remains unestablished.

The [local preservation receipt](local_preservation_receipt_v1.json) records
entry-by-entry verified archives of private pilot evidence and all review packages.
These copies are outside the repository but on the same physical-volume path:
they do not establish off-device protection or remote backup. Git commits and
pushes remain exclusively managed by the researcher under AGENTS.md.
