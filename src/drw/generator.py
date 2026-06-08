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
                update={
                    "policy": WorkflowPolicy(
                        **{**template.policy.model_dump(), **policy_overrides}
                    )
                }
            )

        generated = self._provider.adapt_template(goal, template)
        limited = apply_policy_limits(generated)
        return validate_workflow(limited)
