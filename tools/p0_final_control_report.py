"""Record per-candidate analytical identification separately from human labels."""
import json

from personaslm.journal import utc_now
from p0_final_control_review import ROOT, SESSION, PUBLIC, read, save, digest

COMMON = ["Exact trusted current evidence and current question", "Recent context and original transcript wrapper",
          "Same case and named subject", "Same intervention section position", "Exact total input-token count under recorded native tokenizer"]
FAMILY = {
    "style_generic": {
        "held": ["Speaker style profile heading"],
        "changed": ["Named style prescription replaced by generic discourse description"],
        "confounds": ["Instructional force and semantic salience", "Generic expository register and concise complete sentence", "Heading can frame generic prose as a style exemplar"],
        "interpretation": "Length-matched style-profile versus generic-description replacement, conditional on semantic review; not style versus an inert string",
        "class": "Proposed neutral-style control; validity OPEN"},
    "history_format": {
        "held": ["Same historical date/header", "User then named-speaker roles", "Two turns with question-answer organization"],
        "changed": ["Residence question replaced by a conversation question", "Specific old-city residence replaced by generic discourse content"],
        "confounds": ["Topic relevance", "Personal versus generic factual content", "Internal past reference versus generic statement", "Deictic wording and register"],
        "interpretation": "Format/length-controlled content replacement; not the causal effect of history format or topic alone",
        "class": "Proposed format/length placebo; semantic validity OPEN"},
    "history_topic": {
        "held": ["Exact past-residence question", "Same historical date/header", "Same named speaker and role order", "Two turns"],
        "changed": ["Named past-city answer replaced by a clarification question", "Historical residence assertion removed"],
        "confounds": ["Question-answer versus question-clarification speech act", "Questioning/uncertainty/non-answer priming", "Different epistemic commitment"],
        "interpretation": "Residence-topic-aligned answer-versus-clarification contrast; not an information-only or neutral-placebo intervention",
        "class": "Topic-matched comparison candidate; neutrality unestablished"},
    "history_stale_generalized": {
        "held": ["Exact past-residence question", "Same historical date/header and roles", "Past-city-residence proposition and topic"],
        "changed": ["Named city replaced by the category a city", "Geographic specificity and named alternative-answer exposure removed"],
        "confounds": ["Informativeness", "Vague or evasive answer pragmatics", "Lexical material changes", "Some temporal phrasing changes"],
        "interpretation": "Information-specificity ablation; not a neutral control or a pure temporal-conflict effect",
        "class": "Diagnostic intervention; not a neutral placebo"},
}
STYLE_NOTES = {
    "Riley": "The generic control is itself a concise single sentence, potentially cueing the brevity under investigation.",
    "Samara": "The generic control is formal, grammatical expository prose, potentially overlapping the formality intervention.",
    "Devon": "The control does not use certainly, but changes instruction force and semantic content as well as the lexical preference.",
    "Tessa": "The control uses no contraction; absence of a prescribed contraction habit does not establish style neutrality.",
    "Blair": "The control describes questions and replies; it can frame conversational response structure without explicitly prescribing an acknowledgment.",
    "Robin": "The control itself demonstrates a single sentence, potentially overlapping the active single-sentence response tendency.",
}


def append(path, text):
    with path.open("ab") as handle:
        handle.write(("\n\n" + text.rstrip() + "\n").encode("utf-8"))


