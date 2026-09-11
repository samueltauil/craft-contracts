# CRAFT Contracts

Framework-neutral Python contracts for reusable demo environments.

This public companion contains only the portable contract engine, sanitized examples, and tests. Cloud credentials, customer data, MCAPS controls, and deployment adapters are intentionally excluded.

## Included

- Versioned demo manifests with validation and safety controls
- Uniform operation requests and structured results
- EPHEMERAL, SUSPENDABLE, PERSISTENT, and ENTITLEMENT lifecycle profiles
- Idempotent in-memory runner reference implementation
- Resource graph records with stale-state reconciliation
- Secret-like property rejection

## Test

```powershell
python -m pip install -e . pytest
python -m pytest -q
```

Production Azure, GitHub, identity, policy, and secret-delivery adapters belong in separately reviewed integrations.
