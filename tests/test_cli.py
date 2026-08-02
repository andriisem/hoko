from pathlib import Path

from typer.testing import CliRunner

from hoko.cli.main import app

runner = CliRunner()


def test_list_with_no_capabilities(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No capabilities installed" in result.output


def test_add_unknown_capability(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["add", "does-not-exist"])
    assert result.exit_code == 1


def test_add_and_list_known_capability(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)
    add_result = runner.invoke(app, ["add", "python"])
    assert add_result.exit_code == 0

    list_result = runner.invoke(app, ["list"])
    assert "Python" in list_result.output


def test_add_installs_git_hooks(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "python"])

    assert result.exit_code == 0
    assert ["pre-commit", "install", "--hook-type", "pre-commit"] in fake_precommit


def test_add_commitlint_installs_the_commit_msg_hook_type(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "commitlint"])

    assert result.exit_code == 0
    install_commands = [command for command in fake_precommit if command[1:2] == ["install"]]
    assert install_commands
    assert "--hook-type" in install_commands[0]
    assert "commit-msg" in install_commands[0]


def test_add_commitlint_creates_a_commitlint_config(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "commitlint"])

    assert result.exit_code == 0
    config = Path(".commitlintrc.yaml").read_text()
    assert "@commitlint/config-conventional" in config
    assert ".commitlintrc.yaml" in result.output


def test_add_commitlint_keeps_an_existing_commitlint_config(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "commitlint.config.js").write_text("module.exports = {rules: {}};\n")

    result = runner.invoke(app, ["add", "commitlint"])

    assert result.exit_code == 0
    assert not Path(".commitlintrc.yaml").exists()


def test_add_without_commitlint_writes_no_commitlint_config(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["add", "secrets"])

    assert not Path(".commitlintrc.yaml").exists()
