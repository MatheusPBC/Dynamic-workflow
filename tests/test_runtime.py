from drw.artifacts import LocalArtifactStore
from drw.models.workflow import Step, Workflow
from drw.runtime import StepResult, StepStatus, WorkflowRunResult, WorkflowRuntime


def make_linear_workflow() -> Workflow:
    return Workflow(
        name="test_workflow",
        objective="test objective",
        steps=[
            Step(id="research", type="parallel_research"),
            Step(id="verify", type="verification", depends_on=["research"]),
            Step(id="report", type="report", depends_on=["verify"]),
        ],
    )


def test_step_result_records_success_fields():
    result = StepResult(
        step_id="research",
        status=StepStatus.SUCCESS,
        artifact_path="run-1/research.json",
        output={"ok": True},
    )

    assert result.step_id == "research"
    assert result.status == StepStatus.SUCCESS
    assert result.error is None


def test_workflow_run_result_reports_success_when_all_steps_succeed():
    result = WorkflowRunResult(
        run_id="run-1",
        workflow_name="test_workflow",
        status=StepStatus.SUCCESS,
        steps=[],
    )

    assert result.status == StepStatus.SUCCESS


def test_runtime_executes_workflow_steps_and_writes_artifacts(tmp_path):
    workflow = make_linear_workflow()
    runtime = WorkflowRuntime(artifact_store=LocalArtifactStore(tmp_path))

    result = runtime.run(workflow, run_id="run-1")

    assert result.status == StepStatus.SUCCESS
    assert [step.step_id for step in result.steps] == ["research", "verify", "report"]
    assert [step.status for step in result.steps] == [
        StepStatus.SUCCESS,
        StepStatus.SUCCESS,
        StepStatus.SUCCESS,
    ]
    assert (tmp_path / "run-1" / "research.json").exists()
    assert (tmp_path / "run-1" / "verify.json").exists()
    assert (tmp_path / "run-1" / "report.json").exists()


def test_runtime_skips_downstream_steps_when_dependency_fails(tmp_path):
    workflow = make_linear_workflow()

    def fail_research(*_args):
        raise RuntimeError("research failed")

    runtime = WorkflowRuntime(
        artifact_store=LocalArtifactStore(tmp_path),
        handlers={"research": fail_research},
    )

    result = runtime.run(workflow, run_id="run-1")

    assert result.status == StepStatus.FAILED
    assert [step.status for step in result.steps] == [
        StepStatus.FAILED,
        StepStatus.SKIPPED,
        StepStatus.SKIPPED,
    ]
    assert result.steps[0].error == "research failed"
    assert result.steps[1].error == "dependency failed or skipped"
