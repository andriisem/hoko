from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML

from hoko.capabilities.registry import get_capability
from hoko.config.models import HokoConfig
from hoko.detection.detector import detect_project
from hoko.generators.hook_repos import MANAGED_REPO_URLS, repos_for
from hoko.generators.hooks import hook_ids_for

CONFIG_FILENAME = ".pre-commit-config.yaml"
DEFAULT_HOOK_TYPE = "pre-commit"

_yaml = YAML()
_yaml.preserve_quotes = True


@dataclass
class HealthCheck:
    message: str
    ok: bool


def resolve_command() -> list[str] | None:
    """Find a runnable pre-commit, or None if there isn't one.

    PATH is only the first place to look: hoko is usually installed by pipx or
    Homebrew into an isolated virtualenv whose bin directory is not on PATH, so a
    pre-commit living next to us is invisible to `shutil.which`.
    """
    on_path = shutil.which("pre-commit")
    if on_path:
        return [on_path]

    beside_us = shutil.which("pre-commit", path=os.path.dirname(sys.executable))
    if beside_us:
        return [beside_us]

    if importlib.util.find_spec("pre_commit") is not None:
        return [sys.executable, "-m", "pre_commit"]

    return None


def is_installed() -> bool:
    return resolve_command() is not None


def _install_commands() -> list[list[str]]:
    """Ways to obtain pre-commit, best first.

    Installing into our own interpreter comes first because it works for every
    layout that has pip available (venv, pipx venv, Homebrew venv) and needs
    nothing else on the machine. `pip` as a bare command is never used: plenty of
    systems only ship `pip3`, or no pip launcher at all.
    """
    commands = [[sys.executable, "-m", "pip", "install", "pre-commit"]]
    for installer, arguments in (("uv", ["tool", "install"]), ("pipx", ["install"])):
        executable = shutil.which(installer)
        if executable:
            commands.append([executable, *arguments, "pre-commit"])
    return commands


def ensure_installed() -> bool:
    """Install pre-commit if it is missing. Returns whether it is available afterwards."""
    if is_installed():
        return True

    for command in _install_commands():
        try:
            subprocess.run(command, capture_output=True, check=False)
        except OSError:
            continue
        importlib.invalidate_caches()
        if is_installed():
            return True

    return False


def render_repos(config: HokoConfig) -> list[dict]:
    """Build the `repos:` section of .pre-commit-config.yaml from installed capabilities."""
    ecosystems = detect_project()
    tool_ids: list[str] = []
    for name in config.capabilities:
        capability = get_capability(name)
        if capability is None:
            continue
        for tool_id in hook_ids_for(capability, ecosystems):
            if tool_id not in tool_ids:
                tool_ids.append(tool_id)
    return repos_for(tool_ids)


def _load_document(path: Path) -> dict:
    if not path.exists():
        return {"repos": []}
    with path.open() as handle:
        document = _yaml.load(handle)
    return document if document is not None else {"repos": []}


def _merge_repos(existing_repos: list, managed_repos: list[dict]) -> list:
    """Keep repos the user added by hand; replace hoko's own repos with fresh ones.

    A repo counts as "hand-added" if its `repo:` URL isn't one hoko manages
    (see MANAGED_REPO_URLS) — this covers local hooks, custom repos, or
    anything not sourced from a hoko capability.
    """
    user_owned = [
        repo for repo in existing_repos if repo.get("repo") not in MANAGED_REPO_URLS
    ]
    return user_owned + managed_repos


def write_config(config: HokoConfig, path: Path | None = None) -> None:
    path = path or Path(CONFIG_FILENAME)
    document = _load_document(path)
    document["repos"] = _merge_repos(document.get("repos") or [], render_repos(config))
    with path.open("w") as handle:
        _yaml.dump(document, handle)


def required_hook_types(config: HokoConfig) -> list[str]:
    """Git hook types that must be installed for the configured capabilities.

    Most hooks run at the default `pre-commit` stage, but some live elsewhere:
    commitlint only fires on `commit-msg`, which is a separate git hook file and
    is never created by a plain `pre-commit install`.
    """
    hook_types = [DEFAULT_HOOK_TYPE]
    for repo in render_repos(config):
        for hook in repo["hooks"]:
            for stage in hook.get("stages", []):
                if stage not in hook_types:
                    hook_types.append(stage)
    return hook_types


def install_hooks(config: HokoConfig | None = None, quiet: bool = False) -> bool:
    command = resolve_command()
    if command is None:
        return False

    config = HokoConfig.load() if config is None else config
    arguments: list[str] = []
    for hook_type in required_hook_types(config):
        arguments += ["--hook-type", hook_type]

    # `pre-commit install` writes its own confirmation line straight to the
    # inherited stdout. Callers that need clean, parseable stdout (e.g.
    # `hoko doctor --json`) pass quiet=True to capture it instead.
    result = subprocess.run([*command, "install", *arguments], capture_output=quiet)
    return result.returncode == 0


def update_hooks(config: HokoConfig) -> None:
    command = resolve_command()
    if command is not None:
        subprocess.run([*command, "autoupdate"], check=True)


def run_all_hooks() -> int:
    command = resolve_command()
    if command is None:
        return 1
    result = subprocess.run([*command, "run", "--all-files"])
    return result.returncode


def health_checks(config: HokoConfig) -> list[HealthCheck]:
    return [
        HealthCheck("pre-commit available", is_installed()),
        HealthCheck(
            "Hooks installed", (Path(".git") / "hooks" / "pre-commit").exists()
        ),
        HealthCheck("Configuration valid", Path(CONFIG_FILENAME).exists()),
    ]


def health_score(checks: list[HealthCheck]) -> int:
    """The 0-100 score `doctor` reports, derived from `health_checks`."""
    passed = sum(1 for check in checks if check.ok)
    return int(100 * passed / len(checks)) if checks else 100
