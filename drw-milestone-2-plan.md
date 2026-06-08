# DRW Milestone 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real CLI-backed provider path for DRW by introducing a safe subprocess runner and a `CodexProvider` that adapts workflow templates from Codex CLI JSON output.

**Architecture:** This milestone keeps the Milestone 1 generator pipeline intact and adds an injectable command execution boundary. Unit tests use fake runners only; no test calls Codex, OpenCode, Hermes, network, Docker, MCP, database, or VPS.

**Tech Stack:** Python 3.13+, Pydantic v2, pytest, ruff, subprocess, json, standard library.

---

## File Structure

Create or modify these files under `/home/matheus/.config/superpowers/worktrees/drw/milestone-2`:

```text
src/drw/
  command.py              # subprocess boundary and result models
  providers/
    codex.py              # CodexProvider implementation
    fake.py               # keep existing fake provider unchanged unless needed
tests/
  test_command.py         # command runner behavior
  test_codex_provider.py  # CodexProvider behavior using fake runner
```

Responsibilities:

- `command.py`: no-shell command execution, timeout mapping, output capture, safe error type.
- `providers/codex.py`: prompt construction, command invocation, JSON parsing, Pydantic workflow validation.
- `tests/test_command.py`: verifies runner success, non-zero exit, timeout via fake subprocess injection where practical.
- `tests/test_codex_provider.py`: verifies provider success/failure modes without Codex real.

## Constraints

- Do not call real `codex` in automated tests.
- Do not add MCP server.
- Do not add Docker.
- Do not add PostgreSQL/artifact storage.
- Do not add runtime workers or async scheduler.
- Do not add OpenCode/Hermes providers in this milestone.
- Do not use `shell=True`.
- Do not log or expose environment variables.

## Tasks

### Task 1: Command Runner Models And Success Path

**Files:**
- Create: `src/drw/command.py`
- Create: `tests/test_command.py`

- [ ] **Step 1: Write failing tests for command result and success execution**

Create `tests/test_command.py`:

```python
from drw.command import CommandResult, SubprocessCommandRunner


class CompletedProcessStub:
    def __init__(self, args, returncode=0, stdout="", stderr=""):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_command_result_success_property():
    result = CommandResult(args=("codex", "exec"), returncode=0, stdout="ok", stderr="")

    assert result.succeeded is True


def test_subprocess_runner_returns_captured_output():
    calls = []

    def fake_run(args, capture_output, text, timeout, check):
        calls.append(
            {
                "args": args,
                "capture_output": capture_output,
                "text": text,
                "timeout": timeout,
                "check": check,
            }
        )
        return CompletedProcessStub(args=args, stdout="workflow json", stderr="")

    runner = SubprocessCommandRunner(run_command=fake_run)

    result = runner.run(["codex", "exec"], timeout_seconds=15)

    assert result == CommandResult(
        args=("codex", "exec"),
        returncode=0,
        stdout="workflow json",
        stderr="",
    )
    assert calls == [
        {
            "args": ["codex", "exec"],
            "capture_output": True,
            "text": True,
            "timeout": 15,
            "check": False,
        }
    ]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_command.py -v`

Expected: FAIL because `drw.command` does not exist yet.

- [ ] **Step 3: Implement command runner success path**

Create `src/drw/command.py`:

```python
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import subprocess


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class SubprocessCommandRunner:
    def __init__(self, run_command: RunCommand | None = None) -> None:
        self._run_command = run_command or subprocess.run

    def run(self, args: Sequence[str], timeout_seconds: int) -> CommandResult:
        completed = self._run_command(
            list(args),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return CommandResult(
            args=tuple(args),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
```

- [ ] **Step 4: Run command tests**

Run: `pytest tests/test_command.py -v`

Expected: PASS for the first two tests.

### Task 2: Command Runner Failure Modes

**Files:**
- Modify: `src/drw/command.py`
- Modify: `tests/test_command.py`

- [ ] **Step 1: Add failing tests for non-zero and timeout**

Append to `tests/test_command.py`:

```python
import subprocess

from drw.command import CommandExecutionError


def test_subprocess_runner_raises_for_non_zero_exit():
    def fake_run(args, capture_output, text, timeout, check):
        return CompletedProcessStub(args=args, returncode=2, stdout="", stderr="bad auth")

    runner = SubprocessCommandRunner(run_command=fake_run)

    try:
        runner.run(["codex", "exec"], timeout_seconds=15)
    except CommandExecutionError as exc:
        assert exc.result.returncode == 2
        assert "bad auth" in str(exc)
    else:
        raise AssertionError("Expected CommandExecutionError")


def test_subprocess_runner_maps_timeout_to_command_error():
    def fake_run(args, capture_output, text, timeout, check):
        raise subprocess.TimeoutExpired(cmd=args, timeout=timeout, output="partial", stderr="slow")

    runner = SubprocessCommandRunner(run_command=fake_run)

    try:
        runner.run(["codex", "exec"], timeout_seconds=1)
    except CommandExecutionError as exc:
        assert exc.result.returncode == -1
        assert exc.result.stdout == "partial"
        assert exc.result.stderr == "slow"
        assert "timed out" in str(exc)
    else:
        raise AssertionError("Expected CommandExecutionError")
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_command.py -v`

