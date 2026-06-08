import json
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError

from drw.command import SubprocessCommandRunner
from drw.models.workflow import Workflow


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


def _build_prompt(goal: str, template: Workflow) -> str:
    return (
        "Adapt this DRW workflow template to the user goal. "
        "Return only valid JSON matching the Workflow schema.\n\n"
        f"Goal:\n{goal}\n\n"
        f"Template JSON:\n{template.model_dump_json()}"
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
            "config": {"type": "object"},
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


def _parse_workflow(raw_output: str) -> Workflow:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise CodexProviderError("Codex returned invalid JSON") from exc

    try:
        return Workflow.model_validate(payload)
    except ValidationError as exc:
        raise CodexProviderError("Codex returned invalid Workflow JSON") from exc
