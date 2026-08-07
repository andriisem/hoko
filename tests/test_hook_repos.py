from hoko.generators.hook_repos import repos_for


def test_hooks_from_same_repo_and_rev_are_grouped():
    repos = repos_for(["ruff", "ruff-format", "mypy"])

    ruff_repos = [repo for repo in repos if repo["repo"].endswith("ruff-pre-commit")]
    assert len(ruff_repos) == 1

    ruff_repo = ruff_repos[0]
    hook_ids = [hook["id"] for hook in ruff_repo["hooks"]]
    assert hook_ids == ["ruff", "ruff-format"]

    mypy_repos = [repo for repo in repos if repo["repo"].endswith("mirrors-mypy")]
    assert len(mypy_repos) == 1


def test_every_repo_entry_has_repo_and_rev():
    repos = repos_for(["ruff", "gitleaks", "commitlint"])

    for repo in repos:
        assert repo["repo"]
        assert repo["rev"]
        assert repo["hooks"]


def test_duplicate_tool_ids_do_not_duplicate_hooks():
    repos = repos_for(["ruff", "ruff"])

    assert len(repos) == 1
    assert len(repos[0]["hooks"]) == 1


def test_unknown_tool_id_is_skipped():
    assert repos_for(["does-not-exist"]) == []


def test_commitlint_hook_carries_stage_and_dependency_metadata():
    repos = repos_for(["commitlint"])

    hook = repos[0]["hooks"][0]
    assert hook["stages"] == ["commit-msg"]
    assert "@commitlint/config-conventional" in hook["additional_dependencies"]
