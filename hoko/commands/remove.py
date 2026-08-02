from __future__ import annotations

import typer
from rich.console import Console

from hoko.adapters import precommit
from hoko.config.models import HokoConfig

console = Console()


def run(
    capabilities: list[str] = typer.Argument(..., help="One or more capabilities to remove."),
) -> None:
    """Remove a capability."""
    config = HokoConfig.load()

    for name in capabilities:
        if name not in config.capabilities:
            console.print(f"[yellow]Not installed:[/yellow] {name}")
            continue
        config.remove_capability(name)
        console.print(f"[green]✓[/green] Removed {name}")

    precommit.write_config(config)
    config.save()
