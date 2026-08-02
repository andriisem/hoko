from __future__ import annotations

import json

import typer
from rich.console import Console

from hoko.adapters import precommit
from hoko.commands._apply import apply_config
from hoko.config.models import HokoConfig

console = Console()


def _report(checks: list[precommit.HealthCheck]) -> int:
    score = precommit.health_score(checks)

    console.print("[bold]Repository Health[/bold]\n")
    console.print(f"{score} / 100\n")

    for check in checks:
        icon = "[green]✓[/green]" if check.ok else "[yellow]⚠[/yellow]"
        console.print(f"{icon} {check.message}")

    return score


def _print_json(
    config: HokoConfig, checks: list[precommit.HealthCheck], fix_attempted: bool
) -> None:
    # Plain `print`, not `console.print` - guarantees valid, unstyled JSON even
    # when stdout is a real terminal that Rich would otherwise colorize.
    print(
        json.dumps(
            {
                "score": precommit.health_score(checks),
                "capabilities": config.capabilities,
                "fix_attempted": fix_attempted,
                "checks": [{"message": c.message, "ok": c.ok} for c in checks],
            },
            indent=2,
        )
    )


def run(
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Reapply the configured capabilities to repair what's found.",
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Print a machine-readable report (score, capabilities, checks) for CI or dashboards.",
    ),
) -> None:
    """Check repository health."""
    config = HokoConfig.load()
    checks = precommit.health_checks(config)

    if as_json:
        fix_attempted = False
        if fix and precommit.health_score(checks) < 100:
            apply_config(config, quiet=True)
            checks = precommit.health_checks(config)
            fix_attempted = True
        _print_json(config, checks, fix_attempted)
        return

    score = _report(checks)

    if score == 100:
        return

    if not fix:
        console.print("\n[bold]Recommendation[/bold]\n")
        console.print("hoko doctor --fix")
        return

    console.print("\n[bold]Fixing[/bold]\n")
    apply_config(config)

    console.print()
    _report(precommit.health_checks(config))