Expected: FAIL because `CommandExecutionError` does not exist and non-zero exits are not raised.

- [ ] **Step 3: Implement failure handling**

Modify `src/drw/command.py`:

```python
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import subprocess


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class CommandExecutionError(RuntimeError):
    def __init__(self, message: str, result: CommandResult) -> None:
        super().__init__(message)
        self.result = result


class SubprocessCommandRunner:
    def __init__(self, run_command: RunCommand | None = None) -> None:
        self._run_command = run_command or subprocess.run

    def run(self, args: Sequence[str], timeout_seconds: int) -> CommandResult:
        try:
            completed = self._run_command(
                list(args),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            result = CommandResult(
                args=tuple(args),
                returncode=-1,
                stdout=_coerce_output(exc.output),
                stderr=_coerce_output(exc.stderr),
            )
            raise CommandExecutionError(f"Command timed out after {timeout_seconds}s", result) from exc

        result = CommandResult(
            args=tuple(args),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if not result.succeeded:
            raise CommandExecutionError(_format_failure_message(result), result)
        return result


def _format_failure_message(result: CommandResult) -> str:
    detail = result.stderr.strip() or result.stdout.strip() or "no output"
    return f"Command failed with exit code {result.returncode}: {detail}"


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value
```

- [ ] **Step 4: Run command tests**

Run: `pytest tests/test_command.py -v`

Expected: PASS.

### Task 3: CodexProvider Success Path

**Files:**
- Create: `src/drw/providers/codex.py`
- Create: `tests/test_codex_provider.py`

- [ ] **Step 1: Write failing success test**

Create `tests/test_codex_provider.py`:

```python
from drw.command import CommandResult
from drw.providers.codex import CodexProvider
from drw.templates import WorkflowTemplateName, get_template


class FakeRunner:
    def __init__(self, result: CommandResult):
        self.result = result
        self.calls = []

    def run(self, args, timeout_seconds):
        self.calls.append({"args": list(args), "timeout_seconds": timeout_seconds})
        return self.result


def test_codex_provider_adapts_template_from_valid_json():
    template = get_template(WorkflowTemplateName.RESEARCH)
    runner = FakeRunner(
        CommandResult(
            args=("codex",),
            returncode=0,
            stdout=template.model_copy(
                update={"objective": "pesquise frameworks python de observabilidade"}
            ).model_dump_json(),
            stderr="",
        )
    )
    provider = CodexProvider(runner=runner)

    workflow = provider.adapt_template(
        "pesquise frameworks python de observabilidade",
        template,
    )

    assert workflow.objective == "pesquise frameworks python de observabilidade"
    assert workflow.steps[0].type == "parallel_research"
    assert runner.calls[0]["args"][0] == "codex"
    assert runner.calls[0]["timeout_seconds"] == 60
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_codex_provider.py -v`

Expected: FAIL because `drw.providers.codex` does not exist yet.

- [ ] **Step 3: Implement CodexProvider success path**

Create `src/drw/providers/codex.py`:

```python
import json

from pydantic import ValidationError

from drw.command import SubprocessCommandRunner
from drw.models.workflow import Workflow


class CodexProviderError(RuntimeError):
    pass


class CodexProvider:
    def __init__(
        self,
        runner: SubprocessCommandRunner | None = None,
        command: tuple[str, ...] = ("codex", "exec"),
        timeout_seconds: int = 60,
    ) -> None:
        self._runner = runner or SubprocessCommandRunner()
        self._command = command
        self._timeout_seconds = timeout_seconds

    def adapt_template(self, goal: str, template: Workflow) -> Workflow:
        prompt = _build_prompt(goal, template)
        result = self._runner.run([*self._command, prompt], timeout_seconds=self._timeout_seconds)
        return _parse_workflow(result.stdout)


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
```

- [ ] **Step 4: Run provider success test**

Run: `pytest tests/test_codex_provider.py -v`

Expected: PASS.

### Task 4: CodexProvider Failure Modes

**Files:**
- Modify: `tests/test_codex_provider.py`

- [ ] **Step 1: Add failing tests for invalid provider outputs and runner errors**

Append to `tests/test_codex_provider.py`:

