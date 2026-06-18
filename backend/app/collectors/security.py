"""Mock security-signal collector.

Combines static findings with findings *derived* from the rest of the
inventory (missing owner tags, broad 0.0.0.0/0 rules, internet-facing prod,
unknown/unmapped assets) so the demo reflects real correlation logic.
"""
from app.collectors.base import BaseCollector
from app.seed import dataset


class SecurityCollector(BaseCollector):
    name = "security"
    source_system = "csmp-mock"

    def collect(self) -> dict:
        findings = list(dataset.STATIC_RISK_FINDINGS)

        # Derive: subnets missing an owner tag.
        for sn in dataset.SUBNETS:
            if not sn.get("owner"):
                findings.append({
                    "id": f"rf-missing-owner-{sn['id']}",
                    "type": "missing_tag", "severity": "medium",
                    "asset_type": "subnet", "asset_id": sn["id"],
                    "description": f"Subnet {sn['cidr']} ({sn['name']}) is missing a required owner tag.",
                    "recommendation": "Assign an owner and cost center; map to a CMDB application.",
                })
            if sn.get("application_id") is None:
                findings.append({
                    "id": f"rf-unknown-{sn['id']}",
                    "type": "unknown_asset", "severity": "medium",
                    "asset_type": "subnet", "asset_id": sn["id"],
                    "description": f"Subnet {sn['cidr']} is not mapped to any CMDB application.",
                    "recommendation": "Reconcile with CMDB and assign an owning application.",
                })

        # Derive: internet-facing production subnets.
        for sn in dataset.SUBNETS:
            if sn.get("internet_facing") and sn.get("environment") == "prod":
                findings.append({
                    "id": f"rf-internet-prod-{sn['id']}",
                    "type": "internet_exposure", "severity": "high",
                    "asset_type": "subnet", "asset_id": sn["id"],
                    "description": f"Production subnet {sn['cidr']} is internet-facing.",
                    "recommendation": "Verify exposure is required and security-approved.",
                })

        # Derive: overly broad firewall rules.
        for fw in dataset.FIREWALL_RULES:
            if fw["action"] == "allow" and (fw["source_cidr"] == "0.0.0.0/0" or fw["source_cidr"].endswith("/8")):
                findings.append({
                    "id": f"rf-broad-{fw['id']}",
                    "type": "overly_broad_rule", "severity": "high" if fw["source_cidr"] == "0.0.0.0/0" else "medium",
                    "asset_type": "firewall_rule", "asset_id": fw["id"],
                    "description": f"Firewall rule {fw['id']} allows broad source {fw['source_cidr']} to {fw['destination_cidr']}:{fw['port']}.",
                    "recommendation": "Narrow the source CIDR to the minimum required range.",
                })

        # De-duplicate by id (static + derived may overlap).
        seen, deduped = set(), []
        for f in findings:
            if f["id"] in seen:
                continue
            seen.add(f["id"])
            deduped.append(f)
        return {"risk_findings": deduped}
