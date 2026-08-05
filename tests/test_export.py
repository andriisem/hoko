from pathlib import Path

from typer.testing import CliRunner

from hoko.cli.main import app
from hoko.config.models import HokoConfig

runner = CliRunner()


def test_export_writes_a_preset_with_installed_capabilities(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "python", "secrets"])

    result = runner.invoke(app, ["export"])

    assert result.exit_code == 0
    assert "Exported preset to hoko.yaml" in result.output
    assert HokoConfig.load(Path("hoko.yaml")).capabilities == ["python", "secrets"]


def test_export_to_a_custom_path(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "yaml"])

    result = runner.invoke(app, ["export", "team-preset.yaml"])

    assert result.exit_code == 0
    assert "Exported preset to team-preset.yaml" in result.output
    assert Path("team-preset.yaml").exists()
    assert HokoConfig.load(Path("team-preset.yaml")).capabilities == ["yaml"]


def test_export_with_no_capabilities_writes_an_empty_preset(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["export"])

    assert result.exit_code == 0
    assert HokoConfig.load(Path("hoko.yaml")).capabilities == []
