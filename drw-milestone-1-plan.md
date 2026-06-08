# DRW Milestone 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first DRW milestone: classify a user goal, select a workflow template, generate a constrained workflow DSL, apply `WorkflowPolicy`, and validate the result.

**Architecture:** This milestone intentionally excludes MCP, Codex CLI integration, Docker, PostgreSQL, subprocess workers, and deployment. The system runs locally as a Python package with Pydantic models, deterministic templates, a fake provider for tests, and a CLI smoke command that prints a valid workflow JSON.

**Tech Stack:** Python 3.13+, Pydantic v2, pytest, ruff, argparse, standard library only for runtime.

---

## File Structure

Create this project structure under `/home/matheus/Documentos/laboratorio/drw`:

```text
drw/
  pyproject.toml
  README.md
  src/
    drw/
      __init__.py
      cli.py
      classifier.py
      generator.py
      policy.py
      templates.py
      validation.py
      models/
        __init__.py
        workflow.py
      providers/
        __init__.py
        base.py
        fake.py
  tests/
    test_classifier.py
    test_generator.py
    test_policy.py
    test_templates.py
    test_validation.py
```

Responsibilities:

- `models/workflow.py`: Pydantic DSL models and closed `StepType`.
- `policy.py`: default policy and policy clamping.
- `templates.py`: built-in workflow templates.
- `classifier.py`: deterministic classifier from goal text to template family.
- `providers/base.py`: provider protocol/interface.
- `providers/fake.py`: deterministic fake provider for tests and smoke runs.
- `generator.py`: template + provider + policy pipeline.
- `validation.py`: workflow validation helpers and repair-free failure messages.
- `cli.py`: local smoke entrypoint for milestone verification.

## Constraints

- Do not call Codex, OpenCode, Hermes, OpenRouter, or any external LLM in this milestone.
- Do not create MCP server yet.
- Do not add Docker yet.
- Do not add PostgreSQL or artifact storage yet.
- Do not allow free-form step types.
- Do not let generated workflows exceed `WorkflowPolicy`.

## Tasks

### Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/drw/__init__.py`
- Create: `src/drw/models/__init__.py`
- Create: `src/drw/providers/__init__.py`

- [ ] **Step 1: Create package metadata**

Create `pyproject.toml`:

```toml
[project]
name = "drw"
version = "0.1.0"
description = "Dynamic Research Workflows"
requires-python = ">=3.13"
dependencies = [
  "pydantic>=2.10.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
  "ruff>=0.8.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: Create README**

Create `README.md`:

```markdown
# Dynamic Research Workflows

Private workflow generator and runtime for agent-driven research.

## Milestone 1

This milestone validates the core workflow-generation contract:

- classify a user goal;
- select a workflow template;
- generate a constrained Workflow DSL;
- apply WorkflowPolicy limits;
- validate the final workflow.

No MCP, Codex CLI, Docker, database, or deployment is included in this milestone.
```

- [ ] **Step 3: Create package marker files**

Create `src/drw/__init__.py`:

```python
"""Dynamic Research Workflows."""
```

Create `src/drw/models/__init__.py`:

```python
"""DRW Pydantic models."""
```

Create `src/drw/providers/__init__.py`:

```python
"""DRW provider implementations."""
```

- [ ] **Step 4: Verify package metadata**

Run: `python -m pytest --version`

Expected: pytest prints its version after dev dependencies are installed.

### Task 2: Workflow Models

**Files:**
- Create: `src/drw/models/workflow.py`
- Test: `tests/test_validation.py`

- [ ] **Step 1: Write failing tests for closed step types and valid workflow shape**

Create `tests/test_validation.py`:

```python
import pytest
from pydantic import ValidationError

from drw.models.workflow import Step, Workflow, WorkflowPolicy


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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_validation.py -v`

Expected: FAIL because `drw.models.workflow` does not exist yet.

- [ ] **Step 3: Implement workflow models**

Create `src/drw/models/workflow.py`:

```python
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


StepType = Literal[
    "parallel_research",
    "aggregation",
    "verification",
    "critic",
    "refinement",
    "report",
    "cli_agent_task",
]


class RetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=2, ge=1, le=3)
    backoff_seconds: float = Field(default=1.0, ge=0.0, le=30.0)


class WorkflowPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_workers: int = Field(default=12, ge=1, le=25)
    max_parallel_workers: int = Field(default=4, ge=1, le=8)
    max_runtime_minutes: int = Field(default=20, ge=1, le=60)
    max_artifacts: int = Field(default=50, ge=1, le=100)
    max_cli_invocations: int = Field(default=6, ge=0, le=10)
    max_refinement_rounds: int = Field(default=1, ge=0, le=3)
    max_estimated_cost: float = Field(default=0.0, ge=0.0)


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: StepType
    config: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    concurrency: int = Field(default=1, ge=1, le=8)
    timeout_seconds: int = Field(default=120, ge=1, le=900)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)


