"""Internal policy engine.

Evaluates a subnet change against governance rules and returns a structured
result: status (allowed/warning/denied), risk level, reasons, warnings,
required approval roles, evidence (source record IDs) and a recommended action.

The engine is deterministic and pure given the DB snapshot, which makes it easy
to test and lets the LLM call it as a tool without surprises.
"""
from typing import Any
from sqlalchemy.orm import Session

from app.models import Subnet, VPC, BusinessUnit, Team, Application, Route
from app.policies import cidr

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
SENSITIVE_BUS = {"bu-payroll", "bu-identity", "bu-data"}


def _get(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _max_risk(current: str, candidate: str) -> str:
    return candidate if RISK_ORDER[candidate] > RISK_ORDER[current] else current


def evaluate(db: Session, data: Any) -> dict:
    """`data` may be a SubnetRequest ORM row, a dict, or a PolicyEvaluateInput."""
    cidr_str = _get(data, "requested_cidr", "") or ""
    vpc_ref = _get(data, "vpc", "") or ""
    environment = (_get(data, "environment", "") or "").lower()
    bu_name = _get(data, "business_unit", "") or ""
    team_name = _get(data, "team", "") or ""
    app_name = _get(data, "application", "") or ""
    owner = _get(data, "owner", "") or ""
    cost_center = _get(data, "cost_center", "") or ""
    justification = _get(data, "business_justification", "") or ""
    data_class = (_get(data, "data_classification", "") or "internal").lower()
    internet = bool(_get(data, "internet_exposure_required", False))

    reasons: list[str] = []
    warnings: list[str] = []
    required: list[str] = []
    evidence: list[str] = []
    risk = "low"

    # ----- Resolve referenced entities -----------------------------------
    bu = (
        db.query(BusinessUnit)
        .filter((BusinessUnit.name == bu_name) | (BusinessUnit.id == bu_name) | (BusinessUnit.code == bu_name))
        .first()
    )
    vpc = db.query(VPC).filter((VPC.id == vpc_ref) | (VPC.name == vpc_ref)).first()
    app = db.query(Application).filter(
        (Application.name == app_name) | (Application.id == app_name)
    ).first()

    # ----- HARD DENY: required fields ------------------------------------
    if not owner:
        reasons.append("Subnet request is missing an owner. Every subnet must have an owner.")
    if not environment:
        reasons.append("Subnet request is missing an environment (dev/staging/prod).")
    if not justification:
        reasons.append("Subnet request is missing a business justification.")
    if not cost_center:
        reasons.append("Subnet request is missing a cost center tag.")
    if not app:
        reasons.append(f"Application '{app_name}' is not mapped in the CMDB. Subnets must map to a known application.")
        risk = _max_risk(risk, "medium")

    # ----- HARD DENY: CIDR validity & overlap ----------------------------
    if not cidr.parse(cidr_str):
        reasons.append(f"Requested CIDR '{cidr_str}' is not a valid IPv4 network.")
    else:
        existing = db.query(Subnet).all()
        for sn in existing:
            if cidr.overlaps(cidr_str, sn.cidr):
                reasons.append(f"Requested CIDR {cidr_str} overlaps with existing subnet {sn.cidr} ({sn.name}).")
                evidence.append(sn.id)
                risk = _max_risk(risk, "high")

        # ----- HARD DENY: inside allowed BU parent range -----------------
        if bu and bu.parent_cidr:
            if not cidr.contains(bu.parent_cidr, cidr_str):
                reasons.append(
                    f"Requested CIDR {cidr_str} is outside the allowed {bu.name} parent range {bu.parent_cidr}."
                )
                evidence.append(bu.id)
        elif bu_name:
            warnings.append(f"Business unit '{bu_name}' has no registered parent CIDR range to validate against.")

    # ----- HARD DENY: team must own / have access to target VPC ----------
    if vpc:
        evidence.append(vpc.id)
        owner_team = db.get(Team, vpc.owner_team_id) if vpc.owner_team_id else None
        team_ok = owner_team is not None and (
            owner_team.name == team_name or owner_team.id == team_name
        )
        bu_ok = bu is not None and vpc.business_unit_id == bu.id
        if not (team_ok or bu_ok):
            reasons.append(
                f"Team '{team_name}' does not own or have delegated access to target VPC {vpc.name}."
            )
    elif vpc_ref:
        warnings.append(f"Target VPC '{vpc_ref}' was not found in inventory.")

    # ----- APPROVAL GATES ------------------------------------------------
    required.append("network_admin")  # baseline for any subnet creation
    if environment == "prod":
        required.append("approver")    # production requires two approvals
        risk = _max_risk(risk, "medium")
        reasons_prod = "Production subnet requires two approvals (network_admin + approver)."
        if reasons_prod not in warnings:
            warnings.append(reasons_prod)
    if internet:
        required.append("security_reviewer")
        risk = _max_risk(risk, "high")
        warnings.append("Internet exposure requires a security review before approval.")
    if app and app.criticality == "critical":
        if "security_reviewer" not in required:
            required.append("security_reviewer")
        risk = _max_risk(risk, "high")
        warnings.append(f"Application '{app.name}' is critical; additional security approval required.")
    elif app and app.criticality == "high":
        risk = _max_risk(risk, "medium")
        warnings.append(f"Application '{app.name}' is high criticality; review impact carefully.")

    # ----- WARNINGS ------------------------------------------------------
    if data_class in ("confidential", "regulated"):
        warnings.append(f"Data classification '{data_class}' is sensitive; ensure encryption and access controls.")
        risk = _max_risk(risk, "medium")

    # Larger-than-expected subnet (bigger than a /24).
    net = cidr.parse(cidr_str)
    if net and net.prefixlen < 24:
        warnings.append(f"Requested subnet {cidr_str} is larger than the standard /24 allocation.")
        risk = _max_risk(risk, "medium")

    # Routing to sensitive systems.
    if vpc:
        routes = db.query(Route).filter(Route.vpc_id == vpc.id).all()
        if any(r.target == "transit_gateway" for r in routes):
            warnings.append(
                f"Target VPC {vpc.name} has a transit gateway route; new subnet may reach sensitive systems."
            )
            risk = _max_risk(risk, "medium")
    if bu and bu.id in SENSITIVE_BUS:
        warnings.append(f"Business unit {bu.name} hosts sensitive systems; verify segmentation.")
        risk = _max_risk(risk, "medium")

    # ----- Decision ------------------------------------------------------
    if reasons:
        status = "denied"
        risk = _max_risk(risk, "high")
        recommended = "Resolve the denial reasons (overlap, missing fields, ownership) and resubmit."
    elif warnings:
        status = "warning"
        recommended = (
            "Request is allowable but requires the listed approvals and review of warnings before merge."
        )
    else:
        status = "allowed"
        recommended = "Request passes policy. Obtain the required approvals, then generate the Terraform PR."

    # De-dup approvals preserving order.
    required = list(dict.fromkeys(required))
    evidence = list(dict.fromkeys(evidence))

    return {
        "status": status,
        "risk_level": risk,
        "reasons": reasons,
        "warnings": warnings,
        "required_approvals": required,
        "evidence": evidence,
        "recommended_action": recommended,
    }
