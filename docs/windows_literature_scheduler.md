# Windows daily literature scheduler recovery

This runbook restores and verifies the repository's local Windows Task Scheduler integration. It does not replace or modify `.github/workflows/daily-literature-monitor.yml`. The historical scheduler evidence under `docs/validation/literature_monitor_v1/` records what was observed at that time; a clone or interrupted workstation session must verify current external scheduler state independently.

The versioned task contract is `personaslm_windows_literature_scheduler_v1`. It runs `tools/run_daily_literature_monitor.ps1` every day at 04:23 local time with the current user's interactive token, no stored password, battery operation allowed, missed-start recovery enabled, duplicate concurrent starts rejected, and a 20-minute limit. Installation never starts the task. The wrapper validates the public policy and reviewed ledger before collection and writes automated discovery only to the ignored `.local/literature-monitor/` directory. It performs no model inference and does not edit the reviewed ledger.

Inspect the intended contract without reading or changing Task Scheduler:

```powershell
.\tools\install_daily_literature_scheduler.ps1 -Describe
```

Install a missing task or reconcile that named task to the versioned contract. Run this under the Windows account that should own the interactive task:

```powershell
.\tools\install_daily_literature_scheduler.ps1 -Install
```

The command first runs the wrapper's offline `-ValidateOnly` check. If the current task already matches, it returns `changed: false`; otherwise it registers the corrected definition and verifies it. It neither prompts for nor stores credentials.

Verify the live external state without changing it:

```powershell
.\tools\install_daily_literature_scheduler.ps1 -VerifyOnly
```

Verification emits JSON and exits nonzero if the task is missing or differs in action, schedule, principal, or safety settings. It does not execute the scheduled action, so a separate observed scheduled run is still required before claiming that collection succeeded. Because the task uses an interactive token, the workstation must be on and the owning user logged in. The GitHub Actions schedule remains the preferred durable mechanism after default-branch integration and an observed scheduled run.
