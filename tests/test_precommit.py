import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

from hoko.adapters import precommit
from hoko.adapters.precommit import render_repos, write_config
from hoko.config.models import HokoConfig

_yaml = YAML()


def test_render_repos_is_empty_for_no_capabilities():
    assert render_repos(HokoConfig()) == []


def test_render_repos_produces_valid_repo_rev_hooks_shape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["python", "secrets"])

    repos = render_repos(config)

    assert repos
    for repo in repos:
        assert set(repo) == {"repo", "rev", "hooks"}
        for hook in repo["hooks"]:
            assert "id" in hook


def test_render_repos_dedupes_shared_tools_across_capabilities(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("")
    config = HokoConfig(capabilities=["python", "formatting"])

    repos = render_repos(config)

    ruff_repos = [repo for repo in repos if repo["repo"].endswith("ruff-pre-commit")]
    assert len(ruff_repos) == 1
    hook_ids = [hook["id"] for hook in ruff_repos[0]["hooks"]]
    assert hook_ids == ["ruff", "ruff-format"]


def test_write_config_creates_file_when_none_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["secrets"])

    write_config(config)

    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    assert document["repos"][0]["repo"].endswith("detect-secrets")


def test_write_config_preserves_hand_added_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".pre-commit-config.yaml"
    config_path.write_text(
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: my-custom-check\n"
        "        name: My Custom Check\n"
        "        entry: ./scripts/check.sh\n"
        "        language: script\n"
    )

    write_config(HokoConfig(capabilities=["secrets"]))

    document = _yaml.load(config_path.read_text())
    local_repos = [repo for repo in document["repos"] if repo["repo"] == "local"]
    assert len(local_repos) == 1
    assert local_repos[0]["hooks"][0]["id"] == "my-custom-check"

    managed_repos = [repo for repo in document["repos"] if repo["repo"] != "local"]
    assert any(repo["repo"].endswith("detect-secrets") for repo in managed_repos)


def test_write_config_drops_stale_managed_repo_when_capability_removed(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    write_config(HokoConfig(capabilities=["secrets", "markdown"]))
    write_config(HokoConfig(capabilities=["secrets"]))

    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    repo_urls = [repo["repo"] for repo in document["repos"]]
    assert any(url.endswith("detect-secrets") for url in repo_urls)
    assert not any(url.endswith("markdownlint-cli") for url in repo_urls)


def test_write_config_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["python", "secrets"])

    write_config(config)
    write_config(config)

    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    assert document["repos"] == render_repos(config)


def test_write_config_preserves_other_top_level_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".pre-commit-config.yaml"
    config_path.write_text(
        "default_language_version:\n  python: python3.12\nrepos: []\n"
    )

    write_config(HokoConfig(capabilities=["secrets"]))

    document = _yaml.load(config_path.read_text())
    assert document["default_language_version"]["python"] == "python3.12"


def test_required_hook_types_is_just_pre_commit_by_default():
    assert precommit.required_hook_types(HokoConfig(capabilities=["secrets"])) == [
        "pre-commit"
    ]


def test_required_hook_types_includes_commit_msg_for_commitlint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    hook_types = precommit.required_hook_types(
        HokoConfig(capabilities=["secrets", "commitlint"])
    )

    assert hook_types == ["pre-commit", "commit-msg"]


