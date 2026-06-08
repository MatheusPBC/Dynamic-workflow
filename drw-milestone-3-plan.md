# DRW Milestone 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the existing DRW workflow generator through a minimal private MCP HTTP server.

**Architecture:** This milestone adds a thin FastMCP entrypoint over the Milestone 1/2 generator pipeline. It exposes synchronous tools for health checks and workflow generation, defaults to `FakeLLMProvider`, and keeps Codex real execution opt-in only through provider construction code, not automated tests.

**Tech Stack:** Python 3.13+, FastMCP, Pydantic v2, pytest, ruff.

---

## File Structure

Create or modify these files under `/home/matheus/.config/superpowers/worktrees/drw/milestone-3`:

```text
src/drw/
  mcp_server.py          # FastMCP app, tools, provider selection, run entrypoint
tests/
  test_mcp_server.py     # tool-level tests without starting network server
pyproject.toml           # add fastmcp dependency and script entrypoint
README.md                # document MCP milestone and local run command
```

## Constraints

- Do not add runtime workers.
- Do not add PostgreSQL.
- Do not add artifact storage.
- Do not add Docker or VPS deploy yet.
- Do not call real Codex in automated tests.
- Default MCP provider must be fake.
- Bind host defaults to `127.0.0.1`; Tailscale/VPS binding is a later deployment concern.
- Use HTTP transport. SSE is not implemented in this milestone because current FastMCP docs mark SSE as legacy/deprecated.

## Tasks

### Task 1: Add FastMCP Dependency And Server Skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `src/drw/mcp_server.py`
- Create: `tests/test_mcp_server.py`

- [ ] **Step 1: Write failing tests for health and fake workflow tool functions**

Create `tests/test_mcp_server.py`:

```python
from drw.mcp_server import generate_workflow, health


def test_health_returns_status_payload():
    assert health() == {"status": "ok", "service": "drw"}


def test_generate_workflow_returns_valid_workflow_payload_with_fake_provider():
    payload = generate_workflow("pesquise frameworks python de observabilidade")

    assert payload["name"] == "research_workflow"
    assert payload["objective"] == "pesquise frameworks python de observabilidade"
    assert payload["steps"][0]["type"] == "parallel_research"
    assert payload["steps"][-1]["type"] == "report"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_mcp_server.py -v`

Expected: FAIL because `drw.mcp_server` does not exist yet.

- [ ] **Step 3: Add FastMCP dependency and script entrypoint**

Modify `pyproject.toml` dependencies and scripts:

```toml
dependencies = [
  "fastmcp>=2.0.0",
  "pydantic>=2.10.0"
]

[project.scripts]
drw = "drw.cli:main"
drw-mcp = "drw.mcp_server:main"
```

- [ ] **Step 4: Implement MCP server skeleton and tool functions**

Create `src/drw/mcp_server.py`:

```python
import os
from typing import Any

from fastmcp import FastMCP

from drw.generator import WorkflowGenerator
from drw.providers.fake import FakeLLMProvider


mcp = FastMCP("DRW")


@mcp.tool
def health() -> dict[str, str]:
    return {"status": "ok", "service": "drw"}


@mcp.tool
def generate_workflow(goal: str) -> dict[str, Any]:
    generator = WorkflowGenerator(provider=FakeLLMProvider())
    workflow = generator.generate(goal)
    return workflow.model_dump(mode="json")


def main() -> None:
    host = os.getenv("DRW_MCP_HOST", "127.0.0.1")
    port = int(os.getenv("DRW_MCP_PORT", "8765"))
    mcp.run(transport="http", host=host, port=port)
```

- [ ] **Step 5: Run MCP server tests**

Run: `pytest tests/test_mcp_server.py -v`

Expected: PASS.

### Task 2: Provider Selection For MCP Tools

**Files:**
- Modify: `src/drw/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Add failing tests for provider selection**

Append to `tests/test_mcp_server.py`:

```python
import pytest

from drw.mcp_server import build_provider
from drw.providers.codex import CodexProvider
from drw.providers.fake import FakeLLMProvider


def test_build_provider_defaults_to_fake():
    assert isinstance(build_provider(None), FakeLLMProvider)


