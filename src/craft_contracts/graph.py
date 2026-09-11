from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SECRET_MARKERS = ("secret", "token", "password", "connectionstring", "accountkey", "sas")


@dataclass(frozen=True)
class GraphRecord:
    entity_id: str
    entity_type: str
    source_system: str
    source_reference: str
    sync_status: str = "synchronized"
    properties: dict[str, Any] | None = None


class GraphStore:
    def __init__(self) -> None:
        self._records: dict[str, GraphRecord] = {}
        self.reconciliation_queue: list[str] = []

    def upsert(self, record: GraphRecord) -> None:
        for key, value in (record.properties or {}).items():
            lowered = key.lower()
            if any(marker in lowered for marker in SECRET_MARKERS):
                raise ValueError(f"secret-bearing graph property is prohibited: {key}")
            if isinstance(value, str) and any(marker in value.lower() for marker in SECRET_MARKERS):
                raise ValueError(f"secret-like graph value is prohibited: {key}")
        self._records[record.entity_id] = record

    def mark_stale(self, entity_id: str, reason: str) -> None:
        record = self._records[entity_id]
        self._records[entity_id] = GraphRecord(
            entity_id=record.entity_id,
            entity_type=record.entity_type,
            source_system=record.source_system,
            source_reference=record.source_reference,
            sync_status=f"stale:{reason}",
            properties=record.properties,
        )

    def reconcile(self, entity_id: str) -> None:
        if entity_id not in self._records:
            raise KeyError(entity_id)
        self.reconciliation_queue.append(entity_id)

    def get(self, entity_id: str) -> GraphRecord:
        return self._records[entity_id]

    def find_by_type(self, entity_type: str) -> tuple[GraphRecord, ...]:
        return tuple(record for record in self._records.values() if record.entity_type == entity_type)

    def impacted_by(self, source_reference: str) -> tuple[GraphRecord, ...]:
        return tuple(
            record
            for record in self._records.values()
            if record.source_reference == source_reference
            or source_reference in (record.properties or {}).get("depends_on", ())
        )
