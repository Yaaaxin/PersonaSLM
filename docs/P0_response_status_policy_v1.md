# P0 Response Status Policy v1

Version: `response_status_v1`. This is a measurement policy under Research Protocol v1.1, not a protocol amendment or a new prompt treatment. Primary language: English. The previous four diagnostic tasks, raw outputs and parsers remain unchanged. No prompt or stop rule is tuned on them here.

## Status definitions and precedence

| Status | Operational meaning | What it does not imply |
|---|---|---|
| COMPLETE | A nonempty, identifiable reply has an observed boundary (EOS, certified declared marker or certified native string stop) **and a separately supplied completeness judgment** bound to the raw-response hash | The reply is factually correct, relevant, coherent, or naturally terminated |
| TRUNCATED | The backend reports maximum-token termination and no earlier certified reply boundary is visible | The visible statement is false, or necessarily semantically unfinished; this is a boundary-censored observation |
| CROSS_TURN | The saved output visibly continues beyond the first reply into a recognized speaker turn, or beyond the declared end marker | The extracted first reply is semantically complete or factually wrong |
| AMBIGUOUS | The unit is ambiguous, backend evidence conflicts, the first unit is empty, or sufficient boundary/semantic-completeness evidence is unavailable | A generation failure or an incorrect fact |

Precedence: delimiter/content hazards or contradictory backend evidence -> AMBIGUOUS; visible subsequent turns -> CROSS_TURN; certified end plus independent completeness support -> COMPLETE; certified end without that support -> AMBIGUOUS; otherwise an observed cap -> TRUNCATED; otherwise AMBIGUOUS. All reasons and independent axes survive this single summary status.

The measured first reply is the exact text span before the first recognized line-start role transition, allowing mixed capitalization and horizontal whitespace. Role vocabulary: User, Assistant, System, Human, Bot. One optional leading Assistant prefix is recorded separately. Ordinary newlines are preserved. A declared, whole-line `<END_OF_REPLY>` is recognized; undeclared or arbitrary string stops do not certify boundaries. Inline, quoted, fenced, unknown-label or predeclared literal-delimiter cases are routed conservatively to ambiguity, not silently split as certified replies.

Raw text, UTF-8 SHA-256, exact start/end offsets, prefix and excluded tail are retained. Rejoining these three spans reconstructs the raw text exactly. Backend termination data and generated tokens stay separate from the status. A role continuation can be observed before a later token cap. Missing EOS is not a mandatory failure when another boundary is supported.

## Completeness evidence and honest uncertainty

A completeness judgment requires label COMPLETE / INCOMPLETE / UNCERTAIN, review ID, basis and the exact raw SHA-256. The instrument validates structure and binding, not human identity or independence. Software fixtures explicitly identify their supplied judgments as engineered expectations, never human ratings. No such judgment is invented for actual model output; absence remains UNCERTAIN. A bounded stopped response may therefore be AMBIGUOUS for semantic completeness while still having an identifiable span for factual assessment.

Literal-delimiter risk is declared from the task before generation where known. Automated hazard detection is conservative and does not certify arbitrary code, quoted transcripts, unusual speaker names or inline discourse. Ambiguous outputs stay in the pre-eligible set and require independent adjudication under the existing annotation guidelines. Abstention coverage and status distributions must be reported alongside accuracy.

## Freeze and validation design

Sixteen newly authored software development examples exercise the required mechanisms, separately from the historical four cases. After development checks, save the source, policy documents, test-fixture and dependency hashes and exact UTF-8 snapshots. Then create a separate 24-example software holdout and six new English synthetic inference cases. Seal their hashes and prompt/configuration hashes **before** evaluating the holdout or generating its real outputs. Evaluate once without adapting policy to observed results. Any later changed rule requires a new policy version and a new independent holdout; old failures remain.

Holdout accuracy is exact status agreement with the authored software contract, with a confusion matrix, per-class counts, ambiguous cases and exact span checks. It is not estimated human semantic accuracy: the author knows the policy, no independent annotator is available, and these are constructed inputs. Report accuracy on all cases and coverage excluding AMBIGUOUS separately; do not hide uncertain samples. Real holdout outputs have no independent boundary/semantic ground truth, so report their classifications and limitations rather than inventing an accuracy denominator.

The six real cases use unchanged C0 `transcript_base_v1`, no native stop strings, 96 maximum new tokens, seed 42, temperature 0, top_p 1, CPU 4/4 and context 4096. They test the measurement path; they do not tune prompts, compare Persona effects or demand natural EOS. Retain legacy run scores and add policy-versioned offline sidecars. No full factorial or P1 experiment is performed.

The freeze also binds [evaluation policy v1](P0_evaluation_policy_v1.md). The final report links exact freeze timestamps, hashes and observed results; the source policy remains unchanged after holdout access.
