from pathlib import Path

from typer.testing import CliRunner

from hoko.cli.main import app
from hoko.commands import add, rm
from hoko.config.models import HokoConfig

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


def test_add_commitlint_installs_the_commit_msg_hook_type(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "commitlint"])

    assert result.exit_code == 0
    install_commands = [
        command for command in fake_precommit if command[1:2] == ["install"]
    ]
    assert install_commands
    assert "--hook-type" in install_commands[0]
    assert "commit-msg" in install_commands[0]


def test_add_commitlint_creates_a_commitlint_config(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["add", "commitlint"])

    assert result.exit_code == 0
    config = Path(".commitlintrc.yaml").read_text()
    assert "@commitlint/config-conventional" in config
    assert ".commitlintrc.yaml" in result.output


def test_generated_commitlint_config_passes_default_yamllint_rules(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["add", "commitlint"])

    lines = Path(".commitlintrc.yaml").read_text().splitlines()
    assert lines[0] == "---"
    assert all(len(line) <= 80 for line in lines)


def test_add_commitlint_keeps_an_existing_commitlint_config(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "commitlint.config.js").write_text("module.exports = {rules: {}};\n")

    result = runner.invoke(app, ["add", "commitlint"])

    assert result.exit_code == 0
    assert not Path(".commitlintrc.yaml").exists()


def test_add_without_commitlint_writes_no_commitlint_config(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)

    runner.invoke(app, ["add", "secrets"])

    assert not Path(".commitlintrc.yaml").exists()


def test_rm_removes_an_installed_capability(tmp_path, monkeypatch, fake_precommit):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "python"])

    result = runner.invoke(app, ["rm", "python"])

    assert result.exit_code == 0
    assert "Removed python" in result.output
    assert HokoConfig.load().capabilities == []


def test_remove_still_works_as_a_hidden_alias_for_rm(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "python"])

    result = runner.invoke(app, ["remove", "python"])

    assert result.exit_code == 0
    assert HokoConfig.load().capabilities == []


def test_remove_is_hidden_from_the_command_list(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["--help"])

    assert " rm " in result.output
    assert " remove " not in result.output


def test_add_without_arguments_prompts_for_capabilities(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(add, "is_interactive", lambda: True)
    monkeypatch.setattr(add, "multiselect", lambda message, options: ["python", "yaml"])

    result = runner.invoke(app, ["add"])

    assert result.exit_code == 0
    assert HokoConfig.load().capabilities == ["python", "yaml"]


def test_add_prompt_offers_installed_capabilities_as_disabled(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "python"])
    monkeypatch.setattr(add, "is_interactive", lambda: True)

    offered = {}

    def capture(message, options):
        offered.update({option.value: option.disabled for option in options})
        return []

    monkeypatch.setattr(add, "multiselect", capture)
    runner.invoke(app, ["add"])

    assert offered["python"] == "installed"
    assert offered["yaml"] == ""


def test_rm_without_arguments_prompts_with_installed_capabilities(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "python", "yaml"])
    monkeypatch.setattr(rm, "is_interactive", lambda: True)

    offered = []

    def capture(message, options):
        offered.extend(option.value for option in options)
        return ["yaml"]

    monkeypatch.setattr(rm, "multiselect", capture)
    result = runner.invoke(app, ["rm"])

    assert result.exit_code == 0
    assert offered == ["python", "yaml"]
    assert HokoConfig.load().capabilities == ["python"]


def test_add_without_arguments_outside_a_terminal_reports_the_missing_argument(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(add, "is_interactive", lambda: False)

    result = runner.invoke(app, ["add"])

    assert result.exit_code == 1
    assert "Missing argument" in result.output


def test_rm_without_arguments_outside_a_terminal_reports_the_missing_argument(
    tmp_path, monkeypatch, fake_precommit
):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["add", "python"])
    monkeypatch.setattr(rm, "is_interactive", lambda: False)

    result = runner.invoke(app, ["rm"])

    assert result.exit_code == 1
    assert "Missing argument" in result.output


def test_rm_without_arguments_and_nothing_installed_exits_cleanly(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["rm"])

    assert result.exit_code == 0
    assert "No capabilities installed" in result.output
