# DRW Milestone 5

## Goal
Expose the local workflow runtime through the MCP server with a `run_workflow` tool.

## Tasks
- [ ] Add `run_workflow` tool in `src/drw/mcp_server.py` -> Verify it returns `{status: ok, run: ...}` with fake provider and local artifacts.
- [ ] Add artifact directory parameter to `run_workflow` -> Verify artifacts are written under a `tmp_path` in tests.
- [ ] Add structured error handling for empty goal and unknown provider -> Verify `{status: error, error: ...}`.
- [ ] Document Milestone 5 in `README.md` -> Verify docs mention MCP `run_workflow` and local-only runtime.
- [ ] Final verification -> Run `pytest -v`, `ruff check .`, and CLI smoke remains green.

## Done When
- MCP can generate and run a workflow locally without network/Codex calls by default.
- Tests do not start an HTTP server and do not call real Codex.
- Full test suite and ruff pass.
