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

## Milestone 4

Milestone 4 adds a local-only runtime skeleton and filesystem artifact store.

Runtime behavior:

- Executes validated workflow steps in dependency order.
- Writes each successful step output as JSON under the artifact directory.
- Marks downstream steps as `skipped` when a dependency fails or is skipped.
- Uses deterministic fake handlers only; no real Codex, Docker, VPS, database, queues, or remote storage.

Run and persist local artifacts:

```bash
drw --run --artifact-dir .drw-artifacts "pesquise frameworks python de observabilidade"
```

## Milestone 5

Milestone 5 connects the local runtime to the MCP server.

New MCP tool:

- `run_workflow`: generates a workflow for a goal, runs it locally, and returns the run result.

The tool accepts an `artifact_dir` parameter and writes successful step outputs as local JSON files.
It defaults to the fake provider and does not call real Codex, Docker, VPS, database, queues, or remote storage.

## Milestone 6

Milestone 6 adds a local run registry and MCP artifact inspection tools.

New MCP tools:

- `get_run`: reads the stored run result by `run_id`.
- `list_run_artifacts`: lists step artifact IDs for a run.
- `read_artifact`: reads one step artifact by `run_id` and `step_id`.

Run metadata is stored as `run.json` in the local artifact directory. This remains filesystem-only and does not use a database, Docker, VPS, remote storage, or real Codex calls by default.
