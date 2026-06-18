"""Audit log endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, identity
from app.api.serializers import row_to_dict, rows
from app.services import rbac
from app.models import AuditEvent

router = APIRouter(tags=["audit"])


@router.get("/audit/events")
def list_events(limit: int = 200, action: str | None = None, request_id: str | None = None,
                db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "audit:view")
    q = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc())
    if action:
        q = q.filter(AuditEvent.action == action)
    if request_id:
        q = q.filter(AuditEvent.request_id == request_id)
    return rows(q.limit(limit).all())


@router.get("/audit/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "audit:view")
    ev = db.get(AuditEvent, event_id)
    if not ev:
        raise HTTPException(404, "Audit event not found")
    return row_to_dict(ev)
