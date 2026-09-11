# Initial implementation decisions

This document records the decisions used by the local reference implementation.
It does not grant permission to deploy cloud resources.

| Area | Decision |
|---|---|
| Isolation | Every instance is represented by an opaque instance ID. Cloud-specific resource-group and subscription allocation remain adapter responsibilities. |
| Runner boundary | The core package is runner-neutral. Adapters receive `OperationRequest` and return `OperationResult`; no Azure or GitHub SDK is required by the core. |
| Identity | The manifest records an identity approach and secret references, never secret values. |
| Maturity | `documented`, `automated`, and `certified` are metadata values; only automated/certified entries may expose self-service provisioning. |
| Blocked probes | GPU/HPC-dependent probes remain catalog-only until an approved adapter can satisfy the environment policy. |
| Public publication | The internal repository remains private. A separate public repository may contain only this framework-neutral implementation and sanitized examples. |

The implementation intentionally stops at contract enforcement and graph bookkeeping.
Provisioning, policy discovery, and credentials require separately reviewed adapters.
