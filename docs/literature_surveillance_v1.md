# PersonaSLM daily literature surveillance v1

Status: implemented prospective research support. This subsystem does not amend Research Protocol v1.1, approve a protocol change, establish novelty, or perform model inference.

## Scientific boundary

The system deliberately separates two evidence layers:

1. **Automated discovery.** A daily job queries free metadata services and writes an `UNVERIFIED_AUTOMATED_DISCOVERY` snapshot. Search matches, abstracts, venue strings, and identifier links at this layer are leads, not scientific findings.
2. **Reviewed literature ledger.** A record enters the versioned ledger only after an agent or researcher checks a primary paper record or manuscript and writes an explicit PersonaSLM impact assessment. `human_confirmation` distinguishes an AI-assisted primary-source review from a researcher-confirmed judgment.

The initial reviewed ledger is selective rather than systematic. Absence from it is not evidence that a paper or method does not exist. An overlap classification is not a priority determination, and no automated record may alter an approved protocol or frozen experiment.

## Persistent daily execution

`.github/workflows/daily-literature-monitor.yml` is configured to run every day at 04:23 UTC and can also be started manually. It has `contents: read`, uses no secret or API token, and cannot commit. It uploads `daily_snapshot.json` as a GitHub Actions artifact retained for 30 days. This is the preferred repository-level persistence mechanism while respecting the repository rule that the researcher controls commits and pushes.

The GitHub workflow is operational only after these files are included in a researcher-created checkpoint, merged into the repository's default branch, pushed to GitHub, and GitHub Actions is enabled. GitHub does not run a `schedule` merely because the workflow exists on a non-default research branch; before default-branch integration that branch provides reviewable configuration, not an active cloud scheduler. Until a successful scheduled run from the default branch is observed, its cloud state is **configured, locally tested, not remotely observed**.

An equivalent local Windows Task Scheduler task, `PersonaSLM-Daily-Literature-Monitor`, is also installed on the research workstation. It invokes `tools/run_daily_literature_monitor.ps1` every day at 04:23 local time, uses no stored credential, permits battery operation, starts when an earlier trigger was missed, rejects concurrent duplicate runs, and has a 20-minute execution limit. Interrupted-session recovery found the task missing and restored it idempotently with `tools/install_daily_literature_scheduler.ps1`. The recovered contract passed verification, and Task Scheduler recorded a real successful run at 2026-10-18T09:28:51Z. Its private ignored snapshot contains 196 unreviewed discovery records; 12/13 source requests succeeded and one Crossref HTTP failure was retained rather than interpreted as “no papers.” Evidence is in `docs/validation/literature_monitor_v1/local_scheduler_recovery_2026-10-18_v1.json`. This local scheduler is independent of an open Codex chat, but its `INTERACTIVE_ONLY` logon mode means the workstation must be on and the researcher logged in; it is therefore less durable than the unactivated GitHub schedule.

The collector queries:

- arXiv's public Atom API for primary preprint metadata and versions;
- Crossref for DOI/publication discovery;
- OpenAlex for identifier/publication discovery.

Crossref and OpenAlex records are discovery metadata, not substitutes for an author manuscript, ACL Anthology paper, OpenReview paper page, or official proceedings record. Subsequent scientific assessment should prefer those primary sources. Source failures are written into the snapshot; a run in which every source request fails exits unsuccessfully rather than reporting “no new papers.”

## Topics and query freeze

The versioned query groups cover persona conditioning, dialogue reliability, persona fidelity, personalization, temporal factual consistency, outdated and historical memory, evidence conflict, style/content separation, and CPU-efficient small-model personalization. Exact strings, endpoints, lookback, result caps, and request spacing are in `docs/validation/literature_monitor_v1/config_v1.json`.

Changing the query configuration creates a new surveillance-policy version. It must not silently rewrite earlier snapshots or be represented as the query used historically.

## Stable identifiers and versions

Records are deduplicated by stable aliases in this priority order:

1. DOI;
2. arXiv base ID, excluding `vN`;
3. ACL Anthology ID;
4. OpenReview forum ID;
5. OpenAlex work ID as a discovery fallback.

arXiv revisions remain entries in the record's `versions` array. The collector compares observed version labels with the reviewed ledger and emits `POSSIBLE_VERSION_UPDATE` when appropriate. Records sharing a DOI across Crossref and OpenAlex merge deterministically. Official DataCite aliases of the form `10.48550/arxiv.<base-id>` also match the corresponding `arxiv:<base-id>` record, while an explicitly supplied conflicting arXiv identifier is not silently replaced by a DOI-derived alias.

For the same `--as-of` date and identical API response bytes, normalized snapshot output is deterministic. Public APIs can change their metadata, so runs on different dates or against changed responses are not claimed to be byte-identical. Each request records its exact public query URL plus URL and response SHA-256 values.

## Reviewed ledger fields

The JSON Schema requires title, authors, venue/status, publication date, stable identifiers, primary source URL, verified paraphrase or methods summary, methodology, experimental factors, benchmarks, overlap, difference, novelty threat, useful baselines, methodological improvements, relevance classification, versions, verification scope, and date last checked.

