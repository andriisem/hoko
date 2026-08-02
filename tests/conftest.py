import subprocess

import pytest

from hoko.adapters import precommit


@pytest.fixture
def fake_precommit(monkeypatch):
    """Pretend pre-commit is installed and record the commands hoko runs against it.

    Keeps command-level tests off the real binary, which would otherwise make
    them depend on whatever happens to be installed on the machine.
    """
    commands: list[list[str]] = []

    monkeypatch.setattr(precommit, "resolve_command", lambda: ["pre-commit"])

    def run(command, **kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(precommit.subprocess, "run", run)
    return commands
