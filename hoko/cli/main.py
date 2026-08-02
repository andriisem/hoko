from __future__ import annotations

import typer

from hoko.commands import add, check, doctor, export, import_, init, rm, update
from hoko.commands import list as list_cmd

app = typer.Typer(
    name="hoko",
    help="Developer workflows in one command.",
    no_args_is_help=True,
)

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
