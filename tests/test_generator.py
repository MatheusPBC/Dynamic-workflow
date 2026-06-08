import pytest

from drw.generator import WorkflowGenerator
from drw.models.workflow import Step, Workflow, WorkflowPolicy
from drw.providers.fake import FakeLLMProvider
from drw.validation import validate_workflow


def test_generator_returns_valid_workflow_for_observability_goal():
    generator = WorkflowGenerator(provider=FakeLLMProvider())

    workflow = generator.generate("pesquise frameworks python de observabilidade")

    assert workflow.name == "research_workflow"
    assert workflow.objective == "pesquise frameworks python de observabilidade"
    assert workflow.steps[0].type == "parallel_research"
    assert workflow.steps[-1].type == "report"


def test_generator_applies_policy_limits():
    generator = WorkflowGenerator(provider=FakeLLMProvider())

    workflow = generator.generate(
        "pesquise frameworks python de observabilidade",
        policy_overrides={"max_parallel_workers": 2},
    )

    assert workflow.steps[0].concurrency == 2


def test_validate_workflow_rejects_missing_dependency():
    workflow = Workflow(
        name="bad",
        objective="bad",
        policy=WorkflowPolicy(),
        steps=[
            Step(id="report", type="report", config={}, depends_on=["missing"]),
        ],
    )

    with pytest.raises(ValueError, match="depends on missing step"):
        validate_workflow(workflow)
