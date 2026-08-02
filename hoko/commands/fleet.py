from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from hoko.adapters import precommit
from hoko.commands._apply import apply_config
from hoko.config.models import HokoConfig

console = Console()


@contextlib.contextmanager
def _in_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _check_repo(path: Path, fix: bool) -> dict:
    """Run the same health check (and optional fix) `doctor` runs, scoped to `path`.

    hoko's config loading and health checks are all cwd-relative by design (a
    single repo is always "the current directory"), so fleet reuses them as-is
    by hopping into each repo in turn rather than threading a root path through
    every layer of the precommit adapter.
    """
    if not path.is_dir():
        return {"path": str(path), "error": "path does not exist"}
    if not (path / ".git").is_dir():
        return {"path": str(path), "error": "not a git repository"}

    with _in_directory(path):
        config = HokoConfig.load()
        checks = precommit.health_checks(config)
        fix_attempted = False

        if fix and precommit.health_score(checks) < 100:
            apply_config(config, quiet=True)
            checks = precommit.health_checks(config)
            fix_attempted = True

    return {
        "path": str(path),
        "score": precommit.health_score(checks),
        "capabilities": config.capabilities,
        "fix_attempted": fix_attempted,
        "checks": [{"message": c.message, "ok": c.ok} for c in checks],
    }


def _print_json(results: list[dict]) -> None:
    healthy = sum(1 for result in results if result.get("score") == 100)
    errors = sum(1 for result in results if "error" in result)
    print(
        json.dumps(
            {
                "repos": results,
                "summary": {
                    "count": len(results),
                    "healthy": healthy,
                    "errors": errors,
                },
            },
            indent=2,
        )
    )


def _print_table(results: list[dict]) -> None:
    table = Table(title="Fleet Health")
    table.add_column("Repo")
    table.add_column("Score", justify="right")
    table.add_column("Status")

    for result in results:
        if "error" in result:
            table.add_row(result["path"], "-", f"[red]{result['error']}[/red]")
            continue
        score = result["score"]
        status = (
            "[green]✓ healthy[/green]"
            if score == 100
            else "[yellow]⚠ needs attention[/yellow]"
        )
        table.add_row(result["path"], f"{score} / 100", status)

    console.print(table)

    healthy = sum(1 for result in results if result.get("score") == 100)
    console.print(f"\n{healthy} / {len(results)} repositories healthy.")


def run(
    repos: list[Path] = typer.Argument(..., help="Repository directories to check."),
    fix: bool = typer.Option(
        False, "--fix", help="Repair each repo that isn't fully healthy."
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Print a machine-readable rollup instead of a table, for CI or dashboards.",
    ),
) -> None:
    """Check (and optionally fix) repository health across many repos at once."""
    results = [_check_repo(path, fix) for path in repos]

    if as_json:
        _print_json(results)
        return

    _print_table(results)
