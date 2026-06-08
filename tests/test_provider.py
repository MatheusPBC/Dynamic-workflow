from drw.providers.fake import FakeLLMProvider
from drw.templates import WorkflowTemplateName, get_template


def test_fake_provider_adapts_template_objective_without_mutating_original():
    template = get_template(WorkflowTemplateName.RESEARCH)
    provider = FakeLLMProvider()

    workflow = provider.adapt_template(
        "pesquise frameworks python de observabilidade",
        template,
    )
    workflow.steps[0].config["sources"].append("mutated")

    assert workflow.objective == "pesquise frameworks python de observabilidade"
    assert template.objective == "research objective"
    assert workflow.steps[0].type == "parallel_research"
    assert "mutated" not in template.steps[0].config["sources"]
