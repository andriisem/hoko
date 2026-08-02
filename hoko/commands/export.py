from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from hoko.config.models import HokoConfig

console = Console()


def run(
    output: Path = typer.Argument(Path("hoko.yaml"), help="Path to write the preset to."),
) -> None:
    """Export installed capabilities as a preset."""
    config = HokoConfig.load()
    config.export_preset(output)
    console.print(f"[green]Exported preset to {output}[/green]")
