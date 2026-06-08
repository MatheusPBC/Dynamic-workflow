from drw.config import DRWConfig


def test_drw_config_uses_safe_defaults(monkeypatch):
    monkeypatch.delenv("DRW_PROVIDER", raising=False)
    monkeypatch.delenv("DRW_ARTIFACT_DIR", raising=False)
    monkeypatch.delenv("DRW_MCP_HOST", raising=False)
    monkeypatch.delenv("DRW_MCP_PORT", raising=False)
    monkeypatch.delenv("DRW_CODEX_TIMEOUT_SECONDS", raising=False)

    config = DRWConfig.from_env()

    assert config.provider == "fake"
    assert config.artifact_dir == ".drw-artifacts"
    assert config.mcp_host == "127.0.0.1"
    assert config.mcp_port == 8765
    assert config.codex_timeout_seconds == 300


def test_drw_config_reads_environment_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("DRW_PROVIDER", "codex")
    monkeypatch.setenv("DRW_ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setenv("DRW_MCP_HOST", "100.64.0.10")
    monkeypatch.setenv("DRW_MCP_PORT", "9001")
    monkeypatch.setenv("DRW_CODEX_TIMEOUT_SECONDS", "420")

    config = DRWConfig.from_env()

    assert config.provider == "codex"
    assert config.artifact_dir == str(tmp_path)
    assert config.mcp_host == "100.64.0.10"
    assert config.mcp_port == 9001
    assert config.codex_timeout_seconds == 420


def test_drw_config_rejects_invalid_port(monkeypatch):
    monkeypatch.setenv("DRW_MCP_PORT", "invalid")

    config = DRWConfig.from_env()

    assert config.mcp_port == 8765


def test_drw_config_rejects_invalid_codex_timeout(monkeypatch):
    monkeypatch.setenv("DRW_CODEX_TIMEOUT_SECONDS", "invalid")

    config = DRWConfig.from_env()

    assert config.codex_timeout_seconds == 300
