"""LLM Assistant Service.

Orchestrates the rule-based assistant across two modes:
  Mode 1 (qa)  - read-only network Q&A with evidence.
  Mode 2 (iac) - generates Terraform PR *proposals* (never approves/merges/deploys).

Internal components used: intent classifier, retrieval/context builder (tools),
graph/IPAM/CMDB/policy tools, IaC + PR generator, risk explanation, audit logger.

Safety guarantees enforced here:
  * The assistant never approves its own PR, merges, or deploys.
  * It never bypasses the policy engine - every proposal is policy-evaluated.
  * Denied requests produce an explanation + safe alternative, never a PR.
  * Low confidence -> ask for clarification instead of generating IaC.
  * Every question and proposal is written to the audit log with sources.
"""
import uuid

from sqlalchemy.orm import Session

from app.models import Conversation, Message, SubnetRequest, Application, BusinessUnit
from app.llm import intent as intent_mod, tools
from app.llm.provider import get_provider
from app.services import subnet_request as req_service
from app.iac import pr_generator
from app.audit import logger as audit

SAFETY_NOTE = (
    "This is an automated proposal. NetOps-AI cannot approve, merge, or deploy changes - "
    "a human reviewer with the required role must do that."
)


# --------------------------------------------------------------------------- #
# Conversation helpers
# --------------------------------------------------------------------------- #
def _get_or_create_conversation(db: Session, conversation_id: str | None, user: str) -> Conversation:
    if conversation_id:
        conv = db.get(Conversation, conversation_id)
        if conv:
            return conv
    conv = Conversation(id=f"conv-{uuid.uuid4().hex[:10]}", user=user)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _record(db: Session, conv: Conversation, role: str, content: str, meta: dict | None = None):
    db.add(Message(id=f"msg-{uuid.uuid4().hex[:10]}", conversation_id=conv.id,
                   role=role, content=content, meta=meta or {}))
    db.commit()


def _env_from_text(text: str) -> str:
    low = text.lower()
    if "prod" in low:
        return "prod"
    if "staging" in low or "stage" in low:
        return "staging"
    return "dev"


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #
def ask(db: Session, question: str, conversation_id: str | None, user: str, role: str) -> dict:
    conv = _get_or_create_conversation(db, conversation_id, user)
    _record(db, conv, "user", question)
    audit.log(db, actor=user, role=role, action="llm_question_asked",
              target_type="conversation", target_id=conv.id, conversation_id=conv.id)

    cls = intent_mod.classify(question)
    if cls["mode"] == "iac":
        answer = _propose_iac(db, question, conv, user, role)
    else:
        answer = _answer_qa(db, question, cls, conv)

    answer["conversation_id"] = conv.id
    answer["intent"] = cls["intent"]
    _record(db, conv, "assistant", answer["answer"], meta={
        "sources": answer.get("sources", []), "risk_level": answer.get("risk_level"),
        "intent": cls["intent"], "confidence": answer.get("confidence"),
    })
    return answer


def propose_iac(db: Session, request_text: str, conversation_id: str | None, user: str, role: str) -> dict:
    conv = _get_or_create_conversation(db, conversation_id, user)
    _record(db, conv, "user", request_text)
    audit.log(db, actor=user, role=role, action="llm_question_asked",
              target_type="conversation", target_id=conv.id, conversation_id=conv.id)
    answer = _propose_iac(db, request_text, conv, user, role)
    answer["conversation_id"] = conv.id
    answer["intent"] = "iac_proposal"
    _record(db, conv, "assistant", answer["answer"], meta={
        "sources": answer.get("sources", []), "risk_level": answer.get("risk_level"),
        "proposal": bool(answer.get("proposal")),
    })
    return answer


