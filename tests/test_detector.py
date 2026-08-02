from hoko.detection.detector import detect_project


def test_detects_python_via_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    assert detect_project(tmp_path) == ["python"]


def test_detects_docker_via_dockerfile(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    assert "docker" in detect_project(tmp_path)


def test_detects_github_actions_when_workflows_present(tmp_path):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n")
    assert "github-actions" in detect_project(tmp_path)


def test_empty_workflows_dir_is_not_detected(tmp_path):
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    assert "github-actions" not in detect_project(tmp_path)


def test_missing_github_dir_is_not_detected(tmp_path):
    assert "github-actions" not in detect_project(tmp_path)


def test_detects_multiple_signals_in_spec_example_order(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "Dockerfile").write_text("")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("")

    assert detect_project(tmp_path) == ["python", "docker", "github-actions"]


def test_no_markers_detects_nothing(tmp_path):
    assert detect_project(tmp_path) == []
