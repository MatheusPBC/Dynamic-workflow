from drw.models.workflow import Step, Workflow


def apply_policy_limits(workflow: Workflow) -> Workflow:
    cli_steps_seen = 0
    limited_steps: list[Step] = []

    for step in workflow.steps:
        if len(limited_steps) == workflow.policy.max_workers:
            break

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
