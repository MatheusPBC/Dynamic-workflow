import os
from typing import Any
from uuid import uuid4

from fastmcp import FastMCP

from drw.artifacts import LocalArtifactStore
from drw.generator import WorkflowGenerator
from drw.providers.base import LLMProvider
from drw.providers.codex import CodexProvider
from drw.providers.fake import FakeLLMProvider
from drw.runtime import WorkflowRuntime


mcp = FastMCP("DRW")


def build_provider(provider_name: str | None = None) -> LLMProvider:
    selected = (provider_name or os.getenv("DRW_PROVIDER", "fake")).lower()
    if selected == "fake":
        return FakeLLMProvider()
    if selected == "codex":
        return CodexProvider()
    raise ValueError(f"Unsupported provider: {selected}")


@mcp.tool
def health() -> dict[str, str]:
    return {"status": "ok", "service": "drw"}


@mcp.tool
def generate_workflow(goal: str, provider: str | None = None) -> dict[str, Any]:
    if not goal.strip():
        return {"status": "error", "error": "goal must not be empty"}

    try:
        generator = WorkflowGenerator(provider=build_provider(provider))
        workflow = generator.generate(goal)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "workflow": workflow.model_dump(mode="json")}


@mcp.tool
def run_workflow(
    goal: str,
    provider: str | None = None,
    artifact_dir: str = ".drw-artifacts",
) -> dict[str, Any]:
    if not goal.strip():
        return {"status": "error", "error": "goal must not be empty"}

    try:
        generator = WorkflowGenerator(provider=build_provider(provider))
        workflow = generator.generate(goal)
        artifact_store = LocalArtifactStore(artifact_dir)
        runtime = WorkflowRuntime(artifact_store=artifact_store)
        result = runtime.run(workflow, run_id=f"run-{uuid4().hex}")
        artifact_store.write_run_result(result.run_id, result.model_dump(mode="json"))
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "run": result.model_dump(mode="json")}


@mcp.tool
def get_run(run_id: str, artifact_dir: str = ".drw-artifacts") -> dict[str, Any]:
    try:
        run = LocalArtifactStore(artifact_dir).read_run_result(run_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "run": run}


@mcp.tool
def list_run_artifacts(run_id: str, artifact_dir: str = ".drw-artifacts") -> dict[str, Any]:
    try:
        artifacts = LocalArtifactStore(artifact_dir).list_step_artifacts(run_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "artifacts": artifacts}


@mcp.tool
def read_artifact(
    run_id: str,
    step_id: str,
    artifact_dir: str = ".drw-artifacts",
) -> dict[str, Any]:
    try:
        artifact = LocalArtifactStore(artifact_dir).read_step_artifact(run_id, step_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "artifact": artifact}


def main() -> None:
    host = os.getenv("DRW_MCP_HOST", "127.0.0.1")
    port = int(os.getenv("DRW_MCP_PORT", "8765"))
    mcp.run(transport="http", host=host, port=port)
