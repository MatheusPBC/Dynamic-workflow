from typing import Any
from uuid import uuid4

from fastmcp import FastMCP

from drw.artifacts import LocalArtifactStore
from drw.config import DRWConfig
from drw.generator import WorkflowGenerator
from drw.providers.base import LLMProvider
from drw.providers.codex import CodexProvider
from drw.providers.fake import FakeLLMProvider
from drw.runtime import WorkflowRuntime


mcp = FastMCP("DRW")


def build_provider(provider_name: str | None = None) -> LLMProvider:
    config = DRWConfig.from_env()
    selected = (provider_name or config.provider).lower()
    if selected == "fake":
        return FakeLLMProvider()
    if selected == "codex":
        return CodexProvider(timeout_seconds=config.codex_timeout_seconds)
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
    artifact_dir: str | None = None,
) -> dict[str, Any]:
    if not goal.strip():
        return {"status": "error", "error": "goal must not be empty"}

    try:
        selected_provider = build_provider(provider)
        generator = WorkflowGenerator(provider=selected_provider)
        workflow = generator.generate(goal)
        artifact_store = LocalArtifactStore(_artifact_dir(artifact_dir))
        runtime = WorkflowRuntime(
            artifact_store=artifact_store,
            handlers=_step_handlers(selected_provider, workflow),
        )
        result = runtime.run(workflow, run_id=f"run-{uuid4().hex}")
        artifact_store.write_run_result(result.run_id, result.model_dump(mode="json"))
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "run": result.model_dump(mode="json")}


@mcp.tool
def get_run(run_id: str, artifact_dir: str | None = None) -> dict[str, Any]:
    if not run_id.strip():
        return {"status": "error", "error": "run_id must not be empty"}

    try:
        run = LocalArtifactStore(_artifact_dir(artifact_dir)).read_run_result(run_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "run": run}


@mcp.tool
def list_run_artifacts(run_id: str, artifact_dir: str | None = None) -> dict[str, Any]:
    if not run_id.strip():
        return {"status": "error", "error": "run_id must not be empty"}

    try:
        artifacts = LocalArtifactStore(_artifact_dir(artifact_dir)).list_step_artifacts(run_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "artifacts": artifacts}


@mcp.tool
def read_artifact(
    run_id: str,
    step_id: str,
    artifact_dir: str | None = None,
) -> dict[str, Any]:
    if not run_id.strip():
        return {"status": "error", "error": "run_id must not be empty"}
    if not step_id.strip():
        return {"status": "error", "error": "step_id must not be empty"}

    try:
        artifact = LocalArtifactStore(_artifact_dir(artifact_dir)).read_step_artifact(run_id, step_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "ok", "artifact": artifact}


@mcp.tool
def get_runtime_status() -> dict[str, Any]:
    config = DRWConfig.from_env()
    try:
        LocalArtifactStore(config.artifact_dir)
        storage = "ok"
    except Exception:
        storage = "error"

    return {
        "status": "ok",
        "provider": config.provider,
        "artifact_dir": config.artifact_dir,
        "mcp_host": config.mcp_host,
        "mcp_port": config.mcp_port,
        "codex_timeout_seconds": config.codex_timeout_seconds,
        "storage": storage,
    }


def main() -> None:
    config = DRWConfig.from_env()
    mcp.run(transport="http", host=config.mcp_host, port=config.mcp_port)


def _artifact_dir(artifact_dir: str | None) -> str:
    return artifact_dir or DRWConfig.from_env().artifact_dir


def _step_handlers(provider: LLMProvider, workflow) -> dict:
    return {
        step.id: lambda current_workflow, current_step, results_by_step: provider.execute_step(
            current_workflow,
            current_step,
            results_by_step,
        )
        for step in workflow.steps
    }
