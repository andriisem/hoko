from __future__ import annotations

from rich.console import Console

from hoko.adapters import precommit
from hoko.config.models import HokoConfig

console = Console()


def run() -> None:
    """Check repository health."""
    config = HokoConfig.load()
    checks = precommit.health_checks(config)

    passed = sum(1 for check in checks if check.ok)
    score = int(100 * passed / len(checks)) if checks else 100

    console.print("[bold]Repository Health[/bold]\n")
    console.print(f"{score} / 100\n")

    for check in checks:
        icon = "[green]✓[/green]" if check.ok else "[yellow]⚠[/yellow]"
        console.print(f"{icon} {check.message}")

    if score < 100:
        console.print("\n[bold]Recommendation[/bold]\n")
        console.print("hoko update")
