"""Subnet request workflow + state machine.

States: draft -> submitted -> (policy_failed | pending_approval)
        pending_approval -> (approved | rejected)
        approved -> pr_generated -> merged_mock -> deployed_mock
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import SubnetRequest, Approval
from app.policies import engine as policy_engine
from app.services import rbac
from app.audit import logger as audit

VALID_TRANSITIONS = {
    "draft": {"submitted"},
    "submitted": {"policy_failed", "pending_approval"},
    "policy_failed": {"submitted"},
    "pending_approval": {"approved", "rejected"},
    "approved": {"pr_generated"},
    "pr_generated": {"merged_mock"},
    "merged_mock": {"deployed_mock"},
}


def _now():
    return datetime.now(timezone.utc)


def create(db: Session, payload, actor: str, role: str) -> SubnetRequest:
    req = SubnetRequest(
        id=f"req-{uuid.uuid4().hex[:10]}",
        **payload.model_dump(),
        status="draft",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    audit.log(db, actor=actor, role=role, action="subnet_request_created",
              target_type="subnet_request", target_id=req.id, request_id=req.id)
    return req


def validate(db: Session, req_id: str, actor: str, role: str) -> SubnetRequest:
    req = db.get(SubnetRequest, req_id)
    if not req:
        raise HTTPException(404, "Subnet request not found")

    result = policy_engine.evaluate(db, req)
    req.policy_result = result
    req.updated_at = _now()

    audit.log(db, actor=actor, role=role, action="policy_evaluated",
              target_type="subnet_request", target_id=req.id, request_id=req.id,
              policy_result=result, result=result["status"])

    if result["status"] == "denied":
        req.status = "policy_failed"
        req.required_approvals = []
    else:
        req.status = "pending_approval"
        req.required_approvals = result["required_approvals"]

    db.commit()
    db.refresh(req)
    audit.log(db, actor=actor, role=role, action="subnet_request_validated",
              target_type="subnet_request", target_id=req.id, request_id=req.id,
              result=req.status)
    return req


def add_approval(db: Session, req_id: str, approver: str, role: str, comment: str = "") -> SubnetRequest:
    req = db.get(SubnetRequest, req_id)
    if not req:
        raise HTTPException(404, "Subnet request not found")
    if req.status != "pending_approval":
        raise HTTPException(409, f"Request is in state '{req.status}', not awaiting approval.")

    # Which required role does this user satisfy?
    remaining = list(req.required_approvals or [])
    satisfied = next((r for r in remaining if rbac.can_satisfy_approval(role, r)), None)
    if satisfied is None:
        raise HTTPException(
            403, f"Role '{role}' cannot satisfy any of the outstanding approvals: {remaining}"
        )

    db.add(Approval(
        id=f"apr-{uuid.uuid4().hex[:10]}", request_id=req.id, approver=approver,
        role=satisfied, decision="approved", comment=comment, timestamp=_now(),
    ))
    remaining.remove(satisfied)
    req.required_approvals = remaining
    req.updated_at = _now()

    audit.log(db, actor=approver, role=role, action="approval_added",
              target_type="subnet_request", target_id=req.id, request_id=req.id,
              result=f"satisfied:{satisfied}")

    if not remaining:
        req.status = "approved"
        audit.log(db, actor=approver, role=role, action="subnet_request_approved",
                  target_type="subnet_request", target_id=req.id, request_id=req.id)
    db.commit()
    db.refresh(req)
    return req


def reject(db: Session, req_id: str, approver: str, role: str, reason: str = "") -> SubnetRequest:
    req = db.get(SubnetRequest, req_id)
    if not req:
        raise HTTPException(404, "Subnet request not found")
    db.add(Approval(
        id=f"apr-{uuid.uuid4().hex[:10]}", request_id=req.id, approver=approver,
        role=role, decision="rejected", comment=reason, timestamp=_now(),
    ))
    req.status = "rejected"
    req.updated_at = _now()
    db.commit()
    db.refresh(req)
    audit.log(db, actor=approver, role=role, action="subnet_request_rejected",
              target_type="subnet_request", target_id=req.id, request_id=req.id, result="rejected")
    return req


def approvals_for(db: Session, req_id: str) -> list[Approval]:
    return db.query(Approval).filter(Approval.request_id == req_id).all()


def seed_sample_requests(db: Session) -> None:
    """Create the demo subnet requests and run them through validation."""
    from app.seed.dataset import SAMPLE_REQUESTS

    for spec in SAMPLE_REQUESTS:
        spec = dict(spec)
        spec.pop("seed_status", None)
        rid = spec.pop("id")
        if db.get(SubnetRequest, rid):
            continue
        req = SubnetRequest(id=rid, status="draft", **spec)
        db.add(req)
        db.commit()
        validate(db, rid, actor=req.requester_name, role="requester")
