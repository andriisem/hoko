from __future__ import annotations

from rich.console import Console

from hoko.adapters import precommit
from hoko.config.models import HokoConfig
from hoko.generators.tool_configs import ensure_tool_configs

console = Console()


def apply_config(config: HokoConfig) -> None:
    """Make the repository match `config`: write the files it implies, install its hooks.

    Shared by init, add and import so a single hoko command is always enough to
    reach a working setup - including capabilities like commitlint that need a
    tool config of their own and a non-default git hook type.
    """
    precommit_available = precommit.ensure_installed()

    precommit.write_config(config)
    for filename in ensure_tool_configs(config):
        console.print(f"[green]✓[/green] Created {filename}")
    config.save()

    if not precommit_available:
        console.print(
            "\n[yellow]⚠ pre-commit is missing and hoko could not install it automatically.[/yellow]"
        )
        console.print(
            "  Install it with [bold]pipx install pre-commit[/bold] "
            "(or [bold]uv tool install pre-commit[/bold]), then run this command again."
        )
    elif not precommit.install_hooks(config):
        console.print(
            "\n[yellow]⚠ Could not install git hooks (are you in a git repository?)[/yellow]"
        )
