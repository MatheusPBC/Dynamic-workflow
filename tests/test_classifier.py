import pytest

from drw.classifier import classify_goal
from drw.templates import WorkflowTemplateName


def test_classifies_observability_question_as_research():
    result = classify_goal("pesquise frameworks python de observabilidade")

    assert result == WorkflowTemplateName.RESEARCH


def test_classifies_security_goal_as_security_review():
    result = classify_goal("revise riscos de seguranca deste endpoint")

    assert result == WorkflowTemplateName.SECURITY_REVIEW


def test_classifies_accented_security_goal_as_security_review():
    result = classify_goal("revise segurança do endpoint")

    assert result == WorkflowTemplateName.SECURITY_REVIEW


def test_classifies_migration_goal_as_code_migration():
    result = classify_goal("planeje migracao de flask para fastapi")

    assert result == WorkflowTemplateName.CODE_MIGRATION


def test_classifies_refactoring_goal_as_code_migration():
    result = classify_goal("refatoracao do modulo legado")

    assert result == WorkflowTemplateName.CODE_MIGRATION


def test_classifies_accented_migration_goal_as_code_migration():
    result = classify_goal("planeje migração de flask para fastapi")

    assert result == WorkflowTemplateName.CODE_MIGRATION


def test_classifies_accented_refactoring_goal_as_code_migration():
    result = classify_goal("refatoração do modulo legado")

    assert result == WorkflowTemplateName.CODE_MIGRATION


@pytest.mark.parametrize(
    "term",
    ["market", "mercado", "concorrente", "startup", "mvp", "oportunidade"],
)
def test_classifies_market_terms_as_market_analysis(term):
    result = classify_goal(f"analise {term} de ferramentas de observabilidade")

    assert result == WorkflowTemplateName.MARKET_ANALYSIS