class Workflow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    policy: WorkflowPolicy = Field(default_factory=WorkflowPolicy)
    steps: list[Step] = Field(min_length=1)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_validation.py -v`

Expected: PASS.

### Task 3: WorkflowPolicy Clamping

**Files:**
- Create: `src/drw/policy.py`
- Test: `tests/test_policy.py`

- [ ] **Step 1: Write failing tests for policy clamping**

Create `tests/test_policy.py`:

```python
from drw.models.workflow import Step, Workflow, WorkflowPolicy
from drw.policy import apply_policy_limits


def test_apply_policy_limits_clamps_step_concurrency():
    workflow = Workflow(
        name="test",
        objective="research",
        policy=WorkflowPolicy(max_parallel_workers=3),
        steps=[Step(id="research", type="parallel_research", config={}, concurrency=10)],
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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_policy.py -v`

Expected: FAIL because `drw.policy` does not exist yet.

- [ ] **Step 3: Implement policy limit application**

Create `src/drw/policy.py`:

```python
from drw.models.workflow import Step, Workflow


def apply_policy_limits(workflow: Workflow) -> Workflow:
    cli_steps_seen = 0
    limited_steps: list[Step] = []

    for step in workflow.steps[: workflow.policy.max_workers]:
        if step.type == "cli_agent_task":
            if cli_steps_seen >= workflow.policy.max_cli_invocations:
                continue
            cli_steps_seen += 1

        limited_steps.append(
            step.model_copy(
                update={"concurrency": min(step.concurrency, workflow.policy.max_parallel_workers)}
            )
        )

    return workflow.model_copy(update={"steps": limited_steps})
```

- [ ] **Step 4: Run policy tests**

Run: `pytest tests/test_policy.py -v`

Expected: PASS.

### Task 4: Template System

**Files:**
- Create: `src/drw/templates.py`
- Test: `tests/test_templates.py`

- [ ] **Step 1: Write failing tests for built-in templates**

Create `tests/test_templates.py`:

```python
from drw.templates import WorkflowTemplateName, get_template


def test_research_template_contains_only_allowed_step_types():
    template = get_template(WorkflowTemplateName.RESEARCH)

    assert [step.type for step in template.steps] == [
        "parallel_research",
        "verification",
        "critic",
        "refinement",
        "aggregation",
        "report",
    ]


def test_security_review_template_has_security_sources():
    template = get_template(WorkflowTemplateName.SECURITY_REVIEW)

    research_step = template.steps[0]

    assert "security_advisories" in research_step.config["sources"]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_templates.py -v`

Expected: FAIL because `drw.templates` does not exist yet.

- [ ] **Step 3: Implement templates**

Create `src/drw/templates.py`:

```python
from enum import StrEnum

from drw.models.workflow import Step, Workflow, WorkflowPolicy


class WorkflowTemplateName(StrEnum):
    RESEARCH = "research"
    CODE_MIGRATION = "code_migration"
    SECURITY_REVIEW = "security_review"
    MARKET_ANALYSIS = "market_analysis"


def get_template(name: WorkflowTemplateName) -> Workflow:
    templates = {
        WorkflowTemplateName.RESEARCH: _research_template,
        WorkflowTemplateName.CODE_MIGRATION: _code_migration_template,
        WorkflowTemplateName.SECURITY_REVIEW: _security_review_template,
        WorkflowTemplateName.MARKET_ANALYSIS: _market_analysis_template,
    }
    return templates[name]().model_copy(deep=True)


def _research_template() -> Workflow:
    return Workflow(
        name="research_workflow",
        objective="research objective",
        policy=WorkflowPolicy(),
        steps=[
            Step(
                id="research",
                type="parallel_research",
                config={"sources": ["docs", "github", "articles"]},
                concurrency=4,
            ),
            Step(id="verify_research", type="verification", config={}, depends_on=["research"]),
            Step(id="critic_research", type="critic", config={}, depends_on=["verify_research"]),
            Step(id="refine_research", type="refinement", config={}, depends_on=["critic_research"]),
            Step(id="aggregate", type="aggregation", config={}, depends_on=["refine_research"]),
            Step(id="report", type="report", config={}, depends_on=["aggregate"]),
        ],
    )


def _code_migration_template() -> Workflow:
    workflow = _research_template()
    return workflow.model_copy(
        update={
            "name": "code_migration_workflow",
            "steps": [
                workflow.steps[0].model_copy(
                    update={"config": {"sources": ["repository", "tests", "docs"]}}
                ),
                *workflow.steps[1:],
            ],
        },
        deep=True,
    )


def _security_review_template() -> Workflow:
    workflow = _research_template()
    return workflow.model_copy(
        update={
            "name": "security_review_workflow",
            "steps": [
                workflow.steps[0].model_copy(
                    update={
                        "config": {"sources": ["repository", "security_advisories", "owasp"]}
                    }
                ),
                *workflow.steps[1:],
            ],
        },
        deep=True,
    )


def _market_analysis_template() -> Workflow:
    workflow = _research_template()
    return workflow.model_copy(
        update={
            "name": "market_analysis_workflow",
            "steps": [
                workflow.steps[0].model_copy(
                    update={"config": {"sources": ["web", "competitors", "reports"]}}
                ),
                *workflow.steps[1:],
            ],
        },
        deep=True,
    )
```

- [ ] **Step 4: Run template tests**

Run: `pytest tests/test_templates.py -v`

Expected: PASS.

### Task 5: Workflow Classifier

**Files:**
- Create: `src/drw/classifier.py`
- Test: `tests/test_classifier.py`

- [ ] **Step 1: Write failing classifier tests**

Create `tests/test_classifier.py`:

```python
from drw.classifier import classify_goal
from drw.templates import WorkflowTemplateName


def test_classifies_observability_question_as_research():
    result = classify_goal("pesquise frameworks python de observabilidade")

    assert result == WorkflowTemplateName.RESEARCH


def test_classifies_security_goal_as_security_review():
    result = classify_goal("revise riscos de seguranca deste endpoint")

    assert result == WorkflowTemplateName.SECURITY_REVIEW


def test_classifies_migration_goal_as_code_migration():
    result = classify_goal("planeje migracao de flask para fastapi")

    assert result == WorkflowTemplateName.CODE_MIGRATION
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_classifier.py -v`

Expected: FAIL because `drw.classifier` does not exist yet.

- [ ] **Step 3: Implement deterministic classifier**

Create `src/drw/classifier.py`:

```python
from drw.templates import WorkflowTemplateName


SECURITY_TERMS = ("security", "seguranca", "vulnerability", "risco", "owasp", "auth")
MIGRATION_TERMS = ("migration", "migracao", "migrar", "refactor", "refatoracao")
MARKET_TERMS = ("market", "mercado", "concorrente", "startup", "mvp", "oportunidade")


def classify_goal(goal: str) -> WorkflowTemplateName:
    normalized = goal.lower()

    if _contains_any(normalized, SECURITY_TERMS):
        return WorkflowTemplateName.SECURITY_REVIEW
    if _contains_any(normalized, MIGRATION_TERMS):
        return WorkflowTemplateName.CODE_MIGRATION
    if _contains_any(normalized, MARKET_TERMS):
        return WorkflowTemplateName.MARKET_ANALYSIS

    return WorkflowTemplateName.RESEARCH


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)
```

- [ ] **Step 4: Run classifier tests**

Run: `pytest tests/test_classifier.py -v`

Expected: PASS.

### Task 6: Provider Interface And Fake Provider

**Files:**
- Create: `src/drw/providers/base.py`
- Create: `src/drw/providers/fake.py`
- Test: `tests/test_provider.py`

- [ ] **Step 1: Write failing provider contract test**

Create `tests/test_provider.py`:

```python
from drw.providers.fake import FakeLLMProvider
from drw.templates import WorkflowTemplateName, get_template


