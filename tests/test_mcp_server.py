import pytest

from drw.mcp_server import build_provider, generate_workflow, health
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
