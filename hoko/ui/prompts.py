from __future__ import annotations

import sys
from dataclasses import dataclass

import questionary
import typer
from questionary import Choice, Style

_STYLE = Style(
    [
        ("qmark", "fg:green bold"),
        ("question", "bold"),
        ("pointer", "fg:green bold"),
        ("highlighted", "fg:green bold"),
        ("selected", "fg:green"),
        ("disabled", "fg:#808080 italic"),
        ("answer", "fg:green bold"),
        ("hint", "fg:#808080"),
    ]
)


@dataclass(frozen=True)
class Option:
    value: str
    label: str
    hint: str = ""
    disabled: str = ""


def is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _title(option: Option, label_width: int) -> list[tuple[str, str]]:
    tokens = [("", option.label.ljust(label_width))]
    if option.hint:
        tokens.append(("class:hint", f"  {option.hint}"))
    return tokens


def multiselect(message: str, options: list[Option]) -> list[str]:
    """Ask the user to pick zero or more options. Returns the chosen values."""
    label_width = max(len(option.label) for option in options)
    choices = [
        Choice(
            title=_title(option, label_width),
            value=option.value,
            disabled=option.disabled or None,
        )
        for option in options
    ]

    selected = questionary.checkbox(
        message,
        choices=choices,
        style=_STYLE,
        instruction="(space to select, enter to confirm)",
    ).ask()

    if selected is None:
        raise typer.Exit(code=1)

    return selected
