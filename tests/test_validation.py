import pytest
from pydantic import ValidationError

from drw.models.workflow import RetryPolicy, Step, Workflow, WorkflowPolicy


def test_workflow_accepts_allowed_step_type():
    workflow = Workflow(
        name="observability_research",
        objective="pesquise frameworks python de observabilidade",
        policy=WorkflowPolicy(),
        steps=[
            Step(
                id="research",
                type="parallel_research",
                config={"sources": ["docs", "github"]},
            )
        ],
    )

    assert workflow.steps[0].type == "parallel_research"


def test_workflow_rejects_unknown_step_type():
    with pytest.raises(ValidationError):
        Step(id="bad", type="invented_step", config={})


def test_workflow_policy_uses_conservative_defaults():
    policy = WorkflowPolicy()

    assert policy.max_workers == 12
    assert policy.max_parallel_workers == 4
    assert policy.max_runtime_minutes == 20
    assert policy.max_artifacts == 50
    assert policy.max_cli_invocations == 6
    assert policy.max_refinement_rounds == 1
    assert policy.max_estimated_cost == 0.0


def test_workflow_policy_rejects_too_many_parallel_workers():
    with pytest.raises(ValidationError):
        WorkflowPolicy(max_parallel_workers=9)


def test_workflow_policy_rejects_too_many_workers():
    with pytest.raises(ValidationError):
        WorkflowPolicy(max_workers=26)


def test_step_uses_conservative_defaults():
    step = Step(id="research", type="parallel_research")

    assert step.config == {}
    assert step.depends_on == []
    assert step.concurrency == 1
    assert step.timeout_seconds == 120
    assert step.retry_policy.max_attempts == 2
    assert step.retry_policy.backoff_seconds == 1.0


def test_retry_policy_uses_conservative_defaults():
    retry_policy = RetryPolicy()

    assert retry_policy.max_attempts == 2
    assert retry_policy.backoff_seconds == 1.0


def test_step_rejects_too_much_concurrency():
    with pytest.raises(ValidationError):
        Step(id="research", type="parallel_research", concurrency=9)


def test_step_rejects_too_long_timeout():
    with pytest.raises(ValidationError):
        Step(id="research", type="parallel_research", timeout_seconds=901)


def test_retry_policy_rejects_too_many_attempts():
    with pytest.raises(ValidationError):
        RetryPolicy(max_attempts=4)


def test_retry_policy_rejects_too_long_backoff():
    with pytest.raises(ValidationError):
        RetryPolicy(backoff_seconds=31.0)


def test_workflow_policy_rejects_too_long_runtime():
    with pytest.raises(ValidationError):
        WorkflowPolicy(max_runtime_minutes=61)


def test_workflow_policy_rejects_too_many_artifacts():
    with pytest.raises(ValidationError):
        WorkflowPolicy(max_artifacts=101)


def test_workflow_policy_rejects_too_many_cli_invocations():
    with pytest.raises(ValidationError):
        WorkflowPolicy(max_cli_invocations=11)


def test_workflow_policy_rejects_too_many_refinement_rounds():
    with pytest.raises(ValidationError):
        WorkflowPolicy(max_refinement_rounds=4)
