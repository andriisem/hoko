from pathlib import Path

from typer.testing import CliRunner

from hoko.cli.main import app
from hoko.config.models import HokoConfig

runner = CliRunner()


def test_import_installs_every_capability_from_a_preset(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    preset = tmp_path / "team-preset.yaml"
    preset.write_text("version: 1\ncapabilities:\n  - python\n  - secrets\n")

    result = runner.invoke(app, ["import", str(preset)])

    assert result.exit_code == 0
    # Rich may wrap the long tmp_path across lines, so check the pieces
    # rather than the exact concatenated string.
    assert "Imported preset from" in result.output
    assert preset.name in result.output
    assert HokoConfig.load().capabilities == ["python", "secrets"]
    assert Path(".pre-commit-config.yaml").exists()


def test_import_installs_git_hooks(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)
    preset = tmp_path / "team-preset.yaml"
    preset.write_text("version: 1\ncapabilities:\n  - secrets\n")

    result = runner.invoke(app, ["import", str(preset)])

    assert result.exit_code == 0
    assert ["pre-commit", "install", "--hook-type", "pre-commit"] in fake_precommit


def test_import_missing_preset_file_fails_without_writing_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["import", "does-not-exist.yaml"])

    assert result.exit_code != 0
    assert "does not exist" in result.output
    assert not Path("hoko.yaml").exists()