# --------------------------------------------------------------------------- #
# Mode 1: Q&A
# --------------------------------------------------------------------------- #
def _answer_qa(db: Session, q: str, cls: dict, conv: Conversation) -> dict:
    intent = cls["intent"]
    base = {"risk_level": "low", "confidence": cls["confidence"], "sources": [],
            "related_assets": [], "recommended_action": "", "proposal": None}

    if intent == "owner_lookup":
        sn = tools.find_subnet(db, q)
        if sn:
            info = tools.subnet_owner(db, sn)
            risk = "medium" if sn.data_classification in ("confidential", "regulated") else "low"
            return {**base, "answer": (
                f"Subnet {info['cidr']} ({sn.name}) is owned by {info['owner']}"
                + (f" and supports the {info['application']} application." if info['application'] else ".")
            ), "risk_level": risk, "sources": info["sources"], "related_assets": info["related_assets"],
                "recommended_action": "Review related firewall rules before changing this subnet."}
        vpc = tools.find_vpc(db, q)
        if vpc:
            from app.models import Team
            team = db.get(Team, vpc.owner_team_id) if vpc.owner_team_id else None
            return {**base, "answer": f"VPC {vpc.name} ({vpc.cidr}) is owned by {team.name if team else 'an unknown team'}.",
                    "sources": [f"Cloud inventory {vpc.id}"], "related_assets": [vpc.id]}
        return {**base, "answer": "I couldn't identify the subnet or VPC in your question. "
                "Please include a CIDR (e.g. 10.50.10.0/24) or a VPC name.", "confidence": "low"}

    if intent == "app_for_vpc":
        vpc = tools.find_vpc(db, q)
        if vpc:
            from app.models import Subnet
            apps = {s.application_id for s in db.query(Subnet).filter(Subnet.vpc_id == vpc.id).all() if s.application_id}
            names = [db.get(Application, a).name for a in apps]
            return {**base, "answer": f"VPC {vpc.name} hosts: {', '.join(names) or 'no mapped applications'}.",
                    "sources": [f"Cloud inventory {vpc.id}", "CMDB"], "related_assets": [vpc.id] + list(apps)}
        return {**base, "answer": "Please specify which VPC (e.g. vpc-payroll-prod-use1).", "confidence": "low"}

    if intent == "request_denied":
        req = tools.find_request(db, q)
        if req and req.policy_result:
            pr = req.policy_result
            reasons = "; ".join(pr.get("reasons", [])) or "no hard denials"
            return {**base, "answer": (
                f"Request {req.id} ({req.requested_cidr}) is '{req.status}'. "
                f"Policy status: {pr.get('status')}. Reasons: {reasons}."
            ), "risk_level": pr.get("risk_level", "medium"),
                "sources": [f"Policy result for {req.id}"] + pr.get("evidence", []),
                "related_assets": [req.id], "recommended_action": pr.get("recommended_action", "")}
        return {**base, "answer": "I couldn't find that request. Reference it by ID (e.g. req-overlap) or CIDR.",
                "confidence": "low"}

    if intent == "approvals_required":
        req = tools.find_request(db, q)
        if req:
            pol = req.policy_result or {}
            roles = pol.get("required_approvals", []) or req.required_approvals
            return {**base, "answer": f"Request {req.id} requires approvals from: {', '.join(roles) or 'none'}.",
                    "risk_level": pol.get("risk_level", "low"), "sources": [f"Policy result for {req.id}"],
                    "related_assets": [req.id]}
        return {**base, "answer": "Standard rule: every subnet needs network_admin; production adds approver; "
                "internet exposure and high/critical apps add security_reviewer.", "confidence": "medium"}

    if intent == "internet_facing_prod":
        rows = tools.internet_facing_prod_subnets(db)
        listing = ", ".join(f"{r['cidr']} ({r['owner']})" for r in rows) or "none found"
        return {**base, "answer": f"Internet-facing production subnets: {listing}.",
                "risk_level": "high" if rows else "low",
                "sources": ["Cloud inventory", "Security findings"],
                "related_assets": [r["id"] for r in rows],
                "recommended_action": "Confirm WAF and security approval for each exposed subnet."}

    if intent == "broad_rules":
        rows = tools.broad_firewall_rules(db)
        listing = "; ".join(f"{r['id']} {r['source']}->{r['destination']}:{r['port']} ({r['risk_level']})" for r in rows)
        return {**base, "answer": f"Firewall rules allowing broad access: {listing or 'none'}.",
                "risk_level": "high" if rows else "low", "sources": ["Firewall device inventory"],
                "related_assets": [r["id"] for r in rows],
                "recommended_action": "Narrow source CIDRs; require security review for any 0.0.0.0/0 rule."}

    if intent == "missing_owner":
        rows = tools.missing_owner_assets(db)
        return {**base, "answer": f"Assets missing an owner tag: {', '.join(r['cidr'] for r in rows) or 'none'}.",
                "risk_level": "medium" if rows else "low", "sources": ["Cloud inventory", "Security findings"],
                "related_assets": [r["id"] for r in rows],
                "recommended_action": "Assign owner + cost center and map to a CMDB application."}

    if intent == "unknown_assets":
        rows = tools.unknown_assets(db)
        return {**base, "answer": f"Unknown / unmapped assets (no CMDB application): {', '.join(r['cidr'] for r in rows) or 'none'}.",
                "risk_level": "medium" if rows else "low", "sources": ["CMDB reconciliation"],
                "related_assets": [r["id"] for r in rows]}

    if intent == "terraform_for_vpc":
        vpc = tools.find_vpc(db, q)
        if vpc:
            files = tools.terraform_files_for_vpc(db, vpc)
            return {**base, "answer": f"Terraform files for {vpc.name}: {', '.join(f['path'] for f in files) or 'none'}.",
                    "sources": [f["id"] for f in files], "related_assets": [vpc.id] + [f["id"] for f in files]}
        return {**base, "answer": "Please specify the VPC to look up Terraform files for.", "confidence": "low"}

    if intent in ("cidr_available", "suggest_subnet"):
        return _cidr_check_or_suggest(db, q, base)

    if intent == "risky_paths":
        paths = tools.risky_internet_paths(db)
        listing = "; ".join(f"{p['rule_name']} ({p['source']}) -> {p['target_cidr']}" for p in paths)
        return {**base, "answer": f"Risky internet->sensitive paths: {listing or 'none found'}.",
                "risk_level": "high" if paths else "low", "sources": ["Network graph", "Firewall inventory"],
                "related_assets": [p["firewall_rule"] for p in paths] + [p["target_subnet"] for p in paths],
                "recommended_action": "Remove or tightly scope internet-facing rules into sensitive subnets."}

    # general fallback
    return {**base, "answer": (
        "I can answer questions about ownership, subnets, VPCs, firewall rules, risk, "
        "IPAM availability, Terraform files and subnet requests. Try: "
        "'Who owns 10.50.10.0/24?' or 'Which production subnets are internet-facing?'"
    ), "confidence": "medium",
        "recommended_action": "Rephrase with a CIDR, VPC, application or request ID."}