def test_install_hooks_lets_pre_commit_print_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(precommit, "resolve_command", lambda: ["pre-commit"])

    captured = {}

    def run(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(precommit.subprocess, "run", run)

    precommit.install_hooks(HokoConfig())

    assert not captured.get("capture_output")


def test_install_hooks_quiet_captures_pre_commits_own_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(precommit, "resolve_command", lambda: ["pre-commit"])

    captured = {}

    def run(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(precommit.subprocess, "run", run)

    precommit.install_hooks(HokoConfig(), quiet=True)

    assert captured.get("capture_output") is True


def _fake_which(monkeypatch, found: dict[str | None, str]):
    """Stub shutil.which, keyed by the `path` argument it is called with."""

    def which(name, mode=None, path=None):
        if name != "pre-commit":
            return None
        return found.get(path)

    monkeypatch.setattr(precommit.shutil, "which", which)


def test_resolve_command_prefers_pre_commit_on_path(monkeypatch):
    _fake_which(monkeypatch, {None: "/usr/local/bin/pre-commit"})

    assert precommit.resolve_command() == ["/usr/local/bin/pre-commit"]


def test_resolve_command_finds_pre_commit_beside_our_interpreter(monkeypatch):
    interpreter_bin = str(Path(sys.executable).parent)
    _fake_which(monkeypatch, {interpreter_bin: f"{interpreter_bin}/pre-commit"})

    assert precommit.resolve_command() == [f"{interpreter_bin}/pre-commit"]


def test_resolve_command_falls_back_to_importable_module(monkeypatch):
    _fake_which(monkeypatch, {})
    monkeypatch.setattr(precommit.importlib.util, "find_spec", lambda name: object())

    assert precommit.resolve_command() == [sys.executable, "-m", "pre_commit"]


def test_resolve_command_returns_none_when_unavailable(monkeypatch):
    _fake_which(monkeypatch, {})
    monkeypatch.setattr(precommit.importlib.util, "find_spec", lambda name: None)

    assert precommit.resolve_command() is None


def test_ensure_installed_never_shells_out_to_bare_pip(monkeypatch):
    commands: list[list[str]] = []
    monkeypatch.setattr(precommit, "is_installed", lambda: False)
    monkeypatch.setattr(
        precommit.subprocess,
        "run",
        lambda command, **kwargs: (
            commands.append(command) or subprocess.CompletedProcess(command, 1)
        ),
    )

    assert precommit.ensure_installed() is False
    assert commands
    assert all(Path(command[0]).name not in {"pip", "pip.exe"} for command in commands)
    assert commands[0][:3] == [sys.executable, "-m", "pip"]


def test_ensure_installed_reports_success_once_pre_commit_appears(monkeypatch):
    available = iter([False, True])
    monkeypatch.setattr(precommit, "is_installed", lambda: next(available))
    monkeypatch.setattr(
        precommit.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0),
    )

    assert precommit.ensure_installed() is True


def test_ensure_installed_survives_a_missing_installer(monkeypatch):
    monkeypatch.setattr(precommit, "is_installed", lambda: False)

    def run(command, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", command[0])

    monkeypatch.setattr(precommit.subprocess, "run", run)

    assert precommit.ensure_installed() is False


def _set_detect_secrets_rev(rev: str) -> None:
    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    for repo in document["repos"]:
        if repo["repo"].endswith("detect-secrets"):
            repo["rev"] = rev
    with Path(".pre-commit-config.yaml").open("w") as handle:
        _yaml.dump(document, handle)


def test_is_older_detects_a_behind_pin():
    assert precommit._is_older("v1.4.0", "v1.5.0") is True


def test_is_older_treats_an_equal_pin_as_not_older():
    assert precommit._is_older("v1.5.0", "v1.5.0") is False


def test_is_older_treats_an_ahead_pin_as_not_older():
    assert precommit._is_older("v2.0.0", "v1.5.0") is False


def test_is_older_is_silent_on_unparseable_revs():
    assert precommit._is_older("main", "v1.5.0") is False
    assert precommit._is_older("v1.5.0", "some-branch") is False


def test_write_config_bumps_a_pin_older_than_hokos_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["secrets"])
    write_config(config)
    _set_detect_secrets_rev("v1.0.0")

    write_config(config)

    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    repo = next(r for r in document["repos"] if r["repo"].endswith("detect-secrets"))
    assert repo["rev"] != "v1.0.0"


def test_write_config_never_downgrades_a_pin_ahead_of_hokos_default(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["secrets"])
    write_config(config)
    # Simulate `pre-commit autoupdate` (via `hoko update`) moving the pin
    # ahead of hoko's own bundled default.
    _set_detect_secrets_rev("v9.9.9")

    write_config(config)

    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    repo = next(r for r in document["repos"] if r["repo"].endswith("detect-secrets"))
    assert repo["rev"] == "v9.9.9"


def test_health_checks_flags_a_stale_hook_pin(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["secrets"])
    write_config(config)
    _set_detect_secrets_rev("v1.0.0")

    checks = precommit.health_checks(config)

    stale_check = next(c for c in checks if c.message == "Hook versions current")
    assert stale_check.ok is False


def test_health_checks_does_not_flag_an_autoupdated_pin_as_stale(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["secrets"])
    write_config(config)
    _set_detect_secrets_rev("v9.9.9")

    checks = precommit.health_checks(config)

    stale_check = next(c for c in checks if c.message == "Hook versions current")
    assert stale_check.ok is True


def test_health_checks_include_commit_msg_hook_and_config_checks_for_commitlint():
    checks = precommit.health_checks(HokoConfig(capabilities=["commitlint"]))

    assert any(c.message == "commit-msg hook installed" for c in checks)
    assert any(c.message == "Commitlint config present" for c in checks)


def test_health_checks_omit_commitlint_only_checks_when_not_installed():
    checks = precommit.health_checks(HokoConfig(capabilities=["secrets"]))

    assert not any(c.message == "commit-msg hook installed" for c in checks)
    assert not any(c.message == "Commitlint config present" for c in checks)


def test_health_checks_reports_a_missing_commitlint_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["commitlint"])

    checks = precommit.health_checks(config)

    commitlint_check = next(
        c for c in checks if c.message == "Commitlint config present"
    )
    assert commitlint_check.ok is False


def test_health_checks_passes_once_the_commitlint_config_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["commitlint"])
    from hoko.generators.tool_configs import ensure_tool_configs

    ensure_tool_configs(config)

    checks = precommit.health_checks(config)

    commitlint_check = next(
        c for c in checks if c.message == "Commitlint config present"
    )
    assert commitlint_check.ok is True