def main():
    now = utc_now()
    packet = read(PUBLIC / "P0_final_control_review_v3.json")
    evidence = read(PUBLIC / "P0_final_control_evidence_v3.json")
    frozen = read(PUBLIC / "P0_control_candidate_freeze_v2.json")
    specs = {s["case_id"]: s for s in frozen["case_specs"]}
    observations = {(r["case_id"], r["family"]): r for r in evidence["selected_pairs"]}
    rows = []
    for item in packet["items"]:
        spec = specs[item["case_id"]]
        family = item["candidate_family"]
        f = FAMILY[family]
        if family == "style_generic":
            specific = STYLE_NOTES[item["speaker_name"]]
            information = {"removed": spec["style"], "retained": "Same profile heading and generic discourse statement", "changed": "Style prescription to description"}
        elif family == "history_format":
            specific = "The question and reply concern conversation, not residence; generic propositions replace dated personal information."
            information = {"removed": f"Named old residence {spec['old_city']} and its residence question", "retained": "Date label, attribution and question-answer structure", "changed": "Residence content to generic discourse"}
        elif family == "history_topic":
            specific = ("Adds an address-versus-city distinction not present in the active answer." if "address" in item["candidate_control_text"]
                        else "Uses a second-person clarification about city granularity, not a residence assertion.")
            information = {"removed": f"The assertion of past residence in {spec['old_city']}", "retained": "Past-residence question, date and attribution", "changed": "Answer becomes a question"}
        else:
            changed_time = "back then." in item["candidate_control_text"]
            specific = ("Changes at the time to back then as well as replacing the city name." if changed_time
                        else "Retains at the time verbatim; the city name becomes a city.")
            information = {"removed": f"Exact old-city identity: {spec['old_city']}", "retained": f"{spec['speaker']} lived in some city at the historical time",
                           "changed": "City specificity and response informativeness; " + ("temporal phrase also changes" if changed_time else "temporal phrase unchanged")}
        obs = observations[item["case_id"], family]
        rows.append({"candidate_id": item["candidate_id"], "case_id": item["case_id"], "family": family,
                     "analysis_type": "automated_development_analysis_not_human_annotation", "classification": f["class"],
                     "intended_experimental_contrast": item["intended_comparison"], "variables_held_constant": COMMON + f["held"],
                     "variables_intentionally_manipulated": f["changed"], "remaining_confounders": f["confounds"],
                     "semantic_validity_risks": [specific, "No new human judgment is available; input equivalence does not imply semantic equivalence"],
                     "information_accounting": information, "appropriate_interpretation": f["interpretation"],
                     "original_active_intervention": item["original_active_intervention"], "candidate_control_text": item["candidate_control_text"],
                     "trusted_evidence": item["trusted_evidence"], "current_question": item["current_question"],
                     "reference_date": item["reference_date"], "evaluation_date": item["evaluation_date"], "expected_answer": item["expected_answer"],
                     "actual_tokenizer_evidence": obs, "review_status": "OPEN"})
    save(PUBLIC / "P0_final_control_analysis_v3.json", {"created_utc": now, "analysis_version": "control_identification_v3",
         "review_master_sha256": digest(PUBLIC / "P0_final_control_review_v3.json"), "evidence_sha256": digest(PUBLIC / "P0_final_control_evidence_v3.json"),
         "scope": "Per-candidate input analysis only; no human labels or output-based selection", "candidates": rows})
    tests = read(SESSION / "engineering/full_tests.json")
    if tests["exit_code"] != 0 or "307 passed in 17.08s" not in tests["stdout"]:
        raise ValueError("Unexpected test evidence")
    test_text = f"**307 passed, 0 failed, 0 warnings reported**, pytest **17.08s**, process **{tests['duration_seconds']:.3f}s**, exit **0**. Actual interval: `{tests['started_utc']}` to `{tests['finished_utc']}`."
    table = "\n".join(f"| {r['case_id']} | {r['family']} | {r['actual_tokenizer_evidence']['reference_count']}/{r['actual_tokenizer_evidence']['candidate_count']} | 0 | {r['semantic_validity_risks'][0]} |" for r in rows)
    report = f"""# P0 Final Neutral-Control Validation — Review Preparation v3

Recorded **{now}**. Researcher: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Protocol v1.1; English. **Engineering PASS; exact matching PASS; semantic-control validity OPEN; overall P0 PARTIAL; P1 NOT STARTED.** This is an offline inspection and annotation-package update, not a new model experiment or a protocol amendment.

## Evidence actually inspected

All24 selected records in the v2 CSV/JSON master were read and compared with original active interventions, frozen candidate pools, constructed prompts and the native tokenizer journal. All420 candidate prompts plus24 reference requests match the saved original HTTP request text and decoded response token IDs: **444/444 reconciled**. All24 selected differences remain exactly0. The first-exact-match selection rule replays unchanged. Final wrapper/evidence/question equality was checked, and current construction reproduces the frozen pool.

This validation used saved **real** GGUF observations; it did not approximate counts, start a backend or request new tokenization/generation. Model hash `{evidence['model_sha256']}`; backend hash `{evidence['backend_sha256']}`; build `{evidence['backend_build']}`. Prompt version `transcript_base_v1`; candidate version `neutral_control_candidate_v2_dev`. Original tokenizer options are add_special=true, parse_special=false, with_pieces=false. The source run retains configuration CPU4/4, context4096, seed42/cap96 (unused for tokenization), original source/config hashes and Git dirty state.

Run `{evidence['run_directory']}` has1384 verified chained events. Its20 HTTP503 responses occurred on `/health` during the earlier model startup, before successful tokenizations; they remain preserved. No tokenizer errors or missing IDs were found among the444 responses. These are historical startup observations, not new failures. The original140 generated responses in17 generation runs were neither rerun nor rescored. All23 historical journal inventories remain byte-identical to this task's initial snapshot. [Full offline evidence](validation/P0_final_control_evidence_v3.json).

## Exact candidate inventory and analytical concerns

Counts below are **reference/candidate complete-prompt tokens**. Every row is a development-analysis observation, not a human semantic judgment. The [structured per-item analysis](validation/P0_final_control_analysis_v3.json) gives each candidate's stable ID, full texts, intended contrast, constant/manipulated variables, residual confounds, semantic risks, information removed/retained/changed, appropriate interpretation and exact native request/response sequence numbers and hashes.

| Case | Family | Tokens | Difference | Specific analytical concern |
|---|---|---:|---:|---|
{table}

Each family therefore retains6/6 matching. The six cases are not a holdout or a representative speaker population. Three scenarios were reused from v1 development and three were new in v2; this round adds **no cases, new wording or new selection**. Multiple styles occur across cases, but each style is tied to one synthetic person/scenario. Neither independent style-axis effects nor S/F/H interactions are estimated by this inventory.

N_style removes explicit repeated padding but still demonstrates a register beneath a style-profile heading. A controls presentation length/structure while leaving topic and personal/temporal content unequal. B preserves the residence question but turns its answer into a clarification; three replies add an address-versus-city distinction. C deliberately removes a named old city while retaining vague past-city residence; three cases also change temporal phrasing. **C is a diagnostic, not a neutral placebo.** Named questions eliminate the old implicit person/Alice referent link in these inputs, but do not independently establish speaking-as versus speaking-about fidelity.

The [control identification matrix](P0_control_identification_matrix_v3.md) separates seven dimensions and explicitly states which effects each contrast cannot identify. The official C1–C0/C3–C0 and matched-control contrasts are unchanged. A/B/C have distinct roles; none isolates all historical effects. Prose/dialogue fact-equating and crossed relevance/time/presentation tests remain future proposals requiring approval, not P0 completion requirements.

## Final human-review package

Use **[P0_final_control_review_v3.csv](validation/P0_final_control_review_v3.csv)**, with [English instructions](P0_final_control_review_v3_guide.md) and an [immutable JSON master](validation/P0_final_control_review_v3.json). The CSV has24 rows/65 columns, including candidate/case/family IDs, active/candidate texts, evidence/question, reference/evaluation dates, expected answer, exact counts,15 review questions, blank judgments/quotations/notes/reviewer fields, complete prompts and provenance hashes.

Expected answers are review-only metadata from frozen fixtures. They were not added to experimental prompts. Style blocks have no historical reference date, so that field is explicitly NOT_APPLICABLE. Conditions and answers are visible; this is not blind review. Original v2 masters are unchanged and still available. The new form contains **0/24 human reviews**, and the original40 completed annotations have not been transferred. Old control-suitability counts remain PASS0/PARTIAL40/FAILED0, applying only to the old materials.

The new versioned importer has a default v3 master and a simple input/output command in the guide. It validates exact inventory, labels, frozen content, versions/hashes, reviewer identity/assistance, optional UTC times and actual quotations. Default import requires all24 completed rows; explicit partial import remains available without changing the inventory. Completion does not automatically imply validity. Software fixture reviews used in tests are clearly marked and never written to research annotation fields.

An actual command against the blank form was intentionally tested and rejected with exit1: `Incomplete human review: 0/24`. No output review file was created. This expected negative check demonstrates that blank materials cannot become completed human evaluation. No genuine completed submission was supplied or imported, no reviewer identity/time was invented, and no agreement statistic was computed.

## Acceptance checklist and remaining blockers

| Requirement | Status | Evidence / limitation |
|---|---|---|
| Protocol, title, English scope and research boundaries | PASS | No frozen protocol or factor/endpoint/policy changes |
| Existing engine and logging engineering | PASS within existing scope | Previous real inference retained; this round only reconciles saved evidence |
| Actual full-prompt matching | PASS |24/24 selected pairs, all444 native request/response observations consistent |
| New review package/import tooling | PASS |24 blank complete materials;22 new targeted tests; actual empty-import rejection |
| Original human annotation completion | PASS |40/40 unchanged, old semantic findings still PARTIAL |
| New human annotation completion | PARTIAL / OPEN |0/24; a new presentation does not create a human review |
| Semantic validity of proposed adopted controls | PARTIAL / OPEN |Style, topic, speech-act and specificity findings require human judgment/resolution |
| Historical reproducibility | PASS within scope |23 unchanged journal inventories, source run chain and token replay verified; raw archive remains local |
| Scientific identification | PARTIAL |Narrow replacement estimands documented; pure format/topic/time mechanisms not identified |
| Automated tests | PASS |307 passed, no failures |
| Overall P0 | PARTIAL |Valid adopted controls and justified interpretation remain required; P1 requires separate authorization |

Mandatory closure is real semantic review of the exact controls intended for use and resolution of substantive findings, with a defensible interpretation accepted by the researcher. A completed form alone, token equality, or model fluency is insufficient. Unused alternatives and optional diagnostics do not all become new acceptance gates. A pure-format or pure-temporal-effect claim cannot be licensed by the present controls. Any change to protocol/primary estimands requires explicit approval.

Bounded response instrumentation, missing unsupported backend input-ID arrays and independently unverified upstream quantization fidelity remain documented limitations under their existing claim scope. Perfect Base-model termination or completion of future model-size/external validation experiments is not required for P0 instrumentation. Persona Fidelity remains independent of reliability. No P1, training, unrelated application access or Git mutation was performed.

## Novelty and reproducibility

The [five falsifiable proposals](P0_control_hypotheses_v3.md) retain priorities A–E and specify supporting/falsifying observations and confounds. The [novelty matrix](related_work_novelty_matrix.md) and four rechecked primary sources show direct overlap with persona cues, context interference, factual reliability and authentic-person simulation. The inclusion of2B/3B models in Principled Personas was checked in its PDF. This is scoped source verification, not a systematic review or proof of originality. No persona-effect finding follows from this preparation.

{test_text}

Targeted new tests:22 passed in0.89s, exit0. All positive checks passed on their first run this round; the intentional blank-import exit1 is retained separately. The full suite was not weakened. Existing modules, evaluation policies, candidate-generation code, fixtures and old review masters remain unchanged; only a new review module/test and audit/report tools were added.

Session `{SESSION.relative_to(ROOT).as_posix()}` stores exact command start/end times, outputs, exits and errors under `engineering/`; baseline hashes and original document bytes under `materials/` and `original_documents/`. Starting HEAD `{evidence['current_git_head']}` was dirty (19 preexisting changed/untracked paths). The source tokenizer run retains its original HEAD `{evidence['source_run_git']['commit']}` and dirty=true; current metadata is not backfilled into it. No new model-run manifest is invented for this offline work. [Command/delivery evidence](validation/P0_final_control_delivery_v3.json) records final checks and file changes. Initial read-only interface calls retain transcript provenance; individual missing timestamps are not fabricated.
"""
    with (ROOT / "docs/P0_final_neutral_control_validation_report.md").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(report)
    update = f"""## {now} — Final control review preparation v3

**P0 PARTIAL; P1 NOT STARTED.** [Current validation report](P0_final_neutral_control_validation_report.md), [identification matrix](P0_control_identification_matrix_v3.md), [24-item English review](validation/P0_final_control_review_v3.csv), [import guide](P0_final_control_review_v3_guide.md), [per-item analysis](validation/P0_final_control_analysis_v3.json).

Offline audit reconciled all444 saved native tokenizer requests/responses with420 candidates and24 references. All24 selected pairs retain difference0 and their original wrapper/evidence/question. All23 historical journal inventories are unchanged. Twenty historical /health503 startup records were retained; no new model server, tokenization or completion was run. Original40 human reviews remain complete; new review0/24 remains OPEN. New v3 is a form version, not a prompt revision; all old masters, original prompts, source fixtures and evaluation policies are retained.

N_style still risks generic register/profile-heading effects. A changes topic and historical information. B changes question-answer to clarification, with address granularity added in3/6 replies. C removes six named old cities but retains vague prior-city residence, with temporal phrase changes in3/6; it is a diagnostic, not a neutral placebo. Precise variables and limited replacement estimands are now documented for every candidate. Protocolv1.1, title and primary contrasts are unchanged; no effect or originality claim is made. Four relevant primary sources were rechecked, including direct2B/3B precedent; five falsifiable proposals remain unexecuted future work.

{test_text}

Targeted22 passed in0.89s. Actual blank-import command deliberately returned1 with `Incomplete human review: 0/24`; no review output was created. This is a successful negative validation, not a human annotation or silently discarded error. No corrective implementation changes were needed after this round's tests. New module `control_final_review.py`, its22 tests, offline audit/report tools, CSV/JSON master, evidence/analysis artifacts and English reports were added. Acceptance reports receive dated notices; old report bytes and all old validation artifacts remain preserved.

Session `{SESSION.relative_to(ROOT).as_posix()}`. Initial Git `{evidence['current_git_head']}`, dirty=true,19 preexisting paths; model `{evidence['model_sha256']}`, backend `{evidence['backend_sha256']}` / `{evidence['backend_build']}` are references to the saved tokenizer run, not fresh binary/hardware measurements. Source-run Git/config/tokenizer options/prompt hashes/raw HTTP IDs are in [offline evidence](validation/P0_final_control_evidence_v3.json). Exact commands, times, outputs, exit codes, files and final integrity checks are in [delivery evidence](validation/P0_final_control_delivery_v3.json) and linked local captures. No commits, pushes, identity changes, P1, training or private-data access occurred.
"""
    for name in ("research_development_log.md", "P0_reproducibility_report.md"):
        append(ROOT / "docs" / name, update)
    notice = (f"> **Current update — {now}: P0 PARTIAL; P1 NOT STARTED.** Final review v3 presents the unchanged24 candidates; "
              "all24 exact matches and444 original native tokenizations reconcile offline. New human review0/24 remains OPEN; original40/40 reviews remain complete. "
              "307 tests pass. See [the current control validation report](P0_final_neutral_control_validation_report.md). Earlier dated evidence remains intact.\n\n")
    for name in ("P0_control_acceptance_report.md", "P0_remaining_blockers.md", "P0_acceptance_checklist.md", "P0_final_validation_report.md", "P0_methodology_acceptance_report.md", "P0_policy_acceptance_report.md"):
        path = ROOT / "docs" / name
        path.write_bytes(notice.encode("utf-8") + path.read_bytes())
    append(ROOT / "docs/related_work_novelty_matrix.md", f"""## {now} — Final control identification follow-up

The [v3 identification matrix](P0_control_identification_matrix_v3.md) now states separate style, length, format, relevance, factual-content, temporal-status and identity roles. The [five falsifiable hypotheses](P0_control_hypotheses_v3.md) preserve prioritiesA–E without executing a pilot or changing Protocolv1.1. Every actual selected candidate has a separate [analytical record](validation/P0_final_control_analysis_v3.json); none is a human judgment.

Primary sources rechecked: Principled Personas PDF (setup/result labels confirm Gemma-2-2B, Llama-3.2-3B and Qwen2.5-3B), One Persona/Many Cues record, When Personalization Misleads record, and TwinVoice record/abstract. This strengthens the already documented overlap and resolves the earlier scoped nonverification of the small-model examples only. Other unextracted details remain unverified. No data, code reproduction or private dialogue access occurred. Exact matching, stylistic filler, content decomposition and small-model coverage alone do not establish novelty; independent findings or validated failure boundaries would be needed.
""")
    append(ROOT / "README.md", "## Final neutral-control review\n\nThe [current P0 report](docs/P0_final_neutral_control_validation_report.md) records307 passing tests and offline reconciliation of24 matched candidate pairs. The [final24-item English form](docs/validation/P0_final_control_review_v3.csv) adds dates, expected answers and review questions without changing prompts. New human review remains0/24; P0 remains PARTIAL. See [the import guide](docs/P0_final_control_review_v3_guide.md).")
    save(SESSION / "engineering/report_metadata.json", {"created_utc": now, "analysis_rows": len(rows),
         "test_capture_sha256": digest(SESSION / "engineering/full_tests.json"), "P0": "PARTIAL", "new_human_reviews": 0})
    print(json.dumps({"analysis_rows": len(rows), "tests": 307, "P0": "PARTIAL", "created_utc": now}))


if __name__ == "__main__":
    main()
