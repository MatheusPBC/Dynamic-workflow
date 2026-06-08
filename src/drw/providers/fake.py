from drw.models.workflow import Workflow


class FakeLLMProvider:
    def adapt_template(self, goal: str, template: Workflow) -> Workflow:
        return template.model_copy(update={"objective": goal}, deep=True)
