from __future__ import annotations

from pathlib import Path

_MARKERS: dict[str, str] = {
    "pyproject.toml": "python",
    "setup.py": "python",
    "package.json": "javascript",
    "go.mod": "go",
    "Cargo.toml": "rust",
}


def detect_project(root: Path | None = None) -> list[str]:
    root = root or Path.cwd()
    detected: list[str] = []
    for marker, ecosystem in _MARKERS.items():
        if (root / marker).exists() and ecosystem not in detected:
            detected.append(ecosystem)
    return detected
