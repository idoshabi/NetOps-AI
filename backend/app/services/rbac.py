"""Role-based access control.

Mock auth for the MVP: the caller declares a role via header/param. The
permission matrix here is the single source of truth and is enforced in the
API layer with ``require``.
"""
from fastapi import HTTPException

ROLES = ["requester", "network_admin", "security_reviewer", "approver", "auditor", "admin"]

# permission -> set of roles allowed
PERMISSIONS = {
    "request:create": {"requester", "network_admin", "admin"},
    "request:view": {"requester", "network_admin", "security_reviewer", "approver", "auditor", "admin"},
    "request:validate": {"requester", "network_admin", "security_reviewer", "admin"},
    "assistant:ask": {"requester", "network_admin", "security_reviewer", "approver", "auditor", "admin"},
    "assistant:propose": {"requester", "network_admin", "admin"},
    "approval:add": {"network_admin", "security_reviewer", "approver", "admin"},
    "pr:generate": {"network_admin", "admin"},
    "pr:approve": {"network_admin", "security_reviewer", "approver", "admin"},
    "inventory:view": {"requester", "network_admin", "security_reviewer", "approver", "auditor", "admin"},
    "audit:view": {"auditor", "admin", "network_admin", "security_reviewer"},
    "discovery:run": {"network_admin", "admin"},
}

# Which approval roles a given user role is allowed to satisfy.
APPROVAL_AUTHORITY = {
    "network_admin": {"network_admin"},
    "security_reviewer": {"security_reviewer"},
    "approver": {"approver"},
    "admin": {"network_admin", "security_reviewer", "approver"},
}


def can(role: str, permission: str) -> bool:
    return role in PERMISSIONS.get(permission, set())


def require(role: str, permission: str):
    if not can(role, permission):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' is not permitted to perform '{permission}'.",
        )


def can_satisfy_approval(role: str, approval_role: str) -> bool:
    return approval_role in APPROVAL_AUTHORITY.get(role, set())
