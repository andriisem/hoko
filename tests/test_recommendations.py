from hoko.detection.recommendations import recommended_capabilities


def test_no_signals_still_recommends_secrets():
    assert recommended_capabilities([]) == ["secrets"]


def test_language_signal_adds_formatting_before_secrets():
    assert recommended_capabilities(["python"]) == ["formatting", "secrets"]


def test_javascript_also_triggers_formatting():
    assert "formatting" in recommended_capabilities(["javascript"])


def test_matches_spec_interactive_setup_example():
    assert recommended_capabilities(["python", "docker", "github-actions"]) == [
        "formatting",
        "secrets",
        "yaml",
        "docker",
    ]


def test_docker_and_github_actions_without_a_language():
    result = recommended_capabilities(["docker", "github-actions"])
    assert "formatting" not in result
    assert result == ["secrets", "yaml", "docker"]
