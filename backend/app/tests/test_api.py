"""End-to-end API tests via FastAPI TestClient + RBAC checks."""

ADMIN = {"X-Role": "admin", "X-Actor": "taylor"}
REQ = {"X-Role": "requester", "X-Actor": "dana"}
NET = {"X-Role": "network_admin", "X-Actor": "sam"}


def test_root_and_health(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/").json()["name"] == "NetOps-AI"


def test_dashboard_counts(client):
    d = client.get("/dashboard", headers=ADMIN).json()
    assert d["total_subnets"] >= 8
    assert d["internet_facing_prod"] >= 1
    assert d["missing_owner_tags"] >= 1


def test_inventory_endpoints(client):
    assert len(client.get("/subnets", headers=ADMIN).json()) >= 8
    assert len(client.get("/firewall-rules", headers=ADMIN).json()) >= 5
    assert len(client.get("/security-findings", headers=ADMIN).json()) >= 3
    assert client.get("/graph", headers=ADMIN).json()["stats"]["node_count"] > 0


def test_rbac_requester_cannot_view_audit(client):
    assert client.get("/audit/events", headers=REQ).status_code == 403
    assert client.get("/audit/events", headers=ADMIN).status_code == 200


def test_policy_evaluate_overlap(client):
    body = {"requested_cidr": "10.42.10.128/25", "vpc": "vpc-hr-dev-use1", "environment": "dev",
            "business_unit": "HR", "team": "HR Platform Team", "application": "HR Portal",
            "owner": "HR Platform Team", "cost_center": "HR-2042",
            "business_justification": "x", "data_classification": "internal"}
    r = client.post("/policy/evaluate", json=body, headers=NET).json()
    assert r["status"] == "denied"


def test_full_request_to_pr_flow(client):
    body = {"requester_name": "Dana", "requester_email": "dana@acme.example",
            "team": "HR Platform Team", "application": "HR Portal", "business_unit": "HR",
            "environment": "dev", "requested_cidr": "10.42.21.0/24", "vpc": "vpc-hr-dev-use1",
            "cloud_provider": "aws", "region": "us-east-1", "business_justification": "dev",
            "data_classification": "internal", "internet_exposure_required": False,
            "expected_traffic_pattern": "east-west", "cost_center": "HR-2042",
            "owner": "HR Platform Team", "technical_owner": "Dana"}
    req = client.post("/subnet/request", json=body, headers=REQ).json()
    rid = req["id"]
    client.post(f"/subnet/request/{rid}/validate", headers=REQ)
    client.post(f"/subnet/request/{rid}/approve",
                json={"approver": "Sam", "role": "network_admin"}, headers=NET)
    pr = client.post(f"/subnet/request/{rid}/generate-pr", headers=NET).json()
    assert "aws_subnet" in pr["terraform_diff"]
    # LLM cannot approve its own PR: a human role does it explicitly
    approved = client.post(f"/pull-requests/{pr['id']}/approve",
                           json={"approver": "Sam", "role": "network_admin"}, headers=NET).json()
    assert approved["status"] == "approved"


def test_assistant_ask_endpoint(client):
    r = client.post("/assistant/ask",
                    json={"question": "Show all firewall rules that allow broad access."},
                    headers=REQ).json()
    assert "fw-" in r["answer"]
    assert r["conversation_id"]
