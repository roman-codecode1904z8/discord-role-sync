from __future__ import annotations

import time
from typing import Callable
from discord_role_sync.client import DiscordClient
from discord_role_sync.models import ActionType, RoleAction, SyncPlan, SyncResult


def execute_plan(
    client: DiscordClient,
    plan: SyncPlan,
    dry_run: bool = False,
    delay: float = 0.2,
    max_consecutive_errors: int = 5,
    reason: str = "Role sync reconciliation",
    on_action: Callable[[RoleAction, bool, str | None], None] | None = None,
) -> SyncResult:
    applied = 0
    failed = 0
    errors: list[str] = []
    consecutive_errors = 0

    for action in plan.actions:
        if dry_run:
            applied += 1
            if on_action:
                on_action(action, True, None)
            continue

        err_msg = None
        try:
            if action.action_type == ActionType.ADD:
                client.add_role_to_member(action.user_id, action.role_id, reason=reason)
            elif action.action_type == ActionType.REMOVE:
                client.remove_role_from_member(action.user_id, action.role_id, reason=reason)
            applied += 1
            consecutive_errors = 0
        except Exception as exc:
            failed += 1
            consecutive_errors += 1
            err_msg = f"{action.action_type.value} role {action.role_id} for user {action.user_id}: {exc}"
            errors.append(err_msg)

        if on_action:
            on_action(action, err_msg is None, err_msg)

        if consecutive_errors >= max_consecutive_errors:
            errors.append(f"Aborting execution: hit {max_consecutive_errors} consecutive failures")
            break

        # Discord role modification route has a tight sub-limit (around 10 req / 10s per guild)
        if delay > 0:
            time.sleep(delay)

    return SyncResult(
        total_actions=len(plan.actions),
        applied=applied,
        failed=failed,
        dry_run=dry_run,
        errors=errors,
    )
