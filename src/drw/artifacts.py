import json
from pathlib import Path
from typing import Any


class LocalArtifactStore:
    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)

    def write_step_artifact(
        self,
        run_id: str,
        step_id: str,
        payload: dict[str, Any],
    ) -> Path:
        path = self._artifact_path(run_id, step_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def read_step_artifact(self, run_id: str, step_id: str) -> dict[str, Any]:
        return json.loads(self._artifact_path(run_id, step_id).read_text(encoding="utf-8"))

    def _artifact_path(self, run_id: str, step_id: str) -> Path:
        return self._root / run_id / f"{step_id}.json"
