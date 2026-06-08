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
                    update={"config": {"sources": ["repository", "security_advisories", "owasp"]}}
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
