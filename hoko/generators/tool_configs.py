from __future__ import annotations

import json
from pathlib import Path

from hoko.config.models import HokoConfig

COMMITLINT_CONFIG_FILENAME = ".commitlintrc.yaml"

# Kept within yamllint's default 80-column limit and given an explicit document
# start, so a repo using both the commitlint and yaml capabilities lints clean.
_COMMITLINT_CONFIG = """\
---
# Created by hoko. Safe to edit - hoko never overwrites an existing config.
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


def missing_commitlint_config(config: HokoConfig, root: Path | None = None) -> bool:
    """True if the commitlint capability is installed but has no config of its own.

    Shared by `ensure_tool_configs` (which writes the missing file) and
    `doctor` (which just reports the gap) so the two never disagree about
    what "has a commitlint config" means.
    """
    root = root or Path(".")
    return "commitlint" in config.capabilities and not _has_commitlint_config(root)


def ensure_tool_configs(config: HokoConfig, root: Path | None = None) -> list[str]:
    """Write companion config files that hooks need but pre-commit cannot supply.

    commitlint refuses to run without a config of its own, so a capability that
    only writes a `.pre-commit-config.yaml` entry would fail on first commit.
    Returns the filenames created; existing files are left untouched.
    """
    root = root or Path(".")
    created: list[str] = []

    if missing_commitlint_config(config, root):
        (root / COMMITLINT_CONFIG_FILENAME).write_text(_COMMITLINT_CONFIG)
        created.append(COMMITLINT_CONFIG_FILENAME)

    return created
