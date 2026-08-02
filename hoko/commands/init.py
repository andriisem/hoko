from __future__ import annotations

import sys

import typer
from rich.console import Console

from hoko.adapters import precommit
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

    precommit_available = precommit.ensure_installed()

    precommit.write_config(config)
    config.save()

    if not precommit_available:
        console.print(
            "\n[yellow]⚠ pre-commit is missing and hoko could not install it automatically.[/yellow]"
        )
        console.print(
            "  Install it with [bold]pipx install pre-commit[/bold] "
            "(or [bold]uv tool install pre-commit[/bold]), then run [bold]hoko init[/bold] again."
        )
    elif not precommit.install_hooks():
        console.print("[yellow]⚠ Could not install git hooks (are you in a git repository?)[/yellow]")

    console.print("\n[green]hoko initialized.[/green]")
