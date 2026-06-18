"""Policy engine tests covering the key governance rules."""
from app.policies import engine, cidr


def base(**over):
    data = {
        "requested_cidr": "10.42.18.0/24", "vpc": "vpc-hr-dev-use1", "environment": "dev",
        "business_unit": "HR", "team": "HR Platform Team", "application": "Benefits Engine",
        "owner": "HR Platform Team", "cost_center": "HR-2042",
        "business_justification": "dev subnet", "data_classification": "internal",
        "internet_exposure_required": False,
    }
    data.update(over)
    return data


def test_valid_request_allowed(db):
    r = engine.evaluate(db, base())
    assert r["status"] == "allowed"
    assert r["required_approvals"] == ["network_admin"]


def test_overlap_denied(db):
    r = engine.evaluate(db, base(requested_cidr="10.42.10.128/25"))
    assert r["status"] == "denied"
    assert any("overlaps" in x for x in r["reasons"])
    assert r["risk_level"] in ("high", "critical")


def test_missing_owner_denied(db):
    r = engine.evaluate(db, base(owner=""))
    assert r["status"] == "denied"
    assert any("owner" in x.lower() for x in r["reasons"])


def test_outside_parent_range_denied(db):
    r = engine.evaluate(db, base(requested_cidr="172.16.0.0/24"))
    assert r["status"] == "denied"
    assert any("outside" in x.lower() for x in r["reasons"])


def test_prod_requires_two_approvals(db):
    r = engine.evaluate(db, base(environment="prod", vpc="vpc-hr-prod-use1",
                                 requested_cidr="10.43.40.0/24"))
    assert "network_admin" in r["required_approvals"]
    assert "approver" in r["required_approvals"]


def test_internet_requires_security_review(db):
    r = engine.evaluate(db, base(environment="prod", vpc="vpc-custplat-prod-use1",
                                 business_unit="Customer Platform", team="Customer Platform Team",
                                 application="Customer Login", requested_cidr="10.80.20.0/24",
                                 internet_exposure_required=True, cost_center="CP-6000",
                                 owner="Customer Platform Team", data_classification="confidential"))
    assert "security_reviewer" in r["required_approvals"]


def test_wrong_team_denied(db):
    r = engine.evaluate(db, base(team="Payroll Platform Team"))
    assert r["status"] == "denied"
    assert any("does not own" in x.lower() for x in r["reasons"])


def test_cidr_math():
    assert cidr.overlaps("10.42.10.128/25", "10.42.10.0/24")
    assert not cidr.overlaps("10.42.18.0/24", "10.42.10.0/24")
    assert cidr.contains("10.42.0.0/15", "10.42.18.0/24")
