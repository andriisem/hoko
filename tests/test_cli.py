from typer.testing import CliRunner

from hoko.cli.main import app

runner = CliRunner()


def test_list_with_no_capabilities(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No capabilities installed" in result.output


def test_add_unknown_capability(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["add", "does-not-exist"])
    assert result.exit_code == 1


def test_add_and_list_known_capability(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    add_result = runner.invoke(app, ["add", "python"])
    assert add_result.exit_code == 0

    list_result = runner.invoke(app, ["list"])
    assert "Python" in list_result.output