def _cidr_check_or_suggest(db: Session, q: str, base: dict) -> dict:
    c = tools.extract_cidr(q)
    app = tools.find_application(db, q)
    bu_name = app.business_unit_id if app else None
    bu = db.get(BusinessUnit, bu_name) if bu_name else None
    env = _env_from_text(q)

    if c:
        # availability = no overlap with existing subnets
        from app.models import Subnet
        overlap = [s for s in db.query(Subnet).all() if tools.cidr.overlaps(c, s.cidr)]
        if overlap:
            return {**base, "answer": f"{c} is NOT available - it overlaps with {overlap[0].cidr} ({overlap[0].name}).",
                    "risk_level": "high", "sources": [s.id for s in overlap], "related_assets": [s.id for s in overlap],
                    "recommended_action": "Pick a non-overlapping range; I can suggest one."}
        return {**base, "answer": f"{c} appears available - no overlap with existing subnets.",
                "sources": ["IPAM", "Cloud inventory"],
                "recommended_action": "Submit a subnet request so the full policy check and approvals run."}

    # no CIDR provided -> suggest one
    if bu:
        s = tools.suggest_available_subnet(db, bu.name, env)
        if s.get("suggested_cidr"):
            return {**base, "answer": (
                f"I suggest {s['suggested_cidr']} for {bu.name} {env}. It is inside parent range "
                f"{s['parent_cidr']}, does not overlap existing subnets, and matches the {env} allocation pattern."
            ), "sources": [s["from_range"]], "related_assets": [s["from_range"]],
                "recommended_action": "Create a subnet request for this CIDR to run policy + approvals."}
    return {**base, "answer": "Tell me the business unit/application and environment and I'll suggest an available CIDR.",
            "confidence": "low"}


