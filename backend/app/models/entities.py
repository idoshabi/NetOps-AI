"""SQLAlchemy ORM models for the NetGov graph-style data model.

The model is relational but mirrors a property graph: every table is a node type
and foreign keys / association columns are edges. The graph service
(`app.graph.graph_service`) projects these rows into nodes + typed edges.
"""
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Ownership / org hierarchy
# --------------------------------------------------------------------------- #
class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)


class BusinessUnit(Base):
    __tablename__ = "business_units"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    code: Mapped[str] = mapped_column(String)
    cost_center: Mapped[str] = mapped_column(String, default="")
    # Parent CIDR block this BU is allowed to allocate subnets from.
    parent_cidr: Mapped[str] = mapped_column(String, default="")
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=True)


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    business_unit_id: Mapped[str] = mapped_column(ForeignKey("business_units.id"), nullable=True)


class Owner(Base):
    __tablename__ = "owners"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="requester")  # RBAC role
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=True)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    business_owner: Mapped[str] = mapped_column(String, default="")
    technical_owner: Mapped[str] = mapped_column(String, default="")
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=True)
    business_unit_id: Mapped[str] = mapped_column(ForeignKey("business_units.id"), nullable=True)
    environment: Mapped[str] = mapped_column(String, default="prod")
    criticality: Mapped[str] = mapped_column(String, default="medium")  # low/medium/high/critical
    compliance_scope: Mapped[str] = mapped_column(String, default="")   # e.g. SOX, PCI, GDPR
    data_classification: Mapped[str] = mapped_column(String, default="internal")


# --------------------------------------------------------------------------- #
# Cloud inventory
# --------------------------------------------------------------------------- #
class CloudAccount(Base):
    __tablename__ = "cloud_accounts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String)  # aws / azure / gcp
    account_ref: Mapped[str] = mapped_column(String)  # account id / subscription / project
    name: Mapped[str] = mapped_column(String)
    region: Mapped[str] = mapped_column(String, default="")


class VPC(Base):
    __tablename__ = "vpcs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    cloud_account_id: Mapped[str] = mapped_column(ForeignKey("cloud_accounts.id"), nullable=True)
    cidr: Mapped[str] = mapped_column(String)
    environment: Mapped[str] = mapped_column(String, default="prod")
    region: Mapped[str] = mapped_column(String, default="")
    owner_team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=True)
    business_unit_id: Mapped[str] = mapped_column(ForeignKey("business_units.id"), nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)


class Subnet(Base):
    __tablename__ = "subnets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    vpc_id: Mapped[str] = mapped_column(ForeignKey("vpcs.id"), nullable=True)
    cidr: Mapped[str] = mapped_column(String)
    environment: Mapped[str] = mapped_column(String, default="prod")
    region: Mapped[str] = mapped_column(String, default="")
    availability_zone: Mapped[str] = mapped_column(String, default="")
    business_unit_id: Mapped[str] = mapped_column(ForeignKey("business_units.id"), nullable=True)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), nullable=True)
    owner: Mapped[str] = mapped_column(String, default="")
    technical_owner: Mapped[str] = mapped_column(String, default="")
    cost_center: Mapped[str] = mapped_column(String, default="")
    data_classification: Mapped[str] = mapped_column(String, default="internal")
    internet_facing: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String, default="cloud")  # cloud / ipam / terraform
    terraform_managed: Mapped[bool] = mapped_column(Boolean, default=False)
    terraform_file_id: Mapped[str] = mapped_column(ForeignKey("terraform_files.id"), nullable=True)
    ipam_range_id: Mapped[str] = mapped_column(ForeignKey("ipam_ranges.id"), nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)


class Workload(Base):
    __tablename__ = "workloads"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    # vm / k8s_cluster / load_balancer / nat_gateway / internet_gateway / transit_gateway
    type: Mapped[str] = mapped_column(String, default="vm")
    subnet_id: Mapped[str] = mapped_column(ForeignKey("subnets.id"), nullable=True)
    vpc_id: Mapped[str] = mapped_column(ForeignKey("vpcs.id"), nullable=True)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), nullable=True)
    internet_facing: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)


class SecurityGroup(Base):
    __tablename__ = "security_groups"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    vpc_id: Mapped[str] = mapped_column(ForeignKey("vpcs.id"), nullable=True)
    workload_id: Mapped[str] = mapped_column(ForeignKey("workloads.id"), nullable=True)
    rules: Mapped[list] = mapped_column(JSON, default=list)  # [{direction,cidr,port,protocol,action}]


class FirewallRule(Base):
    __tablename__ = "firewall_rules"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    source_cidr: Mapped[str] = mapped_column(String)
    destination_cidr: Mapped[str] = mapped_column(String)
    port: Mapped[str] = mapped_column(String)
    protocol: Mapped[str] = mapped_column(String, default="tcp")
    action: Mapped[str] = mapped_column(String, default="allow")
    owner: Mapped[str] = mapped_column(String, default="")
    risk_level: Mapped[str] = mapped_column(String, default="low")
    zone: Mapped[str] = mapped_column(String, default="internal")
    internet_facing: Mapped[bool] = mapped_column(Boolean, default=False)
    direction: Mapped[str] = mapped_column(String, default="east-west")  # north-south / east-west
    description: Mapped[str] = mapped_column(Text, default="")


