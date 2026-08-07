from __future__ import annotations

from dataclasses import dataclass, field

ANY_ECOSYSTEM = "*"


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    tools_by_ecosystem: dict[str, list[str]] = field(default_factory=dict)


_CAPABILITIES: dict[str, Capability] = {
    "python": Capability(
        name="python",
        description="Python linting and type checking.",
        tools_by_ecosystem={"python": ["ruff", "mypy"]},
    ),
    "formatting": Capability(
        name="formatting",
        description="Code formatting for the detected language.",
        tools_by_ecosystem={
            "python": ["ruff-format"],
            "javascript": ["prettier"],
            "go": ["gofmt"],
            "rust": ["rustfmt"],
        },
    ),
    "secrets": Capability(
        name="secrets",
        description="Secret scanning.",
        # Exactly one tool per ecosystem key, always - a capability resolves to
        # the one tool that implements it, never a bundle. (`detect-secrets`
        # used to sit alongside `gitleaks` here, which silently installed both
        # scanners on every commit; see CHANGELOG.) gitleaks wins: it's a
        # static binary with no pre-commit venv to build, and it's usable
        # without a baseline file - detect-secrets needs one maintained to
        # avoid re-flagging everything already in the repo, which cuts
        # against "no setup guides".
        tools_by_ecosystem={ANY_ECOSYSTEM: ["gitleaks"]},
    ),
    "markdown": Capability(
        name="markdown",
        description="Markdown linting.",
        tools_by_ecosystem={ANY_ECOSYSTEM: ["markdownlint"]},
    ),
    "yaml": Capability(
        name="yaml",
        description="YAML linting.",
        tools_by_ecosystem={ANY_ECOSYSTEM: ["yamllint"]},
    ),
    "docker": Capability(
        name="docker",
        description="Dockerfile linting.",
        tools_by_ecosystem={ANY_ECOSYSTEM: ["hadolint"]},
    ),
    "commitlint": Capability(
        name="commitlint",
        description="Conventional commit message linting.",
        tools_by_ecosystem={ANY_ECOSYSTEM: ["commitlint"]},
    ),
}


def get_capability(name: str) -> Capability | None:
    return _CAPABILITIES.get(name)


def list_capabilities() -> list[str]:
    return sorted(_CAPABILITIES)


def all_capabilities() -> list[Capability]:
    return [_CAPABILITIES[name] for name in sorted(_CAPABILITIES)]
