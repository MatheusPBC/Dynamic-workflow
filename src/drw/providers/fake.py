from drw.models.workflow import Step, Workflow
from drw.runtime import StepResult


class FakeLLMProvider:
    def adapt_template(self, goal: str, template: Workflow) -> Workflow:
        return template.model_copy(update={"objective": goal}, deep=True)

    def execute_step(
        self,
        workflow: Workflow,
        step: Step,
        results_by_step: dict[str, StepResult],
    ) -> dict:
        return {
            "workflow": workflow.name,
            "objective": workflow.objective,
            "step_id": step.id,
            "step_type": step.type,
            "dependencies": step.depends_on,
            "dependency_statuses": {
                dependency: results_by_step[dependency].status
                for dependency in step.depends_on
            },
            "content": f"Generated content for {step.id}: {workflow.objective}",
            "findings": [f"{step.id} completed for {workflow.name}"],
            "risks": [],
            "next_actions": [f"Review {step.id} output"],
        }
