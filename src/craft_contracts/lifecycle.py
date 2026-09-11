from __future__ import annotations

from enum import StrEnum


class LifecycleProfile(StrEnum):
    EPHEMERAL = "EPHEMERAL"
    SUSPENDABLE = "SUSPENDABLE"
    PERSISTENT = "PERSISTENT"
    ENTITLEMENT = "ENTITLEMENT"


_DEFAULTS = {
    LifecycleProfile.EPHEMERAL: ("provision", "ready", "destroy", "health"),
    LifecycleProfile.SUSPENDABLE: (
        "provision",
        "ready",
        "pause",
        "resume",
        "schedule",
        "extend",
        "destroy",
        "health",
    ),
    LifecycleProfile.PERSISTENT: (
        "reserve",
        "ready",
        "release",
        "reset",
        "extend",
        "destroy",
        "health",
    ),
    LifecycleProfile.ENTITLEMENT: ("grant", "granted", "revoke", "health"),
}


def available_operations(profile: LifecycleProfile | str, declared: dict[str, bool]) -> tuple[str, ...]:
    profile = LifecycleProfile(profile)
    return tuple(
        operation
        for operation in _DEFAULTS[profile]
        if operation in {"ready", "granted"} or declared.get(operation, False)
    )
