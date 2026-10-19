# Persona Fidelity measurement proposal v1

Maintainer: Yaxin ZHENG. P1d/P3/P4/P6; RQ1–3 and H4/H5. AI-assisted prospective measurement development; no human scores or adopted rubric are fabricated. Existing historical metrics are unchanged.

## Constructs and opportunities

Linguistic Fidelity concerns speaker-specific lexical preferences, sentence rhythm, punctuation, register and response style. Behavioral Fidelity concerns validated conversational choices across situations: answer versus acknowledgment ordering, recommendation versus option enumeration, or an established clarification pattern. Neither is factual correctness, task success, generic politeness or similarity to the input prompt. A model can imitate a speaker while giving a wrong answer, or answer correctly in an incompatible style.

Use a profile plus several independently validated reference utterances from disjoint situations. For synthetic data, describe this as fidelity to a constructed profile, not an actual person's behavior. Real-speaker traits require authorized observations and a chronological held-out split. Do not derive the target style from the output being scored. Two broad style instructions repeated under many names are not many independently validated linguistic personas.

Before generation, mark each case's lexical/rhythm/punctuation opportunity and each behavioral choice opportunity. Short fact-only answers often permit too little evidence; record INSUFFICIENT_OPPORTUNITY separately from low fidelity. N/A means the task was predefined as inapplicable, not a failed answer. Missing response, unavailable boundary and unresolved interpretation remain distinct. The new script's eight-word indicator is a provisional diagnostic flag only, not an adopted exclusion rule or validated psychometric threshold.

## Independent scoring procedure

1. The quality panel sees evidence, question, frozen first reply and requested date, but not the target style instructions. It assesses factual/temporal support, relevance, coherence, components and task success separately.
2. The fidelity panel sees a pseudonymized profile, disjoint reference utterances, scenario and reply; hide model, condition, other ratings and expected scientific effects. Supply contextual information needed to judge behavior, not a reference task answer. Answer values can be masked in a separately assessed sensitivity view; never silently delete cues needed for style/behavior.
3. Score linguistic and behavioral dimensions independently on 1–5: 1 clear repeated incompatibility; 2 mostly inconsistent; 3 mixed or weakly expressed; 4 clear alignment with a minor deviation; 5 clear alignment across the **available** opportunities. Cite separate spans/features and an alternative interpretation. Insufficient evidence is not forced to 3 or 1. Do not award points for exact prompt phrase copying alone.
4. Behavioral scoring uses a predeclared scenario-specific choice code, then a separate fidelity judgment. Appropriate exceptions to a preference (e.g. a genuine need for clarification) require the reference policy to allow them; do not reward rigid repetition or unnecessary questions.
5. Obtain independent judgments before revealing AI proposals or other raters. Register researcher adoption of AI suggestions separately. Adjudication produces a resolved label without retroactively describing the original judges as agreeing.

Masking does not guarantee semantic blindness: tone, names or response format may reveal an intervention. Record suspected unmasking and keep it separate from a score. No independent reviewer has been recruited or rated this material.

## Working materials and objective aids

`validation/research_alignment_v1/` contains three authored profiles, 12 counterexamples, a fidelity-only blind review CSV and a separate quality panel CSV. Examples deliberately cross correct/incorrect facts with compatible/incompatible style, and compatible linguistic form with reversed behavioral ordering. These are calibration examples, not model outputs or a validation set. All researcher fields are blank.

`tools/personaslm_alignment.py` extracts word count, sentence rhythm, contractions, semicolons and emphatic punctuation. These are inspectable features, not an automatic fidelity score. Reference-conditioned distributions, alternative legitimate expressions and content dependence must be validated. Perfect feature matching would not establish identity or behavioral fidelity. The current eight Instruct responses permit only the original narrow brief/calm style assessment; behavioral fidelity was not predefined and is not retrofitted as a confirmed outcome.

## Independent validation and analysis

Prospectively sample paired cases across every S/F/H cell, task family, model and template block before reading outcomes. An initial **measurement-only** target is 24 independently constructed cases, all eight cells (192 replies if later authorized), balanced across four task families, with two genuinely independent human reviewers. This is a proposed annotation workload, not a generation authorization or a sample-size justification for factorial effects. Include boundary ambiguity and short-answer strata by prespecified sampling with known probabilities; report both stratum results and weighted overall summaries.

Use ordinal agreement (weighted kappa or ordinal alpha) separately for linguistic and behavioral scores, categorical agreement for applicability/choice states, and raw contingency tables. Bootstrap whole speaker/case blocks for uncertainty; do not pool dimensions. Examine ceiling/floor rates, cross-construct concordance, wrong-but-stylish and correct-but-unstylish counterexamples. Final acceptable disagreement limits require rubric calibration before confirmatory freeze. If a second reviewer is unavailable, report the absence and keep the measurement claim limited; AI adoption is not inter-rater reliability.

The protocol draws on multidimensional persona evaluation already studied in [TwinVoice](https://aclanthology.org/2026.findings-acl.981.pdf) and extended-interaction fidelity in [Persistent Personas?](https://aclanthology.org/2026.eacl-long.246.pdf); it does not claim those constructs as new. Remaining evidence is reliable use of separate fidelity and correctness measurements in the controlled CPU S/F/H programme.
