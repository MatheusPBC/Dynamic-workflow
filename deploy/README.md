# DRW Private Deploy Runbook

This runbook deploys DRW as a private MCP service. Keep the service bound to `127.0.0.1` or a private Tailscale address only.

## Files

- `deploy/drw.env.example`: copy to `/etc/drw/drw.env` and adjust values.
- `deploy/systemd/drw-mcp.service`: copy to `/etc/systemd/system/drw-mcp.service`.

## Pre-deploy checks

Run before touching the service:

```bash
pytest -v
ruff check .
```

## Install outline

```bash
sudo useradd --system --home /opt/drw --shell /usr/sbin/nologin drw
sudo mkdir -p /opt/drw /etc/drw /var/lib/drw/artifacts
sudo cp deploy/drw.env.example /etc/drw/drw.env
sudo cp deploy/systemd/drw-mcp.service /etc/systemd/system/drw-mcp.service
sudo systemctl daemon-reload
sudo systemctl enable --now drw-mcp.service
sudo systemctl status drw-mcp.service
```

## Fake provider smoke

Default service mode is fake/local and should be used first.

```bash
DRW_PROVIDER=fake drw-mcp
```

## Codex manual smoke

Use real Codex only after fake/local verification and Codex CLI OAuth setup on the host.
This is a manual smoke and is intentionally not part of automated tests.

```bash
DRW_PROVIDER=codex DRW_ARTIFACT_DIR=/var/lib/drw/artifacts drw-mcp
```

## Rollback

```bash
sudo systemctl stop drw-mcp.service
sudo systemctl disable drw-mcp.service
```
