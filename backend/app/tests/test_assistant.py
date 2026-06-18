"""LLM assistant tests: Q&A grounding + IaC proposal safety."""
from app.llm import assistant
from app.models import PullRequest, AuditEvent


def ask(db, q):
    return assistant.ask(db, q, conversation_id=None, user="demo", role="admin")


def test_owner_lookup_has_evidence(db):
    a = ask(db, "Who owns the payroll production subnet?")
    assert "Payroll" in a["answer"]
    assert a["sources"]
    assert a["related_assets"]


def test_internet_facing_query(db):
    a = ask(db, "Which production subnets are internet-facing?")
    assert "10.80.10.0/24" in a["answer"]
    assert a["risk_level"] == "high"


def test_cidr_overlap_check(db):
    a = ask(db, "Can I create 10.42.10.128/25 for HR dev?")
    assert "NOT available" in a["answer"]


def test_suggest_available(db):
    a = ask(db, "Suggest an available subnet for HR dev.")
    assert "10.42" in a["answer"]


def test_iac_proposal_creates_pr_and_audit(db):
    before = db.query(PullRequest).count()
    a = assistant.propose_iac(db, "Create a new dev subnet for the HR application.",
                              conversation_id=None, user="demo", role="network_admin")
    assert a["proposal"] is not None
    assert a["proposal"]["pull_request_id"]
    assert "aws_subnet" in a["proposal"]["terraform"]
    assert db.query(PullRequest).count() == before + 1
    # safety: every proposal is audited
    assert db.query(AuditEvent).filter(AuditEvent.action == "llm_iac_proposal_generated").count() >= 1


def test_iac_denied_returns_alternative_no_pr(db):
    before = db.query(PullRequest).count()
    a = assistant.propose_iac(db, "Create a subnet 10.42.10.128/25 for the HR application.",
                              conversation_id=None, user="demo", role="network_admin")
    assert a["proposal"] is None            # denied -> no PR
    assert "can't propose" in a["answer"].lower() or "safer alternative" in a["answer"].lower()
    assert db.query(PullRequest).count() == before   # no PR created on denial


def test_low_confidence_asks_for_clarification(db):
    a = assistant.propose_iac(db, "Create a subnet please.",
                              conversation_id=None, user="demo", role="network_admin")
    assert a["confidence"] == "low"
    assert a["proposal"] is None
