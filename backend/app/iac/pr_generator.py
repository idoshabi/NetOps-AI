"""Mock GitHub/GitLab pull-request generator.

Builds a PR *proposal* object. It never calls a real Git provider in the MVP;
the architecture leaves hooks for GitHub Actions, terraform plan, OPA/Conftest
and ServiceNow change requests. PRs are always proposals requiring human
approval and can never be self-merged.
"""
import re
import uuid

from sqlalchemy.orm import Session

from app.models import SubnetRequest, PullRequest, Application
from app.iac import terraform
from app.policies import engine as policy_engine
from app.audit import logger as audit

# Map outstanding approval roles -> a concrete reviewer name (from seeded owners).
REVIEWER_BY_ROLE = {
    "network_admin": "Sam Rivera (Cloud Network Engineering)",
    "security_reviewer": "Alex Chen (Security Engineering)",
    "approver": "Jordan Blake (Application Approver)",
}


def _branch(req: SubnetRequest) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", f"{req.application}-{req.environment}-{req.requested_cidr}".lower()).strip("-")
    return f"netops-ai/subnet/{slug}"


def generate_pr(db: Session, req: SubnetRequest, actor: str, role: str) -> PullRequest:
    """Generate a PR proposal for an approved (or policy-passing) request."""
    # Re-evaluate policy so the PR always carries a current result.
    policy = req.policy_result or policy_engine.evaluate(db, req)

    file_path, code = terraform.render_subnet(req)
    diff = terraform.render_diff(file_path, code)

    app = db.query(Application).filter(Application.name == req.application).first()
    reviewers = [REVIEWER_BY_ROLE.get(r, r) for r in policy.get("required_approvals", [])]

    title = f"Add {req.environment} subnet {req.requested_cidr} for {req.application} in {req.region}"
    description = _render_description(req, policy)
    risk_summary = (
        f"Risk level: {policy.get('risk_level', 'low').upper()}. "
        + ("Warnings: " + "; ".join(policy.get("warnings", [])) if policy.get("warnings") else "No warnings.")
    )
    rollback = (
        "Revert this PR and run `terraform apply`. The subnet has no dependent "
        "workloads at creation time, so removal is non-disruptive. IPAM allocation "
        f"{req.requested_cidr} will be released back to the available pool."
    )
    test_plan = (
        "1. `terraform plan` shows exactly one aws_subnet to add and no replacements.\n"
        "2. CI policy check (OPA/Conftest) passes.\n"
        "3. Post-apply: confirm subnet CIDR, tags, and route-table association.\n"
        "4. Connectivity smoke test from an existing workload in the VPC."
    )

    audit_event = audit.log(
        db, actor=actor, role=role, action="pr_generated",
        target_type="subnet_request", target_id=req.id, request_id=req.id,
        policy_result=policy, commit=False,
    )

    pr = PullRequest(
        id=f"pr-{uuid.uuid4().hex[:10]}",
        request_id=req.id,
        branch=_branch(req),
        title=title,
        description=description,
        business_justification=req.business_justification,
        risk_summary=risk_summary,
        policy_result=policy,
        reviewers=reviewers,
        files_changed=[file_path],
        terraform_diff=diff,
        rollback_notes=rollback,
        test_plan=test_plan,
        approval_requirements=policy.get("required_approvals", []),
        status="open",
        audit_event_id=audit_event.id,
    )
    db.add(pr)
    audit_event.pr_id = pr.id

    if req.status in ("approved", "pending_approval", "warning"):
        req.status = "pr_generated"

    db.commit()
    db.refresh(pr)
    return pr


def _render_description(req: SubnetRequest, policy: dict) -> str:
    checks = []
    if policy.get("status") == "denied":
        checks.append("❌ Policy: DENIED")
    elif policy.get("status") == "warning":
        checks.append("⚠️ Policy: ALLOWED WITH WARNINGS")
    else:
        checks.append("✅ Policy: ALLOWED")
    for r in policy.get("reasons", []):
        checks.append(f"  - ❌ {r}")
    for w in policy.get("warnings", []):
        checks.append(f"  - ⚠️ {w}")

    return f"""## Subnet provisioning request

| Field | Value |
|-------|-------|
| Requested by | {req.requester_name} <{req.requester_email}> |
| Application | {req.application} |
| Environment | {req.environment} |
| VPC / VNet | {req.vpc} |
| Requested CIDR | {req.requested_cidr} |
| Cloud / Region | {req.cloud_provider} / {req.region} |
| Owner | {req.owner} |
| Cost center | {req.cost_center} |
| Data classification | {req.data_classification} |
| Internet exposure | {req.internet_exposure_required} |

### Business justification
{req.business_justification}

### Policy checks
{chr(10).join(checks)}

### Risk assessment
Risk level: **{policy.get('risk_level', 'low').upper()}**

### Required approvals
{', '.join(policy.get('required_approvals', [])) or 'none'}

> This pull request is an automated **proposal**. It must be reviewed and
> approved by the required reviewers and merged by a human. NetOps-AI never
> self-approves, merges, or deploys infrastructure.
"""


def approve_pr(db: Session, pr: PullRequest, approver: str, role: str, comment: str = "") -> PullRequest:
    pr.status = "approved"
    db.commit()
    db.refresh(pr)
    audit.log(db, actor=approver, role=role, action="pr_approved",
              target_type="pull_request", target_id=pr.id, request_id=pr.request_id, pr_id=pr.id)
    return pr


def reject_pr(db: Session, pr: PullRequest, approver: str, role: str, reason: str = "") -> PullRequest:
    pr.status = "rejected"
    db.commit()
    db.refresh(pr)
    audit.log(db, actor=approver, role=role, action="pr_rejected",
              target_type="pull_request", target_id=pr.id, request_id=pr.request_id, pr_id=pr.id,
              result="rejected")
    return pr