# --------------------------------------------------------------------------- #
# Mode 2: IaC proposal
# --------------------------------------------------------------------------- #
def _propose_iac(db: Session, text: str, conv: Conversation, user: str, role: str) -> dict:
    base = {"risk_level": "low", "confidence": "high", "sources": [], "related_assets": [],
            "recommended_action": "", "proposal": None}

    app = tools.find_application(db, text)
    if not app:
        return {**base, "confidence": "low", "answer": (
            "I need to know which application this is for before I can propose Terraform. "
            "Which application (e.g. HR Portal, Payroll API)?"
        )}

    bu = db.get(BusinessUnit, app.business_unit_id)
    env = _env_from_text(text)
    cidr_req = tools.extract_cidr(text)
    chosen_explanation = ""

    if not cidr_req:
        sugg = tools.suggest_available_subnet(db, bu.name if bu else "", env)
        cidr_req = sugg.get("suggested_cidr")
        if not cidr_req:
            return {**base, "confidence": "low", "answer": (
                f"I couldn't find an available range for {app.name} ({env}). "
                "Please specify a CIDR or business unit range."
            )}
        chosen_explanation = (
            f"I selected {cidr_req} because it is inside the {bu.name} parent range "
            f"{sugg.get('parent_cidr')}, does not overlap existing subnets, and matches the {env} "
            f"allocation pattern."
        )

    internet = "internet" in text.lower() or "public" in text.lower()
    params = {
        "requested_cidr": cidr_req, "vpc": _guess_vpc(db, app, env), "environment": env,
        "business_unit": bu.name if bu else "", "team": _team_name(db, app),
        "application": app.name, "owner": app.technical_owner or app.team_id,
        "cost_center": bu.cost_center if bu else "", "business_justification":
            f"LLM-assisted subnet provisioning for {app.name} ({env}): {text}",
        "data_classification": app.data_classification, "internet_exposure_required": internet,
    }

    # SAFETY: always run the policy engine; never bypass it.
    policy = tools.evaluate_change(db, params)

    if policy["status"] == "denied":
        # Explain + propose a safe alternative; do NOT generate a PR.
        alt = tools.suggest_available_subnet(db, bu.name if bu else "", env)
        audit.log(db, actor=user, role=role, action="llm_iac_proposal_generated",
                  target_type="conversation", target_id=conv.id, conversation_id=conv.id,
                  policy_result=policy, result="denied")
        return {**base, "risk_level": policy["risk_level"], "answer": (
            f"I can't propose Terraform for {cidr_req}: {('; '.join(policy['reasons']))}. "
            + (f"A safer alternative is {alt['suggested_cidr']} (no overlap, inside the approved range)."
               if alt.get("suggested_cidr") else "")
            + f" {SAFETY_NOTE}"
        ), "sources": ["Policy engine"] + policy.get("evidence", []),
            "recommended_action": policy.get("recommended_action", ""), "confidence": "high"}

    # Allowed/warning -> create a real request, validate, and generate a PR proposal.
    req = SubnetRequest(
        id=f"req-{uuid.uuid4().hex[:10]}", status="draft",
        requester_name=user, requester_email=f"{user}@acme.example",
        team=params["team"], application=app.name, business_unit=params["business_unit"],
        environment=env, requested_cidr=cidr_req, vpc=params["vpc"], cloud_provider="aws",
        region=app.environment and "us-east-1" or "us-east-1",
        business_justification=params["business_justification"],
        data_classification=app.data_classification, internet_exposure_required=internet,
        expected_traffic_pattern="north-south" if internet else "east-west",
        cost_center=params["cost_center"], owner=params["owner"], technical_owner=app.technical_owner,
    )
    db.add(req)
    db.commit()
    req = req_service.validate(db, req.id, actor=user, role="requester")
    pr = pr_generator.generate_pr(db, req, actor=user, role=role)

    audit.log(db, actor=user, role=role, action="llm_iac_proposal_generated",
              target_type="pull_request", target_id=pr.id, request_id=req.id,
              conversation_id=conv.id, pr_id=pr.id, policy_result=policy)

    answer = (
        f"Proposed Terraform PR for a {env} subnet ({cidr_req}) for {app.name}. "
        + (chosen_explanation + " " if chosen_explanation else "")
        + f"Policy status: {policy['status']} (risk {policy['risk_level']}). "
        f"Required reviewers: {', '.join(pr.reviewers) or 'none'}. {SAFETY_NOTE}"
    )
    return {**base, "risk_level": policy["risk_level"], "answer": answer,
            "sources": ["Network graph", "IPAM", "CMDB", "Policy engine", "Terraform state"],
            "related_assets": [app.id, req.id, pr.id, params["vpc"]],
            "recommended_action": "Route the PR to the listed reviewers for human approval.",
            "proposal": {
                "request_id": req.id, "pull_request_id": pr.id, "branch": pr.branch,
                "title": pr.title, "terraform": _extract_code(pr.terraform_diff),
                "files_changed": pr.files_changed, "reviewers": pr.reviewers,
                "policy_result": policy, "risk_summary": pr.risk_summary,
                "rollback_notes": pr.rollback_notes, "test_plan": pr.test_plan,
                "status": pr.status, "explanation": chosen_explanation,
            }}


def _extract_code(diff: str) -> str:
    return "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))


def _guess_vpc(db: Session, app: Application, env: str) -> str:
    from app.models import VPC
    vpcs = db.query(VPC).filter(VPC.business_unit_id == app.business_unit_id).all()
    for v in vpcs:
        if v.environment == env:
            return v.id
    return vpcs[0].id if vpcs else ""


def _team_name(db: Session, app: Application) -> str:
    from app.models import Team
    t = db.get(Team, app.team_id) if app.team_id else None
    return t.name if t else ""
