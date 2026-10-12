"""Append the observed v2 development evidence without rewriting earlier reports."""
from collections import Counter
import json
from pathlib import Path

from personaslm.journal import utc_now
from p0_control_development_v2 import ROOT, SESSION, PUBLIC, FREEZE, VALIDATION, read, save, digest


def append(path, text):
    with path.open("ab") as handle:
        handle.write(("\n\n" + text.rstrip() + "\n").encode("utf-8"))


def main():
    observed = read(VALIDATION)
    frozen = read(FREEZE)
    integrity = read(PUBLIC / "P0_control_development_integrity_v2.json")
    tests = read(SESSION / "engineering/full_tests.json")
    now = utc_now()
    test_summary = tests["stdout"].strip().splitlines()[-1]
    if tests["exit_code"] != 0 or not test_summary.startswith("285 passed"):
        raise ValueError("Report requires the actually observed complete test result")
    counts = {s["case_id"]: {} for s in frozen["case_specs"]}
    selected = []
    for p in observed["pairs"]:
        a = p["attempts"][p["matching"]["best_candidate_index"]]
        counts[p["case_id"]][p["family"]] = f'{p["reference_token_count"]}/{a["token_count"]}'
        selected.append({"case_id": p["case_id"], "family": p["family"], "reference_condition": p["reference_condition"],
                         "reference_token_count": p["reference_token_count"], "neutral_token_count": a["token_count"],
                         "token_difference": a["token_difference"], "candidate_index": a["candidate_index"],
                         "conditioning_text": a["conditioning_text"], "prompt_sha256": a["prompt_sha256"],
                         "trusted_evidence_hash": p["trusted_evidence_hash"], "prompt_template_version": p["prompt_template_version"],
                         "attempts": len(p["attempts"]), "exact_candidates_in_pool": sum(t["token_difference"] == 0 for t in p["attempts"]),
                         "shared_suffix_tokens": a["shared_suffix_tokens"], "human_review": "OPEN"})
    save(PUBLIC / "P0_control_development_selection_v2.json", {"created_utc": now, "validation_sha256": digest(VALIDATION),
        "selected": selected, "selection": "First exact match from the frozen pool; no completions or human labels used"})
    table = "\n".join("| " + " | ".join([case_id, row["style_generic"], row["history_format"], row["history_topic"], row["history_stale_generalized"]]) + " |"
                      for case_id, row in counts.items())
    test_text = f"**285 passed, 0 failed, 0 warnings reported**, pytest **15.44s**, process **{tests['duration_seconds']:.3f}s**, exit **0**. Actual interval: `{tests['started_utc']}` to `{tests['finished_utc']}`."
    report = f"""# P0 Control Development v2 — Engineering and Identification Report

Recorded **{now}**. **P0 PARTIAL; neutral-control validity OPEN; P1 NOT STARTED.** Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Protocol v1.1 and the English scope are unchanged. Researcher/maintainer: Yaxin ZHENG.

## Scope and frozen development selection

This is tokenizer-only engineering, not a reliability experiment. Candidate version `neutral_control_candidate_v2_dev`; prompt version `transcript_base_v1`. Six invented development cases were specified before tokenization: Riley, Samara and Devon reuse the three v1 development scenarios, while Tessa, Blair and Robin are newly authored. All six were included by construction; none was selected using answer quality. They are not a holdout or a confirmatory set. The three reused cases support declared engineering repair, not out-of-sample generalization. The original four response-boundary examples were not reused for tuning.

Each case uses the original `build_prompt` factory, the unchanged style-profile heading, fixed named speaker in current question/evidence, and the same evidence/question across all variants. The historical twenty-case dataset, its forty controls and all researcher annotations are unchanged. New synthetic cases and exact source bytes are contained in [the freeze](validation/P0_control_candidate_freeze_v2.json); no private dialogue was used.

The entire pool was frozen at `{frozen['created_utc']}` before requests. It contains 32 single-sentence style candidates, 16 neutral-format question/answer pairs, 12 topic-clarification replies and 10 generalized-residence replies per case: **420 candidate prompts plus 24 reference tokenizations = 444 requests**. Selection is the first exact match in fixed order; fallback is smallest absolute difference, then earliest index. Tolerance remains **0**. All failed alternatives remain in the artifact, even though every pair has at least one match. No adaptive pool expansion or generation followed the observed counts.

## Why v1 style matching failed

The old pool concatenated one or two complete sentences, leaving gaps in achievable lengths. Actual saved counts were 94/95/102/103/104 against target 100 for Riley, 96/97/104/105/106 against 100 for Samara, and 94/95/102/103/104 against 98 for Devon. Best differences remained +2/-3/-3. These are observed candidate-coverage failures, not evidence of a faulty tokenizer. Old failures remain intact.

V1 also used `Speaker context:` instead of the original wrapper's `Speaker style profile:`. V2 restores the original factory for both arms, so the first three reference lengths become 101/101/99. This explicit version change means the v1/v2 numbers are not silently presented as the same prompts. The new pool supplies a broader range of natural single-sentence lengths without repetitive sentence padding or copied answer facts. No assertion that generic prose is stylistically inert follows from its wording.

## Actual complete-prompt token matching

Numbers are **reference/candidate** counts, including backend special-token behavior, for the selected candidate. Every difference is zero. A/B/C refer to the distinct history families below, not additional official factorial conditions.

| Case | Style | History A: format | History B: topic | History C: generalization |
|---|---:|---:|---:|---:|
{table}

Thus **style 6/6, A 6/6, B 6/6, C 6/6**, or **24/24 engineering matches**. All 420 candidate constructions preserve wrapper, trusted evidence and current question. Selected complete-prompt token arrays share 31–35 suffix tokens with their references; exact IDs and prompt hashes are saved. Byte offsets inside variable-length additions are not asserted to be identical. Overall input token length, intervention position and unchanged outer text are controlled. This is bounded verification on six cases, not universal matching performance.

Sources: [all attempts and token IDs](validation/P0_control_tokenizer_validation_v2.json), [selected texts and hashes](validation/P0_control_development_selection_v2.json). Run `{observed['run_directory']}` contains **{observed['journal_events']} chained events**. Tokenizer `/tokenize`: `add_special=true`, `parse_special=false`, `with_pieces=false`. Owned llama.cpp `/props` reports **{observed['backend_binding']['build_info']}**, matching model path and context 4096; model/server preflight and postflight hashes agree. Configured CPU threads/batch 4/4 and zero GPU layers are retained in the server journal. This run does not independently repeat prior hardware measurements or generate new performance data.

GGUF SHA-256: `{observed['model_sha256']}`. Server SHA-256: `{observed['server_sha256']}`. File identity does not establish independently reproduced upstream quantization fidelity. **Completion requests: 0.** No new raw or parsed model responses, output tokens, EOS or factual scores exist for these candidates; those fields are not applicable, not fabricated zeros from a generation experiment.

## Control families and estimands

| Comparison | What is held fixed | Defensible proposed interpretation | Residual confounds / limits |
|---|---|---|---|
| C1–C0 | Trusted evidence, current question, recent context | Total insertion effect of this style profile | Added length, heading, semantics and style all change |
| C1–new N_style | Above plus heading, position and total tokens | Replacing generic discourse description with a style profile | Generic prose has its own register; heading can cue style; semantic salience and instruction force differ. Human validation required |
| C3–C0 | Trusted current evidence/question | Total effect of adding the specified dated old-residence dialogue | Length, old information, topic, temporal cues and dialogue format are bundled |
| C3–A `history_format` | Named speaker, date/header syntax, User-to-speaker turn order, two turns, position and total tokens | Residence history versus an equally presented unrelated exchange | Topic relevance, personal information, assertion type and internal past reference differ; cannot isolate historical format |
| C3–B `history_topic` | Same historical question, residence topic, speaker, date, structure, position and total tokens | Old-residence answer versus a residence clarification | Answer/clarification speech acts differ; potential questioning, uncertainty and abstention priming; not a semantic placebo |
| C3–C `history_stale_generalized` | Residence topic, dated prior-city residence, speaker, question, structure and total tokens | Named old city versus an unspecified old city: information-specificity ablation | Informativeness, lexical choices and evasiveness change; no pure stale-fact mechanism or neutral-control claim |

Example selected style: `A conversation includes an exchange of questions and replies between participants.` It contains no named city or new personal fact, but its generic expository register may still affect behavior. A selected A exchange asks `What does a conversation involve?` and replies `An exchange of questions and replies.` It repairs the earlier unrelated document-statement adjacency, while remaining off the residence topic. B uses `The city or the address?` or `Are you asking about the city?`, retaining the historical question but adding clarification behavior. C uses `In a city back then.` or `In a city at the time.`; it preserves a vague past-residence assertion deliberately.

The explicit name in every development question/evidence fixes the earlier `the person`/Alice referent ambiguity only for these new inputs. Date values and timestamp syntax are mechanically equal across each history pair. A lacks the reference's internal past-tense residence relation. B retains the old-time question but provides no historical fact. C retains past-city residence without its name. Natural coherence, temporal interference and unintended style remain **unreviewed human questions**, despite mechanical checks.

Exact token equality controls total context length, not token content, attention allocation, within-block information position or semantic difficulty. A cannot isolate topic relevance; B cannot isolate factual content independently of response pragmatics; C cannot isolate temporal conflict from named-answer competition. A named old city valid in the past is not itself a false statement. Identifying temporal-conflict effects would require a separately approved time-validity manipulation with content balanced. Identifying history presentation would require the **same facts** in prose and dialogue, with length/position checks. Neither diagnostic was executed here. Track A trusted evidence remains fixed, and Persona Fidelity remains separate from Dialogue Reliability.

## New human review and acceptance

The [new CSV](validation/P0_control_development_review_v2.csv), [JSON master](validation/P0_control_development_review_v2.json) and [English guide](P0_control_development_review_v2_guide.md) cover **24 items: 18 proposed neutral/control alternatives and 6 non-neutral diagnostics**. All human labels, identities, times and notes are blank: **0/24 reviewed**. Fourteen judgment axes, exact evidence-quote fields, version/hash checks and an immutable importer support tracking. Optional review time remains blank when unavailable. The software importer was tested with clearly marked artificial fixtures only; no actual human import occurred.

The original **40/40** researcher reviews remain complete, with original overall **PASS 0 / PARTIAL 40 / FAILED 0**. They do not transfer to new wording. This package offers alternatives: adopting every family or reviewing unused diagnostics is not a new blanket P0 gate. Before adoption, review the selected intended control inventory and resolve FAIL/UNCERTAIN findings with defensible claim boundaries. No new annotations or acceptance decision have been supplied.

| Requirement | Status | Evidence / remaining limitation |
|---|---|---|
| Exact final-prompt accounting and wrapper preservation | PASS | 24/24 selected pairs, tolerance 0; all attempts retained |
| Candidate source/version freeze and no answer-based selection | PASS | Freeze precedes 444 tokenizer calls; no completion calls |
| Old records and frozen protocol/policies preserved | PASS | 110 protected files and 22 historical journal inventories unchanged |
| Journal integrity and selected-result reconstruction | PASS | All 23 current chains checked; 24 new pair results reconstructed |
| Old human review completeness | PASS | 40/40 unchanged; validity remains PARTIAL |
| New candidate semantic review | PARTIAL / OPEN | 0/24; actual human review needed for controls to be adopted |
| Historical control validity | PARTIAL | Existing style/topic/identity findings unresolved for old materials |
| Identification of isolated style/history/time mechanisms | PARTIAL | Narrow replacement contrasts specified; residual confounds explicit |
| New development software | PASS | {test_summary}; existing runner/evaluators unchanged |
| Overall P0 acceptance | PARTIAL | Engineering matches do not close semantic validity; P1 requires closure and researcher approval |

Acceptable limitations include bounded model termination behavior under the frozen policies, unsupported backend evaluated-input arrays and unverified upstream quantization equivalence, within the already stated scope. Future robustness, fidelity studies and mechanism experiments are research extensions; perfect model performance or all external interfaces are not prerequisites. Neither P1 nor training was started.

## Tests, errors and reproducibility

{test_text}

Initial new-module tests: **16 passed, 6 failed**, exit 1, 0.36s. A `dataclasses.asdict` result retained a tuple of facts while the existing schema correctly requires a list. The new development serializer was corrected to emit lists; the old schema and tests were not weakened. Targeted rerun: **22 passed**, 0.13s, exit 0. A read-only inspection initially used nonexistent `schema.py`; the correct `schemas.py` was then read. That PowerShell command continued with exit 0 despite the read error. Both limitations are recorded rather than suppressed.

Starting HEAD: `{integrity['git_commit']}`, dirty **true**, with 40 preexisting uncommitted files. New run manifests retain the exact commit, dirty status, dataset/source/tool bytes and hashes, config, candidate freeze, prompt IDs and requests. No commit, push, history edit or author configuration occurred. All 22 prior journals remain byte-identical; the new journal adds tokenizer evidence only. Existing 140 generations across 17 generation runs remain unchanged.

Engineering command/error captures are under `{SESSION.relative_to(ROOT).as_posix()}/engineering/`; experimental evidence is under `experiments/`; pre-change inventory and development data under `materials/`. [Integrity evidence](validation/P0_control_development_integrity_v2.json) and [command index](validation/P0_control_development_commands_v2.json) provide traceability. Early read-only tool calls retain transcript provenance; their individual times are not reconstructed. Fresh reproduction requires a new session and artifact version; immutable outputs refuse overwrite. Late reporting-source changes are retained in a separate delivery snapshot, not backfilled into the experimental freeze.

The [novelty matrix addendum](related_work_novelty_matrix.md) checks three additional primary papers. Length/structure controls and persona/context contrasts have prior art. These improvements establish engineering feasibility, not a verified original methodological contribution or a persona-reliability result.
"""
    report_path = ROOT / "docs/P0_control_development_report_v2.md"
    with report_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(report)
    notice = (f"> **Current update — {now}: P0 PARTIAL; P1 NOT STARTED.** "
              "Historical human review remains complete (40/40). New development controls have 24/24 exact tokenizer matches "
              "across six cases and four families, with 0/24 new human reviews; semantic acceptance is OPEN. "
              "The full suite passes 285 tests. See [the v2 control-development report](P0_control_development_report_v2.md). "
              "All earlier dated evidence below is retained.\n\n")
    report_names = ["P0_control_acceptance_report.md", "P0_remaining_blockers.md", "P0_policy_acceptance_report.md",
                    "P0_final_validation_report.md", "P0_methodology_acceptance_report.md", "P0_acceptance_checklist.md",
                    "P0_real_inference_report.md", "P0_neutral_control_diagnostic.md"]
    for name in report_names:
        path = ROOT / "docs" / name
        path.write_bytes(notice.encode("utf-8") + path.read_bytes())
    block = f"""## {now} — Development control v2 validation

**P0 PARTIAL; P1 NOT STARTED.** [Full report](P0_control_development_report_v2.md), [selected controls](validation/P0_control_development_selection_v2.json), [all tokenizer observations](validation/P0_control_tokenizer_validation_v2.json), [new review guide](P0_control_development_review_v2_guide.md), [integrity audit](validation/P0_control_development_integrity_v2.json), [command index](validation/P0_control_development_commands_v2.json).

Objective: repair style matching while preserving the original wrapper, and separate history format, topic and old-fact-specificity controls. Candidate version `neutral_control_candidate_v2_dev`, prompt `transcript_base_v1`; six predetermined development cases, 420 candidate prompts, 444 native tokenizer requests, 24/24 matches, tolerance zero, no generations. The earlier 0/3 style failures are preserved, with observed length gaps diagnosed as pool coverage. No model answer was used for selection. New human review is 0/24 (18 alternatives plus 6 non-neutral diagnostics); old human review remains 40/40, with 40 PARTIAL overall suitability judgments. Review only transfers to its exact materials.

Session `{SESSION.relative_to(ROOT).as_posix()}`; run `{Path(observed['run_directory']).name}`; {observed['journal_events']} chained events. Git `{integrity['git_commit']}`, dirty true; 40 changes predated this task. Qwen3.5-2B-Base Q4_K_M SHA-256 `{observed['model_sha256']}`; server SHA-256 `{observed['server_sha256']}`; b11573 / `0f701c882`; configured CPU4/4, context4096, zero GPU layers. Pre/postflight identity and /props binding pass. New independent hardware measurements were not made. Seed42 and cap96 are inherited configuration only; generation parameters/output/parser/evaluation scores are not applicable to the tokenizer run. Frozen response/evaluation policies remain untouched.

New sources: `control_candidates_v2.py`, `control_review_v2.py`, `test_control_candidates_v2.py`, `p0_control_development_v2.py` and the v2 report utility. English reports, access/command indexes, candidate freeze/selection/tokenizer/integrity artifacts and blank review CSV/JSON are separate additions. Existing acceptance documents receive a current notice without removing historical text; development and reproducibility logs are appended. The related-work matrix gains a primary-source addendum; protocol, old prompts, raw generations, evaluations and old annotations remain unchanged.

{test_text}

Actual earlier failure: targeted tests returned 16 passed/6 failed in0.36s, exit1, because newly serialized facts were tuples; fixed the new serializer to produce schema-compatible lists. Rerun22 passed in0.13s, exit0. Original schema/tests unchanged. A read-only request for nonexistent `schema.py` was corrected to `schemas.py`; PowerShell reported the error but returned0 after later reads. Full errors and exact actual command start/end times are retained in local engineering captures. Initial uncaptured read-only operations retain interface-transcript provenance; no missing timestamps are fabricated.

All 110 protected source/data/annotation files are unchanged; all 22 old journals retain the same members and bytes. All 23 chains pass; 24 new observations and deterministic matching decisions replay from saved IDs without re-inference. Existing140 generations/17generation runs remain intact. Freeze/source/config/input hashes and complete native HTTP response bodies support reconstruction; new scientific claims, perfect determinism and independent human semantic validation are not inferred. No Git mutation, P1, training or unrelated application access occurred.

Literature: three primary papers were inspected, with exact versions and access limitations in the [novelty addendum](related_work_novelty_matrix.md). Persona length/structure controls already exist. Character-versus-token wording in one paper was distinguished from independently verified exact matching. New controls are engineering improvements with unproven novelty. P0 remains open for semantic findings and defensible adoption of chosen replacement contrasts, not for perfect model behavior or review of every optional future diagnostic.
"""
    for name in ("P0_reproducibility_report.md", "research_development_log.md"):
        append(ROOT / "docs" / name, block)
    append(ROOT / "docs/P0_remaining_blockers.md", f"""## {now} — Precise remaining control gate

New matching is engineering PASS (24/24); semantic validity is still PARTIAL. Obtain human judgments for the v2 controls actually proposed for adoption and resolve failures/uncertainties, with explicitly approved narrow estimands. The 24-item package includes alternative history families and six diagnostics; unused alternatives are not a new mandatory gate. Original40 reviews are complete and must not be recycled onto new wording. History A changes topic, B changes reply pragmatics, C changes specificity and is non-neutral. A pure historical-format or temporal-conflict mechanism remains unidentified and must not be claimed. Protocol changes require researcher approval. No P1 execution is authorized by a successful tokenizer match.
""")
    readme = ROOT / "README.md"
    raw = readme.read_bytes()
    raw = raw.replace(b"the latest suite passes 263 tests", b"the latest suite passes 285 tests")
    raw = raw.replace(b"Only the 20 fictional P0 cases in `data/synthetic/p0_cases.jsonl` are used.",
                      b"The historical benchmark uses the 20 fictional P0 cases in `data/synthetic/p0_cases.jsonl`; separately versioned synthetic development fixtures support methods validation.")
    readme.write_bytes(raw)
    append(readme, "## Control development v2\n\nSix development cases yield 24/24 exact final-prompt token matches across style and three history families. These are engineering checks only; new human review is 0/24 and P0 remains PARTIAL. See [the report](docs/P0_control_development_report_v2.md) and [English review guide](docs/P0_control_development_review_v2_guide.md). Historical controls, annotations and model generations remain preserved.")
    save(SESSION / "engineering/report_creation.json", {"recorded_utc": now, "report": report_path.relative_to(ROOT).as_posix(),
         "acceptance_notices": report_names, "test_capture_sha256": digest(SESSION / "engineering/full_tests.json"),
         "scope": "Report generated after tokenizer freeze; earlier records retained"})
    print(json.dumps({"recorded_utc": now, "report": report_path.relative_to(ROOT).as_posix(), "P0": "PARTIAL", "new_human_reviews": "0/24", "tests": test_summary}))


if __name__ == "__main__":
    main()
