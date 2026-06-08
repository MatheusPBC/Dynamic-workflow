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
