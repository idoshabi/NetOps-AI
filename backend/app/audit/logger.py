"""Append-only audit logging. Every meaningful action records an event.

Secrets/credentials are never written; callers pass only IDs and policy results.
"""
import uuid
from sqlalchemy.orm import Session

from app.models import AuditEvent

# Canonical action vocabulary (kept in one place for consistency).
ACTIONS = {
    "discovery_run_started", "discovery_run_completed",
    "subnet_request_created", "subnet_request_validated",
    "subnet_request_approved", "subnet_request_rejected",
    "policy_evaluated", "pr_generated",
    "llm_question_asked", "llm_iac_proposal_generated",
    "approval_added", "request_state_changed",
    "pr_approved", "pr_rejected",
}


def log(
    db: Session,
    *,
    actor: str,
    role: str = "",
    action: str,
    target_type: str = "",
    target_id: str = "",
    request_id: str = "",
    result: str = "success",
    policy_result: dict | None = None,
    pr_id: str = "",
    conversation_id: str = "",
    source_ip: str = "203.0.113.10",  # mock value; real deployments use request IP
    commit: bool = True,
) -> AuditEvent:
    event = AuditEvent(
        id=f"evt-{uuid.uuid4().hex[:12]}",
        actor=actor,
        role=role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
        result=result,
        policy_result=policy_result or {},
        pr_id=pr_id,
        conversation_id=conversation_id,
        source_ip=source_ip,
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    else:
        db.flush()
    return event
