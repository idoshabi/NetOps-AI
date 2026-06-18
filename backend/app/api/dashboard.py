"""Dashboard aggregation endpoint (convenience for the frontend)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, identity
from app.api.serializers import rows
from app.services import rbac
from app.models import (
    Subnet, VPC, Workload, Application, FirewallRule, RiskFinding, SubnetRequest, AuditEvent,
)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    subnets = db.query(Subnet).all()
    findings = db.query(RiskFinding).all()
    requests = db.query(SubnetRequest).all()
    high_risk_fw = db.query(FirewallRule).filter(FirewallRule.risk_level == "high").count()
    return {
        "total_assets": (
            db.query(Subnet).count() + db.query(VPC).count()
            + db.query(Workload).count() + db.query(Application).count()
        ),
        "total_subnets": len(subnets),
        "total_vpcs": db.query(VPC).count(),
        "total_applications": db.query(Application).count(),
        "unknown_assets": sum(1 for s in subnets if s.application_id is None),
        "missing_owner_tags": sum(1 for s in subnets if not s.owner),
        "internet_facing_prod": sum(1 for s in subnets if s.internet_facing and s.environment == "prod"),
        "high_risk_firewall_rules": high_risk_fw,
        "open_findings": len(findings),
        "pending_requests": sum(1 for r in requests if r.status == "pending_approval"),
        "policy_failed_requests": sum(1 for r in requests if r.status == "policy_failed"),
        "recent_audit_events": rows(
            db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(8).all()
        ),
        "findings_by_severity": {
            sev: sum(1 for f in findings if f.severity == sev)
            for sev in ("critical", "high", "medium", "low")
        },
    }
