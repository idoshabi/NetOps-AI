"""Subnet request workflow + approvals + PR generation tests."""
import pytest
from app.services import subnet_request as svc
from app.iac import pr_generator
from app.models import SubnetRequest
from app.schemas import SubnetRequestCreate


def _make(db, **over):
    payload = SubnetRequestCreate(
        requester_name="Dana Whitfield", requester_email="dana@acme.example",
        team="HR Platform Team", application="HR Portal", business_unit="HR",
        environment="dev", requested_cidr="10.42.19.0/24", vpc="vpc-hr-dev-use1",
        cloud_provider="aws", region="us-east-1", business_justification="dev",
        data_classification="internal", internet_exposure_required=False,
        expected_traffic_pattern="east-west", cost_center="HR-2042",
        owner="HR Platform Team", technical_owner="Dana Whitfield", **over,
    )
    return svc.create(db, payload, actor="dana", role="requester")


def test_seeded_requests_states(db):
    states = {r.id: r.status for r in db.query(SubnetRequest).all()}
    assert states["req-overlap"] == "policy_failed"
    assert states["req-valid"] == "pending_approval"
    assert states["req-prod-two"] == "pending_approval"
    assert states["req-internet"] == "pending_approval"


def test_validate_then_approve_flow(db):
    req = _make(db)
    req = svc.validate(db, req.id, actor="dana", role="requester")
    assert req.status == "pending_approval"
    assert req.required_approvals == ["network_admin"]
    req = svc.add_approval(db, req.id, approver="Sam Rivera", role="network_admin")
    assert req.status == "approved"
    assert req.required_approvals == []


def test_prod_needs_two_distinct_approvals(db):
    req = svc.validate(db, "req-prod-two", actor="t", role="requester")
    assert set(req.required_approvals) == {"network_admin", "approver"}
    svc.add_approval(db, req.id, approver="Sam", role="network_admin")
    req = svc.add_approval(db, req.id, approver="Jordan", role="approver")
    assert req.status == "approved"


def test_pr_generation_after_approval(db):
    req = _make(db)
    svc.validate(db, req.id, actor="dana", role="requester")
    svc.add_approval(db, req.id, approver="Sam", role="network_admin")
    req = db.get(SubnetRequest, req.id)
    pr = pr_generator.generate_pr(db, req, actor="sam", role="network_admin")
    assert pr.branch.startswith("netops-ai/subnet/")
    assert "aws_subnet" in pr.terraform_diff
    assert pr.audit_event_id
    assert db.get(SubnetRequest, req.id).status == "pr_generated"


def test_wrong_role_cannot_satisfy_approval(db):
    req = svc.validate(db, "req-prod-two", actor="t", role="requester")
    with pytest.raises(Exception):
        # security_reviewer is not among the required roles for this request
        svc.add_approval(db, req.id, approver="Alex", role="security_reviewer")
