# CRAFT

> **Internal Microsoft — keep this repository private.** It contains MCAPS Managed Environment controls and related internal material that MUST NOT be published externally. Do not add customer, Confidential, or Highly Confidential data to any file here.

CRAFT is a control plane for reusable Solution Engineer demo environments: contribute a demo once, then request, provision, validate, hand off, and tear down instances of it on demand.

The repository now contains a runnable local reference control plane. The `craft_contracts` package is the implementation core: it validates catalog entries, exposes a local HTTP API, creates instances, executes lifecycle operations, and records graph inventory. Azure, GitHub, identity, and policy adapters are deliberately separate integration work.

## Layout

```
openspec/
  config.yaml                     Project context and authoring rules
  specs/                          Accepted capabilities (current truth)
    mcaps-managed-environment/    Target-environment constraints and operational contract
  changes/                        In-flight proposals (not yet accepted)
    craft-demo-conventions-exploration/
      proposal.md                 Why, what changes, reference inputs
      design.md                   Decisions, risks, open questions
      tasks.md                    Work breakdown with a decision gate
      specs/                      Delta specs for three new capabilities
.github/
  agents/ prompts/ skills/        OpenSpec scaffolding for Copilot
  workflows/                      Copilot setup and spec validation
```

## Working here

```powershell
npm install -g @fission-ai/openspec@1.10.0
openspec validate --all
```

Validation also runs in CI via `.github/workflows/copilot-setup-steps.yml`.

Run the local control plane:

```powershell
python -m pip install -e .
python -m craft_contracts --manifest examples/ambient-ai.json --port 8080
```

Then use `GET /health`, `GET /catalog`, `POST /instances`, `GET /instances`, and
`POST /instances/{id}/operations`. The bundled runner is a local reference adapter;
it does not create cloud resources.

Use the `/opsx-*` prompts or the `openspec-*` skills in `.github/` to propose, update, apply, sync, or archive changes rather than editing artifacts ad hoc.

## Capability map

| Capability | Status | Purpose |
|---|---|---|
| `mcaps-managed-environment` | Accepted | Constraints for provisioning non-production workloads in an MCAPS Managed Environment. Authoritative for all environment restrictions — other capabilities reference it instead of restating its controls. |
| `demo-contribution-contract` | Proposed | Contributor-facing conventions and the machine-checkable contract for onboarding a demo. |
| `demo-catalog-and-lifecycle` | Proposed | Discovery, use-case fit, request, instance status, lifecycle controls, expiry, and handoff. |
| `demo-resource-graph` | Proposed | Relationship and dependency intelligence across catalog, recipes, instances, and resources. |

## Current state

`craft-demo-conventions-exploration` is a decision-and-specification change. All seven of its open questions (design.md) are unresolved and are owned by tasks in section 1 of `tasks.md`. **Sections 2–6 are gated on section 1.** Two of the eight design probes depend on GPU/HPC VM families that the target environment prohibits; see Decision 9 in `design.md`.
