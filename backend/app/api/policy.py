"""Policy evaluation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, identity
from app.services import rbac
from app.policies import engine
from app.models import SubnetRequest
from app.schemas import PolicyEvaluateInput
from app.audit import logger as audit

router = APIRouter(tags=["policy"])


@router.post("/policy/evaluate")
def evaluate(body: PolicyEvaluateInput, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "request:validate")
    result = engine.evaluate(db, body)
    audit.log(db, actor=who["actor"], role=who["role"], action="policy_evaluated",
              target_type="adhoc", target_id=body.requested_cidr,
              policy_result=result, result=result["status"])
    return result


@router.get("/policy/results/{request_id}")
def results(request_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "request:view")
    req = db.get(SubnetRequest, request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    return req.policy_result or {}
