from __future__ import annotations

import typer
from rich.console import Console

from hoko.adapters import precommit
from hoko.config.models import HokoConfig

console = Console()


def run() -> None:
    """Update all managed hook versions."""
    if not precommit.is_installed():
        console.print("[yellow]pre-commit is not available. Run [bold]hoko init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    config = HokoConfig.load()
    precommit.update_hooks(config)
    console.print("[green]All hooks updated.[/green]")
