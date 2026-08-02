from __future__ import annotations

import sys

import typer
from rich.console import Console

from hoko.commands._apply import apply_config
from hoko.config.models import HokoConfig
from hoko.detection.detector import SIGNAL_LABELS, detect_project
from hoko.detection.recommendations import recommended_capabilities

console = Console()


def run(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Install recommended capabilities without prompting."
    ),
) -> None:
    """Initialize hoko in the current repository."""
    detected = detect_project()
    if detected:
        console.print("[bold]Detected[/bold]\n")
        for signal in detected:
            console.print(f"[green]✓[/green] {SIGNAL_LABELS.get(signal, signal.title())}")
        console.print()

    config = HokoConfig.load()
    recommended = [name for name in recommended_capabilities(detected) if name not in config.capabilities]

    if recommended:
        console.print("[bold]Install recommended capabilities?[/bold]\n")
        for name in recommended:
            console.print(f"[green]✓[/green] {name.title()}")
        console.print()

        install_recommended = yes
        if not install_recommended and sys.stdin.isatty():
            install_recommended = typer.confirm("Continue?", default=True)

        if install_recommended:
            for name in recommended:
                config.add_capability(name)

    apply_config(config)

    console.print("\n[green]hoko initialized.[/green]")
