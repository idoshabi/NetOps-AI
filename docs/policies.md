# NetGov — Policy Engine

The policy engine (`app/policies/engine.py`) is deterministic and pure given the DB
snapshot. It evaluates a subnet change and returns a structured result.

## Result shape

```json
{
  "status": "denied",            // allowed | warning | denied
  "risk_level": "high",          // low | medium | high | critical
  "reasons": ["..."],            // hard-deny explanations
  "warnings": ["..."],           // non-blocking concerns
  "required_approvals": ["network_admin", "security_reviewer"],
  "evidence": ["existing_subnet_payroll_prod", "ipam_range_hr_prod"],
  "recommended_action": "Resolve the denial reasons and resubmit."
}
```

## Rules

### Hard denials (status = denied)

| Rule | Explanation |
|------|-------------|
| Overlapping CIDR | Requested CIDR overlaps any existing subnet (evidence = subnet id) |
| Invalid CIDR | Not a valid IPv4 network |
| Missing owner | No owner — every subnet must have one |
| Missing environment | dev/staging/prod required |
| Missing justification | Business justification required |
| Missing cost center | Cost center tag required |
| Missing application mapping | Application must exist in the CMDB |
| Outside allowed range | CIDR not inside the requesting business unit's parent range |
| Team lacks VPC access | Requesting team does not own / is not delegated the target VPC |

### Approval gates (elevate required_approvals)

| Condition | Adds |
|-----------|------|
| Any subnet creation | `network_admin` (baseline) |
| Production environment | `approver` (→ two approvals total) |
| Internet exposure required | `security_reviewer` |
| High / critical application | `security_reviewer` |

### Warnings (status = warning, still approvable)

- Subnet can route to sensitive systems (transit-gateway route present).
- Firewall / exposure broadens access (internet exposure requested).
- Requested subnet larger than the standard /24.
- Application is high criticality.
- Data classification is confidential or regulated.
- Business unit hosts sensitive systems (Payroll / Identity / Data).

## Risk scoring

Risk starts at `low` and is escalated to the max of any triggered contribution:
overlap/missing-field → high; internet exposure → high; critical app → high; prod,
sensitive data, large subnet, sensitive routing → medium. Any denial is at least high.

## Worked examples (from seed data)

| Request | CIDR | Outcome | Why |
|---------|------|---------|-----|
| `req-overlap` | 10.42.10.128/25 | **denied** | Overlaps `10.42.10.0/24` (sn-hr-dev-private) |
| `req-valid` | 10.42.18.0/24 | **allowed** | Inside HR parent range, no overlap, dev |
| `req-prod-two` | 10.43.40.0/24 | **warning**, 2 approvals | Production → network_admin + approver |
| `req-internet` | 10.80.20.0/24 | **warning**, 3 approvals | Prod + internet + high-criticality app → adds security_reviewer |

## Extending

Add a rule by appending to `evaluate()` — push a string to `reasons` (deny) or
`warnings`, add roles to `required`, push source ids to `evidence`, and escalate
`risk` via `_max_risk`. A future version can delegate to OPA/Conftest for the same
contract.
