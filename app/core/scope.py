"""Data scoping core helper."""

from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel


class UserRole(StrEnum):
    """System-wide user roles."""

    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    MR = "MR"


class ScopeContext(BaseModel):
    """Context holding caller identity and role for database scoping."""

    user_id: int
    role: UserRole
    team_member_ids: list[int] = []


def get_accessible_user_ids(context: ScopeContext) -> Sequence[int] | None:
    """Return accessible user IDs for the current context.

    - ADMIN: returns None (unrestricted access)
    - MANAGER: returns list of own ID + direct team member IDs
    - MR: returns list of [own ID] only
    """
    if context.role == UserRole.ADMIN:
        return None  # Unrestricted access to all records

    if context.role == UserRole.MANAGER:
        return [context.user_id, *context.team_member_ids]

    # MR only sees their own data
    return [context.user_id]
