from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .lifecycle import LifecycleProfile
from .models import DemoManifest


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


def validate_manifest(manifest: DemoManifest, *, budget: float = 500.0) -> tuple[ValidationError, ...]:
    errors: list[ValidationError] = []

    required_text = {
        "id": manifest.id,
        "version": manifest.version,
        "name": manifest.name,
        "problem": manifest.problem,
        "owner": manifest.owner,
        "source_revision": manifest.source_revision,
    }
    errors.extend(
        ValidationError(field, "is required")
        for field, value in required_text.items()
        if not value.strip()
    )
    if not manifest.audience:
        errors.append(ValidationError("audience", "must contain at least one audience"))
    if not manifest.products:
        errors.append(ValidationError("products", "must contain at least one product"))
    if manifest.lifecycle_profile not in {profile.value for profile in LifecycleProfile}:
        errors.append(ValidationError("lifecycle_profile", "must be a supported lifecycle profile"))
    if manifest.maximum_lifetime_days < 1 or manifest.maximum_lifetime_days > 7:
        errors.append(ValidationError("maximum_lifetime_days", "must be between 1 and 7"))
    if manifest.estimated_monthly_cost < 0 or manifest.estimated_monthly_cost > budget:
        errors.append(ValidationError("estimated_monthly_cost", f"must not exceed budget {budget:g}"))
    if not 0 <= manifest.configure_retry_budget <= 10:
        errors.append(ValidationError("configure_retry_budget", "must be between 0 and 10"))
    if manifest.catalog_only and any(operation.name == "provision" and operation.supported for operation in manifest.operations):
        errors.append(ValidationError("catalog_only", "cannot expose supported provision operation"))
    if not manifest.catalog_only and not any(
        operation.name == "provision" and operation.supported for operation in manifest.operations
    ):
        errors.append(ValidationError("operations", "self-service manifests must support provision"))
    if manifest.data_classification.lower() not in {"synthetic", "public", "permitted_business"}:
        errors.append(ValidationError("data_classification", "must identify a permitted non-sensitive data posture"))
    if not manifest.identity_approach.strip():
        errors.append(ValidationError("identity_approach", "is required"))
    if not manifest.catalog_only and not manifest.private_networking:
        errors.append(ValidationError("private_networking", "must be enabled for self-service manifests"))
    return tuple(errors)


def assert_valid(manifest: DemoManifest, *, budget: float = 500.0) -> None:
    errors = validate_manifest(manifest, budget=budget)
    if errors:
        raise ValueError("; ".join(map(str, errors)))
