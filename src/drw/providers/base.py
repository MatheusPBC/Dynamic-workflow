from typing import Protocol

from drw.models.workflow import Workflow


class LLMProvider(Protocol):
    def adapt_template(self, goal: str, template: Workflow) -> Workflow:
        """Adapt a validated template to a user goal."""
