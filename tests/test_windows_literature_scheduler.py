import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "install_daily_literature_scheduler.ps1"


class WindowsLiteratureSchedulerTests(unittest.TestCase):
    def test_described_contract_is_safe_and_reproducible(self):
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable")

        completed = subprocess.run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(SCRIPT),
                "-Describe",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)
        contract = report["contract"]

        self.assertEqual(report["schema_version"], "personaslm_windows_literature_scheduler_v1")
        self.assertEqual(report["mode"], "DESCRIBE")
        self.assertFalse(report["changed"])
        self.assertFalse(report["task_started"])
        self.assertEqual(contract["task_name"], "PersonaSLM-Daily-Literature-Monitor")
        self.assertEqual(contract["schedule"], {
            "frequency": "DAILY",
            "local_time": "04:23",
            "days_interval": 1,
        })
        self.assertEqual(contract["principal"]["logon_type"], "INTERACTIVE_TOKEN")
        self.assertFalse(contract["principal"]["stored_credentials"])
        self.assertTrue(contract["settings"]["allow_start_on_batteries"])
        self.assertTrue(contract["settings"]["start_when_available"])
        self.assertEqual(contract["settings"]["multiple_instances"], "IGNORE_NEW")
        self.assertEqual(contract["settings"]["execution_time_limit_minutes"], 20)
        self.assertEqual(
            Path(contract["action"]["wrapper"]).resolve(),
            (ROOT / "tools" / "run_daily_literature_monitor.ps1").resolve(),
        )

    def test_installer_never_starts_or_deletes_the_task(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Register-ScheduledTask", text)
        self.assertIn("Get-ScheduledTask", text)
        self.assertIn("SecurityIdentifier", text)
        self.assertNotIn("Start-ScheduledTask", text)
        self.assertNotIn("Unregister-ScheduledTask", text)
        self.assertNotIn("schtasks.exe", text.lower())
        self.assertNotIn("-RunLevel Highest", text)


if __name__ == "__main__":
    unittest.main()
