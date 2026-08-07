from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HookDef:
    repo: str
    rev: str
    hook_id: str
    args: list[str] = field(default_factory=list)
    additional_dependencies: list[str] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)

    def to_hook_entry(self) -> dict:
        entry: dict = {"id": self.hook_id}
        if self.args:
            entry["args"] = list(self.args)
        if self.additional_dependencies:
            entry["additional_dependencies"] = list(self.additional_dependencies)
        if self.stages:
            entry["stages"] = list(self.stages)
        return entry


# Default repo/rev pins shipped with hoko. `hoko update` refreshes these
# via `pre-commit autoupdate` rather than requiring a hoko release.
_HOOK_DEFS: dict[str, HookDef] = {
    "ruff": HookDef(
        repo="https://github.com/astral-sh/ruff-pre-commit",
        rev="v0.6.9",
        hook_id="ruff",
        args=["--fix"],
    ),
    "ruff-format": HookDef(
        repo="https://github.com/astral-sh/ruff-pre-commit",
        rev="v0.6.9",
        hook_id="ruff-format",
    ),
    "mypy": HookDef(
        repo="https://github.com/pre-commit/mirrors-mypy",
        rev="v1.11.2",
        hook_id="mypy",
    ),
    "prettier": HookDef(
        repo="https://github.com/pre-commit/mirrors-prettier",
        rev="v4.0.0-alpha.8",
        hook_id="prettier",
    ),
    "gofmt": HookDef(
        repo="https://github.com/dnephin/pre-commit-golang",
        rev="v0.5.1",
        hook_id="go-fmt",
    ),
    "rustfmt": HookDef(
        repo="https://github.com/doublify/pre-commit-rust",
        rev="v1.0",
        hook_id="fmt",
    ),
    "gitleaks": HookDef(
        repo="https://github.com/gitleaks/gitleaks",
        rev="v8.18.4",
        hook_id="gitleaks",
    ),
    "markdownlint": HookDef(
        repo="https://github.com/igorshubovych/markdownlint-cli",
        rev="v0.41.0",
        hook_id="markdownlint",
    ),
    "yamllint": HookDef(
        repo="https://github.com/adrienverge/yamllint",
        rev="v1.35.1",
        hook_id="yamllint",
    ),
    "hadolint": HookDef(
        repo="https://github.com/hadolint/hadolint",
        rev="v2.13.1-beta",
        hook_id="hadolint-docker",
    ),
    "commitlint": HookDef(
        repo="https://github.com/alessandrojcm/commitlint-pre-commit-hook",
        rev="v9.16.0",
        hook_id="commitlint",
        stages=["commit-msg"],
        additional_dependencies=["@commitlint/config-conventional"],
    ),
}


def get_hook_def(tool_id: str) -> HookDef | None:
    return _HOOK_DEFS.get(tool_id)


# Repo URLs hoko owns. Any repo entry in an existing .pre-commit-config.yaml
# whose `repo` is NOT in this set was added by hand and is left untouched
# when hoko merges its own managed hooks into the file.
MANAGED_REPO_URLS: frozenset[str] = frozenset(
    hook_def.repo for hook_def in _HOOK_DEFS.values()
)


def repos_for(tool_ids: list[str]) -> list[dict]:
    """Group resolved tool ids into `.pre-commit-config.yaml` repo entries.

    Hooks that share a (repo, rev) pair are combined under a single repo
    entry, matching the structure pre-commit expects.
    """
    order: list[tuple[str, str]] = []
    grouped: dict[tuple[str, str], list[HookDef]] = {}

    for tool_id in tool_ids:
        hook_def = get_hook_def(tool_id)
        if hook_def is None:
            continue
        key = (hook_def.repo, hook_def.rev)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        if hook_def.hook_id not in {existing.hook_id for existing in grouped[key]}:
            grouped[key].append(hook_def)

    return [
        {
            "repo": repo,
            "rev": rev,
            "hooks": [hook_def.to_hook_entry() for hook_def in grouped[(repo, rev)]],
        }
        for repo, rev in order
    ]
