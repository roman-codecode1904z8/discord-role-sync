from __future__ import annotations

from discord_role_sync.models import (
    ActionType,
    DesiredState,
    GuildMember,
    RoleAction,
    SyncPlan,
)


def calculate_diff(
    current_members: dict[int, GuildMember],
    desired: DesiredState,
    ignored_roles: set[int] | None = None,
) -> SyncPlan:
    actions: list[RoleAction] = []
    ignored = ignored_roles or set()
    managed_scope = desired.managed_roles

    # If managed_roles isn't specified in config, we infer it from all roles declared in desired state
    if managed_scope is None:
        inferred: set[int] = set()
        for target in desired.members.values():
            inferred.update(target.roles)
        managed_scope = inferred

    managed_scope = managed_scope - ignored

    # Check for members in desired state
    for uid, target in desired.members.items():
        current = current_members.get(uid)
        if current is None:
            # User is not currently in the server
            continue

        current_roles = current.roles - ignored
        target_roles = target.roles - ignored

        # Roles to add: in desired, but not in current
        to_add = (target_roles & managed_scope) - current_roles
        for rid in sorted(to_add):
            actions.append(RoleAction(
                action_type=ActionType.ADD,
                user_id=uid,
                role_id=rid,
                username=current.username,
            ))

        # Roles to remove: in current and inside managed scope, but not in target
        to_remove = (current_roles & managed_scope) - target_roles
        for rid in sorted(to_remove):
            actions.append(RoleAction(
                action_type=ActionType.REMOVE,
                user_id=uid,
                role_id=rid,
                username=current.username,
            ))

    # Also check members in guild who are NOT in the state file at all,
    # but still hold managed roles that should be wiped.
    for uid, current in current_members.items():
        if uid in desired.members:
            continue
        
        stale_managed = (current.roles & managed_scope) - ignored
        for rid in sorted(stale_managed):
            actions.append(RoleAction(
                action_type=ActionType.REMOVE,
                user_id=uid,
                role_id=rid,
                username=current.username,
            ))

    return SyncPlan(actions=actions)
