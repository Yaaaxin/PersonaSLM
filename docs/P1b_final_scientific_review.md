# P1b Final Scientific Review and Tokenizer Verification — v1

Maintainer: Yaxin ZHENG. Target journal: PLOS ONE. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Formal baseline: Protocol v1.1; proposed v1.2 r1 remains unchanged and unadopted.

## Recommendation

**NO-GO for starting the 192-request calibration now.** Technical prompt/tokenizer preflight has passed. The supplied materials are AI suggestions and contain **0/24 researcher decisions**. They cannot close the existing human stimulus-review gate. No new scientific defect requiring another stimulus version was established in this inspection. Recommend retaining development v2 for a bounded calibration once the existing review and narrow interpretation are confirmed, then explicitly authorizing the run through an appropriate execution adapter.

This is not a request for another broad stimulus search, harder tasks, a new model, perfect natural termination or a new algorithm. No response was generated. The previous preparation reports remain historical; this report resolves their pending tokenizer/date checks with new evidence.

## Supplied materials and preservation

The requested Markdown report was found at [its actual supplied path](validation/p1b/PersonaSLM_P1b_independent_stimulus_audit_v1.md), not at the shorter `docs/P1b_independent_stimulus_audit_v1.md` path. Both supplied CSVs were read in full:

- [24-case AI audit](validation/p1b/review_support/PersonaSLM_P1b_24case_independent_AI_stimulus_audit_v1.csv): 24 rows, 27 columns.
- [Original review with AI suggestions](validation/p1b/review_support/PersonaSLM_P1b_stimulus_review_v2_with_AI_suggestions.csv): 24 rows, 59 columns, including the original 41 fields.

The [source registration](validation/p1b/final_review_v1/source_registration_v1.json) compares every original field: **984/984 unchanged**. IDs, source hashes, answer JSON, exact quotations, original notes and all human fields are preserved. The advertised original review SHA-256 `810ca7e751895aaf3f50b308f1af79aa3c2c67fb9ae6032e93daa0e1cd8658f9` matches the actual file. The original 13 positive-criterion check columns and reviewer decision/provenance columns remain blank. The separate AI-prefixed fields are analysis, not imported human labels.

Original AI status counts remain 13 `HOLD_REFERENCE_DATE_VISIBILITY`, 10 `REVIEW_READY_WITH_LIMITATIONS`, 1 `HOLD_TURN_BOUNDARY_CHECK`. New resolutions are separate, not replacements. Their provenance is researcher-supplied AI analysis awaiting researcher confirmation; no independent blind human review or human timestamp is inferred. Case-specific references are not 24 distinct answer strings: some answers recur across cases.

Dataset `p1b_development_proposed_v2` remains byte-identical, SHA-256 `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6`. The 24 cases, questions, references, S/F/H, recent contexts, applicability, template and request order are unchanged. **No dataset v3 was needed.** A [new tokenized manifest](validation/p1b/final_review_v1/calibration_manifest_v2.json) extends the old preparation with actual IDs/counts, preserving all 192 prompts and their hashes.

## Reference-date visibility: resolved

All **24×8=192** actual model-facing strings contain this exact line, once, before the evidence block:

```text
Evaluation reference: 2027-04-15.
```

The evidence header explicitly describes fictional records. The 13 undated questions in A/B/D/F and H_L1 therefore have an exposed common reference clock; it is not merely CSV metadata and does not come from the computer's current date. Date exposure is verified, not model obedience. Explicit question dates still govern historical propositions, including March 20 in G_L2/G_L3 and April 10 in C/H. The [prompt audit](validation/p1b/final_review_v1/prompt_audit_v1.json) records exact offsets, quotes, hashes and per-condition checks.

All eight cells reconstruct from the original template. Evidence stays in the same prefix location; question, fixed context, answer references and applicability remain equal within case. Only assigned S/F/H additions change. Literal/source-based leakage and contradiction checks remain scoped analytic checks, not a substitute for semantic human review.

## H_L3 boundaries: explicit, with a documented same-speaker follow-up

The following suffix is identical in all eight H_L3 prompts:

```text
RECENT CONVERSATION:
User: Arden Vale has Parcel 151 and Parcel 111.
Assistant: Which one are we arranging?
User: Please focus on Parcel 111.

User: Which desk should it go to on 2027-04-10?
Assistant:
```

Its role sequence is User / Assistant / User / User / Assistant-stub. Both successive User messages are explicitly labelled. The final question is not part of the assistant answer, and the final empty `Assistant:` boundary is present exactly where intended. The focus selects Parcel 111 → Recipient 131 → Ash Desk, valid on April 10. No evidence or role label is missing.

This native Base transcript is not a chat-message array that requires alternating roles. Two consecutive labelled messages from the same user are an explicit follow-up, not demonstrated source corruption. The [source ambiguity check](validation/p1b/final_review_v1/context_necessity_v1.json) finds two possible answers without the focus (Parcel 111→Ash Desk, Parcel 151→Oak Desk). With focus, the source supports one answer. This proves a distinction in the supplied information, **not that the model will use the context correctly**.

