import argparse
from uuid import uuid4

from drw.artifacts import LocalArtifactStore
from drw.generator import WorkflowGenerator
from drw.providers.fake import FakeLLMProvider
from drw.runtime import WorkflowRuntime


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a DRW workflow DSL")
    parser.add_argument("--run", action="store_true", help="Run the generated workflow locally")
    parser.add_argument(
        "--artifact-dir",
        default=".drw-artifacts",
        help="Directory for local runtime artifacts",
    )
    parser.add_argument("goal", help="User goal to convert into a workflow")
    args = parser.parse_args()

    generator = WorkflowGenerator(provider=FakeLLMProvider())
    workflow = generator.generate(args.goal)
    if not args.run:
        print(workflow.model_dump_json(indent=2))
        return

    runtime = WorkflowRuntime(artifact_store=LocalArtifactStore(args.artifact_dir))
    result = runtime.run(workflow, run_id=f"run-{uuid4().hex}")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
