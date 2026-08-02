from __future__ import annotations

from rich.console import Console

from hoko.config.models import HokoConfig

console = Console()


def run() -> None:
    """List installed capabilities."""
    config = HokoConfig.load()

    console.print("[bold]Installed[/bold]\n")
    if not config.capabilities:
        console.print("No capabilities installed. Run 'hoko add <capability>'.")
        return

    for name in config.capabilities:
        console.print(f"[green]✓[/green] {name.title()}")
