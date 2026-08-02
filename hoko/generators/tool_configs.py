from __future__ import annotations

import json
from pathlib import Path

from hoko.config.models import HokoConfig

COMMITLINT_CONFIG_FILENAME = ".commitlintrc.yaml"

_COMMITLINT_CONFIG = """\
# Created by hoko. Edit freely - hoko never overwrites an existing commitlint config.
extends:
  - "@commitlint/config-conventional"
"""

# Every filename commitlint's config loader looks for. If the user already has
# any of them we leave their setup alone rather than adding a second config.
_COMMITLINT_CONFIG_NAMES = (
    ".commitlintrc",
    ".commitlintrc.json",
    ".commitlintrc.yaml",
    ".commitlintrc.yml",
    ".commitlintrc.js",
    ".commitlintrc.cjs",
    ".commitlintrc.mjs",
    ".commitlintrc.ts",
    "commitlint.config.js",
    "commitlint.config.cjs",
    "commitlint.config.mjs",
    "commitlint.config.ts",
)


def _has_commitlint_config(root: Path) -> bool:
    if any((root / name).exists() for name in _COMMITLINT_CONFIG_NAMES):
        return True

    package_json = root / "package.json"
    if not package_json.exists():
        return False
    try:
        document = json.loads(package_json.read_text())
    except ValueError:
        return False
    return isinstance(document, dict) and "commitlint" in document


def ensure_tool_configs(config: HokoConfig, root: Path | None = None) -> list[str]:
    """Write companion config files that hooks need but pre-commit cannot supply.

    commitlint refuses to run without a config of its own, so a capability that
    only writes a `.pre-commit-config.yaml` entry would fail on first commit.
    Returns the filenames created; existing files are left untouched.
    """
    root = root or Path(".")
    created: list[str] = []

    if "commitlint" in config.capabilities and not _has_commitlint_config(root):
        (root / COMMITLINT_CONFIG_FILENAME).write_text(_COMMITLINT_CONFIG)
        created.append(COMMITLINT_CONFIG_FILENAME)

    return created
