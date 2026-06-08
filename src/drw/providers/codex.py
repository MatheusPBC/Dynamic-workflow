import json
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError

from drw.command import SubprocessCommandRunner
from drw.models.workflow import Step, Workflow
from drw.runtime import StepResult


class CodexProviderError(RuntimeError):
    pass


class CodexProvider:
    def __init__(
        self,
        runner: SubprocessCommandRunner | None = None,
        command: tuple[str, ...] = ("codex", "exec", "--skip-git-repo-check"),
        timeout_seconds: int = 60,
    ) -> None:
        self._runner = runner or SubprocessCommandRunner()
        self._command = command
        self._timeout_seconds = timeout_seconds

    def adapt_template(self, goal: str, template: Workflow) -> Workflow:
        prompt = _build_prompt(goal, template)
        with TemporaryDirectory(prefix="drw-codex-") as tmp_dir:
            output_path = Path(tmp_dir) / "last-message.json"
            schema_path = Path(tmp_dir) / "workflow-schema.json"
            schema_path.write_text(
                json.dumps(_workflow_output_schema()),
                encoding="utf-8",
            )
            result = self._runner.run(
                [
                    *self._command,
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(output_path),
                    prompt,
                ],
                timeout_seconds=self._timeout_seconds,
            )
            raw_output = output_path.read_text(encoding="utf-8") or result.stdout

        return _parse_workflow(raw_output)

    def execute_step(
        self,
        workflow: Workflow,
        step: Step,
        results_by_step: dict[str, StepResult],
    ) -> dict:
        prompt = _build_step_prompt(workflow, step, results_by_step)
        with TemporaryDirectory(prefix="drw-codex-step-") as tmp_dir:
            output_path = Path(tmp_dir) / "last-message.json"
            schema_path = Path(tmp_dir) / "step-output-schema.json"
            schema_path.write_text(
                json.dumps(_step_output_schema()),
                encoding="utf-8",
            )
            result = self._runner.run(
                [
                    *self._command,
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(output_path),
                    prompt,
                ],
                timeout_seconds=self._timeout_seconds,
            )
            raw_output = output_path.read_text(encoding="utf-8") or result.stdout

        output = json.loads(raw_output)
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
            **output,
        }


def _build_prompt(goal: str, template: Workflow) -> str:
    return (
        "Adapt this DRW workflow template to the user goal. "
        "Return only valid JSON matching the Workflow schema.\n\n"
        f"Goal:\n{goal}\n\n"
        f"Template JSON:\n{template.model_dump_json()}"
    )


def _build_step_prompt(
    workflow: Workflow,
    step: Step,
    results_by_step: dict[str, StepResult],
) -> str:
    dependency_outputs = {
        dependency: results_by_step[dependency].output
        for dependency in step.depends_on
    }
    return (
        "Execute this DRW workflow step. Return only valid JSON matching the "
        "step output schema. Be concise, actionable, and write in the user's "
        "language when clear from the objective.\n\n"
        f"Workflow name:\n{workflow.name}\n\n"
        f"Workflow objective:\n{workflow.objective}\n\n"
        f"Step JSON:\n{step.model_dump_json()}\n\n"
        f"Dependency outputs JSON:\n{json.dumps(dependency_outputs, default=str)}"
    )


def _workflow_output_schema() -> dict:
    retry_policy = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "max_attempts": {"type": "integer", "minimum": 1, "maximum": 3},
            "backoff_seconds": {"type": "number", "minimum": 0, "maximum": 30},
        },
    }
    retry_policy["required"] = list(retry_policy["properties"])

    policy = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "max_workers": {"type": "integer", "minimum": 1, "maximum": 25},
            "max_parallel_workers": {"type": "integer", "minimum": 1, "maximum": 8},
            "max_runtime_minutes": {"type": "integer", "minimum": 1, "maximum": 60},
            "max_artifacts": {"type": "integer", "minimum": 1, "maximum": 100},
            "max_cli_invocations": {"type": "integer", "minimum": 0, "maximum": 10},
            "max_refinement_rounds": {"type": "integer", "minimum": 0, "maximum": 3},
            "max_estimated_cost": {"type": "number", "minimum": 0},
        },
    }
    policy["required"] = list(policy["properties"])

    step = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "type": {
                "type": "string",
                "enum": [
                    "parallel_research",
                    "aggregation",
                    "verification",
                    "critic",
                    "refinement",
                    "report",
                    "cli_agent_task",
                ],
            },
            "config": {
                "type": "object",
                "additionalProperties": False,
                "properties": {},
                "required": [],
            },
            "depends_on": {"type": "array", "items": {"type": "string"}},
            "concurrency": {"type": "integer", "minimum": 1, "maximum": 8},
            "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 900},
            "retry_policy": retry_policy,
        },
    }
    step["required"] = list(step["properties"])

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "objective": {"type": "string", "minLength": 1},
            "policy": policy,
            "steps": {"type": "array", "minItems": 1, "items": step},
        },
        "required": ["name", "objective", "policy", "steps"],
    }


def _step_output_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "content": {"type": "string", "minLength": 1},
            "findings": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "string"}},
            "next_actions": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["content", "findings", "risks", "next_actions"],
    }


def _parse_workflow(raw_output: str) -> Workflow:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise CodexProviderError("Codex returned invalid JSON") from exc

    try:
        return Workflow.model_validate(payload)
    except ValidationError as exc:
        raise CodexProviderError("Codex returned invalid Workflow JSON") from exc
