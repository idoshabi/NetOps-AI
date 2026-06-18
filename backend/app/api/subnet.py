"""Subnet request workflow endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, identity
from app.api.serializers import row_to_dict, rows
from app.services import rbac, subnet_request as svc
from app.iac import pr_generator
from app.models import SubnetRequest, PullRequest
from app.schemas import SubnetRequestCreate, ApprovalInput, RejectInput

router = APIRouter(tags=["subnet-requests"])


def _req_dict(req: SubnetRequest) -> dict:
    return row_to_dict(req)


@router.post("/subnet/request")
def create_request(payload: SubnetRequestCreate, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "request:create")
    req = svc.create(db, payload, actor=who["actor"], role=who["role"])
    return _req_dict(req)


@router.get("/subnet/request")
def list_requests(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "request:view")
    return rows(db.query(SubnetRequest).order_by(SubnetRequest.created_at.desc()).all())


@router.get("/subnet/request/{req_id}")
def get_request(req_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "request:view")
    req = db.get(SubnetRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    out = _req_dict(req)
    out["approvals"] = rows(svc.approvals_for(db, req_id))
    return out


@router.post("/subnet/request/{req_id}/validate")
def validate_request(req_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "request:validate")
    req = svc.validate(db, req_id, actor=who["actor"], role=who["role"])
    return _req_dict(req)


@router.post("/subnet/request/{req_id}/approve")
def approve_request(req_id: str, body: ApprovalInput, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "approval:add")
    req = svc.add_approval(db, req_id, approver=body.approver, role=body.role, comment=body.comment)
    return _req_dict(req)


@router.post("/subnet/request/{req_id}/reject")
def reject_request(req_id: str, body: RejectInput, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "approval:add")
    req = svc.reject(db, req_id, approver=body.approver, role=body.role, reason=body.reason)
    return _req_dict(req)


@router.post("/subnet/request/{req_id}/generate-pr")
def generate_pr(req_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "pr:generate")
    req = db.get(SubnetRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if (req.policy_result or {}).get("status") == "denied":
        raise HTTPException(409, "Cannot generate a PR for a policy-denied request.")
    pr = pr_generator.generate_pr(db, req, actor=who["actor"], role=who["role"])
    return row_to_dict(pr)
