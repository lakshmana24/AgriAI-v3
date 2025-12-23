from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_role
from app.schemas.auth import UserRole
from app.schemas.officer import EscalationRecord, OfficerVerifiedAdviceRequest
from app.services.escalation_store import EscalationNotFound, escalation_store

router = APIRouter(prefix="/officer", tags=["officer"])


@router.get("/escalations", response_model=list[EscalationRecord])
async def list_escalations(_user=Depends(require_role(UserRole.OFFICER))) -> list[EscalationRecord]:
    return escalation_store.list_all()


@router.post("/respond/{id}", response_model=EscalationRecord)
async def respond(
    id: str,
    payload: OfficerVerifiedAdviceRequest,
    _user=Depends(require_role(UserRole.OFFICER)),
) -> EscalationRecord:
    try:
        return escalation_store.respond(id, response_text=payload.response_text, citations=payload.citations)
    except EscalationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
