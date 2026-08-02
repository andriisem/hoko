import json
from pathlib import Path

from typer.testing import CliRunner

from hoko.cli.main import app

runner = CliRunner()


def _make_repo(path: Path, healthy: bool = False) -> None:
    hooks_dir = path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    if healthy:
        (hooks_dir / "pre-commit").write_text("#!/bin/sh\n")
        (path / ".pre-commit-config.yaml").write_text("repos: []\n")


def test_fleet_reports_a_missing_path_without_crashing(tmp_path, fake_precommit):
    missing = tmp_path / "does-not-exist"

    result = runner.invoke(app, ["fleet", str(missing), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["repos"][0]["error"] == "path does not exist"
    assert payload["summary"]["errors"] == 1


def test_fleet_reports_error_for_a_non_git_directory(tmp_path, fake_precommit):
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()

    result = runner.invoke(app, ["fleet", str(not_a_repo), "--json"])

    payload = json.loads(result.output)
    assert payload["repos"][0]["error"] == "not a git repository"
    assert payload["summary"]["errors"] == 1


def test_fleet_json_rolls_up_multiple_repos(tmp_path, fake_precommit):
    healthy = tmp_path / "healthy-repo"
    unhealthy = tmp_path / "unhealthy-repo"
    healthy.mkdir()
    unhealthy.mkdir()
    _make_repo(healthy, healthy=True)
    _make_repo(unhealthy, healthy=False)

    result = runner.invoke(app, ["fleet", str(healthy), str(unhealthy), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"]["count"] == 2
    assert payload["summary"]["healthy"] == 1
    scores = {entry["path"]: entry["score"] for entry in payload["repos"]}
    assert scores[str(healthy)] == 100
    assert scores[str(unhealthy)] < 100


def test_fleet_does_not_fix_without_the_fix_flag(tmp_path, fake_precommit):
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_repo(repo, healthy=False)
    (repo / "hoko.yaml").write_text("version: 1\ncapabilities:\n  - secrets\n")

    result = runner.invoke(app, ["fleet", str(repo), "--json"])

    payload = json.loads(result.output)
    assert payload["repos"][0]["fix_attempted"] is False
    assert not (repo / ".pre-commit-config.yaml").exists()


def test_fleet_fix_repairs_each_unhealthy_repo(tmp_path, fake_precommit):
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_repo(repo, healthy=False)
    (repo / "hoko.yaml").write_text("version: 1\ncapabilities:\n  - secrets\n")

    result = runner.invoke(app, ["fleet", str(repo), "--fix", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    entry = payload["repos"][0]
    assert entry["fix_attempted"] is True
    assert entry["capabilities"] == ["secrets"]
    assert (repo / ".pre-commit-config.yaml").exists()


def test_fleet_restores_the_original_working_directory(
    tmp_path, fake_precommit, monkeypatch
):
    caller_cwd = tmp_path / "caller"
    caller_cwd.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_repo(repo, healthy=True)
    monkeypatch.chdir(caller_cwd)

    runner.invoke(app, ["fleet", str(repo)])

    assert Path.cwd() == caller_cwd


def test_fleet_table_output_lists_each_repo(tmp_path, fake_precommit):
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_repo(repo, healthy=True)

    result = runner.invoke(app, ["fleet", str(repo)])

    assert result.exit_code == 0
    assert "healthy" in result.output.lower()
    assert "1 / 1 repositories healthy" in result.output
