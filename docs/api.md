# NetGov — API Reference

Base URL (dev): `http://localhost:8000`. Interactive docs at `/docs` (Swagger) and
`/redoc`. The Vite dev server proxies `/api/*` → backend.

## Authentication (mock)

Every request carries two headers (defaults shown). In production these are derived
from a verified SSO/JWT token.

```
X-Actor: dana          # the acting user
X-Role:  network_admin # one of: requester|network_admin|security_reviewer|approver|auditor|admin
```

## Discovery & inventory

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| POST | `/discovery/run` | discovery:run | Run all collectors, upsert inventory |
| GET | `/discovery/status` | — | Last run summary |
| GET | `/assets` | inventory:view | All assets (typed) |
| GET | `/assets/{id}` | inventory:view | One asset |
| GET | `/subnets` | inventory:view | Subnet inventory |
| GET | `/vpcs` | inventory:view | VPCs / VNets |
| GET | `/applications` | inventory:view | Applications (CMDB) |
| GET | `/owners` | inventory:view | Owners |
| GET | `/firewall-rules` | inventory:view | Firewall rules |
| GET | `/routes` | inventory:view | Route tables |
| GET | `/security-findings` | inventory:view | Risk findings |
| GET | `/dashboard` | inventory:view | Aggregated dashboard metrics |

## Graph

| Method | Path | Description |
|--------|------|-------------|
| GET | `/graph` | Full `{nodes, edges, stats}` |
| GET | `/graph/node/{id}` | Node + neighbors |
| GET | `/graph/path?src=&dst=` | Shortest path between two nodes |
| GET | `/graph/application/{appId}` | Focused subgraph around an application |
| GET | `/graph/subnet/{subnetId}` | Focused subgraph around a subnet |
| GET | `/graph/risky-paths` | Internet → sensitive-subnet paths |

## Subnet requests

| Method | Path | Description |
|--------|------|-------------|
| POST | `/subnet/request` | Create (draft) |
| GET | `/subnet/request` | List |
| GET | `/subnet/request/{id}` | Detail + approvals |
| POST | `/subnet/request/{id}/validate` | Run policy → pending_approval / policy_failed |
| POST | `/subnet/request/{id}/approve` | Record an approval |
| POST | `/subnet/request/{id}/reject` | Reject |
| POST | `/subnet/request/{id}/generate-pr` | Generate Terraform PR proposal |

## Policy

| Method | Path | Description |
|--------|------|-------------|
| POST | `/policy/evaluate` | Evaluate an ad-hoc change (no persistence) |
| GET | `/policy/results/{requestId}` | Stored policy result for a request |

## IaC / Pull requests

| Method | Path | Description |
|--------|------|-------------|
| POST | `/iac/generate` | Generate PR for an existing request |
| POST | `/iac/propose-change` | LLM natural-language IaC proposal |
| GET | `/pull-requests` | List PR proposals |
| GET | `/pull-requests/{id}` | PR detail (diff, reviewers, plan) |
| POST | `/pull-requests/{id}/approve` | Human approval |
| POST | `/pull-requests/{id}/reject` | Human rejection |

## Assistant

| Method | Path | Description |
|--------|------|-------------|
| POST | `/assistant/ask` | Read-only Q&A (mode 1) |
| POST | `/assistant/propose-iac` | IaC proposal (mode 2) |
| GET | `/assistant/conversations` | List conversations |
| GET | `/assistant/conversations/{id}` | Conversation transcript |

## Audit

| Method | Path | Description |
|--------|------|-------------|
| GET | `/audit/events?action=&request_id=&limit=` | Filterable audit log |
| GET | `/audit/events/{id}` | One event |

## Example calls

```bash
# 1. Re-run discovery
curl -s -XPOST localhost:8000/discovery/run -H 'X-Role: admin'

# 2. Dashboard
curl -s localhost:8000/dashboard -H 'X-Role: admin'

# 3. Evaluate an overlapping CIDR (expect DENIED)
curl -s -XPOST localhost:8000/policy/evaluate -H 'X-Role: network_admin' \
  -H 'Content-Type: application/json' -d '{
    "requested_cidr":"10.42.10.128/25","vpc":"vpc-hr-dev-use1","environment":"dev",
    "business_unit":"HR","team":"HR Platform Team","application":"HR Portal",
    "owner":"HR Platform Team","cost_center":"HR-2042","business_justification":"x"}'

# 4. Create + validate a valid request
RID=$(curl -s -XPOST localhost:8000/subnet/request -H 'X-Role: requester' \
  -H 'Content-Type: application/json' -d '{
    "requester_name":"Dana","requester_email":"dana@acme.example","team":"HR Platform Team",
    "application":"HR Portal","business_unit":"HR","environment":"dev",
    "requested_cidr":"10.42.18.0/24","vpc":"vpc-hr-dev-use1","cloud_provider":"aws",
    "region":"us-east-1","business_justification":"dev subnet","data_classification":"internal",
    "internet_exposure_required":false,"expected_traffic_pattern":"east-west",
    "cost_center":"HR-2042","owner":"HR Platform Team","technical_owner":"Dana"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
curl -s -XPOST localhost:8000/subnet/request/$RID/validate -H 'X-Role: requester'

# 5. Approve (network_admin) then generate PR
curl -s -XPOST localhost:8000/subnet/request/$RID/approve -H 'X-Role: network_admin' \
  -H 'Content-Type: application/json' -d '{"approver":"Sam","role":"network_admin"}'
curl -s -XPOST localhost:8000/subnet/request/$RID/generate-pr -H 'X-Role: network_admin'

# 6. Ask the assistant
curl -s -XPOST localhost:8000/assistant/ask -H 'X-Role: requester' \
  -H 'Content-Type: application/json' -d '{"question":"Who owns the payroll production subnet?"}'

# 7. LLM IaC proposal
curl -s -XPOST localhost:8000/assistant/propose-iac -H 'X-Role: network_admin' \
  -H 'Content-Type: application/json' -d '{"request":"Create a new dev subnet for the HR application."}'
```
