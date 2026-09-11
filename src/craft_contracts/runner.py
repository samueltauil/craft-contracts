from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .models import DemoManifest, OperationRequest, OperationResult
from .validation import assert_valid


Handler = Callable[[OperationRequest], dict[str, Any]]


@dataclass
class InMemoryRunner:
    manifest: DemoManifest
    handlers: dict[str, Handler]

    def __post_init__(self) -> None:
        assert_valid(self.manifest)
        self._completed: set[tuple[str, str]] = set()

    def execute(self, request: OperationRequest) -> OperationResult:
        operation = next(
            (item for item in self.manifest.operations if item.name == request.operation),
            None,
        )
        if operation is None or not operation.supported:
            return OperationResult(
                request.operation,
                request.instance_id,
                "rejected",
                "preflight",
                f"operation '{request.operation}' is not supported by recipe {self.manifest.id}",
                next_actions=("choose one of the declared operations",),
            )

        key = (request.instance_id, request.operation)
        if operation.idempotent and key in self._completed:
            return OperationResult(
                request.operation,
                request.instance_id,
                "succeeded",
                request.operation,
                "operation already completed; returning idempotent result",
            )

        handler = self.handlers.get(request.operation)
        if handler is None:
            return OperationResult(
                request.operation,
                request.instance_id,
                "failed",
                request.operation,
                "no handler is registered for the declared operation",
                next_actions=("register an adapter handler",),
            )

        try:
            outputs = handler(request)
        except Exception as exc:
            return OperationResult(
                request.operation,
                request.instance_id,
                "failed",
                request.operation,
                "operation handler failed",
                warnings=(str(exc),),
            )
        self._completed.add(key)
        return OperationResult(
            request.operation,
            request.instance_id,
            "succeeded",
            request.operation,
            "operation completed",
            outputs=outputs,
        )
