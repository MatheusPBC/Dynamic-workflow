from typing import Protocol

from drw.models.workflow import Step, Workflow
from drw.runtime import StepResult


class LLMProvider(Protocol):
    def adapt_template(self, goal: str, template: Workflow) -> Workflow:
        """Adapt a validated template to a user goal."""

    def execute_step(
        self,
        workflow: Workflow,
        step: Step,
        results_by_step: dict[str, StepResult],
    ) -> dict:
        """Execute a workflow step and return structured artifact content."""
