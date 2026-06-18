"""LLM Assistant endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, identity
from app.api.serializers import row_to_dict, rows
from app.services import rbac
from app.llm import assistant
from app.models import Conversation

router = APIRouter(tags=["assistant"])

from app.schemas import AssistantAsk, AssistantProposeIaC


@router.post("/assistant/ask")
def ask(body: AssistantAsk, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "assistant:ask")
    return assistant.ask(db, body.question, body.conversation_id, body.user, who["role"])


@router.post("/assistant/propose-iac")
def propose(body: AssistantProposeIaC, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "assistant:propose")
    return assistant.propose_iac(db, body.request, body.conversation_id, body.user, who["role"])


@router.get("/assistant/conversations")
def list_conversations(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "assistant:ask")
    return rows(db.query(Conversation).order_by(Conversation.created_at.desc()).all())


@router.get("/assistant/conversations/{conv_id}")
def get_conversation(conv_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "assistant:ask")
    conv = db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return {"id": conv.id, "user": conv.user, "created_at": conv.created_at.isoformat(),
            "messages": rows(conv.messages)}
