from __future__ import annotations

import typer
from rich.console import Console

from hoko.adapters import precommit

console = Console()


def run() -> None:
    """Run all configured hooks without creating a commit."""
    if not precommit.is_installed():
        console.print("[yellow]pre-commit is not available. Run [bold]hoko init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    exit_code = precommit.run_all_hooks()
    if exit_code != 0:
        raise typer.Exit(code=exit_code)
    console.print("[green]All checks passed.[/green]")
