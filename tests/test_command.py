import subprocess

from drw.command import CommandExecutionError, CommandResult, SubprocessCommandRunner


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
