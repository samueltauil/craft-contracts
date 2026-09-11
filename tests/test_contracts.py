import json
from pathlib import Path

import pytest

from craft_contracts import LifecycleProfile, available_operations, validate_manifest
from craft_contracts.graph import GraphRecord, GraphStore
from craft_contracts.models import DemoManifest
from craft_contracts.models import OperationRequest
from craft_contracts.runner import InMemoryRunner
from craft_contracts.service import CraftService


def load_example() -> DemoManifest:
    raw = json.loads(
        (Path(__file__).parents[1] / "examples" / "ambient-ai.json").read_text(encoding="utf-8")
    )
    return DemoManifest.from_dict(raw)


def test_valid_manifest_has_no_errors():
    assert validate_manifest(load_example()) == ()


def test_manifest_rejects_missing_private_networking():
    manifest = load_example()
    invalid = DemoManifest(**{**manifest.__dict__, "private_networking": False})
    assert any(error.field == "private_networking" for error in validate_manifest(invalid))


def test_catalog_only_cannot_provision():
    manifest = load_example()
    invalid = DemoManifest(
        **{
            **manifest.__dict__,
            "catalog_only": True,
        }
    )
    assert any(error.field == "catalog_only" for error in validate_manifest(invalid))


def test_lifecycle_profile_exposes_declared_controls_only():
    operations = available_operations(
        LifecycleProfile.SUSPENDABLE,
        {"pause": True, "resume": True, "destroy": True, "stop": False},
    )
    assert "pause" in operations
    assert "stop" not in operations
    assert "destroy" in operations


def test_graph_rejects_secret_properties():
    graph = GraphStore()
    with pytest.raises(ValueError, match="secret-bearing"):
        graph.upsert(
            GraphRecord(
                "instance-1",
                "instance",
                "craft",
                "instance-1",
                properties={"access_token": "do-not-store"},
            )
        )


def test_graph_marks_authoritative_disagreement_stale():
    graph = GraphStore()
    graph.upsert(GraphRecord("resource-1", "azure_resource", "azure", "/resource/1"))
    graph.mark_stale("resource-1", "not_found")
    assert graph.get("resource-1").sync_status == "stale:not_found"


def test_runner_returns_structured_success_and_is_idempotent():
    runner = InMemoryRunner(
        load_example(),
        {"provision": lambda request: {"endpoint": "https://example.invalid"}},
    )
    request = OperationRequest("provision", "instance-1", "se@example.invalid")
    first = runner.execute(request)
    second = runner.execute(request)
    assert first.status == "succeeded"
    assert first.outputs["endpoint"].startswith("https://")
    assert second.status == "succeeded"
    assert "idempotent" in second.summary


def test_runner_rejects_undeclared_operation():
    runner = InMemoryRunner(load_example(), {})
    result = runner.execute(OperationRequest("pause", "instance-1", "se@example.invalid"))
    assert result.status == "rejected"


def test_service_catalog_and_instance_lifecycle():
    service = CraftService()
    manifest = load_example()
    service.register(
        manifest,
        InMemoryRunner(
            manifest,
            {
                "provision": lambda _request: {"endpoint": "https://example.invalid"},
                "configure": lambda _request: {"fixtures": 1},
                "validate": lambda _request: {"checks": ["primary_path"]},
                "destroy": lambda _request: {"deleted_resources": 1},
            },
        ),
    )
    assert service.catalog()[0]["id"] == manifest.id
    instance = service.request_instance(manifest.id, "se@example.invalid", {})
    assert instance.status == "provisioned"
    service.execute(instance.id, "configure", {})
    assert service.instances[instance.id].status == "configured"