class Route(Base):
    __tablename__ = "routes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    route_table: Mapped[str] = mapped_column(String)
    destination_cidr: Mapped[str] = mapped_column(String)
    target: Mapped[str] = mapped_column(String)  # igw / natgw / tgw / local / peering
    vpc_id: Mapped[str] = mapped_column(ForeignKey("vpcs.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")


# --------------------------------------------------------------------------- #
# IPAM
# --------------------------------------------------------------------------- #
class IPAMRange(Base):
    __tablename__ = "ipam_ranges"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    cidr: Mapped[str] = mapped_column(String)
    parent_id: Mapped[str] = mapped_column(ForeignKey("ipam_ranges.id"), nullable=True)
    type: Mapped[str] = mapped_column(String, default="allocated")  # parent/allocated/reserved/available
    business_unit_id: Mapped[str] = mapped_column(ForeignKey("business_units.id"), nullable=True)
    environment: Mapped[str] = mapped_column(String, default="")
    region: Mapped[str] = mapped_column(String, default="")
    owner: Mapped[str] = mapped_column(String, default="")
    dns_zone: Mapped[str] = mapped_column(String, default="")
    dhcp_leases: Mapped[int] = mapped_column(Integer, default=0)


# --------------------------------------------------------------------------- #
# Terraform / IaC
# --------------------------------------------------------------------------- #
class TerraformModule(Base):
    __tablename__ = "terraform_modules"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    repo_path: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")


class TerraformFile(Base):
    __tablename__ = "terraform_files"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    path: Mapped[str] = mapped_column(String)
    repo_path: Mapped[str] = mapped_column(String)
    module_id: Mapped[str] = mapped_column(ForeignKey("terraform_modules.id"), nullable=True)
    defines: Mapped[str] = mapped_column(String, default="")  # what resource kind it defines
    owner: Mapped[str] = mapped_column(String, default="")
    last_modified: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    state_resources: Mapped[list] = mapped_column(JSON, default=list)


# --------------------------------------------------------------------------- #
# Workflow: requests, PRs, approvals
# --------------------------------------------------------------------------- #
class SubnetRequest(Base):
    __tablename__ = "subnet_requests"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    requester_name: Mapped[str] = mapped_column(String)
    requester_email: Mapped[str] = mapped_column(String)
    team: Mapped[str] = mapped_column(String, default="")
    application: Mapped[str] = mapped_column(String, default="")
    business_unit: Mapped[str] = mapped_column(String, default="")
    environment: Mapped[str] = mapped_column(String, default="dev")
    requested_cidr: Mapped[str] = mapped_column(String)
    vpc: Mapped[str] = mapped_column(String, default="")
    cloud_provider: Mapped[str] = mapped_column(String, default="aws")
    region: Mapped[str] = mapped_column(String, default="")
    business_justification: Mapped[str] = mapped_column(Text, default="")
    data_classification: Mapped[str] = mapped_column(String, default="internal")
    internet_exposure_required: Mapped[bool] = mapped_column(Boolean, default=False)
    expected_traffic_pattern: Mapped[str] = mapped_column(String, default="")
    cost_center: Mapped[str] = mapped_column(String, default="")
    owner: Mapped[str] = mapped_column(String, default="")
    technical_owner: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="draft")
    policy_result: Mapped[dict] = mapped_column(JSON, default=dict)
    required_approvals: Mapped[list] = mapped_column(JSON, default=list)  # roles still needed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PullRequest(Base):
    __tablename__ = "pull_requests"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("subnet_requests.id"), nullable=True)
    branch: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    business_justification: Mapped[str] = mapped_column(Text, default="")
    risk_summary: Mapped[str] = mapped_column(Text, default="")
    policy_result: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewers: Mapped[list] = mapped_column(JSON, default=list)
    files_changed: Mapped[list] = mapped_column(JSON, default=list)
    terraform_diff: Mapped[str] = mapped_column(Text, default="")
    rollback_notes: Mapped[str] = mapped_column(Text, default="")
    test_plan: Mapped[str] = mapped_column(Text, default="")
    approval_requirements: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="open")  # open/approved/rejected/merged_mock
    audit_event_id: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    request_id: Mapped[str] = mapped_column(String, default="")
    pull_request_id: Mapped[str] = mapped_column(String, default="")
    approver: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    decision: Mapped[str] = mapped_column(String, default="approved")  # approved / rejected
    comment: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# --------------------------------------------------------------------------- #
# Risk + audit + assistant
# --------------------------------------------------------------------------- #
class RiskFinding(Base):
    __tablename__ = "risk_findings"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String)  # internet_exposure / missing_tag / broad_access ...
    severity: Mapped[str] = mapped_column(String, default="medium")
    asset_type: Mapped[str] = mapped_column(String, default="")
    asset_id: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    recommendation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    actor: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="")
    action: Mapped[str] = mapped_column(String)
    target_type: Mapped[str] = mapped_column(String, default="")
    target_id: Mapped[str] = mapped_column(String, default="")
    request_id: Mapped[str] = mapped_column(String, default="")
    source_ip: Mapped[str] = mapped_column(String, default="")
    result: Mapped[str] = mapped_column(String, default="success")
    policy_result: Mapped[dict] = mapped_column(JSON, default=dict)
    pr_id: Mapped[str] = mapped_column(String, default="")
    conversation_id: Mapped[str] = mapped_column(String, default="")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String)  # user / assistant
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)  # sources, riskLevel, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
