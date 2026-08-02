from __future__ import annotations

from rich.console import Console

from hoko.adapters import precommit
from hoko.config.models import HokoConfig
from hoko.detection.detector import detect_project

console = Console()


def run() -> None:
    """Initialize hoko in the current repository."""
    detected = detect_project()
    if detected:
        console.print("[bold]Detected[/bold]\n")
        for ecosystem in detected:
            console.print(f"[green]✓[/green] {ecosystem.title()}")
        console.print()

    config = HokoConfig.load()
    precommit.ensure_installed()
    precommit.write_config(config)
    precommit.install_hooks()
    config.save()

    console.print("[green]hoko initialized.[/green]")
