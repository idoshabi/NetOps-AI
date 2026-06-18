"""Pydantic request/response schemas."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Subnet requests
# --------------------------------------------------------------------------- #
class SubnetRequestCreate(BaseModel):
    requester_name: str
    requester_email: str
    team: str
    application: str
    business_unit: str
    environment: str = Field(default="dev", description="dev | staging | prod")
    requested_cidr: str
    vpc: str
    cloud_provider: str = "aws"
    region: str = ""
    business_justification: str = ""
    data_classification: str = "internal"
    internet_exposure_required: bool = False
    expected_traffic_pattern: str = ""
    cost_center: str = ""
    owner: str = ""
    technical_owner: str = ""


class SubnetRequestOut(BaseModel):
    id: str
    requester_name: str
    requester_email: str
    team: str
    application: str
    business_unit: str
    environment: str
    requested_cidr: str
    vpc: str
    cloud_provider: str
    region: str
    business_justification: str
    data_classification: str
    internet_exposure_required: bool
    expected_traffic_pattern: str
    cost_center: str
    owner: str
    technical_owner: str
    status: str
    policy_result: dict
    required_approvals: list
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------- #
# Policy
# --------------------------------------------------------------------------- #
class PolicyEvaluateInput(BaseModel):
    """Evaluate an ad-hoc subnet change without persisting a request."""
    requested_cidr: str
    vpc: str = ""
    environment: str = "dev"
    business_unit: str = ""
    team: str = ""
    application: str = ""
    owner: str = ""
    cost_center: str = ""
    business_justification: str = ""
    data_classification: str = "internal"
    internet_exposure_required: bool = False


class PolicyResult(BaseModel):
    status: str                       # allowed | warning | denied
    risk_level: str                   # low | medium | high | critical
    reasons: list[str] = []
    warnings: list[str] = []
    required_approvals: list[str] = []
    evidence: list[str] = []
    recommended_action: str = ""


# --------------------------------------------------------------------------- #
# Approvals
# --------------------------------------------------------------------------- #
class ApprovalInput(BaseModel):
    approver: str
    role: str
    comment: str = ""


class RejectInput(BaseModel):
    approver: str
    role: str
    reason: str = ""


# --------------------------------------------------------------------------- #
# Assistant
# --------------------------------------------------------------------------- #
class AssistantAsk(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    user: str = "demo-user"
    role: str = "requester"


class AssistantProposeIaC(BaseModel):
    request: str
    conversation_id: Optional[str] = None
    user: str = "demo-user"
    role: str = "requester"


class AssistantAnswer(BaseModel):
    answer: str
    risk_level: str = "low"
    confidence: str = "high"
    sources: list[str] = []
    related_assets: list[str] = []
    recommended_action: str = ""
    intent: str = "qa"
    conversation_id: str = ""
    proposal: Optional[dict[str, Any]] = None  # PR preview when in IaC mode


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #
class DiscoveryRunOut(BaseModel):
    run_id: str
    status: str
    sources: list[str]
    counts: dict
    started_at: datetime
    completed_at: Optional[datetime] = None


# --------------------------------------------------------------------------- #
# Generic IaC generate input (assistant-independent)
# --------------------------------------------------------------------------- #
class IaCGenerateInput(BaseModel):
    request_id: Optional[str] = None
    actor: str = "demo-user"
    role: str = "network_admin"
