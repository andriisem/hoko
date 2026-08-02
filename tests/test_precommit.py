from hoko.adapters.precommit import render_repos
from hoko.config.models import HokoConfig


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
