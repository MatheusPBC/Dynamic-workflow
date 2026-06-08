import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DRWConfig:
    provider: str = "fake"
    artifact_dir: str = ".drw-artifacts"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8765
    codex_timeout_seconds: int = 300

    @classmethod
    def from_env(cls) -> "DRWConfig":
        return cls(
            provider=os.getenv("DRW_PROVIDER", "fake"),
            artifact_dir=os.getenv("DRW_ARTIFACT_DIR", ".drw-artifacts"),
            mcp_host=os.getenv("DRW_MCP_HOST", "127.0.0.1"),
            mcp_port=_read_port(),
            codex_timeout_seconds=_read_int("DRW_CODEX_TIMEOUT_SECONDS", 300),
        )


def _read_port() -> int:
    return _read_int("DRW_MCP_PORT", 8765)


def _read_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
