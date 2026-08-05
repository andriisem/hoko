from typer.testing import CliRunner

from hoko.adapters import precommit
from hoko.cli.main import app

runner = CliRunner()


def test_update_without_precommit_available_exits_with_a_hint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(precommit, "resolve_command", lambda: None)

    result = runner.invoke(app, ["update"])

    assert result.exit_code == 1
    assert "hoko init" in result.output


def test_update_runs_pre_commit_autoupdate(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["update"])

    assert result.exit_code == 0
    assert "All hooks updated." in result.output
    assert ["pre-commit", "autoupdate"] in fake_precommit
