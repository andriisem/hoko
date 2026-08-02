from typer.testing import CliRunner

from hoko.adapters import precommit
from hoko.cli.main import app
from hoko.config.models import HokoConfig

runner = CliRunner()


def test_init_without_yes_does_not_auto_install(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Dockerfile").write_text("")

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Install recommended capabilities?" in result.output
    assert "Docker" in result.output
    assert HokoConfig.load().capabilities == []


def test_init_with_yes_installs_recommended_capabilities(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Dockerfile").write_text("")

    result = runner.invoke(app, ["init", "--yes"])

    assert result.exit_code == 0
    capabilities = HokoConfig.load().capabilities
    assert "secrets" in capabilities
    assert "docker" in capabilities


def test_init_always_offers_secrets_even_with_no_detection(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Detected" not in result.output
    assert "Install recommended capabilities?" in result.output
    assert "Secrets" in result.output


def test_init_does_not_recommend_already_installed_capabilities(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    HokoConfig(capabilities=["secrets"]).save()

    result = runner.invoke(app, ["init", "--yes"])

    assert result.exit_code == 0
    assert result.output.count("Secrets") == 0


def test_init_persists_config_even_if_hook_install_fails(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        precommit, "install_hooks", lambda config=None, quiet=False: False
    )

    result = runner.invoke(app, ["init", "--yes"])

    assert result.exit_code == 0
    assert "Could not install git hooks" in result.output
    assert "secrets" in HokoConfig.load().capabilities


def test_init_explains_how_to_install_pre_commit_when_it_is_unavailable(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(precommit, "resolve_command", lambda: None)

    result = runner.invoke(app, ["init", "--yes"])

    assert result.exit_code == 0
    assert "pipx install pre-commit" in result.output
    assert "Could not install git hooks" not in result.output
    assert "secrets" in HokoConfig.load().capabilities
