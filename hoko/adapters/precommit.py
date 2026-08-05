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
from hoko.generators.tool_configs import missing_commitlint_config

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


def _numeric_version(rev: str) -> tuple[int, ...] | None:
    """Best-effort numeric version tuple from a tag like `v0.6.9` or `v4.0.0-alpha.8`.

    Only the leading dotted-numeric run is used - `v4.0.0-alpha.8` reads as
    (4, 0, 0), a pre-release suffix isn't weighed. Returns None for tags that
    don't start with a comparable numeric segment (e.g. a hand-picked branch
    name); callers must treat that as "can't tell", never as "older".
    """
    text = rev[1:] if rev.startswith("v") else rev
    prefix = text.split("-")[0].split("+")[0]
    numbers: list[int] = []
    for part in prefix.split("."):
        if not part.isdigit():
            break
        numbers.append(int(part))
    return tuple(numbers) if numbers else None


def _is_older(rev: str, than: str) -> bool:
    """True only when `rev` is a strictly older, comparable version than `than`.

    Unparseable or equal revs are never reported as older - staleness
    detection would rather stay silent than wrongly flag (or downgrade) a
    pin it can't confidently compare.
    """
    current = _numeric_version(rev)
    reference = _numeric_version(than)
    if current is None or reference is None:
        return False
    return current < reference


def _merge_repos(existing_repos: list, managed_repos: list[dict]) -> list:
    """Keep repos the user added by hand; refresh hoko's own repos in place.

    A repo counts as "hand-added" if its `repo:` URL isn't one hoko manages
    (see MANAGED_REPO_URLS) — this covers local hooks, custom repos, or
    anything not sourced from a hoko capability.

    For a managed repo, the hook list always comes from `managed_repos` (it
    must reflect the currently configured capabilities), but its `rev` is
    only bumped up to hoko's bundled default when the existing pin is older -
    never downgraded. `hoko update` (via `pre-commit autoupdate`) is free to
    move a managed repo's rev ahead of hoko's own bundled pin; regenerating
    the file must not silently undo that, or "safe and idempotent" stops
    being true for anyone who has ever run `hoko update`.
    """
    user_owned = [
        repo for repo in existing_repos if repo.get("repo") not in MANAGED_REPO_URLS
    ]
    existing_rev_by_repo = {
        repo.get("repo"): repo.get("rev")
        for repo in existing_repos
        if repo.get("repo") in MANAGED_REPO_URLS
    }

    refreshed_managed = []
    for repo in managed_repos:
        existing_rev = existing_rev_by_repo.get(repo["repo"])
        if existing_rev and not _is_older(existing_rev, repo["rev"]):
            repo = {**repo, "rev": existing_rev}
        refreshed_managed.append(repo)

    return user_owned + refreshed_managed


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


def _stale_managed_repos(config: HokoConfig, path: Path | None = None) -> list[str]:
    """Managed repo URLs whose pinned rev is older than hoko's bundled default.

    A repo missing from the file entirely isn't reported here - that's the
    "Configuration valid" / hooks-installed checks' job. This only flags a
    rev that's present and behind, per `_is_older`'s conservative rules.
    """
    path = path or Path(CONFIG_FILENAME)
    current_rev_by_repo = {
        repo.get("repo"): repo.get("rev")
        for repo in _load_document(path).get("repos") or []
    }
    return [
        repo["repo"]
        for repo in render_repos(config)
        if _is_older(current_rev_by_repo.get(repo["repo"], repo["rev"]), repo["rev"])
    ]


def health_checks(config: HokoConfig) -> list[HealthCheck]:
    checks = [HealthCheck("pre-commit available", is_installed())]

    for hook_type in required_hook_types(config):
        label = (
            "Hooks installed"
            if hook_type == DEFAULT_HOOK_TYPE
            else f"{hook_type} hook installed"
        )
        checks.append(HealthCheck(label, (Path(".git") / "hooks" / hook_type).exists()))

    checks.append(HealthCheck("Configuration valid", Path(CONFIG_FILENAME).exists()))
    checks.append(
        HealthCheck("Hook versions current", not _stale_managed_repos(config))
    )

    if "commitlint" in config.capabilities:
        checks.append(
            HealthCheck(
                "Commitlint config present",
                not missing_commitlint_config(config),
            )
        )

    return checks


def health_score(checks: list[HealthCheck]) -> int:
    """The 0-100 score `doctor` reports, derived from `health_checks`."""
    passed = sum(1 for check in checks if check.ok)
    return int(100 * passed / len(checks)) if checks else 100
