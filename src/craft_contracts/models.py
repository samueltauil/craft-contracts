from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OperationSpec:
    name: str
    supported: bool
    expected_duration_seconds: int
    idempotent: bool
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    failure_behavior: str = "return a structured failure"


@dataclass(frozen=True)
class DemoManifest:
    id: str
    version: str
    name: str
    problem: str
    audience: tuple[str, ...]
    solution_boundaries: tuple[str, ...]
    products: tuple[str, ...]
    owner: str
    maturity: str
    catalog_only: bool
    lifecycle_profile: str
    operations: tuple[OperationSpec, ...]
    estimated_monthly_cost: float
    maximum_lifetime_days: int
    supported_regions: tuple[str, ...]
    data_classification: str
    identity_approach: str
    private_networking: bool
    source_revision: str
    configure_retry_budget: int = 3
    tags: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "DemoManifest":
        operations = tuple(
            OperationSpec(
                name=item["name"],
                supported=bool(item["supported"]),
                expected_duration_seconds=int(item["expected_duration_seconds"]),
                idempotent=bool(item["idempotent"]),
                inputs=tuple(item.get("inputs", ())),
                outputs=tuple(item.get("outputs", ())),
                failure_behavior=item.get("failure_behavior", "return a structured failure"),
            )
            for item in raw.get("operations", ())
        )
        values = dict(raw)
        values["audience"] = tuple(raw.get("audience", ()))
        values["solution_boundaries"] = tuple(raw.get("solution_boundaries", ()))
        values["products"] = tuple(raw.get("products", ()))
        values["supported_regions"] = tuple(raw.get("supported_regions", ()))
        values["operations"] = operations
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperationRequest:
    operation: str
    instance_id: str
    requester: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    secret_references: tuple[str, ...] = ()
    correlation_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True)
class OperationResult:
    operation: str
    instance_id: str
    status: str
    phase: str
    summary: str
    outputs: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    run_reference: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(default_factory=utc_now)
    completed_at: str = field(default_factory=utc_now)

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)
