# NetOps-AI — Demo Flow

A ~5-minute scripted walkthrough that shows discovery → understanding → risk →
validation → governed change. Start the backend and frontend (see the README), then
open http://localhost:5173.

## 1. Discovery & Dashboard
- The backend seeds itself on first boot (or run `python seed.py`).
- Open **Dashboard**. Point out: total assets, internet-facing prod (≥1), high-risk
  firewall rules, missing owner tags (≥1), pending requests, recent audit events.
- Click **Re-run discovery** to show the collector pipeline (cloud, IPAM, firewall,
  CMDB, Terraform, security) populating inventory.

## 2. Network Graph
- Open **Network Graph**. Click a legend type (e.g. `subnet`) to focus; click a node
  to inspect owner, environment, risk and source.
- Scroll to **Risky internet → sensitive paths**: `fw-101` exposes the customer portal
  subnet from `0.0.0.0/0`.

## 3. Ask the LLM who owns something
- Open **LLM Assistant**. Ask: **"Who owns the payroll production subnet?"**
- Answer cites CMDB (Payroll API), IPAM range and the Terraform file — with evidence
  and a recommended next action.

## 4. Detect an unsafe request (CIDR overlap)
- Ask: **"Can I create 10.42.10.128/25 for HR dev?"**
- The assistant reports it is **NOT available** — it overlaps `10.42.10.0/24`.

## 5. Get a safe suggestion
- Ask: **"Suggest an available subnet for HR dev."**
- The assistant proposes **10.42.18.0/24** and explains why (inside the HR parent
  range, no overlap, matches the dev pattern).

## 6. Create the request and watch policy validate it
- Open **New Subnet Request** (pre-filled with the valid HR dev request).
- Click **Preview policy** → status **ALLOWED**, required approval `network_admin`.
- (Optional) change the CIDR to `10.42.10.128/25` and preview again → **DENIED** with
  the overlap reason and evidence.
- Click **Submit request** → routed to the Request Review page.

## 7. Approvals
- On **Request Review**, see policy result, risk, required approvals and actions.
- Switch the sidebar role to **network_admin** and click **Approve**.
- For the seeded **req-prod-two** (production), note it needs *two* approvals
  (network_admin + approver); for **req-internet**, it also needs security_reviewer.

## 8. Generate the Terraform PR proposal
- Once approved, click **Generate Terraform PR**.
- The **PR Preview** shows title, branch, description, reviewers, the Terraform diff,
  policy summary, rollback plan, test plan, and the audit event id.
- Approve/Reject the PR as a human — NetOps-AI never self-merges.

## 9. End-to-end via the assistant (mode 2)
- Back in **LLM Assistant**, ask: **"Create a new dev subnet for the HR application."**
- The assistant queries graph/IPAM/CMDB, runs the policy engine, generates Terraform,
  produces a PR proposal with reviewers, explains its CIDR choice, and links to the PR
  — all logged to the audit trail.

## 10. Audit trail
- Open **Audit Log** (role auditor/admin/reviewer). Every step above is present:
  `discovery_run_*`, `policy_evaluated`, `subnet_request_*`, `approval_added`,
  `pr_generated`, `llm_question_asked`, `llm_iac_proposal_generated`.

## CLI equivalent
See `docs/api.md` → "Example calls" for a `curl` script that performs steps 3–7.
