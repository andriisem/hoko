import subprocess

from typer.testing import CliRunner

from hoko.adapters import precommit
from hoko.cli.main import app

runner = CliRunner()


def test_check_without_precommit_available_exits_with_a_hint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(precommit, "resolve_command", lambda: None)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1
    assert "hoko init" in result.output


def test_check_runs_all_hooks_and_reports_success(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 0
    assert "All checks passed." in result.output
    assert ["pre-commit", "run", "--all-files"] in fake_precommit


def test_check_propagates_a_failing_hooks_exit_code(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)

    def failing_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(precommit.subprocess, "run", failing_run)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1
    assert "All checks passed." not in result.output
