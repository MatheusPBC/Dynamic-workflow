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
