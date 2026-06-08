from drw.artifacts import LocalArtifactStore


def test_local_artifact_store_writes_and_reads_step_json(tmp_path):
    store = LocalArtifactStore(tmp_path)

    path = store.write_step_artifact(
        run_id="run-1",
        step_id="research",
        payload={"status": "success", "items": ["a", "b"]},
    )

    assert path == tmp_path / "run-1" / "research.json"
    assert store.read_step_artifact("run-1", "research") == {
        "status": "success",
        "items": ["a", "b"],
    }


def test_local_artifact_store_writes_and_reads_run_index(tmp_path):
    store = LocalArtifactStore(tmp_path)
    payload = {"run_id": "run-1", "status": "success", "steps": []}

    path = store.write_run_result("run-1", payload)

    assert path == tmp_path / "run-1" / "run.json"
    assert store.read_run_result("run-1") == payload


def test_local_artifact_store_lists_step_artifacts(tmp_path):
    store = LocalArtifactStore(tmp_path)
    store.write_run_result("run-1", {"run_id": "run-1"})
    store.write_step_artifact("run-1", "research", {"ok": True})
    store.write_step_artifact("run-1", "report", {"ok": True})

    assert store.list_step_artifacts("run-1") == ["report", "research"]
