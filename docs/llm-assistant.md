# NetOps-AI — LLM Assistant Service

> "Ask the network in natural language, understand ownership and risk, and generate
> safe Terraform PR proposals with governance built in."

## Two modes

**Mode 1 — Read-only Q&A.** Answers questions about topology, ownership, risk, IPAM
availability, firewall exposure, Terraform files and request history. Every answer is
grounded with evidence.

**Mode 2 — IaC proposal.** Produces a Terraform **PR proposal** for a natural-language
request. It never approves, merges, or deploys.

## Answer contract

```json
{
  "answer": "Subnet 10.50.10.0/24 is owned by the Payroll Platform Team and supports Payroll API.",
  "risk_level": "medium",
  "confidence": "high",
  "sources": ["CMDB application app-payroll-api", "IPAM range ipam-payroll-app", "Terraform file network/payroll/subnets.tf"],
  "related_assets": ["sn-payroll-prod-app", "app-payroll-api", "vpc-payroll-prod-use1"],
  "recommended_action": "Review broad firewall rule fw-102 ...",
  "intent": "owner_lookup",
  "conversation_id": "conv-…",
  "proposal": null
}
```

## Internal components

```
intent classifier ─▶ retrieval/context builder (tools) ─▶ provider (render)
        │                     │
        │            ┌────────┴─────────────────────────────────┐
        │            graph tool · IPAM tool · CMDB tool ·         
        │            policy tool · IaC generator · PR generator   
        ▼                                                         
  qa  → grounded answer + evidence                                
  iac → suggest CIDR → policy check → (deny: explain+alt) / (ok: request+PR proposal)
        ▼
   audit logger (every question + every proposal)
```

- **Intent classifier** (`llm/intent.py`): rule/keyword router → intent + mode + confidence.
- **Tools** (`llm/tools.py`): the *only* way the assistant touches data; each returns
  evidence (source ids).
- **Provider** (`llm/provider.py`): `MockProvider` (offline, deterministic) behind an
  interface ready for OpenAI / Azure OpenAI / Anthropic / internal LLMs.
- **Orchestrator** (`llm/assistant.py`): runs the pipeline and enforces safety.

## IaC proposal pipeline (mode 2)

1. Classify intent. 2. Identify the application (else ask for clarification).
3. Resolve business unit + environment. 4. Suggest an available CIDR from IPAM if none
given. 5. Resolve the target VPC and ownership. 6. **Run the policy engine.**
7. If denied → explain + propose a safe alternative, **no PR**. 8. If allowed/warning →
create a real subnet request, validate it, generate a Terraform PR proposal, assign
reviewers from the required approval roles, and explain the choice.
9. Log `llm_iac_proposal_generated` with the data sources used.

Example explanation:

> "I selected 10.42.18.0/24 because it is inside the HR parent range 10.42.0.0/16, does
> not overlap with existing subnets, matches the dev allocation pattern, and is
> associated with the approved VPC vpc-hr-dev-use1."

## Safety guarantees (enforced in code)

- The LLM **cannot** approve its own PR, merge, or deploy.
- The LLM **cannot** bypass the policy engine — every proposal is policy-evaluated.
- The LLM **cannot** create production infrastructure without the required approvals;
  PRs are created with status `open` and required-reviewer roles.
- Denied requests yield an explanation + safe alternative, never a PR.
- Low confidence → ask for clarification instead of generating IaC.
- Every question and proposal is written to the audit log with sources.
- No secrets, tokens, or credential values are stored or emitted.

## Example questions the assistant handles

Who owns this subnet? · Which application uses this VPC? · Is this CIDR available? ·
Why was this request denied? · What approvals are required? · Which production subnets
are internet-facing? · Show firewall rules with broad access · Which resources are
missing owner tags? · Which Terraform files define this VPC? · Show risky paths from
the internet to sensitive systems · Suggest an available subnet for HR dev ·
Create a new dev subnet for the HR application.

## Wiring a real model

Set `LLM_PROVIDER=openai|azure|anthropic` and `LLM_API_KEY`, then implement
`OpenAICompatibleProvider.complete()` in `llm/provider.py`. The orchestration, tools,
policy gating and audit logging are unchanged — only the natural-language rendering and
(optionally) the intent router move to the model.
