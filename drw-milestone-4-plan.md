# DRW Milestone 4

## Goal
Add a local workflow runtime skeleton that executes validated workflows step-by-step and writes step artifacts to the local filesystem.

## Constraints
- No real Codex execution.
- No Docker, VPS, database, queues, or remote storage.
- Runtime handlers are deterministic fakes for now.
- Artifact output must be JSON and filesystem-only.
- Tests must be hermetic with `tmp_path`.

## Tasks
- [ ] Add runtime models in `src/drw/runtime.py`: `StepStatus`, `StepResult`, `WorkflowRunResult` -> Verify with unit tests for success/failure fields.
- [ ] Add `LocalArtifactStore` in `src/drw/artifacts.py` -> Verify JSON artifact writes/reads under `tmp_path`.
- [ ] Add `WorkflowRuntime` in `src/drw/runtime.py` to execute steps in dependency order -> Verify a generated research workflow completes all steps.
- [ ] Add failure handling: failed dependency skips downstream steps -> Verify dependent steps become `skipped`.
- [ ] Wire optional CLI flag `--run` in `src/drw/cli.py` to generate and run locally -> Verify smoke command prints run result JSON.
- [ ] Document Milestone 4 in `README.md` -> Verify docs mention local-only runtime and artifact directory.
- [ ] Final verification -> Run `pytest -v`, `ruff check .`, and `PYTHONPATH=src python -m drw.cli --run "pesquise frameworks python de observabilidade"`.

## Done When
- Runtime executes workflow steps deterministically without external calls.
- Artifacts are persisted as local JSON files.
- Failure/skipped behavior is covered by tests.
- Full test suite and ruff pass.
