"""Dated English acceptance addenda; old reports and experimental bytes retained."""
import json
from pathlib import Path

from personaslm.journal import utc_now

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "results/p0_neutral_validity/20261012T195226"
PUBLIC = ROOT / "docs/validation"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def create(path, text):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main():
    now = utc_now()
    tests = read(SESSION / "engineering/full_tests.json")
    audit = read(PUBLIC / "P0_neutral_validity_delivery_v1.json")
    reviews = read(PUBLIC / "P0_researcher_verified_annotation_v1_revision2.json")
    assert tests["exit_code"] == 0 and "263 passed in 10.11s" in tests["stdout"]
    test_sentence = (f"**263 passed, 0 failed, 0 warnings reported**, pytest **10.11s**, process **{tests['duration_seconds']:.3f}s**, "
        f"exit **0**. Actual test interval: `{tests['started_utc']}` to `{tests['finished_utc']}`.")
    decision = f"""# P0 Control Validity and Human Annotation Acceptance

Recorded **{now}**. **Overall P0: PARTIAL. Human annotation completion: PASS (40/40). Control validity: PARTIAL, resolution OPEN. P1: NOT STARTED / BLOCKED pending methodological closure and separate researcher approval.**

Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Research Protocol v1.1. Primary language: English. Research target: Real-Speaker Persona Modeling. Maintainer: Yaxin ZHENG. This is a P0 methods/engineering decision, not a scientific comparison or protocol amendment.

## Current acceptance checklist

| Requirement | Status | Evidence | Remaining limitation / action |
|---|---|---|---|
| Frozen objectives, S/F/H, tracks, English scope and Git policy | PASS | Protected files unchanged; no P1, training, unrelated application access or Git mutation | Researcher alone authorizes changes and experiments |
| Real CPU model execution and pinned files | PASS within recorded scope | Existing real inference retained; new tokenizer-only run uses same Qwen3.5-2B-Base Q4_K_M / b11573 | No fresh generation or performance benchmark claimed |
| Input/evidence reconstruction | PASS | 100 original prompts reconstructed byte-for-byte; all 100 token-ID arrays reproduced by real backend | Twenty repeated synthetic cases, one speaker/style |
| Original token matching | PASS | 40/40 exact matches, tolerance zero | Does not prove semantic validity |
| Response/evaluation instrumentation | PASS within frozen scope | `response_status_v1`, `separate_axes_policy_v1`, previous holdout and replay evidence unchanged | Ambiguous units/manual routing, narrow factual coverage; completeness distinct from truth |
| Human annotation completion | PASS | `researcher_verified_annotation_v1`, registration revision 2, Yaxin_ZHENG, 40 unique reviewed rows and 240 core judgments | AI-assisted final review, not blind; original review time unavailable |
| Semantic-control suitability | PARTIAL / OPEN | Researcher overall: PASS 0 / PARTIAL 40 / FAILED 0; all 40 neutrality ratings uncertain | Resolve style contamination, topic/information imbalance and identity/coherence ambiguity |
| Dimension-level repair routing | PARTIAL | Separate software disposition: PASS 0 / PARTIAL 20 / FAILED 20 | Twenty N_style extra-style failures; this does not overwrite the human overall rating |
| Annotation provenance/version comparison | PASS for available files; PARTIAL for earlier lineage | Raw versions archived; 0 judgment changes between available versions; metadata changed in 40 rows | Untouched AI original, initial independent pass and declared intermediate file absent; total earlier changes unknown |
| Candidate controls | PARTIAL / DEVELOPMENT ONLY | Three new cases, 132 attempts; N_history 3/3 matches; N_style 0/3, best +2/-3/-3 | No candidate semantic approval or generation; old controls unchanged |
| Follow-up annotation tooling | PASS | Locked English packet and quote-validating importer; original strict v3 importer unchanged | No fabricated follow-up reviews, second reviewer, consensus or agreement |
| Historical logs/integrity | PASS | {len(audit['historical_journals'])} original journal inventories unchanged; all {len(audit['all_journal_chains'])} current journals chain-verified | Hash integrity is not cryptographic proof of independent authorship |
| Researcher annotation reconstruction | PASS | Re-import reproduces saved content exactly excluding actual registration time | Software validates structure; human authenticity rests on researcher attestation |
| Automated tests | PASS | 263 passed, exit 0 | Software tests are not experimental or human ground truth |
| Model upstream equivalence / unsupported evaluated-ID arrays | PARTIAL, documented limitations | Pinned artifact/backend and supported token accounting | No independently reproduced quantization equivalence or invented missing backend IDs |
| P1 preparation | PARTIAL (proposal only) | Design proposal and nine-study primary-source novelty matrix | No final confirmatory set, power claim, proven novelty or P1 execution |
| Overall P0 research acceptance | PARTIAL | Engineering checks and review completion pass, control-validity findings unresolved | Do not convert reviewed-but-uncertain controls into PASS |

## What still prevents acceptance

The mandatory remaining issue is **valid experimental controls or an explicitly approved, defensible interpretation of their replacement contrasts**. Human review is now complete; requesting another reviewer merely because this review was AI-assisted would be a new requirement and is not used to keep P0 open. The observed unresolved findings themselves keep control validity open.

N_style has a confirmed extra-style cue in all 20 rows. N_history replaces relevant residence dialogue with document descriptions; matching tokens, dates and roles does not separate content relevance from historical formatting. Ten history rows also identify implicit speaker-reference binding. All 40 semantic-neutrality ratings remain uncertain. A future approved revision must preserve the old artifacts, pass exact matching and receive real semantic review. The unsuccessful development candidates are evidence of remaining work, not a reason to relax tolerance or revise old results.

An adequate single-reply policy need not force every Base-model response to end naturally. Existing cap/continuation behavior is a measurable model limitation under the frozen response/evaluation policies. Missing backend interfaces, unverified upstream quantization fidelity, initial AI-review edit history and lack of a second control reviewer qualify claims but are not additional blanket P0 gates. Open-ended scientific output judgments must still follow the protocol's later independent annotation requirements.

## Evidence and test results

{test_sentence}

Initial new-module tests: **29 passed, 1 failed**, due to a test fixture using an out-of-project temporary directory. The fix configured that fixture as a temporary repository; the production path restriction was retained. Targeted rerun: **30 passed**, exit 0. Eight further resolution tests and two provenance/time checks are included in the final 263. The failed test log remains available.

[Neutral diagnostic](P0_neutral_control_diagnostic.md); [human registration report](P0_researcher_annotation_report.md); [latest registration](validation/P0_researcher_verified_annotation_v1_revision2.json); [version differences](validation/P0_researcher_annotation_version_comparison_v1.json); [tokenizer results](validation/P0_control_tokenizer_validation_v1.json); [delivery checks](validation/P0_neutral_validity_delivery_v1.json); [P1 proposal](P1_experimental_design_proposal.md); [related-work matrix](related_work_novelty_matrix.md).

No raw generation, historical score, frozen policy or Protocol v1.1 content was edited. All changes remain uncommitted for researcher review.
"""
    create(ROOT / "docs/P0_control_acceptance_report.md", decision)
    notice = (f"> **Current assessment — {now}:** Human annotation **PASS, 40/40 completed**; final review is AI-assisted and not blind. "
        "Semantic-control validity remains **PARTIAL / resolution OPEN**; researcher overall ratings are PASS 0 / PARTIAL 40 / FAILED 0. "
        "Overall **P0 PARTIAL; P1 NOT STARTED**. See the [current control acceptance report](P0_control_acceptance_report.md) "
        "and [researcher annotation report](P0_researcher_annotation_report.md). Tests: **263 passed**. "
        "All earlier status/readiness statements below are preserved dated history, including earlier 0/40 review counts.\n\n")
    originals = SESSION / "engineering/report_originals"
    originals.mkdir(exist_ok=False)
    reports = ("P0_remaining_blockers.md", "P0_policy_acceptance_report.md", "P0_final_validation_report.md",
        "P0_methodology_acceptance_report.md", "P0_reproducibility_report.md", "P0_acceptance_checklist.md",
        "P0_real_inference_report.md", "P0_neutral_review_instructions.md", "P0_neutral_annotation_form_v3.md")
    for name in reports:
        path = ROOT / "docs" / name
        original = path.read_bytes()
        (originals / name).write_bytes(original)
        path.write_bytes(notice.encode("utf-8") + original)
    repro = f"""

## {now} — Control validity and researcher annotation provenance

Session: `results/p0_neutral_validity/20261012T195226/`. Starting HEAD: `4d00ee1adbe538d24175d5c3e83c318bff8365a3`; initial working copy contained the researcher's untracked earlier CSV. New runs record actual dirty state and exact source snapshots. Preparation inventories were saved before experimental or historical-file changes.

Tokenizer-only run: `20261012T195708-1dc4429d05c94341bf5a92c6da48c020`, **756 chained events**, **238 tokenizations**, **0 completions**. Native request/response bodies, server log, `/props` binding, CPU launch arguments, configuration, pre/postflight hashes and exact prompt/ID arrays are retained. GGUF SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; server SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; b11573 / `0f701c882`; CPU 4/4, context 4096. Tokenizer options: add_special=true, parse_special=false, with_pieces=false. Generation parameters/raw/parsed responses are not applicable to this new run because no generation was requested; the inherited runtime seed/cap are logged but unused.

The historical `transcript_base_v1` prompts and IDs match 100/100. `neutral_control_candidate_v1_dev` / `control_candidate_prompt_v1_dev` was frozen before tokenization, with all 132 attempts retained; three history matches and three style failures. The dataset identifier in the new reconstruction is an analysis-local label; exact file SHA identifies the unchanged historical dataset. No token approximation or tolerance change was used.

All **{len(audit['historical_journals'])} historical journal inventories remain byte-identical**; all **{len(audit['all_journal_chains'])} current journals passed fresh chain validation**. Existing **140 raw generations across 17 generation runs** remain historical, with no new outputs. Annotation import replay reproduces the final registration excluding the new actual import time. Legacy scores and frozen response/evaluation policies remain unchanged. See [delivery evidence](validation/P0_neutral_validity_delivery_v1.json).

The prior source CSV, final researcher CSV and both registration records are separate. The final registration records reviewer identity from explicit researcher confirmation and final source metadata, no invented review time. Zero judgment edits between available snapshots does not establish zero edits from the unavailable initial AI/independent-pass versions. The declared intermediate source hash is preserved as an unverified link. Missing earlier versions limit edit-history reconstruction but do not erase the observed completed final review.

{test_sentence}

Engineering command/error captures are under `engineering/`; source/config/input freezes and original incoming files under `materials/`; backend HTTP journals under `experiments/`. The public [command index](validation/P0_neutral_validity_commands_v1.json) links summarized actions to full local logs. Initial uncaptured read-only commands retain tool-transcript provenance; their individual timestamps are not backfilled. All public additions use English and repository-relative paths.

The literature review used primary web sources. Access/query metadata are in [the access index](validation/P0_literature_access_v1.json); selected tool responses are preserved locally under `literature/`. Two unavailable guessed HTML URLs returned 404 and were replaced with available versioned PDF sources. A revised real-person simulation paper's new title/author list was detected and recorded without combining version-specific findings. Literature results were not independently reproduced and novelty remains unproven.
"""
    with (ROOT / "docs/P0_reproducibility_report.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(repro)
    log = f"""

## {now} — P0 control diagnosis and researcher-verified annotation

Phase: **P0 only**. Objective: investigate semantic controls, reconstruct all original inputs, test versioned development candidates with the actual tokenizer, register supplied human judgments, and prepare proposals/literature review without executing P1. Maintainer: Yaxin ZHENG. Git HEAD `{audit['git_commit']}`; dirty working state recorded in source/run snapshots. No commit, push, history rewrite or author-identity change.

Read the project instructions, frozen protocol, annotation guide, current acceptance reports, conditioning/fixture implementation, original synthetic cases and 40-row annotation materials. The actual matched overrides were distinguished from unused fixture defaults. Reconstructed **100 prompts**, with identical evidence/questions and historical hashes/IDs. All 20 cases share one style and persona ID; ten have implicit “the person”/Alice binding. N_style repeats formatting language; N_history changes residence discourse to unrelated document dialogue. Findings and admissible contrast interpretations are in [the diagnostic](P0_neutral_control_diagnostic.md).

Researcher delivery occurred during this work. The first file was archived with SHA `f09a128f212a1405b9276ccc27ffd871c2365df5798d6e8feec6194dbca1733e` before its original working path disappeared. The researcher then supplied `PersonaSLM_P0_Researcher_Reviewed_v3.csv`, SHA `06629e8bc69684b3a276ec00a71558291c5762c64acc23dac619cc86d88bfb42`. Registered **40/40 human-reviewed records**, reviewer `Yaxin_ZHENG`, type `researcher_human_review`, version `researcher_verified_annotation_v1`, latest registration revision 2. Source process: claimed independent first pass, then AI-reference consultation/revision; final review is AI-assisted, not blind. Review timestamps/second reviewer/agreement remain unavailable. Initial registration and both source versions remain separate.

Available-version comparison: **0 changes across six core/two auxiliary judgment fields**, metadata/provenance changes in **40 records**. The source preceding final v3 had already been described as researcher-corrected, so it is not mislabeled as untouched AI assessment. Original AI CSV, independently saved first-pass CSV and one intermediate declared hash are unavailable: total earlier corrected judgments cannot be verified. No missing version or timestamp was fabricated.

Human overall control suitability: **PASS 0 / PARTIAL 40 / FAILED 0**. Separate deterministic dimension routing: **PASS 0 / PARTIAL 20 / FAILED 20**, reflecting 20 explicit unintended-style findings and 20 uncertain history controls. All 40 overall semantic-neutrality judgments are uncertain. Human annotation completion passes; unresolved control validity keeps P0 PARTIAL. A second reviewer is not introduced as a new blanket gate.

Development-only candidate version `neutral_control_candidate_v1_dev`, template `control_candidate_prompt_v1_dev`: all three new fictional cases, **36 style +8 history candidates each**, frozen before tokenizer access. **132 candidate attempts**, 6 reference counts, 100 historical rechecks; native GGUF tokenizer, exact tolerance 0. History **3/3** matches; style **0/3**, best signed differences **+2, -3, -3**. Failed lengths were preserved; candidate pools were not enlarged after observation and no generation answers were consulted. **Zero completions**. New history content may cue abstention, and style metadiscourse may still prime behavior; no semantic acceptance claimed.

Full tokenizer config/raw HTTP/tokens/input hashes, model/server pre/postflight and Git/source snapshot are in journal `20261012T195708-1dc4429d05c94341bf5a92c6da48c020`. Model and backend hashes match the prior pinned values; see the reproducibility addendum. All **21 original journal inventories** unchanged; all **22 current journal chains** freshly validated; annotation reconstruction also matches. Prior 140 generations, failures, parser/evaluation versions and dataset bytes preserved.

New modules: `researcher_review.py`, `control_candidates.py`, `control_resolution_review.py`; new regression files test their actual import/path/material/quote/matching failure modes. Original strict v3 importer and historical inference/evaluation code were not edited. A blank 40-item follow-up resolution form supplies original comparison materials and quotation fields; no follow-up judgments or human identities were invented. [Guide](P0_neutral_control_resolution_guide.md).

Prepared [P1 design proposal](P1_experimental_design_proposal.md), preserving S/F/H, eight factorial cells, two matched controls, separate tracks and fidelity/reliability. The illustrative 480-generation allocation is arithmetic only; no pilot or confirmatory set was generated. Reviewed nine primary-source studies in [the novelty matrix](related_work_novelty_matrix.md), including overlapping persona/factuality, memory, speaker simulation and context research. Five falsifiable proposals are not claims of established novelty. No private conversation datasets were downloaded.

Errors preserved: an early inline Python inspection failed with `SyntaxError: unterminated string literal` because Windows shell quoting removed quotes; subsequent inspections used stdin scripts/files. This was a read-only failure, not a model failure. First targeted tests: **29 passed /1 failed**, because an integration fixture used a temporary directory outside the modeled repository. Corrected the test repository root with a fixture; production path restrictions unchanged. Rerun **30 passed**. Two paper HTML routes returned 404; used available versioned PDF/abstract sources and recorded the failures.

Final full command `.\\.venv\\Scripts\\python.exe -m pytest -q`: {test_sentence}

Changed files include the three additive modules/tests, control validation/report tools, new diagnostic/registration/resolution/proposal/literature reports and immutable JSON/CSV artifacts. Current-status notices were added to nine existing reports/guides with original bytes archived; README points to current evidence. Protocol and prior experiment/evaluation sources are unchanged. Exact file inventory, hashes and command captures are indexed in the delivery evidence and command index. Tool-assisted implementation is described neutrally; no claim of exclusively manual authorship is made.

The new [current acceptance checklist](P0_control_acceptance_report.md) distinguishes completed engineering, completed human review, unresolved methodological controls, acceptable artifact/backend limitations and future research. **Overall P0 PARTIAL. P1 NOT STARTED.** Historical 0/40 entries remain accurate records of earlier moments, not current status. All Git changes await researcher review and commit.
"""
    with (ROOT / "docs/research_development_log.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(log)
    print(json.dumps({"recorded_utc": now, "reports_with_history_preserved": len(reports),
                      "tests": 263, "human_reviews": reviews["annotation_count"], "p0": "PARTIAL"}))


if __name__ == "__main__":
    main()
