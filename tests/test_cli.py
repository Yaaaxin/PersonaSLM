import json

import pytest

from personaslm.cli import main


def test_cli_preflight_is_blocked_and_has_actionable_missing_fields(capsys):
    with pytest.raises(SystemExit) as stopped:
        main(["preflight"])
    assert stopped.value.code == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "BLOCKED"
    assert "model_sha256" in report["checks"][0]["reason"]


def test_cli_bad_override_is_not_ignored(capsys):
    with pytest.raises(SystemExit) as stopped:
        main(["preflight", "--threads", "0"])
    assert stopped.value.code == 2
    assert "threads" in json.loads(capsys.readouterr().out)["reason"]


def test_cli_missing_journal_is_blocked(capsys, local_tmp):
    with pytest.raises(SystemExit) as stopped:
        main(["audit-run", "--run-dir", str(local_tmp / "missing")])
    assert stopped.value.code == 2
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"