Recommend preserving this context. Merging the two User messages or inventing an assistant acknowledgement would change the stimulus without an established validity benefit. The format remains atypical relative to other cases and may affect Base-model continuation. It is a case-specific limitation and not an isolated format treatment. Researcher confirmation of retaining that narrow interpretation is still required; no model behavior was tested or assumed.

## Shortcut and discrimination assessment

| Cases | Concrete risk | Recommended retained role / prohibited inference |
|---|---|---|
| A_L1–L3 | Target archive fact always first; added supply boxes do not add reasoning hops | Easy retrieval anchors with different distractor counts. Do not claim proven difficulty ordering or position robustness |
| B_L1–L3 | 2/3/4 requested answer components; repeated role; output demand covaries with designed level | Integration/output-coverage probes. Record component omissions separately from unsupported or contradictory claims |
| C_L1–L3 | Explicit date filters and inclusive endpoints can be straightforward | Valid interval/boundary probes, not guaranteed discriminative tasks |
| D_L1–L3 | Only one terminal locker/room/building can permit bypassing intermediate links | Evidence-chain calibration candidates, not proof of multi-hop reasoning |
| E_L1–L3 | Relevant true past residence differs from unrelated H in other families | Current/past branch-selection probes; relevance and temporal mechanisms remain entangled with family |
| F_L1 | Question gives exact Morgan North identifier | Deliberate easy identity-lookup baseline, not an entity-disambiguation stress test |
| F_L2/L3 | North/archivist mapping and answer templates recur | Limited role/link probes, not broad entity-resolution evidence |
| G_L1–L3 | Explicit dates identify historical/current states | Valid temporal baselines; a requested past value is not an outdated-answer error |
| H_L1/H_L2 | Only one parcel and one date-appropriate answer without focus | Easy follow-up baselines. They do not establish context necessity |
| H_L3 | Two possible parcel answers; adjacent User messages; record order may still cue a shortcut | Context-sensitive source design with format limitations; no empirical context-use claim |

The offline H diagnostic obtains one possible answer for H_L1, one for H_L2, and two for H_L3. It does not create context-deleted Track A treatments or send ablated prompts to a model. Prior symbolic fact-removal refusals remain oracle diagnostics, not proof that all reasoning links are indispensable for a language model.

**Preserve easy cases:** a calibration bank benefits from valid retrieval anchors alongside more demanding candidates. Making every item harder would remove a useful comparison and risk outcome-driven selection. All 24 remain selected before responses, with the existing family/level labels retained as designed metadata. Future independent material could counterbalance answer position, decoy terminal entities, role mappings and style realizations if a specific hypothesis requires it. That is not required to make the present development questions answerable.

Uniform bookmark facts, style nested in speaker, numbered entities, short evidence and task-family-dependent history remain confounds. S/F/H comparisons measure operational intervention packages, not pure style or temporal mechanisms. No neutral-adjusted P1b effect is planned. The 24 old Wave 1 controls remain OPEN and are not transferred to this dataset.

## Actual pinned GGUF tokenization

An owned local llama.cpp process loaded the pinned model and serviced **192 native `/tokenize` requests**, with `add_special=true`, `parse_special=false`, `with_pieces=false`. Every returned ID array/count is bound to the exact frozen prompt and native response bytes. The adapter rejects `/completion` and other generation routes before HTTP. The raw journal contains **657 events; generation requests 0, responses 0**.

