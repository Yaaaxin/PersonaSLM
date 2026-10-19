# RealPersonaChat v1.0.0 Intake and Study Boundary

Status: **dataset intake verified; no model generation; no semantic claim**.

## Scientific purpose

RealPersonaChat (RPC) is the closest located public corpus for a genuine-speaker
S/F/H study: participants wrote their own ten-sentence personas, the public
release retains pseudonymous speaker IDs and timestamps, and many speaker pairs
have repeated dialogues. It can support an exploratory, aggregate study of
persona-conditioning effects. It must not be used to impersonate, identify, or
publish generations about a particular participant.

The authoritative sources are the [v1.0.0 repository](https://github.com/nu-dialogue/real-persona-chat)
and the [PACLIC 2023 paper](https://aclanthology.org/2023.paclic-1.85/).
The paper reports Nagoya University ethics approval and participant agreement,
before collection, not to disclose personal information, to waive copyright,
and to allow public release. The repository distributes the corpus under CC
BY-SA 4.0, says that personal information was masked and ethically problematic
dialogues were withheld, and expressly warns against re-identification and
impersonation. Copyright permission does not erase privacy or personality-right
constraints; this project adopts the narrower repository boundary.

## Pinned local source

- Release: `1.0.0`; Git tag: `v1.0.0`.
- Commit: `28d0b6b3865b29cabc26c230a2db37cdf315e937`.
- Local location: ignored `.local/datasets/real-persona-chat`; raw data must not
  be staged, committed, or copied into public evidence.
- The versioned intake receipt records exact LICENSE, README, VERSION,
  interlocutor-file, and dialogue-manifest hashes. It emits no participant text
  or speaker IDs.

The public release was recalculated as 13,583 dialogues, 408,619 utterances,
233 speaker records, and 1,572 speaker pairs. All 233 persona records contain
ten sentences. There are 408,267 populated timestamps and 352 `NaT` values.
The public filtering changes one paper-era boundary: the released data contain
4--203 dialogues per speaker, whereas the paper describes 5--204 in the
original 14,000-dialogue collection. Analyses must use release statistics.

## Prospective separation

Speaker IDs are assigned by ascending SHA-256 of
`PersonaSLM-RPC-speaker-split-v1`, a NUL byte, and the pseudonymous ID:

- development: 117 speakers;
- exploratory test: 58 speakers;
- independent validation reserve: 58 speakers.

Only dialogues whose two participants belong to the same split are eligible.
Cross-split dialogues are excluded, preventing both target-speaker and partner
identity from crossing partitions. The pinned release yields 3,636 development,
813 exploratory-test, and 813 validation-reserve dialogues; 8,321 cross-split
dialogues are excluded. This deliberately sacrifices data for leakage control.
The validation reserve is not available for development decisions.

S, F, H, and targets must be temporally and textually disjoint within a speaker.
F may use only the participant-authored persona sentences. Personality scales,
demographics, and text-chat-experience fields are excluded. Any pilot must
pre-register how earlier dialogues supply S/H and how later turns supply targets,
then audit exact and near-duplicate leakage before inference.

## Measurement and publication boundary

No current automatic metric establishes Japanese individual-speaker Persona
Fidelity. Lexical copying is not a valid substitute. A generation pilot is
therefore blocked until a Japanese-capable, condition-blinded semantic rubric is
frozen and its applicability is demonstrated. Genuine researcher review would
still be single-rater evidence, not inter-rater reliability or independent
validation.

Only aggregate results may enter public reports. Row-level prompts, outputs,
speaker mappings, persona sentences, histories, demographic data, and sensitive
content remain local. The study must be described as pseudonymous aggregate
effect estimation, never as recreation of identifiable people.

## Current decision

`GO` for local, read-only materialization and leakage/evaluator development on
the development split. `NO-GO` for model generation until the semantic
instrument and finite prospective allocation are frozen. `NO-GO` for
impersonation, re-identification, row-level publication, demographic/personality
prediction, training, or use of the independent validation reserve during
development.
