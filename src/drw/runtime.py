from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from drw.artifacts import LocalArtifactStore
from drw.models.workflow import Step, Workflow


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    status: StepStatus
    artifact_path: str | None = None
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class WorkflowRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow_name: str
    status: StepStatus
    steps: list[StepResult]


StepHandler = Callable[[Workflow, Step, dict[str, StepResult]], dict[str, Any]]


class WorkflowRuntime:
    def __init__(
        self,
        artifact_store: LocalArtifactStore,
        handlers: dict[str, StepHandler] | None = None,
    ) -> None:
        self._artifact_store = artifact_store
        self._handlers = handlers or {}

    def run(self, workflow: Workflow, run_id: str) -> WorkflowRunResult:
        results_by_step: dict[str, StepResult] = {}
        ordered_results: list[StepResult] = []

        for step in workflow.steps:
            result = self._run_step(workflow, step, run_id, results_by_step)
            results_by_step[step.id] = result
            ordered_results.append(result)

        status = self._workflow_status(ordered_results)
        return WorkflowRunResult(
            run_id=run_id,
            workflow_name=workflow.name,
            status=status,
            steps=ordered_results,
        )

    def _run_step(
        self,
        workflow: Workflow,
        step: Step,
        run_id: str,
        results_by_step: dict[str, StepResult],
    ) -> StepResult:
        if self._has_failed_dependency(step, results_by_step):
            return StepResult(
                step_id=step.id,
                status=StepStatus.SKIPPED,
                error="dependency failed or skipped",
            )

        try:
            output = self._execute_step(workflow, step, results_by_step)
        except Exception as exc:
            return StepResult(step_id=step.id, status=StepStatus.FAILED, error=str(exc))

        artifact_path = self._artifact_store.write_step_artifact(run_id, step.id, output)
        return StepResult(
            step_id=step.id,
            status=StepStatus.SUCCESS,
            artifact_path=self._relative_artifact_path(artifact_path),
            output=output,
        )

    def _execute_step(
        self,
        workflow: Workflow,
        step: Step,
        results_by_step: dict[str, StepResult],
    ) -> dict[str, Any]:
        handler = self._handlers.get(step.id) or self._default_handler
        return handler(workflow, step, results_by_step)

    def _default_handler(
        self,
        workflow: Workflow,
        step: Step,
        results_by_step: dict[str, StepResult],
    ) -> dict[str, Any]:
        return {
            "workflow": workflow.name,
            "objective": workflow.objective,
            "step_id": step.id,
            "step_type": step.type,
            "dependencies": step.depends_on,
            "dependency_statuses": {
                dependency: results_by_step[dependency].status
                for dependency in step.depends_on
            },
        }

    def _has_failed_dependency(
        self,
        step: Step,
        results_by_step: dict[str, StepResult],
    ) -> bool:
        failed_statuses = {StepStatus.FAILED, StepStatus.SKIPPED}
        return any(results_by_step[dependency].status in failed_statuses for dependency in step.depends_on)

    def _workflow_status(self, results: list[StepResult]) -> StepStatus:
        if any(result.status == StepStatus.FAILED for result in results):
            return StepStatus.FAILED
        return StepStatus.SUCCESS

    def _relative_artifact_path(self, path: Path) -> str:
        return str(path)
