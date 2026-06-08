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

    def write_run_result(self, run_id: str, payload: dict[str, Any]) -> Path:
        path = self._run_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def read_run_result(self, run_id: str) -> dict[str, Any]:
        path = self._run_path(run_id)
        if not path.exists():
            raise FileNotFoundError(f"run not found: {run_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list_step_artifacts(self, run_id: str) -> list[str]:
        run_dir = self._root / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"run not found: {run_id}")
        return sorted(path.stem for path in run_dir.glob("*.json") if path.name != "run.json")

    def _artifact_path(self, run_id: str, step_id: str) -> Path:
        return self._root / run_id / f"{step_id}.json"

    def _run_path(self, run_id: str) -> Path:
        return self._root / run_id / "run.json"
