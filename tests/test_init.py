from typer.testing import CliRunner

import hoko.commands.init as init_module
from hoko.cli.main import app
from hoko.config.models import HokoConfig

runner = CliRunner()


def _stub_out_precommit_binary(monkeypatch):
    monkeypatch.setattr(init_module.precommit, "ensure_installed", lambda: True)
    monkeypatch.setattr(init_module.precommit, "install_hooks", lambda: True)


def test_init_without_yes_does_not_auto_install(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _stub_out_precommit_binary(monkeypatch)
    (tmp_path / "Dockerfile").write_text("")

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Install recommended capabilities?" in result.output
    assert "Docker" in result.output
    assert HokoConfig.load().capabilities == []


def test_init_with_yes_installs_recommended_capabilities(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _stub_out_precommit_binary(monkeypatch)
    (tmp_path / "Dockerfile").write_text("")

    result = runner.invoke(app, ["init", "--yes"])

    assert result.exit_code == 0
    capabilities = HokoConfig.load().capabilities
    assert "secrets" in capabilities
    assert "docker" in capabilities


def test_init_always_offers_secrets_even_with_no_detection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _stub_out_precommit_binary(monkeypatch)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Detected" not in result.output
    assert "Install recommended capabilities?" in result.output
    assert "Secrets" in result.output


def test_init_does_not_recommend_already_installed_capabilities(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _stub_out_precommit_binary(monkeypatch)
    HokoConfig(capabilities=["secrets"]).save()

    result = runner.invoke(app, ["init", "--yes"])

    assert result.exit_code == 0
    assert result.output.count("Secrets") == 0


def test_init_persists_config_even_if_hook_install_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(init_module.precommit, "ensure_installed", lambda: True)
    monkeypatch.setattr(init_module.precommit, "install_hooks", lambda: False)

    result = runner.invoke(app, ["init", "--yes"])

    assert result.exit_code == 0
    assert "Could not install git hooks" in result.output
    assert "secrets" in HokoConfig.load().capabilities


def test_init_explains_how_to_install_pre_commit_when_it_is_unavailable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(init_module.precommit, "ensure_installed", lambda: False)

    def fail(*args, **kwargs):
        raise AssertionError("hooks must not be installed without pre-commit")

    monkeypatch.setattr(init_module.precommit, "install_hooks", fail)

    result = runner.invoke(app, ["init", "--yes"])

    assert result.exit_code == 0
    assert "pipx install pre-commit" in result.output
    assert "secrets" in HokoConfig.load().capabilities
