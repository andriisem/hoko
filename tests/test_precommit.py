from pathlib import Path

from ruamel.yaml import YAML

from hoko.adapters.precommit import render_repos, write_config
from hoko.config.models import HokoConfig

_yaml = YAML()


def test_render_repos_is_empty_for_no_capabilities():
    assert render_repos(HokoConfig()) == []


def test_render_repos_produces_valid_repo_rev_hooks_shape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["python", "secrets"])

    repos = render_repos(config)

    assert repos
    for repo in repos:
        assert set(repo) == {"repo", "rev", "hooks"}
        for hook in repo["hooks"]:
            assert "id" in hook


def test_render_repos_dedupes_shared_tools_across_capabilities(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("")
    config = HokoConfig(capabilities=["python", "formatting"])

    repos = render_repos(config)

    ruff_repos = [repo for repo in repos if repo["repo"].endswith("ruff-pre-commit")]
    assert len(ruff_repos) == 1
    hook_ids = [hook["id"] for hook in ruff_repos[0]["hooks"]]
    assert hook_ids == ["ruff", "ruff-format"]


def test_write_config_creates_file_when_none_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["secrets"])

    write_config(config)

    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    assert document["repos"][0]["repo"].endswith("detect-secrets")


def test_write_config_preserves_hand_added_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".pre-commit-config.yaml"
    config_path.write_text(
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: my-custom-check\n"
        "        name: My Custom Check\n"
        "        entry: ./scripts/check.sh\n"
        "        language: script\n"
    )

    write_config(HokoConfig(capabilities=["secrets"]))

    document = _yaml.load(config_path.read_text())
    local_repos = [repo for repo in document["repos"] if repo["repo"] == "local"]
    assert len(local_repos) == 1
    assert local_repos[0]["hooks"][0]["id"] == "my-custom-check"

    managed_repos = [repo for repo in document["repos"] if repo["repo"] != "local"]
    assert any(repo["repo"].endswith("detect-secrets") for repo in managed_repos)


def test_write_config_drops_stale_managed_repo_when_capability_removed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    write_config(HokoConfig(capabilities=["secrets", "markdown"]))
    write_config(HokoConfig(capabilities=["secrets"]))

    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    repo_urls = [repo["repo"] for repo in document["repos"]]
    assert any(url.endswith("detect-secrets") for url in repo_urls)
    assert not any(url.endswith("markdownlint-cli") for url in repo_urls)


def test_write_config_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = HokoConfig(capabilities=["python", "secrets"])

    write_config(config)
    write_config(config)

    document = _yaml.load(Path(".pre-commit-config.yaml").read_text())
    assert document["repos"] == render_repos(config)


def test_write_config_preserves_other_top_level_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".pre-commit-config.yaml"
    config_path.write_text("default_language_version:\n  python: python3.12\nrepos: []\n")

    write_config(HokoConfig(capabilities=["secrets"]))

    document = _yaml.load(config_path.read_text())
    assert document["default_language_version"]["python"] == "python3.12"