def test_build_provider_accepts_fake():
    assert isinstance(build_provider("fake"), FakeLLMProvider)


def test_build_provider_accepts_codex_without_running_it():
    assert isinstance(build_provider("codex"), CodexProvider)


def test_build_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported provider"):
        build_provider("hermes")
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_mcp_server.py -v`

Expected: FAIL because `build_provider` does not exist yet.

- [ ] **Step 3: Implement provider selection**

Modify `src/drw/mcp_server.py`:

```python
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
    generator = WorkflowGenerator(provider=build_provider(provider))
    workflow = generator.generate(goal)
    return workflow.model_dump(mode="json")


def main() -> None:
    host = os.getenv("DRW_MCP_HOST", "127.0.0.1")
    port = int(os.getenv("DRW_MCP_PORT", "8765"))
    mcp.run(transport="http", host=host, port=port)
```

- [ ] **Step 4: Run MCP server tests**

Run: `pytest tests/test_mcp_server.py -v`

Expected: PASS.

### Task 3: Error Shape For Tool-Level Failures

**Files:**
- Modify: `src/drw/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Add failing tests for invalid input and unsupported provider payloads**

Append to `tests/test_mcp_server.py`:

```python

def test_generate_workflow_rejects_empty_goal():
    payload = generate_workflow("")

    assert payload["status"] == "error"
    assert payload["error"] == "goal must not be empty"


def test_generate_workflow_returns_error_for_unknown_provider():
    payload = generate_workflow("pesquise frameworks python", provider="hermes")

    assert payload["status"] == "error"
    assert "Unsupported provider" in payload["error"]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_mcp_server.py -v`

Expected: FAIL because current function raises instead of returning structured error.

- [ ] **Step 3: Implement structured tool errors**

Modify `generate_workflow` in `src/drw/mcp_server.py`:

```python
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
```

Update previous success test expectations from direct workflow fields to `payload["workflow"]`.

- [ ] **Step 4: Run MCP server tests**

Run: `pytest tests/test_mcp_server.py -v`

Expected: PASS.

### Task 4: README MCP Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Milestone 3 docs**

Append to `README.md`:

```markdown
## Milestone 3

Milestone 3 exposes the workflow generator through a minimal FastMCP HTTP server.

Tools:

- `health`: returns service status.
- `generate_workflow`: returns a validated Workflow DSL for a goal.

Run locally:

```bash
drw-mcp
```

Environment variables:

- `DRW_MCP_HOST`: defaults to `127.0.0.1`.
- `DRW_MCP_PORT`: defaults to `8765`.
- `DRW_PROVIDER`: defaults to `fake`; `codex` is opt-in and requires Codex CLI auth.

This milestone does not include VPS deploy, Docker, database, artifacts, or runtime workers.
```

- [ ] **Step 2: Run MCP tests**

Run: `pytest tests/test_mcp_server.py -v`

Expected: PASS.

### Task 5: Quality Gate

**Files:**
- All created/modified files

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`

Expected: PASS.

- [ ] **Step 2: Run ruff**

Run: `ruff check .`

Expected: PASS.

- [ ] **Step 3: Run fake CLI smoke**

Run: `PYTHONPATH=src python -m drw.cli "pesquise frameworks python de observabilidade"`

Expected: valid JSON output.

## Done When

- `pytest -v` passes.
- `ruff check .` passes.
- Fake CLI smoke still prints valid workflow JSON.
- MCP tool functions are testable without starting a network server.
- `generate_workflow` defaults to fake provider.
- `codex` provider is selectable but not executed in automated tests.
- No Docker, DB, runtime workers, artifact storage or VPS deployment exists in this milestone.

## Self-Review

- Spec coverage: plan implements the minimal MCP boundary only.
- Intentional gaps: auth/token, Tailscale bind, Docker, VPS deploy, persistence, runtime and artifacts are deferred.
- Placeholder scan: no placeholders or unspecified implementation steps remain.
- Type consistency: `generate_workflow`, `health`, `build_provider`, `WorkflowGenerator`, `FakeLLMProvider`, and `CodexProvider` names are consistent across tasks.
