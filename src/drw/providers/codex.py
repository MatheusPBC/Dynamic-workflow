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
                json.dumps(Workflow.model_json_schema()),
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


def _parse_workflow(raw_output: str) -> Workflow:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise CodexProviderError("Codex returned invalid JSON") from exc

    try:
        return Workflow.model_validate(payload)
    except ValidationError as exc:
        raise CodexProviderError("Codex returned invalid Workflow JSON") from exc
