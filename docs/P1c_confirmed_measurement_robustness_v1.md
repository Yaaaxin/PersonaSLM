# P1c confirmed boundary and missingness robustness v1

Maintainer: Yaxin ZHENG. This report uses the researcher-adopted primary and secondary views, with no resampling of model outputs and no new ratings. Original response_status_v1 remains frozen.

## Structural and semantic cross-tabulation

All 72 requests succeeded: 64 CROSS_TURN and eight AMBIGUOUS, zero COMPLETE/TRUNCATED. All 64 identifiable first replies are semantically complete; their factual labels are 43 Correct, 20 Incorrect and one Unverifiable. Their temporal labels are 43 Correct, 15 Incorrect and six Unverifiable. Thus cross-turn continuation is compatible with either a correct or wrong complete first answer. It is not automatic factual failure. The eight AMBIGUOUS units retain primary factual/temporal Unverifiable, uncertain task/completeness and unscorable ordinal/component ratings.

All 64 CROSS_TURN outputs reached the token budget. Six ambiguous outputs also reached it; two ended by EOS. Budget termination is therefore compatible with 64 complete first replies. Both EOS outputs remain structurally ambiguous. Native termination and first-reply validity are separate observations. No causal output-budget claim follows without a controlled budget/template experiment.

## Eight sensitivity-only prefixes

Every candidate is a byte-preserved substring of the raw continuation, with raw/prefix hashes, parser trace and excluded tail in the immutable source. A section heading supports the proposed cut but is not a native turn token; document-continuation interpretations remain. All eight primary structural statuses stay AMBIGUOUS. The accepted sensitivity does not certify unique boundaries.

| ID | Native stop | Generated tokens | Secondary factual | Secondary temporal | Secondary task (1/0) |
| --- | --- | ---: | --- | --- | ---: |
| PC010 | eos | 85 | Correct | Correct | 1 |
| PC023 | eos | 93 | Correct | Correct | 1 |
| PC033 | limit | 96 | Incorrect | Unverifiable | 0 |
| PC039 | limit | 96 | Incorrect | Unverifiable | 0 |
| PC042 | limit | 96 | Incorrect | Unverifiable | 0 |
| PC044 | limit | 96 | Correct | Correct | 1 |
| PC054 | limit | 96 | Incorrect | Incorrect | 0 |
| PC063 | limit | 96 | Correct | Correct | 1 |

The [confirmed eight-item export](validation/p1c/confirmed_semantic_v1/robustness_exports/eight_confirmed_sensitivity_records_v1.csv) retains original blank proposal-confirmation fields as source history and appends explicit registered scope. It does not pretend those original fields were independently entered by the researcher. PC023's two revised ordinal scores are included only in the accepted secondary view.

## All registered measurement-effect differences

Compute secondary-minus-primary **within output**, then apply the original contrast within case, then equal speaker means. This avoids subtracting means from differently selected assessable subsets. All values below are percentage points. F-C denotes Correct-label incidence, T-I temporal Incorrect-label incidence. Intervals are 10,000-draw whole-speaker bootstrap sensitivity, seed 715004, not guaranteed population confidence coverage.

| Contrast | Change in F-C effect | Resampling interval for change | Change in T-I effect | Primary AMBIGUOUS incidence effect |
| --- | ---: | --- | ---: | ---: |
| N_history-H_none | +8.33 | [+0.00, +25.00] | +0.00 | +8.33 |
| R | +4.17 | [+0.00, +12.50] | +4.17 | +12.50 |
| R0T0-H_none | +8.33 | [+0.00, +25.00] | +0.00 | +8.33 |
| R0T0-N_history | +0.00 | [+0.00, +0.00] | +0.00 | +0.00 |
| R0T1-H_none | +0.00 | [+0.00, +0.00] | +0.00 | +8.33 |
| R0T1-N_history | -8.33 | [-25.00, +0.00] | +0.00 | +0.00 |
| R0T1-R0T0 | -8.33 | [-25.00, +0.00] | +0.00 | +0.00 |
| R1T0-H_none | +8.33 | [+0.00, +25.00] | +8.33 | +25.00 |
| R1T0-N_history | +0.00 | [-25.00, +25.00] | +8.33 | +16.67 |
| R1T0-R0T0 | +0.00 | [-25.00, +25.00] | +8.33 | +16.67 |
| R1T1-H_none | +8.33 | [+0.00, +25.00] | +0.00 | +16.67 |
| R1T1-N_history | +0.00 | [+0.00, +0.00] | +0.00 | +8.33 |
| R1T1-R0T1 | +8.33 | [+0.00, +25.00] | +0.00 | +8.33 |
| R1T1-R1T0 | +0.00 | [-25.00, +25.00] | -8.33 | -8.33 |
| RxT | +8.33 | [-25.00, +50.00] | -8.33 | -8.33 |
| T | -4.17 | [-12.50, +0.00] | -4.17 | -4.17 |

R/T/RxT factual Correct-incidence effects move by +4.17/-4.17/+8.33 points, respectively, yielding zero secondary means. This is a property of these measurement views and six synthetic clusters, not proof that the primary is wrong or that the secondary is true. Some case contributions still cancel. Temporal Incorrect-incidence effects move by +4.17/-4.17/-8.33 points. Do not select a boundary rule according to these signs.

## Unknown outcomes and identification limits

Primary factual/task uncertainty includes eight unresolved boundaries and one interpretation issue. Temporal uncertainty additionally includes five entity/interval attribution issues. Secondary factual/task uncertainty leaves PC006; temporal uncertainty remains on nine units. No U label is recoded as a factual error. No unknown ordinal score is set to zero. All 72 outcomes remain eligible.

For scalar sensitivities, a case contrast is point identified only when every required nonzero-weight cell is known. Otherwise its original signed weights and the endpoint range produce lower/upper bounds. Speaker means retain both cases; no surviving-cell reweighting. Secondary-minus-primary scalar differences remain unknown if either value is unknown. Their conservative bounds span possible differences rather than fabricating paired values. Resampled bound endpoints and leave-one-speaker-out bounds are supplied separately from point-estimate intervals.

Categorical label incidence includes Unverifiable as an observed category, while C-versus-I sensitivity excludes U from assessability and discloses the selected cases. These represent different estimands. Null numeric scores are reason-preserving unscorability/uncertainty, not absent researcher decisions. Administrative missing confirmations are zero.

Six purposive clusters and only two speakers per task family limit all population interpretation. Apparent ambiguity differences can influence evaluation coverage; the study does not establish a latent response-boundary mechanism. No confirmatory significance tests or new endpoint hierarchy were introduced.

## Algorithmic Opportunity Assessment

**Observed Failure Modes:** headings can precede extra generated content, and native EOS does not guarantee a single reply. **Existing Methods and Published Prior Art:** the [offline baseline report](P1c_offline_boundary_baseline_assessment_v1.md) compares native stopping, literal roles, headings and a code-fence guard, and reviews constrained generation and verification. **Potential Algorithmic Improvements:** cautious abstention is a known engineering candidate; no original algorithm is established. **Validation Feasibility:** independent span adjudication and held-out quoted-role/heading examples are necessary, followed by separately authorized template/stop experiments where useful. **Publication Value:** measurement robustness can improve the empirical paper, but recovery of the eight inspected prefixes is not independently validated accuracy or publication readiness.
