# DRW Milestone 6

## Goal
Add local run registry and MCP artifact inspection tools.

## Tasks
- [ ] Add run index support to `LocalArtifactStore` -> Verify a run result can be saved and loaded by `run_id`.
- [ ] Add artifact listing to `LocalArtifactStore` -> Verify step artifact names are listed for a run.
- [ ] Add MCP tools `get_run`, `list_run_artifacts`, `read_artifact` -> Verify structured success/error payloads with `tmp_path`.
- [ ] Update `run_workflow` to save the run index -> Verify a later `get_run` can read it.
- [ ] Document Milestone 6 in `README.md` -> Verify docs mention local-only registry/artifact inspection.
- [ ] Final verification -> Run `pytest -v`, `ruff check .`, and CLI smoke.

## Done When
- A local run can be inspected after execution by `run_id`.
- Artifacts can be listed and read through MCP tools.
- No external services, database, Docker, VPS, or real Codex calls are used.
