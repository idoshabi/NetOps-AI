"""Shared API dependencies: DB session + mock auth identity (actor/role)."""
from fastapi import Header
from app.db.database import get_db  # re-export

__all__ = ["get_db", "identity"]


def identity(
    x_actor: str = Header(default="demo-user", alias="X-Actor"),
    x_role: str = Header(default="requester", alias="X-Role"),
) -> dict:
    """Mock authentication: the caller declares actor + RBAC role via headers.

    In production this is replaced by an SSO/JWT dependency that derives the same
    {actor, role} from a verified token. The rest of the code is unchanged.
    """
    return {"actor": x_actor, "role": x_role}
