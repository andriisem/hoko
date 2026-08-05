from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("hoko")
except PackageNotFoundError:
    # Running from source without hoko itself installed (e.g. a bare
    # `python -m hoko` against a checkout). pyproject.toml's `version` is the
    # single source of truth in every installed case - this is a dev-only
    # fallback for the one case where package metadata isn't available.
    __version__ = "0.0.0+unknown"
