from __future__ import annotations

import typer
from rich.console import Console

from hoko.capabilities.registry import all_capabilities
from hoko.commands._apply import apply_config
from hoko.config.models import HokoConfig
from hoko.detection.detector import SIGNAL_LABELS, detect_project
from hoko.detection.recommendations import recommended_capabilities
from hoko.ui.prompts import Option, is_interactive, multiselect

console = Console()


def _select_capabilities(config: HokoConfig, recommended: list[str]) -> list[str]:
    """Same checkbox picker `hoko add` uses, pre-checked with what's recommended.

    Shows the full catalog (not just the recommended subset) so opting into a
    capability detection didn't flag - `python`'s stricter checks, say - takes
    one pass through init instead of a follow-up `hoko add`.
    """
    available = [c for c in all_capabilities() if c.name not in config.capabilities]
    if not available:
        return []

    options = [
        Option(
            value=capability.name,
            label=capability.name,
            hint=capability.description,
            checked=capability.name in recommended,
        )
        for capability in available
    ]
    return multiselect("Which capabilities do you want to install?", options)


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
            console.print(
                f"[green]✓[/green] {SIGNAL_LABELS.get(signal, signal.title())}"
            )
        console.print()

    config = HokoConfig.load()
    recommended = [
        name
        for name in recommended_capabilities(detected)
        if name not in config.capabilities
    ]

    if is_interactive() and not yes:
        for name in _select_capabilities(config, recommended):
            config.add_capability(name)
    elif recommended:
        console.print("[bold]Install recommended capabilities?[/bold]\n")
        for name in recommended:
            console.print(f"[green]✓[/green] {name.title()}")
        console.print()

        if yes:
            for name in recommended:
                config.add_capability(name)

    apply_config(config)

    console.print("\n[green]hoko initialized.[/green]")
