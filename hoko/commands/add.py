from __future__ import annotations

import typer
from rich.console import Console

from hoko.adapters import precommit
from hoko.capabilities.registry import get_capability, list_capabilities
from hoko.config.models import HokoConfig

console = Console()


def complete_capability(incomplete: str) -> list[str]:
    return [name for name in list_capabilities() if name.startswith(incomplete)]


def run(
    capabilities: list[str] = typer.Argument(
        ...,
        help=f"One or more capabilities to install. Available: {', '.join(list_capabilities())}.",
        autocompletion=complete_capability,
    ),
) -> None:
    """Install one or more capabilities."""
    config = HokoConfig.load()

    for name in capabilities:
        capability = get_capability(name)
        if capability is None:
            console.print(f"[red]Unknown capability:[/red] {name}")
            console.print(f"Available: {', '.join(list_capabilities())}")
            raise typer.Exit(code=1)

        config.add_capability(name)
        console.print(f"[green]✓[/green] Added {capability.name}")

    precommit.write_config(config)
    config.save()
