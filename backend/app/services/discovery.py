"""Discovery orchestration: run collectors and upsert inventory into the DB."""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.collectors import ALL_COLLECTORS
from app.audit import logger as audit
from app.models import (
    Organization, BusinessUnit, Team, Owner, Application, CloudAccount, VPC,
    Subnet, Workload, SecurityGroup, FirewallRule, Route, IPAMRange,
    TerraformModule, TerraformFile, RiskFinding,
)

# table name -> ORM model
TABLE_MODELS = {
    "organizations": Organization, "business_units": BusinessUnit, "teams": Team,
    "owners": Owner, "applications": Application, "cloud_accounts": CloudAccount,
    "vpcs": VPC, "subnets": Subnet, "workloads": Workload,
    "security_groups": SecurityGroup, "firewall_rules": FirewallRule, "routes": Route,
    "ipam_ranges": IPAMRange, "terraform_modules": TerraformModule,
    "terraform_files": TerraformFile, "risk_findings": RiskFinding,
}

# Last completed run summary (in-memory status, like a job tracker).
_LAST_RUN: dict = {"run_id": None, "status": "never_run", "counts": {}, "sources": []}


def run_discovery(db: Session, actor: str = "system", role: str = "admin") -> dict:
    run_id = f"run-{uuid.uuid4().hex[:10]}"
    started = datetime.now(timezone.utc)
    audit.log(db, actor=actor, role=role, action="discovery_run_started",
              target_type="discovery", target_id=run_id)

    counts: dict[str, int] = {}
    sources: list[str] = []
    for collector_cls in ALL_COLLECTORS:
        collector = collector_cls()
        sources.append(collector.source_system)
        for table, records in collector.collect().items():
            model = TABLE_MODELS.get(table)
            if not model:
                continue
            for rec in records:
                db.merge(model(**rec))  # upsert by primary key
            counts[table] = counts.get(table, 0) + len(records)
    db.commit()

    completed = datetime.now(timezone.utc)
    audit.log(db, actor=actor, role=role, action="discovery_run_completed",
              target_type="discovery", target_id=run_id,
              policy_result={"counts": counts})

    global _LAST_RUN
    _LAST_RUN = {
        "run_id": run_id, "status": "completed", "counts": counts,
        "sources": sources, "started_at": started, "completed_at": completed,
    }
    return _LAST_RUN


def status() -> dict:
    return _LAST_RUN
