# P1b Calibration Next Experiment Decision

Maintainer: Yaxin ZHENG. Version 1. Formal Protocol v1.1; proposed v1.2 r1 remains unchanged and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE.

## Current recommendation

**Complete condition-masked semantic review of the existing 192 outputs before authorizing more inference.** Execution is complete; semantic effect estimation and whether the Wave 1 ceiling was reduced remain pending. This decision does not reopen stimulus approval or require perfect model performance. It uses the information already purchased by the bounded CPU run.

| Option | Information value and trigger | Remaining confounds | Cost / decision |
|---|---|---|---|
| Score existing calibration | Establish factual/temporal discrimination, first-reply completeness and scorer coverage | Assisted/experienced single-researcher review must be disclosed; extraction uncertainty retained | Zero new generations; reviewer effort unmeasured. Recommended now |
| Expand Base on independent cases | Useful precision and replication only after coverage and variance are known | Speaker/style nesting, task templates and unchanged termination may persist | Eight calls per new case. No size or latency extrapolation asserted; not authorized |
| Separate Instruct arm | Could assess whether a different operational configuration improves usable dialogue measurement | Post-training, artifact provenance and native template may change together; not a pure post-training effect | A full 24-case eight-cell arm would require 192 new calls, with unknown per-call CPU cost. Later authorization and hashes required |
| Narrow boundary diagnostic | Valuable if complete first replies are obscured or false cuts materially distort contrasts | Stop strings alter generation opportunity; template differences need independent material | Bounded new allocation must be prospectively justified; no repeated tuning on these answers |
| Independent discriminative material / history R–T diagnostic | Useful if review reveals a specific ceiling or conditional history question | Relevance/time/task family are not separated here; new factors need explicit approval | No new candidate bank or calls now; use independent evidence and retain null/negative outcomes |

The immediate prerequisite is valid outcome measurement, not an algorithm or another model. Once reviewed, report complete denominators, case-paired estimates, speaker uncertainty, negative/null patterns and substantive unresolved ambiguity. The researcher decides the next arm. Neutral-control review remains OPEN; the prior 24 candidates are Wave 1 materials and do not authorize P1b matched comparisons.

## Novelty and publication relevance

The [existing novelty matrix](related_work_novelty_matrix.md) documents direct overlap in persona sensitivity, history-aligned factual distortion, memory selection and structural failures. A new cache-miss fetch does not invalidate or reverify an old literature record. Current primary-record checks are retained in [the access register](validation/p1b/calibration_v1/literature_access_v1.json).

*Principled Personas* already evaluates intended persona effects and sensitivity to irrelevant attributes; persona cues alone are not novel. [Primary record](https://aclanthology.org/2025.emnlp-main.1364/). *When Personalization Misleads* directly studies personalized factual distortion; its claimed mechanism is not proven by our package contrasts. [Primary record](https://aclanthology.org/2026.findings-acl.395/). A possible additional contribution would require reproducible evidence that separating structure from semantic support changes an S/F/H interpretation on independent material. This remains a falsifiable prospective claim, not a discovery from the current unscored bank.

PLOS ONE requires rigorous methods, supported conclusions and sufficient reproducibility, considers negative/null results, and asks close replications to provide a scientific rationale. Successful execution alone does not meet those conditions. [Journal criteria](https://journals.plos.org/plosone/s/criteria-for-publication). This calibration supplies auditable development evidence; independent validation, precision and contribution assessment remain necessary before a publication claim.

## Algorithmic Opportunity Assessment

The separate [assessment](P1b_calibration_algorithmic_opportunity.md) considers selection, temporal validity, style/evidence separation, response boundaries and verification. It recommends no algorithm implementation now. Natural continuation is observable; factual failure mechanisms and the benefit of a correction remain unestablished without review and identifying comparisons.
