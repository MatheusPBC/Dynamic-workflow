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
