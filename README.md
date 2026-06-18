# NetOps-AI — Network Discovery, Graph, LLM Intelligence & Subnet Governance

Two demos showing different UI styles and layouts:

- https://netgraph-copilot.vercel.app/
- https://netops-ai.vercel.app/

NetOps-AI is an enterprise MVP that **discovers network assets, builds a real-time network
graph, answers questions in natural language, detects risk, validates subnet requests,
and lets an LLM generate safe Infrastructure-as-Code pull-request proposals that still
require human approval.**

> It does not just show inventory — it **prevents unsafe infrastructure changes before
> they happen.**

## What it does

- **Discovery** across mock Cloud (AWS/Azure/GCP), IPAM (Infoblox-style), Firewall,
  CMDB (ServiceNow-style), Terraform/IaC state, and Security signals.
- **Property-graph** of applications, VPCs, subnets, workloads, firewall rules, routes,
  IPAM ranges, owners and Terraform files — with risky internet→sensitive path detection.
- **Policy engine** that blocks CIDR overlaps, missing ownership/tags, out-of-range
  allocations, wrong-team VPC access, and enforces production/internet/critical approval
  gates.
- **Subnet request workflow** with a full state machine and multi-role approvals.
- **Terraform PR generator** producing realistic diffs, reviewers, rollback and test
  plans (mock PR objects — no real Git calls).
- **LLM assistant** (offline rule-based, pluggable) for grounded Q&A and **safe IaC
  proposals** with strict safety controls.
- **RBAC + append-only audit log** over every action.

## Architecture

See [`docs/architecture.md`](docs/architecture.md). In short:

```
React/Vite frontend  →  FastAPI backend  →  Services (discovery, policy, graph,
workflow, IaC/PR, LLM assistant, audit, RBAC)  →  Collectors  →  SQLite + in-memory graph
```

## Project layout

```
NetOps-AI/
  backend/      FastAPI + SQLAlchemy + policy/graph/LLM services + pytest
  frontend/     React + Vite multi-page UI
  docs/         architecture, api, policies, llm-assistant, demo-flow
  run_backend.sh / run_frontend.sh
```

## Prerequisites

- Python 3.10+ and `pip`
- Node 18+ and `npm`

## Run the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py            # builds netops_ai.db and loads mock inventory + demo requests
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- The app also self-seeds on first startup if the DB is empty, so `seed.py` is optional
  but recommended (it prints what was loaded).
- Convenience: `./run_backend.sh` does venv + install + seed + serve.

## Run the frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api -> :8000)
```

Convenience: `./run_frontend.sh`.

## Run the tests

```bash
cd backend
pip install -r requirements.txt
pytest             # policy, workflow, assistant, and end-to-end API tests
```

## Seed the data

`python seed.py` drops/recreates the SQLite DB, runs all collectors via the discovery
service, and seeds four demo subnet requests (overlap-denied, valid, prod-two-approvals,
internet-needs-security-review). Set `NETOPS_AI_RESET=0` to keep existing data.

## Demo script

Follow [`docs/demo-flow.md`](docs/demo-flow.md) for a 10-step walkthrough:
discovery → graph → ask the LLM who owns a subnet → detect a CIDR overlap → get a safe
suggestion → create + validate a request → approve → generate a Terraform PR →
end-to-end LLM proposal → audit trail.

## Roles (mock auth)

Switch roles in the sidebar (sent as the `X-Role` header):
`requester`, `network_admin`, `security_reviewer`, `approver`, `auditor`, `admin`.
See [`docs/api.md`](docs/api.md) for the permission matrix and `curl` examples.

## Example generated Terraform

```hcl
resource "aws_subnet" "hr_portal_dev_private_1" {
  vpc_id            = var.vpc_hr_dev_use1_id
  cidr_block        = "10.42.18.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name               = "hr-portal-dev-private-1"
    Environment        = "dev"
    Application        = "hr_portal"
    Owner              = "HR Platform Team"
    CostCenter         = "HR-2042"
    DataClassification = "internal"
    BusinessUnit       = "hr"
    ManagedBy          = "terraform"
  }
}
```

## Configuration

Copy `backend/.env.example` → `.env` (or export vars):

| Var | Default | Notes |
|-----|---------|-------|
| `DATABASE_URL` | `sqlite:///./netops_ai.db` | Use a PostgreSQL URL in production |
| `LLM_PROVIDER` | `mock` | `mock` (offline) / `openai` / `azure` / `anthropic` |
| `LLM_API_KEY` | — | Required only for a real provider |
| `CORS_ORIGINS` | localhost:5173 | Comma-separated allowed origins |

## Deploy (Vercel)

Production: https://netops-ai.vercel.app/

```bash
npx vercel --prod
```

The repo root `vercel.json` deploys the Vite frontend and FastAPI backend (`/api/*`).

## Future production integrations

GitHub/GitLab PR creation · GitHub Actions + `terraform plan` · OPA/Conftest policy
checks · ServiceNow change requests · SSO/JWT auth · PostgreSQL · Neo4j behind the
graph abstraction. All are stubbed behind clean interfaces in the MVP.

## Safety model (LLM)

The assistant proposes; humans approve and merge. The LLM cannot approve its own PR,
merge, deploy, bypass the policy engine, or create production infra without the required
approvals. Every proposal is policy-checked and audited with its data sources. See
[`docs/llm-assistant.md`](docs/llm-assistant.md).
