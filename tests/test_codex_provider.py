import pytest

from drw.command import CommandExecutionError, CommandResult
from drw.providers.codex import CodexProvider, CodexProviderError
from drw.templates import WorkflowTemplateName, get_template


class FakeRunner:
    def __init__(self, result: CommandResult):
        self.result = result
        self.calls = []

    def run(self, args, timeout_seconds):
        self.calls.append({"args": list(args), "timeout_seconds": timeout_seconds})
        if "--output-last-message" in args:
            output_path = args[args.index("--output-last-message") + 1]
            with open(output_path, "w", encoding="utf-8") as output_file:
                output_file.write(self.result.stdout)
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
    assert "--skip-git-repo-check" in runner.calls[0]["args"]
    assert "--output-last-message" in runner.calls[0]["args"]
    assert "--output-schema" in runner.calls[0]["args"]
    assert runner.calls[0]["timeout_seconds"] == 60


def test_codex_provider_rejects_invalid_json():
    template = get_template(WorkflowTemplateName.RESEARCH)
    runner = FakeRunner(
        CommandResult(args=("codex",), returncode=0, stdout="not json", stderr="")
    )
    provider = CodexProvider(runner=runner)

    with pytest.raises(CodexProviderError, match="invalid JSON"):
        provider.adapt_template("goal", template)


def test_codex_provider_rejects_invalid_workflow_json():
    template = get_template(WorkflowTemplateName.RESEARCH)
    runner = FakeRunner(
        CommandResult(args=("codex",), returncode=0, stdout='{"name":"bad"}', stderr="")
    )
    provider = CodexProvider(runner=runner)

    with pytest.raises(CodexProviderError, match="invalid Workflow JSON"):
        provider.adapt_template("goal", template)


def test_codex_provider_propagates_command_errors():
    class FailingRunner:
        def run(self, args, timeout_seconds):
            result = CommandResult(
                args=tuple(args), returncode=2, stdout="", stderr="bad auth"
            )
            raise CommandExecutionError(result, "bad auth")

    provider = CodexProvider(runner=FailingRunner())
    template = get_template(WorkflowTemplateName.RESEARCH)

    with pytest.raises(CommandExecutionError) as exc_info:
        provider.adapt_template("goal", template)

    assert exc_info.value.result.returncode == 2
    assert exc_info.value.result.stderr == "bad auth"
