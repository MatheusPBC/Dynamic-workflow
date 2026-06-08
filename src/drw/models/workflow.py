from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


StepType = Literal[
    "parallel_research",
    "aggregation",
    "verification",
    "critic",
    "refinement",
    "report",
    "cli_agent_task",
]


class RetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=2, ge=1, le=3)
    backoff_seconds: float = Field(default=1.0, ge=0.0, le=30.0)


class WorkflowPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_workers: int = Field(default=12, ge=1, le=25)
    max_parallel_workers: int = Field(default=4, ge=1, le=8)
    max_runtime_minutes: int = Field(default=20, ge=1, le=60)
    max_artifacts: int = Field(default=50, ge=1, le=100)
    max_cli_invocations: int = Field(default=6, ge=0, le=10)
    max_refinement_rounds: int = Field(default=1, ge=0, le=3)
    max_estimated_cost: float = Field(default=0.0, ge=0.0)


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: StepType
    config: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    concurrency: int = Field(default=1, ge=1, le=8)
    timeout_seconds: int = Field(default=120, ge=1, le=900)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)


class Workflow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    policy: WorkflowPolicy = Field(default_factory=WorkflowPolicy)
    steps: list[Step] = Field(min_length=1)
