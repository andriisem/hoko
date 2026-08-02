from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML

from hoko.capabilities.registry import get_capability
from hoko.config.models import HokoConfig
from hoko.detection.detector import detect_project
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
    repos: list[dict] = []
    for name in config.capabilities:
        capability = get_capability(name)
        if capability is None:
            continue
        hook_ids = hook_ids_for(capability, ecosystems)
        if hook_ids:
            repos.append({"hooks": [{"id": hook_id} for hook_id in hook_ids]})
    return repos


def write_config(config: HokoConfig, path: Path | None = None) -> None:
    path = path or Path(CONFIG_FILENAME)
    document = {"repos": render_repos(config)}
    with path.open("w") as handle:
        _yaml.dump(document, handle)


def install_hooks() -> None:
    if is_installed():
        subprocess.run(["pre-commit", "install"], check=True)


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
