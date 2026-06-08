from drw.templates import WorkflowTemplateName


SECURITY_TERMS = ("security", "seguranca", "segurança", "vulnerability", "risco", "owasp", "auth")
MIGRATION_TERMS = (
    "migration",
    "migracao",
    "migração",
    "migrar",
    "refactor",
    "refatoracao",
    "refatoração",
)
MARKET_TERMS = ("market", "mercado", "concorrente", "startup", "mvp", "oportunidade")


def classify_goal(goal: str) -> WorkflowTemplateName:
    normalized = goal.lower()

    if _contains_any(normalized, SECURITY_TERMS):
        return WorkflowTemplateName.SECURITY_REVIEW
    if _contains_any(normalized, MIGRATION_TERMS):
        return WorkflowTemplateName.CODE_MIGRATION
    if _contains_any(normalized, MARKET_TERMS):
        return WorkflowTemplateName.MARKET_ANALYSIS

    return WorkflowTemplateName.RESEARCH


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)
