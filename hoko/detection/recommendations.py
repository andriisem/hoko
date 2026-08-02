from __future__ import annotations

LANGUAGE_SIGNALS = {"python", "javascript", "go", "rust"}


def recommended_capabilities(detected: list[str]) -> list[str]:
    """Map detected signals to the capabilities `hoko init` should offer to install.

    Kept deliberately conservative: cross-cutting, low-risk capabilities
    (formatting, secrets, yaml, docker) are recommended automatically.
    Deeper, more opinionated capabilities (e.g. `python`'s mypy checks)
    are left for the user to opt into explicitly via `hoko add`.
    """
    recommended: list[str] = []

    def add(name: str) -> None:
        if name not in recommended:
            recommended.append(name)

    if LANGUAGE_SIGNALS & set(detected):
        add("formatting")

    add("secrets")

    if "github-actions" in detected:
        add("yaml")

    if "docker" in detected:
        add("docker")

    return recommended
