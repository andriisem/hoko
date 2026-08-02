from __future__ import annotations

import typer
from rich.console import Console

from hoko.adapters import precommit
from hoko.capabilities.registry import get_capability
from hoko.config.models import HokoConfig
from hoko.ui.prompts import Option, is_interactive, multiselect

console = Console()


def complete_installed(incomplete: str) -> list[str]:
    installed = HokoConfig.load().capabilities
    return [name for name in installed if name.startswith(incomplete)]


def _select_capabilities(config: HokoConfig) -> list[str]:
    if not config.capabilities:
        console.print("No capabilities installed. Run 'hoko add'.")
        raise typer.Exit()

    if not is_interactive():
        console.print("[red]Missing argument:[/red] CAPABILITIES...")
        console.print(f"Installed: {', '.join(config.capabilities)}")
        raise typer.Exit(code=1)

    options = []
    for name in config.capabilities:
        capability = get_capability(name)
        options.append(
            Option(
                value=name,
                label=name,
                hint=capability.description if capability else "",
            )
        )

    return multiselect("Which capabilities do you want to remove?", options)


def run(
    capabilities: list[str] = typer.Argument(
        None,
        help="One or more capabilities to remove. Omit to choose interactively.",
        autocompletion=complete_installed,
    ),
) -> None:
    """Remove one or more capabilities."""
    config = HokoConfig.load()

    if not capabilities:
        capabilities = _select_capabilities(config)
        if not capabilities:
            console.print("Nothing selected.")
            raise typer.Exit()

    for name in capabilities:
        if name not in config.capabilities:
            console.print(f"[yellow]Not installed:[/yellow] {name}")
            continue
        config.remove_capability(name)
        console.print(f"[green]✓[/green] Removed {name}")

    precommit.write_config(config)
    config.save()
