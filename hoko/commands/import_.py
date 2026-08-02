from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from hoko.adapters import precommit
from hoko.config.models import HokoConfig

console = Console()


def run(
    preset: Path = typer.Argument(..., help="Path to a hoko preset file."),
) -> None:
    """Install every capability listed in a preset file."""
    config = HokoConfig.import_preset(preset)
    precommit.write_config(config)
    config.save()
    console.print(f"[green]Imported preset from {preset}[/green]")
