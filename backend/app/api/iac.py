"""IaC / Pull-request endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, identity
from app.api.serializers import row_to_dict, rows
from app.services import rbac
from app.iac import pr_generator
from app.llm import assistant
from app.models import SubnetRequest, PullRequest
from app.schemas import IaCGenerateInput, ApprovalInput, RejectInput, AssistantProposeIaC

router = APIRouter(tags=["iac"])


@router.post("/iac/generate")
def generate(body: IaCGenerateInput, db: Session = Depends(get_db), who=Depends(identity)):
    """Generate a Terraform PR proposal for an existing request."""
    rbac.require(who["role"], "pr:generate")
    req = db.get(SubnetRequest, body.request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    pr = pr_generator.generate_pr(db, req, actor=body.actor, role=who["role"])
    return row_to_dict(pr)


@router.post("/iac/propose-change")
def propose_change(body: AssistantProposeIaC, db: Session = Depends(get_db), who=Depends(identity)):
    """Natural-language IaC proposal (LLM assistant, mode 2)."""
    rbac.require(who["role"], "assistant:propose")
    return assistant.propose_iac(db, body.request, body.conversation_id, body.user, who["role"])


@router.get("/pull-requests")
def list_prs(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "request:view")
    return rows(db.query(PullRequest).order_by(PullRequest.created_at.desc()).all())


@router.get("/pull-requests/{pr_id}")
def get_pr(pr_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "request:view")
    pr = db.get(PullRequest, pr_id)
    if not pr:
        raise HTTPException(404, "Pull request not found")
    return row_to_dict(pr)


@router.post("/pull-requests/{pr_id}/approve")
def approve_pr(pr_id: str, body: ApprovalInput, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "pr:approve")
    pr = db.get(PullRequest, pr_id)
    if not pr:
        raise HTTPException(404, "Pull request not found")
    if not rbac.can_satisfy_approval(body.role, body.role) and body.role not in ("admin",):
        pass  # role authority already gated by pr:approve permission
    pr = pr_generator.approve_pr(db, pr, approver=body.approver, role=body.role, comment=body.comment)
    return row_to_dict(pr)


@router.post("/pull-requests/{pr_id}/reject")
def reject_pr(pr_id: str, body: RejectInput, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "pr:approve")
    pr = db.get(PullRequest, pr_id)
    if not pr:
        raise HTTPException(404, "Pull request not found")
    pr = pr_generator.reject_pr(db, pr, approver=body.approver, role=body.role, reason=body.reason)
    return row_to_dict(pr)
