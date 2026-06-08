import pytest

from drw.mcp_server import (
    build_provider,
    generate_workflow,
    get_run,
    health,
    list_run_artifacts,
    read_artifact,
    run_workflow,
)
from drw.providers.codex import CodexProvider
from drw.providers.fake import FakeLLMProvider


def test_health_returns_status_payload():
    assert health() == {"status": "ok", "service": "drw"}


def test_generate_workflow_returns_valid_workflow_payload_with_fake_provider():
    payload = generate_workflow("pesquise frameworks python de observabilidade")
    workflow = payload["workflow"]

    assert payload["status"] == "ok"
    assert workflow["name"] == "research_workflow"
    assert workflow["objective"] == "pesquise frameworks python de observabilidade"
    assert workflow["steps"][0]["type"] == "parallel_research"
    assert workflow["steps"][-1]["type"] == "report"


def test_build_provider_defaults_to_fake():
    assert isinstance(build_provider(None), FakeLLMProvider)


def test_build_provider_accepts_fake():
    assert isinstance(build_provider("fake"), FakeLLMProvider)


def test_build_provider_accepts_codex_without_running_it():
    assert isinstance(build_provider("codex"), CodexProvider)


def test_build_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported provider"):
        build_provider("hermes")


def test_generate_workflow_rejects_empty_goal():
    payload = generate_workflow("")

    assert payload["status"] == "error"
    assert payload["error"] == "goal must not be empty"


def test_generate_workflow_returns_error_for_unknown_provider():
    payload = generate_workflow("pesquise frameworks python", provider="hermes")

    assert payload["status"] == "error"
    assert "Unsupported provider" in payload["error"]


def test_run_workflow_generates_and_runs_local_workflow(tmp_path):
    payload = run_workflow(
        "pesquise frameworks python de observabilidade",
        artifact_dir=str(tmp_path),
    )
    run = payload["run"]

    assert payload["status"] == "ok"
    assert run["status"] == "success"
    assert run["workflow_name"] == "research_workflow"
    assert run["steps"][0]["status"] == "success"
    assert (tmp_path / run["run_id"] / "research.json").exists()


def test_run_workflow_saves_run_for_later_mcp_lookup(tmp_path):
    payload = run_workflow(
        "pesquise frameworks python de observabilidade",
        artifact_dir=str(tmp_path),
    )
    run_id = payload["run"]["run_id"]

    lookup = get_run(run_id, artifact_dir=str(tmp_path))

    assert lookup["status"] == "ok"
    assert lookup["run"]["run_id"] == run_id
    assert lookup["run"]["workflow_name"] == "research_workflow"


def test_mcp_lists_and_reads_run_artifacts(tmp_path):
    payload = run_workflow(
        "pesquise frameworks python de observabilidade",
        artifact_dir=str(tmp_path),
    )
    run_id = payload["run"]["run_id"]

    artifacts = list_run_artifacts(run_id, artifact_dir=str(tmp_path))
    artifact = read_artifact(run_id, "research", artifact_dir=str(tmp_path))

    assert artifacts == {"status": "ok", "artifacts": [
        "aggregate",
        "critic_research",
        "refine_research",
        "report",
        "research",
        "verify_research",
    ]}
    assert artifact["status"] == "ok"
    assert artifact["artifact"]["step_id"] == "research"


def test_get_run_returns_error_when_run_is_missing(tmp_path):
    payload = get_run("missing-run", artifact_dir=str(tmp_path))

    assert payload["status"] == "error"
    assert "not found" in payload["error"]


def test_run_workflow_rejects_empty_goal(tmp_path):
    payload = run_workflow("", artifact_dir=str(tmp_path))

    assert payload["status"] == "error"
    assert payload["error"] == "goal must not be empty"


def test_run_workflow_returns_error_for_unknown_provider(tmp_path):
    payload = run_workflow(
        "pesquise frameworks python",
        provider="hermes",
        artifact_dir=str(tmp_path),
    )

    assert payload["status"] == "error"
    assert "Unsupported provider" in payload["error"]
