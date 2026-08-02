from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML

from hoko.capabilities.registry import get_capability
from hoko.config.models import HokoConfig
from hoko.detection.detector import detect_project
from hoko.generators.hook_repos import MANAGED_REPO_URLS, repos_for
from hoko.generators.hooks import hook_ids_for

CONFIG_FILENAME = ".pre-commit-config.yaml"

_yaml = YAML()
_yaml.preserve_quotes = True


@dataclass
class HealthCheck:
    message: str
    ok: bool


def is_installed() -> bool:
    return shutil.which("pre-commit") is not None


def ensure_installed() -> None:
    if not is_installed():
        subprocess.run(["pip", "install", "pre-commit"], check=True)


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
    user_owned = [repo for repo in existing_repos if repo.get("repo") not in MANAGED_REPO_URLS]
    return user_owned + managed_repos


def write_config(config: HokoConfig, path: Path | None = None) -> None:
    path = path or Path(CONFIG_FILENAME)
    document = _load_document(path)
    document["repos"] = _merge_repos(document.get("repos") or [], render_repos(config))
    with path.open("w") as handle:
        _yaml.dump(document, handle)


def install_hooks() -> bool:
    if not is_installed():
        return False
    result = subprocess.run(["pre-commit", "install"])
    return result.returncode == 0


def update_hooks(config: HokoConfig) -> None:
    if is_installed():
        subprocess.run(["pre-commit", "autoupdate"], check=True)


def run_all_hooks() -> int:
    if not is_installed():
        return 1
    result = subprocess.run(["pre-commit", "run", "--all-files"])
    return result.returncode


def health_checks(config: HokoConfig) -> list[HealthCheck]:
    return [
        HealthCheck("Hooks installed", (Path(".git") / "hooks" / "pre-commit").exists()),
        HealthCheck("Configuration valid", Path(CONFIG_FILENAME).exists()),
    ]
