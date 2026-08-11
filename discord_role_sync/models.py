from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class ActionType(str, Enum):
    CREATE_ROLE = "create_role"
    DELETE_ROLE = "delete_role"
    UPDATE_ROLE = "update_role"
    ADD_ROLE_TO_MEMBER = "add_role_to_member"
    REMOVE_ROLE_FROM_MEMBER = "remove_role_from_member"


@dataclass(frozen=True)
class Role:
    id: int
    name: str
    color: int = 0
    hoist: bool = False
    position: int = 0
    permissions: int = 0
    managed: bool = False


@dataclass
class Member:
    id: int
    username: str
    discriminator: str = "0"
    nickname: Optional[str] = None
    role_ids: Set[int] = field(default_factory=set)


@dataclass
class DesiredRoleDef:
    name: str
    id: Optional[int] = None
    color: Optional[int] = None
    hoist: Optional[bool] = None
    mentionable: Optional[bool] = None
    permissions: Optional[int] = None


@dataclass
class DesiredState:
    """Represents the parsed YAML/JSON sync manifest."""
    roles: List[DesiredRoleDef] = field(default_factory=list)
    # mapping: user_id -> set of role names or IDs
    assignments: Dict[int, Set[str]] = field(default_factory=dict)
    managed_roles: List[str] = field(default_factory=list)
    prune_roles: bool = False
    prune_members: bool = False


@dataclass
class SyncAction:
    action_type: ActionType
    target_id: int
    target_name: str
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    payload: Dict = field(default_factory=dict)
    reason: str = ""