| Verification | Actual result |
|---|---|
| Model | Qwen3.5-2B-Base Q4_K_M; SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` |
| Backend | `/props` build `b11573-0f701c882`; executable SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| Binding | Owned process; reported model path matches pinned local GGUF; binary hashes stable before/after |
| Logged CPU configuration | `n_threads = 4 (n_threads_batch = 4)`; context 4096; `offloaded 0/25 layers to GPU` |
| Input token range | 150–434 |
| Largest input + frozen output budget | 434 + 96 = 530, below 4096 |
| Minimum context headroom after budget | 3566 tokens |
| Context fit / truncation | 192/192 fit; no prompt shortened or truncated |
| Actual generated answers | 0 |

The server performs its normal empty startup warmup; this is visible in the preserved log and is not a calibration response. Its printed chat-template example was not applied: native `/tokenize` received the frozen Base transcript strings directly. The legacy `RuntimeConfig.prompt_template` field is retained only for the existing server transport; the tokenization adapter does not use it to render or replace text. The actual P1b template remains `p1b_transcript_proposed_v1`.

These are new file/backend/tokenizer observations, not proof of upstream quantization fidelity or a hardware benchmark. Output IDs, response latencies and empirical answer completeness do not exist for P1b yet.

Exact input counts, columns C0 through C7:

| Case | C0 | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A_L1 |153|166|165|191|178|204|203|216|
| A_L2 |195|209|207|234|221|248|246|260|
| A_L3 |237|250|249|275|262|288|287|300|
| B_L1 |179|192|190|217|203|230|228|241|
| B_L2 |233|246|245|271|258|284|283|296|
| B_L3 |275|289|287|313|301|327|325|339|
| C_L1 |249|264|261|288|276|303|300|315|
| C_L2 |249|264|261|288|276|303|300|315|
| C_L3 |256|269|268|294|281|307|306|319|
| D_L1 |185|198|196|224|209|237|235|248|
| D_L2 |228|243|240|267|255|282|279|294|
| D_L3 |265|282|276|304|293|321|315|332|
| E_L1 |204|218|216|243|230|257|255|269|
| E_L2 |288|301|300|326|313|339|338|351|
| E_L3 |362|375|373|400|386|413|411|424|
| F_L1 |297|310|309|335|322|348|347|360|
| F_L2 |293|307|305|331|319|345|343|357|
| F_L3 |368|383|380|407|395|422|419|434|
| G_L1 |250|265|262|289|277|304|301|316|
| G_L2 |250|263|262|288|275|301|300|313|
| G_L3 |260|273|271|299|284|312|310|323|
| H_L1 | 150|165|162|189|177|204|201|216|
| H_L2 |252|269|263|291|280|308|302|319|
| H_L3 |345|358|357|383|370|396|395|408|

The [machine-readable counts](validation/p1b/final_review_v1/prompt_token_counts_v1.csv), [tokenizer verification](validation/p1b/final_review_v1/tokenizer_verification_v1.json) and tokenized manifest retain all details. Unequal factorial token lengths are expected when adding S/F/H; this does not establish matched-control equality. No token tolerance was relaxed.

## Output budget and measurement scope

Input fit resolves context capacity only. It does not prove that 96 output tokens are enough for every model realization, especially B_L3's four components or a Base-model reasoning continuation. No extra answers were generated to tune that budget. Keep 96 as the existing controlled calibration setting; record requested/delivered components in completeness/relevance notes. A proposed slot-coverage summary would be a separate diagnostic, not a replacement primary factual metric or an automatic new scoring rule.

Preserve `response_status_v1`, `separate_axes_policy_v1` and the proposed manual P1b routing. Supported partial content need not be factually Incorrect. Unverifiable is not Incorrect. CROSS_TURN can include a complete first reply; AMBIGUOUS units retain uncertainty. A scorer's unsupported syntax remains a coverage failure. All pre-eligible records remain in denominators; no C0-correct filter. Tokenization cannot eliminate the Wave 1 semantic ceiling or predict condition effects.

## Reproducibility and validation

Starting HEAD was **64f5f1a120289df9f4b866687c65bb4e7be4e4af**, with only the three supplied analysis files untracked. New artifacts truthfully retain current Git dirty state, fixed seeds/order, dataset/prompt/source hashes and actual timestamps in structured logs. The tokenized manifest is supplementary to the unchanged preparation manifest; no generated output or historical score was replaced.

The raw tokenizer run is `results/p1b_final_review/v1/runs/20261013T160202-8acbf8a975a04528bf59cd63852cd236`. Raw events/logs and initial exports are local and ignored by Git. Public export revision 2 normalizes only artifact paths and adds links to exact byte source snapshots. Initial exports, their hashes and all 192 token arrays remain available; the [metadata export record](validation/p1b/final_review_v1/metadata_export_v1.json) explains this portable representation. The 44 source byte copies still matched original run hashes when captured; embedded text snapshots may normalize newlines and are not substituted for byte hashes.

Offline replay reconciles all 192 native tokenizer requests/responses and preserves all prompt strings, order and applicability. The 356-file baseline includes the supplied untracked AI material; the only intended historical edit is an append to the development log. Original 3,192 Wave 1 run files remain unchanged. No protocol, P0, Wave 1, earlier review, dataset or template file was edited.

Full test command: `.\.venv\Scripts\python.exe -m pytest -q`. **586 passed, 0 failed, 0 warnings reported, exit 0; pytest 12.38 seconds, captured process 12.989177 seconds.** The 30 added tests cover review-field tampering, actual 192-prompt anchoring, H_L3 boundaries in all cells, competing referents, generation-route refusal, token validation and overflow retention. Targeted tests passed 30 in 0.33 seconds. Their synthetic token arrays are unit-test fixtures only; the published counts above come solely from the real GGUF endpoint.

## Minimal remaining decisions

The [final decision packet](P1b_final_decision_packet_v1.md) has only two unresolved scientific confirmations: complete the existing case-level human validity review, and accept the bounded interpretation of the retained easy/shortcut cases, H_L3 follow-up format and fixed-budget completeness limitation. Mechanical date visibility, invariants and tokenizer fit are already evidenced and need not become new human research tasks.

After those confirmations, the researcher must separately authorize the 192-request run. The existing Wave 1 generator must not be pointed at this dataset: execution still needs a narrow reviewed manifest-consuming path with manual semantic routing. This is the previously recorded operational integration requirement, not a new experiment or scientific acceptance threshold. The tokenization-only tool intentionally cannot generate answers.
