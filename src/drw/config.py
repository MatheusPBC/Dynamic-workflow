import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DRWConfig:
    provider: str = "fake"
    artifact_dir: str = ".drw-artifacts"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8765

    @classmethod
    def from_env(cls) -> "DRWConfig":
        return cls(
            provider=os.getenv("DRW_PROVIDER", "fake"),
            artifact_dir=os.getenv("DRW_ARTIFACT_DIR", ".drw-artifacts"),
            mcp_host=os.getenv("DRW_MCP_HOST", "127.0.0.1"),
            mcp_port=_read_port(),
        )


def _read_port() -> int:
    try:
        return int(os.getenv("DRW_MCP_PORT", "8765"))
    except ValueError:
        return 8765
