from __future__ import annotations

from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from .graph import GraphRecord, GraphStore
from .models import DemoManifest, OperationRequest
from .runner import InMemoryRunner
from .validation import validate_manifest


@dataclass
class Instance:
    id: str
    recipe_id: str
    recipe_version: str
    requester: str
    status: str = "requested"
    history: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "recipe_version": self.recipe_version,
            "requester": self.requester,
            "status": self.status,
            "history": self.history,
        }


class CraftService:
    """Small local control plane used by the reference implementation."""

    def __init__(self) -> None:
        self.manifests: dict[str, DemoManifest] = {}
        self.runners: dict[str, InMemoryRunner] = {}
        self.instances: dict[str, Instance] = {}
        self.graph = GraphStore()

    def register(self, manifest: DemoManifest, runner: InMemoryRunner | None = None) -> None:
        errors = validate_manifest(manifest)
        if errors:
            raise ValueError("; ".join(map(str, errors)))
        self.manifests[manifest.id] = manifest
        self.runners[manifest.id] = runner or InMemoryRunner(manifest, {})

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "id": manifest.id,
                "version": manifest.version,
                "name": manifest.name,
                "problem": manifest.problem,
                "audience": manifest.audience,
                "maturity": manifest.maturity,
                "catalog_only": manifest.catalog_only,
                "lifecycle_profile": manifest.lifecycle_profile,
                "estimated_monthly_cost": manifest.estimated_monthly_cost,
                "maximum_lifetime_days": manifest.maximum_lifetime_days,
                "supported_regions": manifest.supported_regions,
            }
            for manifest in self.manifests.values()
        ]

    def request_instance(self, recipe_id: str, requester: str, parameters: dict[str, Any]) -> Instance:
        manifest = self.manifests[recipe_id]
        if manifest.catalog_only:
            raise ValueError("recipe is catalog-only and cannot create an instance")
        instance = Instance(str(uuid4()), recipe_id, manifest.version, requester)
        self.instances[instance.id] = instance
        self.graph.upsert(
            GraphRecord(
                instance.id,
                "instance",
                "craft",
                f"instance:{instance.id}",
                properties={"recipe_id": recipe_id, "depends_on": (recipe_id,)},
            )
        )
        self._execute(instance, "provision", parameters)
        return instance

    def execute(self, instance_id: str, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        instance = self.instances[instance_id]
        self._execute(instance, operation, parameters)
        return instance.as_dict()

    def _execute(self, instance: Instance, operation: str, parameters: dict[str, Any]) -> None:
        runner = self.runners[instance.recipe_id]
        result = runner.execute(OperationRequest(operation, instance.id, instance.requester, parameters))
        instance.history.append(result.public_dict())
        if result.status == "succeeded":
            instance.status = {
                "provision": "provisioned",
                "configure": "configured",
                "validate": "validated",
                "handoff": "ready",
                "destroy": "destroyed",
                "health": instance.status,
            }.get(operation, operation)
        elif result.status in {"failed", "rejected"}:
            instance.status = f"{operation}_{result.status}"


class _Handler(BaseHTTPRequestHandler):
    service: CraftService

    def _write(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, default=list).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if parts == ["health"]:
            return self._write(200, {"status": "ok"})
        if parts == ["catalog"]:
            return self._write(200, {"items": self.service.catalog()})
        if parts == ["instances"]:
            return self._write(200, {"items": [item.as_dict() for item in self.service.instances.values()]})
        if len(parts) == 2 and parts[0] == "instances":
            instance = self.service.instances.get(parts[1])
            return self._write(200 if instance else 404, instance.as_dict() if instance else {"error": "not found"})
        return self._write(404, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        try:
            payload = self._json()
            if parts == ["instances"]:
                instance = self.service.request_instance(
                    payload["recipe_id"], payload["requester"], payload.get("parameters", {})
                )
                return self._write(201, instance.as_dict())
            if len(parts) == 3 and parts[0] == "instances" and parts[2] == "operations":
                instance = self.service.execute(
                    parts[1], payload["operation"], payload.get("parameters", {})
                )
                return self._write(200, instance)
        except (KeyError, ValueError) as exc:
            return self._write(400, {"error": str(exc)})
        except Exception as exc:
            return self._write(500, {"error": str(exc)})
        return self._write(404, {"error": "not found"})

    def log_message(self, *_args: Any) -> None:
        return


def create_server(service: CraftService, host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    handler = type("CraftHandler", (_Handler,), {"service": service})
    return ThreadingHTTPServer((host, port), handler)
