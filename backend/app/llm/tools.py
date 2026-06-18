"""Read-only retrieval tools the assistant can call.

These are the only ways the assistant touches data. Each returns plain dicts
with evidence (source IDs) so answers are always grounded and auditable.
"""
import re
from sqlalchemy.orm import Session

from app.models import (
    Subnet, VPC, Application, Team, FirewallRule, TerraformFile, IPAMRange,
    RiskFinding, SubnetRequest, Owner,
)
from app.policies import cidr, engine as policy_engine
from app.graph import graph_service

CIDR_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}\b")


def extract_cidr(text: str) -> str | None:
    m = CIDR_RE.search(text or "")
    return m.group(0) if m else None


def find_subnet(db: Session, text: str) -> Subnet | None:
    c = extract_cidr(text)
    if c:
        sn = db.query(Subnet).filter(Subnet.cidr == c).first()
        if sn:
            return sn
    low = (text or "").lower()
    for sn in db.query(Subnet).all():
        if sn.id.lower() in low or sn.name.lower() in low:
            return sn
    # keyword heuristics for the demo ("payroll production subnet")
    if "payroll" in low and "prod" in low:
        return db.query(Subnet).filter(Subnet.id == "sn-payroll-prod-app").first()
    if "hr" in low and "prod" in low:
        return db.query(Subnet).filter(Subnet.id == "sn-hr-prod-private").first()
    return None


def find_application(db: Session, text: str) -> Application | None:
    low = (text or "").lower()
    for app in db.query(Application).all():
        if app.name.lower() in low or app.id.lower() in low:
            return app
    for key, app_id in {"payroll": "app-payroll-api", "hr": "app-hr-portal",
                         "identity": "app-identity-svc", "customer": "app-customer-login",
                         "data": "app-data-warehouse"}.items():
        if key in low:
            return db.get(Application, app_id)
    return None


def find_vpc(db: Session, text: str) -> VPC | None:
    low = (text or "").lower()
    for v in db.query(VPC).all():
        if v.id.lower() in low or v.name.lower() in low:
            return v
    return None


def subnet_owner(db: Session, sn: Subnet) -> dict:
    app = db.get(Application, sn.application_id) if sn.application_id else None
    tf = db.get(TerraformFile, sn.terraform_file_id) if sn.terraform_file_id else None
    ipam = db.get(IPAMRange, sn.ipam_range_id) if sn.ipam_range_id else None
    sources, related = [], [sn.id]
    if app:
        sources.append(f"CMDB application {app.id}")
        related.append(app.id)
    if ipam:
        sources.append(f"IPAM range {ipam.id} ({ipam.cidr})")
    if tf:
        sources.append(f"Terraform file {tf.path}")
        related.append(tf.id)
    if sn.vpc_id:
        related.append(sn.vpc_id)
    return {
        "subnet": sn.id, "cidr": sn.cidr, "owner": sn.owner or "(missing owner tag)",
        "application": app.name if app else None, "vpc": sn.vpc_id,
        "data_classification": sn.data_classification, "sources": sources,
        "related_assets": related,
    }


def internet_facing_prod_subnets(db: Session) -> list[dict]:
    rows = db.query(Subnet).filter(Subnet.internet_facing == True, Subnet.environment == "prod").all()  # noqa: E712
    return [{"id": s.id, "cidr": s.cidr, "owner": s.owner, "vpc": s.vpc_id} for s in rows]


def broad_firewall_rules(db: Session) -> list[dict]:
    rows = db.query(FirewallRule).filter(FirewallRule.action == "allow").all()
    out = []
    for fw in rows:
        if fw.source_cidr == "0.0.0.0/0" or fw.source_cidr.endswith("/8") or fw.risk_level in ("high",):
            out.append({"id": fw.id, "name": fw.name, "source": fw.source_cidr,
                        "destination": fw.destination_cidr, "port": fw.port,
                        "risk_level": fw.risk_level})
    return out


def missing_owner_assets(db: Session) -> list[dict]:
    rows = db.query(Subnet).filter((Subnet.owner == "") | (Subnet.owner.is_(None))).all()
    return [{"id": s.id, "cidr": s.cidr, "vpc": s.vpc_id} for s in rows]


def unknown_assets(db: Session) -> list[dict]:
    rows = db.query(Subnet).filter(Subnet.application_id.is_(None)).all()
    return [{"id": s.id, "cidr": s.cidr, "vpc": s.vpc_id} for s in rows]


def terraform_files_for_vpc(db: Session, vpc: VPC) -> list[dict]:
    out = []
    for tf in db.query(TerraformFile).all():
        if vpc.id in (tf.state_resources or []):
            out.append({"id": tf.id, "path": tf.path, "defines": tf.defines})
    # also subnets in that VPC reference tf files
    for sn in db.query(Subnet).filter(Subnet.vpc_id == vpc.id).all():
        if sn.terraform_file_id:
            tf = db.get(TerraformFile, sn.terraform_file_id)
            if tf and not any(o["id"] == tf.id for o in out):
                out.append({"id": tf.id, "path": tf.path, "defines": tf.defines})
    return out


def suggest_available_subnet(db: Session, business_unit: str, environment: str = "dev",
                             prefixlen: int = 24) -> dict:
    """Find an available CIDR in the BU's environment parent range with no overlap."""
    # Find the matching IPAM parent for that BU + environment.
    parents = db.query(IPAMRange).filter(IPAMRange.type.in_(["parent", "allocated"])).all()
    taken = [s.cidr for s in db.query(Subnet).all()]
    bu_id = None
    from app.models import BusinessUnit
    bu = db.query(BusinessUnit).filter(
        (BusinessUnit.name == business_unit) | (BusinessUnit.id == business_unit) | (BusinessUnit.code == business_unit)
    ).first()
    if bu:
        bu_id = bu.id
    candidates = [
        r for r in parents
        if (bu_id is None or r.business_unit_id == bu_id)
        and (not environment or r.environment in ("", environment))
    ]
    # prefer the most specific (allocated /16) range
    candidates.sort(key=lambda r: cidr.parse(r.cidr).prefixlen if cidr.parse(r.cidr) else 0, reverse=True)
    for rng in candidates:
        suggestion = cidr.suggest_next_available(rng.cidr, prefixlen, taken)
        if suggestion:
            return {"suggested_cidr": suggestion, "from_range": rng.id,
                    "parent_cidr": rng.cidr, "owner": rng.owner}
    return {"suggested_cidr": None, "reason": "No available range found for that business unit/environment."}


def evaluate_change(db: Session, params: dict) -> dict:
    return policy_engine.evaluate(db, params)


def risky_internet_paths(db: Session) -> list[dict]:
    return graph_service.internet_to_sensitive_paths(db)


def find_request(db: Session, text: str) -> SubnetRequest | None:
    low = (text or "").lower()
    for r in db.query(SubnetRequest).all():
        if r.id.lower() in low:
            return r
    c = extract_cidr(text)
    if c:
        return db.query(SubnetRequest).filter(SubnetRequest.requested_cidr == c).first()
    return None
