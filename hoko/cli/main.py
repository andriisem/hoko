from __future__ import annotations

import typer
from rich.console import Console

from hoko import __version__
from hoko.commands import add, check, doctor, export, import_, init, rm, update
from hoko.commands import list as list_cmd

console = Console()

app = typer.Typer(
    name="hoko",
    help="Developer workflows in one command.",
    no_args_is_help=True,
)


def _version_callback(show_version: bool) -> None:
    if show_version:
        console.print(f"hoko {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show hoko's version and exit.",
    ),
) -> None:
    pass


app.command("init")(init.run)
app.command("add")(add.run)
app.command("rm")(rm.run)
app.command("list")(list_cmd.run)
app.command("doctor")(doctor.run)
app.command("update")(update.run)
app.command("check")(check.run)
app.command("export")(export.run)
app.command("import")(import_.run)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
