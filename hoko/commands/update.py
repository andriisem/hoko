from __future__ import annotations

from rich.console import Console

from hoko.adapters import precommit
from hoko.config.models import HokoConfig

console = Console()


def run() -> None:
    """Update all managed hook versions."""
    config = HokoConfig.load()
    precommit.update_hooks(config)
    console.print("[green]All hooks updated.[/green]")
