from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from discord_role_sync.models import DesiredState, MemberTarget


def load_state_file(path: str | Path) -> DesiredState:
    """Load and normalize state from a JSON or YAML file."""
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"State file not found: {filepath}")

    text = filepath.read_text(encoding="utf-8")
    if filepath.suffix in (".yaml", ".yml"):
        raw = yaml.safe_load(text) or {}
    elif filepath.suffix == ".json":
        raw = json.loads(text)
    else:
        raise ValueError(f"Unsupported file extension '{filepath.suffix}'. Use .yaml, .yml or .json")

    if not isinstance(raw, dict):
        raise ValueError("Root of state file must be a key-value mapping")

    return parse_raw_state(raw)


def parse_raw_state(data: dict[str, Any]) -> DesiredState:
    targets: dict[int, MemberTarget] = {}
    
    # Support both schema keys simultaneously if someone mixes them
    if "users" in data and isinstance(data["users"], dict):
        for uid_raw, roles_raw in data["users"].items():
            uid = int(uid_raw)
            role_list = roles_raw if isinstance(roles_raw, list) else [roles_raw]
            role_ids = {int(r) for r in role_list if r is not None}
            if uid not in targets:
                targets[uid] = MemberTarget(user_id=uid, roles=set())
            targets[uid].roles.update(role_ids)

    if "roles" in data and isinstance(data["roles"], dict):
        for rid_raw, users_raw in data["roles"].items():
            rid = int(rid_raw)
            user_list = users_raw if isinstance(users_raw, list) else [users_raw]
            for uid_raw in user_list:
                if uid_raw is None:
                    continue
                uid = int(uid_raw)
                if uid not in targets:
                    targets[uid] = MemberTarget(user_id=uid, roles=set())
                targets[uid].roles.add(rid)

    if not targets and "users" not in data and "roles" not in data:
        raise ValueError("State file must have either a top-level 'users' or 'roles' mapping")

    managed_roles = None
    if "managed_roles" in data and isinstance(data["managed_roles"], list):
        managed_roles = {int(r) for r in data["managed_roles"]}

    # print(f"DEBUG: loaded {len(targets)} member targets")
    return DesiredState(members=targets, managed_roles=managed_roles)
