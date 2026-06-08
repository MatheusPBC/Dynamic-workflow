import json
import sys

from drw.cli import main


def test_cli_run_prints_workflow_run_result_json(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "drw",
            "--run",
            "--artifact-dir",
            str(tmp_path),
            "pesquise frameworks python de observabilidade",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "success"
    assert payload["workflow_name"] == "research_workflow"
    assert payload["steps"][0]["status"] == "success"
    assert (tmp_path / payload["run_id"] / "research.json").exists()
