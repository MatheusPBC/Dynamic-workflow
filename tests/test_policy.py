from drw.models.workflow import Step, Workflow, WorkflowPolicy
from drw.policy import apply_policy_limits


def test_apply_policy_limits_clamps_step_concurrency():
    workflow = Workflow(
        name="test",
        objective="research",
        policy=WorkflowPolicy(max_parallel_workers=3),
        steps=[Step(id="research", type="parallel_research", config={}, concurrency=8)],
    )

    limited = apply_policy_limits(workflow)

    assert limited.steps[0].concurrency == 3


def test_apply_policy_limits_limits_cli_steps_when_cli_budget_is_zero():
    workflow = Workflow(
        name="test",
        objective="research",
        policy=WorkflowPolicy(max_cli_invocations=0),
        steps=[
            Step(id="research", type="parallel_research", config={}),
            Step(id="agent", type="cli_agent_task", config={}),
        ],
    )

    limited = apply_policy_limits(workflow)

    assert [step.id for step in limited.steps] == ["research"]


def test_apply_policy_limits_limits_steps_to_max_workers():
    workflow = Workflow(
        name="test",
        objective="research",
        policy=WorkflowPolicy(max_workers=2),
        steps=[
            Step(id="first", type="parallel_research", config={}),
            Step(id="second", type="parallel_research", config={}),
            Step(id="third", type="parallel_research", config={}),
        ],
    )

    limited = apply_policy_limits(workflow)

    assert [step.id for step in limited.steps] == ["first", "second"]


def test_apply_policy_limits_counts_max_workers_after_filtering_cli_steps():
    workflow = Workflow(
        name="test",
        objective="research",
        policy=WorkflowPolicy(max_workers=2, max_cli_invocations=0),
        steps=[
            Step(id="cli1", type="cli_agent_task", config={}),
            Step(id="cli2", type="cli_agent_task", config={}),
            Step(id="research", type="parallel_research", config={}),
            Step(id="report", type="parallel_research", config={}),
        ],
    )

    limited = apply_policy_limits(workflow)

    assert [step.id for step in limited.steps] == ["research", "report"]
