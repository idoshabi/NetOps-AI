"""Discovery + inventory endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, identity
from app.api.serializers import row_to_dict, rows
from app.services import discovery
from app.services import rbac
from app.models import (
    Subnet, VPC, Application, Owner, FirewallRule, Route, RiskFinding, Workload,
)

router = APIRouter(tags=["discovery"])

ASSET_MODELS = {"subnet": Subnet, "vpc": VPC, "workload": Workload,
                "application": Application, "firewall_rule": FirewallRule}


@router.post("/discovery/run")
def run_discovery(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "discovery:run")
    return discovery.run_discovery(db, actor=who["actor"], role=who["role"])


@router.get("/discovery/status")
def discovery_status():
    return discovery.status()


@router.get("/assets")
def list_assets(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    out = []
    for t, model in ASSET_MODELS.items():
        for r in db.query(model).all():
            d = row_to_dict(r)
            d["_asset_type"] = t
            out.append(d)
    return {"count": len(out), "assets": out}


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    for model in ASSET_MODELS.values():
        r = db.get(model, asset_id)
        if r:
            return row_to_dict(r)
    raise HTTPException(404, "Asset not found")


@router.get("/subnets")
def list_subnets(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return rows(db.query(Subnet).all())


@router.get("/vpcs")
def list_vpcs(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return rows(db.query(VPC).all())


@router.get("/applications")
def list_applications(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return rows(db.query(Application).all())


@router.get("/owners")
def list_owners(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return rows(db.query(Owner).all())


@router.get("/firewall-rules")
def list_firewall_rules(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return rows(db.query(FirewallRule).all())


@router.get("/routes")
def list_routes(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return rows(db.query(Route).all())


@router.get("/security-findings")
def list_findings(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return rows(db.query(RiskFinding).all())
