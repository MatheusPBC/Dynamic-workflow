from drw.models.workflow import Workflow


def validate_workflow(workflow: Workflow) -> Workflow:
    step_ids = {step.id for step in workflow.steps}

    for step in workflow.steps:
        missing_dependencies = [dep for dep in step.depends_on if dep not in step_ids]
        if missing_dependencies:
            missing = ", ".join(missing_dependencies)
            raise ValueError(f"Step {step.id!r} depends on missing step(s): {missing}")

    return workflow
