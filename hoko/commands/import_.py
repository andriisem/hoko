from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from hoko.commands._apply import apply_config
from hoko.config.models import HokoConfig

console = Console()


def run(
    preset: Path = typer.Argument(
        ...,
        help="Path to a hoko preset file.",
        exists=True,
        dir_okay=False,
    ),
) -> None:
    """Install every capability listed in a preset file."""
    config = HokoConfig.import_preset(preset)
    apply_config(config)
    console.print(f"[green]Imported preset from {preset}[/green]")
