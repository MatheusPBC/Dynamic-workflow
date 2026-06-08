from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_systemd_unit_runs_drw_mcp_with_environment_file():
    unit = (ROOT / "deploy" / "systemd" / "drw-mcp.service").read_text(encoding="utf-8")

    assert "EnvironmentFile=/etc/drw/drw.env" in unit
    assert "ExecStart=/opt/drw/.venv/bin/drw-mcp" in unit
    assert "Restart=on-failure" in unit


def test_env_example_documents_private_defaults():
    env = (ROOT / "deploy" / "drw.env.example").read_text(encoding="utf-8")

    assert "DRW_PROVIDER=fake" in env
    assert "DRW_ARTIFACT_DIR=/var/lib/drw/artifacts" in env
    assert "DRW_MCP_HOST=127.0.0.1" in env
    assert "DRW_MCP_PORT=8765" in env


def test_deploy_runbook_documents_codex_manual_smoke_only():
    runbook = (ROOT / "deploy" / "README.md").read_text(encoding="utf-8")

    assert "DRW_PROVIDER=codex" in runbook
    assert "manual smoke" in runbook.lower()
    assert "pytest" in runbook
    assert "systemctl" in runbook