def test_fake_provider_adapts_template_objective_without_mutating_original():
    template = get_template(WorkflowTemplateName.RESEARCH)
    provider = FakeLLMProvider()

    workflow = provider.adapt_template(
        "pesquise frameworks python de observabilidade",
        template,
    )

    assert workflow.objective == "pesquise frameworks python de observabilidade"
    assert template.objective == "research objective"
    assert workflow.steps[0].type == "parallel_research"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_provider.py -v`

Expected: FAIL because provider modules do not exist yet.

- [ ] **Step 3: Implement provider protocol**

Create `src/drw/providers/base.py`:

```python
from typing import Protocol

from drw.models.workflow import Workflow


class LLMProvider(Protocol):
    def adapt_template(self, goal: str, template: Workflow) -> Workflow:
        """Adapt a validated template to a user goal."""
```

- [ ] **Step 4: Implement fake provider**

Create `src/drw/providers/fake.py`:

```python
from drw.models.workflow import Workflow


class FakeLLMProvider:
    def adapt_template(self, goal: str, template: Workflow) -> Workflow:
        return template.model_copy(update={"objective": goal}, deep=True)
```

- [ ] **Step 5: Run provider tests**

Run: `pytest tests/test_provider.py -v`

Expected: PASS.

### Task 7: Workflow Generator And Validation

**Files:**
- Create: `src/drw/generator.py`
- Create: `src/drw/validation.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write failing generator contract test**

Create `tests/test_generator.py`:

