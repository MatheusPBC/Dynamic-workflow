import os
from typing import Any

from fastmcp import FastMCP

from drw.generator import WorkflowGenerator
from drw.providers.base import LLMProvider
from drw.providers.codex import CodexProvider
from drw.providers.fake import FakeLLMProvider


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


def main() -> None:
    host = os.getenv("DRW_MCP_HOST", "127.0.0.1")
    port = int(os.getenv("DRW_MCP_PORT", "8765"))
    mcp.run(transport="http", host=host, port=port)
