# NetGov — Architecture

NetGov is an enterprise platform that discovers network assets, builds a real-time
network graph, answers natural-language questions about the network, validates subnet
and infrastructure requests against policy, and generates **safe Infrastructure-as-Code
pull-request proposals that always require human approval**.

The product is not just an inventory tool. Its core job is to **prevent unsafe
infrastructure changes before they happen**.

## High-level layers

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                                  │
│  Dashboard · Network Graph · Subnet Inventory · Firewall Rules ·          │
│  Subnet Request Form · Request Review · PR Preview · LLM Assistant · Audit │
└───────────────▲────────────────────────────────────────────────────────────┘
                │  REST / JSON  (X-Role mock auth header)
┌───────────────┴────────────────────────────────────────────────────────────┐
│  Backend API (FastAPI)                                                      │
│  discovery · assets · graph · subnet-requests · policy · iac/PRs ·          │
│  assistant · audit · dashboard                                              │
├──────────────────────────────────────────────────────────────────────────┤
│  Services                                                                   │
│   ┌────────────┐ ┌──────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐ │
│   │ Discovery  │ │ Policy Engine │ │  Graph    │ │ Workflow │ │ RBAC     │ │
│   └────────────┘ └──────────────┘ └───────────┘ └──────────┘ └──────────┘ │
│   ┌────────────────────────┐ ┌──────────────────┐ ┌────────────────────┐   │
│   │ IaC / PR Generator     │ │ Audit Logger     │ │ LLM Assistant Svc  │   │
│   └────────────────────────┘ └──────────────────┘ └────────────────────┘   │
├──────────────────────────────────────────────────────────────────────────┤
│  Collectors (read-only adapters)                                            │
│   Cloud(AWS/Azure/GCP) · IPAM(Infoblox) · Firewall · CMDB(ServiceNow) ·     │
│   Terraform/IaC · Security signals                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  Storage:  SQLite (SQLAlchemy)  +  in-memory property-graph projection      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Request → safe-change pipeline

```
Subnet request ─▶ Policy engine ─▶ (denied? explain + alternative)
                       │ allowed/warning
                       ▼
              Required approvals  ─▶  Human approvers (RBAC roles)
                       │ all satisfied
                       ▼
            IaC / PR generator  ─▶  Terraform diff + PR proposal (status: open)
                       │
                       ▼
            Human reviewer approves/merges (NetGov never self-merges)
                       │
                       ▼
                  Audit log (full trace)
```

## Data model (property graph)

Every table is a node type; foreign keys are edges. The graph service projects rows
into `{nodes, edges}` and supports neighbor lookup, shortest-path and focused
subgraphs without requiring an external graph database (the abstraction is
Neo4j-shaped so it can be swapped later).

**Entities:** Organization, Business Unit, Team, Owner, Application, Cloud Account,
VPC/VNet, Subnet, Workload (VM/K8s/LB/NAT/IGW/TGW), Security Group, Firewall Rule,
Route, IPAM Range, Terraform Module, Terraform File, Subnet Request, Pull Request,
Approval, Audit Event, Risk Finding, Conversation, Message.

**Key relationships:**

```
BusinessUnit ─owns→ Application ─runs_on→ Workload ─runs_inside→ Subnet
Subnet ─belongs_to→ VPC ─belongs_to→ CloudAccount
Subnet ─allocated_from→ IPAMRange
Team ─owns→ VPC
FirewallRule ─allows_to→ Subnet          SecurityGroup ─protects→ Workload
Route ─connects→ VPC/Subnet              TerraformFile ─defines→ Subnet/VPC
SubnetRequest ─validated_by→ PolicyResult ─implemented_by→ PullRequest
Approval ─approves→ PullRequest          RiskFinding ─affects→ Asset
```

## Backend module map

```
backend/app/
  api/          FastAPI routers (one per domain) + deps (mock auth) + serializers
  collectors/   read-only source adapters (cloud, ipam, firewall, cmdb, terraform, security)
  models/       SQLAlchemy ORM entities
  schemas/      Pydantic request/response models
  policies/     policy engine + CIDR math
  graph/        in-memory property-graph projection + path/subgraph queries
  services/     discovery orchestration, subnet-request workflow, RBAC
  iac/          Terraform code generation + mock PR generator
  llm/          assistant orchestration, pluggable provider, intent, retrieval tools
  audit/        append-only audit logger
  seed/         single mock "source-of-truth" dataset + collectors read slices
  tests/        pytest suite (policy, workflow, assistant, API)
```

## Design principles

- **Read-only discovery.** Collectors never mutate source systems.
- **Policy is the gate.** No request reaches PR generation without passing the engine,
  and the LLM cannot bypass it.
- **Human-in-the-loop.** The LLM proposes; humans approve and merge. NetGov never
  approves its own PR, merges, or deploys.
- **Everything is audited.** Discovery, policy evaluations, approvals, PRs and every
  LLM action are written to an append-only log with the data sources used.
- **Pluggable LLM.** A deterministic offline rule-based provider ships by default,
  behind an interface ready for OpenAI / Azure OpenAI / Anthropic / internal LLMs.

## Production integration points (stubbed for the MVP)

- GitHub / GitLab PR creation (currently mock PR objects).
- GitHub Actions + `terraform plan` in CI.
- OPA / Conftest policy checks alongside the internal engine.
- ServiceNow change-request creation/approval.
- SSO / JWT replacing the `X-Role` mock-auth header.
- PostgreSQL via `DATABASE_URL`; Neo4j behind the graph abstraction.
```
