# DRW V1 Operable Plan

## Goal
Ship the remaining V1 surface in one branch: config/hardening, private deploy artifacts, and manual Codex smoke support.

## Tasks
- [ ] Add `DRWConfig` in `src/drw/config.py` -> Verify env defaults and overrides for provider, artifact dir, host, and port.
- [ ] Make MCP tools use `DRW_ARTIFACT_DIR` by default -> Verify `run_workflow` writes to env-configured artifacts without passing `artifact_dir`.
- [ ] Add `get_runtime_status` MCP tool -> Verify provider, artifact dir, host, port, and storage status are returned.
- [ ] Harden MCP input validation -> Verify empty `run_id`/`step_id` return structured errors.
- [ ] Add private deploy artifacts under `deploy/` -> Verify expected env and systemd files exist and reference `drw-mcp`.
- [ ] Add manual Codex smoke command docs -> Verify README documents `DRW_PROVIDER=codex` smoke without automated Codex execution.
- [ ] Final verification -> Run `pytest -v`, `ruff check .`, and CLI smoke.

## Done When
- V1 can run locally and be deployed as a private Tailscale/VPS service from versioned artifacts.
- Tests stay hermetic: no real Codex, network, Docker, VPS, or systemd calls.
- Full test suite and ruff pass.