```python
from drw.generator import WorkflowGenerator
from drw.providers.fake import FakeLLMProvider


def test_generator_returns_valid_workflow_for_observability_goal():
    generator = WorkflowGenerator(provider=FakeLLMProvider())

    workflow = generator.generate("pesquise frameworks python de observabilidade")

    assert workflow.name == "research_workflow"
    assert workflow.objective == "pesquise frameworks python de observabilidade"
    assert workflow.steps[0].type == "parallel_research"
    assert workflow.steps[-1].type == "report"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_generator.py -v`

Expected: FAIL because `drw.generator` does not exist yet.

- [ ] **Step 3: Extend generator tests for policy clamping**

Append to `tests/test_generator.py`:

```python

def test_generator_applies_policy_limits():
    generator = WorkflowGenerator(provider=FakeLLMProvider())

    workflow = generator.generate(
        "pesquise frameworks python de observabilidade",
        policy_overrides={"max_parallel_workers": 2},
    )

    assert workflow.steps[0].concurrency == 2
```

- [ ] **Step 2: Implement validation helpers**

Create `src/drw/validation.py`:

```python
from drw.models.workflow import Workflow


def validate_workflow(workflow: Workflow) -> Workflow:
    step_ids = {step.id for step in workflow.steps}

    for step in workflow.steps:
        missing_dependencies = [dep for dep in step.depends_on if dep not in step_ids]
        if missing_dependencies:
            missing = ", ".join(missing_dependencies)
            raise ValueError(f"Step {step.id!r} depends on missing step(s): {missing}")

    return workflow
```

- [ ] **Step 3: Implement generator pipeline**

Create `src/drw/generator.py`:

```python
from drw.classifier import classify_goal
from drw.models.workflow import Workflow, WorkflowPolicy
from drw.policy import apply_policy_limits
from drw.providers.base import LLMProvider
from drw.templates import get_template
from drw.validation import validate_workflow


class WorkflowGenerator:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def generate(
        self,
        goal: str,
        policy_overrides: dict[str, object] | None = None,
    ) -> Workflow:
        template_name = classify_goal(goal)
        template = get_template(template_name)

        if policy_overrides:
            template = template.model_copy(
                update={"policy": WorkflowPolicy(**{**template.policy.model_dump(), **policy_overrides})}
            )

        generated = self._provider.adapt_template(goal, template)
        limited = apply_policy_limits(generated)
        return validate_workflow(limited)
```

- [ ] **Step 4: Run generator tests**

Run: `pytest tests/test_generator.py -v`

Expected: PASS.

- [ ] **Step 5: Run all tests**

Run: `pytest -v`

Expected: PASS.

### Task 8: CLI Smoke Command

**Files:**
- Create: `src/drw/cli.py`
- Test: manual command

- [ ] **Step 1: Implement CLI**

Create `src/drw/cli.py`:

```python
import argparse

from drw.generator import WorkflowGenerator
from drw.providers.fake import FakeLLMProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a DRW workflow DSL")
    parser.add_argument("goal", help="User goal to convert into a workflow")
    args = parser.parse_args()

    generator = WorkflowGenerator(provider=FakeLLMProvider())
    workflow = generator.generate(args.goal)
    print(workflow.model_dump_json(indent=2))
```

- [ ] **Step 2: Add CLI script entrypoint**

Add to `pyproject.toml` now that `src/drw/cli.py` exists:

```toml
[project.scripts]
drw = "drw.cli:main"
```

- [ ] **Step 3: Run CLI smoke command**

Run: `PYTHONPATH=src python -m drw.cli "pesquise frameworks python de observabilidade"`

Expected: JSON with `name` as `research_workflow`, `objective` as the input text, and steps ending in `report`.

### Task 9: Quality Gate

**Files:**
- All created Python files

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`

Expected: PASS.

- [ ] **Step 2: Run ruff check**

Run: `ruff check .`

Expected: PASS with no lint errors.

- [ ] **Step 3: Run CLI smoke command again**

Run: `PYTHONPATH=src python -m drw.cli "pesquise frameworks python de observabilidade"`

Expected: valid JSON output.

## Done When

- `pytest -v` passes.
- `ruff check .` passes.
- CLI smoke command prints valid workflow JSON.
- The generated workflow uses a closed `StepType`.
- `WorkflowPolicy` clamps concurrency and CLI usage.
- The observability research goal maps to the `research` template.
- No MCP, Codex CLI, Docker, database, or deployment code exists in this milestone.

## Self-Review

- Spec coverage: this plan implements the agreed first milestone only: models, policy, step types, templates, classifier, generator, validation, and smoke output.
- Intentional gaps: MCP, CodexProvider, Docker, PostgreSQL, runtime workers, event bus, artifacts, verifier implementation, and deployment are deferred to later milestones.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: `WorkflowPolicy`, `Step`, `Workflow`, `WorkflowGenerator`, `FakeLLMProvider`, and `WorkflowTemplateName` names are consistent across tasks.
