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
        tools_by_ecosystem={ANY_ECOSYSTEM: ["detect-secrets", "gitleaks"]},
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
