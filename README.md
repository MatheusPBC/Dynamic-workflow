# Dynamic Research Workflows

Private workflow generator and runtime for agent-driven research.

## Milestone 1

This milestone validates the core workflow-generation contract:

- classify a user goal;
- select a workflow template;
- generate a constrained Workflow DSL;
- apply WorkflowPolicy limits;
- validate the final workflow.

No MCP, Codex CLI, Docker, database, or deployment is included in this milestone.

## Milestone 2

Milestone 2 adds a real CLI-backed provider boundary:

- `SubprocessCommandRunner` captures stdout, stderr, return code, and timeouts.
- `CodexProvider` adapts workflow templates from Codex CLI JSON output.
- Automated tests use fake runners and do not call Codex, OAuth, network, Docker, or VPS.

Manual smoke with real Codex is intentionally separate from the test suite.

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
