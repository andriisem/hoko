from __future__ import annotations

import typer
from rich.console import Console

from hoko.capabilities.registry import (
    all_capabilities,
    get_capability,
    list_capabilities,
)
from hoko.commands._apply import apply_config
from hoko.config.models import HokoConfig
from hoko.ui.prompts import Option, is_interactive, multiselect

console = Console()


def complete_capability(incomplete: str) -> list[str]:
    return [name for name in list_capabilities() if name.startswith(incomplete)]


def _select_capabilities(config: HokoConfig) -> list[str]:
    available = [
        name for name in list_capabilities() if name not in config.capabilities
    ]
    if not available:
        console.print("[green]Every capability is already installed.[/green]")
        raise typer.Exit()

    if not is_interactive():
        console.print("[red]Missing argument:[/red] CAPABILITIES...")
        console.print(f"Available: {', '.join(available)}")
        raise typer.Exit(code=1)

    options = [
        Option(
            value=capability.name,
            label=capability.name,
            hint=capability.description,
            disabled="installed" if capability.name in config.capabilities else "",
        )
        for capability in all_capabilities()
    ]

    return multiselect("Which capabilities do you want to install?", options)


def run(
    capabilities: list[str] = typer.Argument(
        None,
        help=(
            "One or more capabilities to install. Omit to choose interactively. "
            f"Available: {', '.join(list_capabilities())}."
        ),
        autocompletion=complete_capability,
    ),
) -> None:
    """Install one or more capabilities."""
    config = HokoConfig.load()

    if not capabilities:
        capabilities = _select_capabilities(config)
        if not capabilities:
            console.print("Nothing selected.")
            raise typer.Exit()

    for name in capabilities:
        capability = get_capability(name)
        if capability is None:
            console.print(f"[red]Unknown capability:[/red] {name}")
            console.print(f"Available: {', '.join(list_capabilities())}")
            raise typer.Exit(code=1)

        config.add_capability(name)
        console.print(f"[green]✓[/green] Added {capability.name}")

    apply_config(config)
