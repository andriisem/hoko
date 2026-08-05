import json
from pathlib import Path

from typer.testing import CliRunner

from hoko.cli.main import app

runner = CliRunner()


def test_doctor_reports_issues_without_fixing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "hoko doctor --fix" in result.output
    assert not Path(".pre-commit-config.yaml").exists()


def test_doctor_fix_repairs_missing_configuration(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "secrets"])
    Path(".pre-commit-config.yaml").unlink()

    result = runner.invoke(app, ["doctor", "--fix"])

    assert result.exit_code == 0
    assert Path(".pre-commit-config.yaml").exists()
    assert ["pre-commit", "install", "--hook-type", "pre-commit"] in fake_precommit


def test_doctor_fix_prints_a_before_and_after_report(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor", "--fix"])

    assert result.exit_code == 0
    assert result.output.count("Repository Health") == 2
    # No capabilities installed, no real .git directory in this tmp_path (the
    # fake pre-commit fixture only records commands, it never touches disk),
    # so "Hooks installed" never turns true here either side of --fix.
    # Before: pre-commit available + Hook versions current pass (2/4).
    assert "50 / 100" in result.output
    # After: Configuration valid also starts passing (3/4).
    assert "75 / 100" in result.output


def test_doctor_does_not_touch_the_repo_without_fix(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["doctor"])

    assert not Path(".pre-commit-config.yaml").exists()
    assert not Path("hoko.yaml").exists()


def test_doctor_json_is_valid_json_with_no_extra_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    json.loads(result.output)


def test_doctor_json_reports_score_capabilities_and_checks(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "secrets"])

    result = runner.invoke(app, ["doctor", "--json"])

    payload = json.loads(result.output)
    assert payload["capabilities"] == ["secrets"]
    assert payload["fix_attempted"] is False
    assert {check["message"] for check in payload["checks"]} == {
        "pre-commit available",
        "Hooks installed",
        "Configuration valid",
        "Hook versions current",
    }


def test_doctor_json_does_not_fix_without_the_fix_flag(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "secrets"])
    Path(".pre-commit-config.yaml").unlink()

    result = runner.invoke(app, ["doctor", "--json"])

    payload = json.loads(result.output)
    assert payload["fix_attempted"] is False
    assert not Path(".pre-commit-config.yaml").exists()


def test_doctor_json_fix_reports_fix_attempted_and_post_fix_state(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "secrets"])
    Path(".pre-commit-config.yaml").unlink()

    result = runner.invoke(app, ["doctor", "--fix", "--json"])

    payload = json.loads(result.output)
    assert payload["fix_attempted"] is True
    # 3 of 4 checks pass: pre-commit available, Configuration valid (just
    # repaired), Hook versions current. "Hooks installed" stays false - this
    # tmp_path has no real .git directory for the fake pre-commit fixture to
    # touch.
    assert payload["score"] == 75
    config_check = next(
        c for c in payload["checks"] if c["message"] == "Configuration valid"
    )
    assert config_check["ok"] is True
    assert Path(".pre-commit-config.yaml").exists()