```python
import pytest

from drw.command import CommandExecutionError
from drw.providers.codex import CodexProviderError


def test_codex_provider_rejects_invalid_json():
    template = get_template(WorkflowTemplateName.RESEARCH)
    runner = FakeRunner(CommandResult(args=("codex",), returncode=0, stdout="not json", stderr=""))
    provider = CodexProvider(runner=runner)

    with pytest.raises(CodexProviderError, match="invalid JSON"):
        provider.adapt_template("goal", template)


def test_codex_provider_rejects_invalid_workflow_json():
    template = get_template(WorkflowTemplateName.RESEARCH)
    runner = FakeRunner(CommandResult(args=("codex",), returncode=0, stdout='{"name":"bad"}', stderr=""))
    provider = CodexProvider(runner=runner)

    with pytest.raises(CodexProviderError, match="invalid Workflow JSON"):
        provider.adapt_template("goal", template)


def test_codex_provider_propagates_command_errors():
    class FailingRunner:
        def run(self, args, timeout_seconds):
            result = CommandResult(args=tuple(args), returncode=2, stdout="", stderr="bad auth")
            raise CommandExecutionError("bad auth", result)

    provider = CodexProvider(runner=FailingRunner())
    template = get_template(WorkflowTemplateName.RESEARCH)

    with pytest.raises(CommandExecutionError):
        provider.adapt_template("goal", template)
```

- [ ] **Step 2: Run provider tests**

Run: `pytest tests/test_codex_provider.py -v`

Expected: PASS. If any test fails, fix only `src/drw/providers/codex.py` or the test setup.

### Task 5: Generator Integration With CodexProvider Contract

**Files:**
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Add test proving generator accepts any provider implementing the protocol**

Append to `tests/test_generator.py`:

```python

class RecordingProvider:
    def __init__(self):
        self.seen_goal = None
        self.seen_template_name = None

    def adapt_template(self, goal, template):
        self.seen_goal = goal
        self.seen_template_name = template.name
        return template.model_copy(update={"objective": goal}, deep=True)


def test_generator_uses_injected_provider_contract():
    provider = RecordingProvider()
    generator = WorkflowGenerator(provider=provider)

    workflow = generator.generate("pesquise frameworks python de observabilidade")

    assert provider.seen_goal == "pesquise frameworks python de observabilidade"
    assert provider.seen_template_name == "research_workflow"
    assert workflow.objective == "pesquise frameworks python de observabilidade"
```

- [ ] **Step 2: Run generator tests**

Run: `pytest tests/test_generator.py -v`

Expected: PASS.

### Task 6: README Documentation For Milestone 2

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with CodexProvider status**

Modify `README.md` to include:

```markdown
## Milestone 2

Milestone 2 adds a real CLI-backed provider boundary:

- `SubprocessCommandRunner` captures stdout, stderr, return code, and timeouts.
- `CodexProvider` adapts workflow templates from Codex CLI JSON output.
- Automated tests use fake runners and do not call Codex, OAuth, network, Docker, or VPS.

Manual smoke with real Codex is intentionally separate from the test suite.
```

- [ ] **Step 2: Verify README wording**

Run: `python -m pytest tests/test_codex_provider.py -v`

Expected: PASS. Documentation change should not affect tests.

### Task 7: Quality Gate

**Files:**
- All created/modified files

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`

Expected: PASS.

- [ ] **Step 2: Run ruff**

Run: `ruff check .`

Expected: PASS.

- [ ] **Step 3: Run existing fake CLI smoke**

Run: `PYTHONPATH=src python -m drw.cli "pesquise frameworks python de observabilidade"`

Expected: valid JSON output.

## Done When

- `pytest -v` passes.
- `ruff check .` passes.
- Existing fake CLI smoke still prints valid workflow JSON.
- `CommandRunner` captures success, non-zero exit and timeout.
- `CodexProvider` parses valid Workflow JSON from runner stdout.
- `CodexProvider` fails clearly for invalid JSON, invalid workflow JSON and command errors.
- No automated test calls real Codex or requires OAuth.
- No MCP, Docker, database, runtime workers, artifacts or deployment code exists in this milestone.

## Self-Review

- Spec coverage: plan implements only the real-provider boundary for Codex CLI via subprocess and keeps tests hermetic.
- Intentional gaps: MCP, runtime, async workers, artifacts, PostgreSQL, VPS deployment and real Codex smoke are deferred.
- Placeholder scan: no placeholders or unspecified implementation steps remain.
- Type consistency: `CommandResult`, `CommandExecutionError`, `SubprocessCommandRunner`, `CodexProvider`, `CodexProviderError`, and `LLMProvider` signatures are consistent across tasks.