Allowed relevance classes are:

- `DIRECT_OVERLAP`
- `PARTIAL_OVERLAP`
- `COMPLEMENTARY`
- `BASELINE_RELEVANT`
- `EVALUATION_RELEVANT`
- `LOW_RELEVANCE`

The ledger must not contain invented bibliographic metadata or summaries copied from unverified secondary pages. It must not promote an automated relevance match to scientific interpretation.

## Local operation

Validate policy and ledger without network access:

```powershell
.\.venv\Scripts\python.exe -B tools/literature_monitor.py validate `
  --config docs/validation/literature_monitor_v1/config_v1.json `
  --ledger docs/validation/literature_monitor_v1/reviewed_ledger_v1.json
```

Create a local discovery snapshot in an already ignored working area:

```powershell
.\.venv\Scripts\python.exe -B tools/literature_monitor.py collect `
  --config docs/validation/literature_monitor_v1/config_v1.json `
  --ledger docs/validation/literature_monitor_v1/reviewed_ledger_v1.json `
  --output .local/literature-monitor/daily_snapshot.json
```

The local scheduled wrapper can be exercised manually without changing the reviewed ledger:

```powershell
.\tools\run_daily_literature_monitor.ps1
```

Run the offline regression tests:

```powershell
.\.venv\Scripts\python.exe -B -m pytest `
  tests/test_literature_monitor.py `
  tests/test_literature_monitor_arxiv_doi_dedup.py `
  tests/test_windows_literature_scheduler.py `
  -q -ra -p no:cacheprovider
```

The collector must not be run with credentials embedded in URLs or configuration. If a future source requires authentication, add neither the credential nor private response data to this public subsystem without a separate security review.

## Review procedure for an important candidate

1. Resolve its DOI, arXiv, ACL Anthology, or OpenReview identifier.
2. Open the primary record and paper; record exactly which sections were inspected.
3. Check publication/acceptance status instead of inferring it from a heading.
4. Compare the actual intervention, population, model scale, controls, endpoints, and analysis unit with PersonaSLM.
5. Assign one allowed relevance class and an independently stated novelty-threat level.
6. Record useful baselines or measurement changes prospectively; never rewrite frozen experiments.
7. Preserve an uncertain conclusion as uncertain. Similar terminology alone is not method identity.

## Current scientific assessment

The 2026-10-18 primary-source review expands the structured ledger from eight to fourteen records. The daily snapshot delta itself contained no substantive alert; the material change came from resolving high-priority backlog and a monitor coverage gap. The closest verified collision is [Beyond similarity retrieval](https://link.springer.com/article/10.1007/s41060-026-01290-8): it combines persona-related governing facts, temporal revisions, stale superseded information, quantized small open-weight models, local CPU inference, and a temporal supersession method. [When Context Changes](https://arxiv.org/abs/2609.38866) already names and investigates old-value selection as stale binding; [MemAdapter](https://arxiv.org/abs/2610.05162) addresses unreliable influence from outdated or context-inappropriate memory; and [Persona Following Is Not Selective Control](https://arxiv.org/abs/2609.35036) shows that a named persona manipulation need not leave non-target attributes unchanged. [Back in Style](https://arxiv.org/abs/2610.10988) supplies deterministic linguistic-fidelity diagnostics, while the publisher record for [Generalization saturation and reasoning divergence](https://www.sciencedirect.com/science/article/pii/S1566253526003568) directly studies persona-consistency versus reasoning-stability trade-offs.

Consequently, PersonaSLM must not claim priority for discovering that persona/history can impair reliability, stale values can dominate current evidence, temporal supersession is useful, small models can be evaluated on CPU, or persona fidelity should be separated from correctness. The remaining testable distinction is narrower: a paired shared-evidence `2^3` Style/Facts/dated-History factorial in approximately 0.8B–3B CPU-deployed models, with outdated-value adoption separated from other error types and reliability, persona fidelity, and CPU cost reported jointly. No reviewed source in this bounded check was verified to implement that entire combination. This is a prospective contribution hypothesis, not proof of originality, factor isolation, or publication readiness.

The important methodological adaptation is prospective: treat SCR-T or an information-equivalent supersession filter as a strong baseline for any future algorithm; require non-target manipulation checks rather than treating token matching as semantic neutrality; and compare linguistic-fidelity measures against genuine researcher annotations before using them for manuscript claims. Frozen experiments and their historical outcomes remain unchanged.

## Limitations

- Metadata APIs have imperfect coverage, delays, and changing records.
- The English queries can miss different terminology and non-English titles.
- A 21-day rolling window is operational monitoring, not a systematic review.
- GitHub artifact retention is finite; scientifically important candidates must be reviewed and deliberately checkpointed by the researcher.
- Daily collection does not imply daily scientific reasoning.
- The monitor does not access restricted annotations, raw experimental outputs, model weights, or MimooPet.
