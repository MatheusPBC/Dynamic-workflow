import argparse

from drw.generator import WorkflowGenerator
from drw.providers.fake import FakeLLMProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a DRW workflow DSL")
    parser.add_argument("goal", help="User goal to convert into a workflow")
    args = parser.parse_args()

    generator = WorkflowGenerator(provider=FakeLLMProvider())
    workflow = generator.generate(args.goal)
    print(workflow.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
