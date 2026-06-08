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
    def __init__(self, result: CommandResult, message: str | None = None) -> None:
        super().__init__(message or _format_failure_message(result))
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
            raise CommandExecutionError(
                result,
                f"Command timed out after {timeout_seconds}s: {_format_failure_message(result)}",
            ) from exc

        result = CommandResult(
            args=tuple(args),
            returncode=completed.returncode,
            stdout=_coerce_output(completed.stdout),
            stderr=_coerce_output(completed.stderr),
        )

        if not result.succeeded:
            raise CommandExecutionError(result)

        return result


def _format_failure_message(result: CommandResult) -> str:
    command = " ".join(result.args)
    details = result.stderr or result.stdout
    message = f"Command failed with exit code {result.returncode}: {command}"
    if details:
        return f"{message}\n{details}"
    return message


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value
