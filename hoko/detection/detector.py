from __future__ import annotations

from pathlib import Path

_FILE_MARKERS: dict[str, str] = {
    "pyproject.toml": "python",
    "setup.py": "python",
    "package.json": "javascript",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "Dockerfile": "docker",
}

_DIR_MARKERS: dict[str, str] = {
    ".github/workflows": "github-actions",
}

SIGNAL_LABELS: dict[str, str] = {
    "python": "Python",
    "javascript": "JavaScript",
    "go": "Go",
    "rust": "Rust",
    "docker": "Docker",
    "github-actions": "GitHub Actions",
}


def detect_project(root: Path | None = None) -> list[str]:
    """Detect language ecosystems and tooling signals present in a repository.

    Returns a flat list mixing language markers (python, javascript, go,
    rust) with tooling signals (docker, github-actions) — capability
    resolution only looks up the ecosystem keys it knows about, so the
    extra signals pass through harmlessly there and exist for detection
    reporting and capability recommendations.
    """
    root = root or Path.cwd()
    detected: list[str] = []

    for marker, signal in _FILE_MARKERS.items():
        if (root / marker).exists() and signal not in detected:
            detected.append(signal)

    for marker, signal in _DIR_MARKERS.items():
        path = root / marker
        if path.is_dir() and any(path.iterdir()) and signal not in detected:
            detected.append(signal)

    return detected
