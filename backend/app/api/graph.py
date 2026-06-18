"""Network graph endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, identity
from app.services import rbac
from app.graph import graph_service

router = APIRouter(tags=["graph"])


@router.get("/graph")
def full_graph(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return graph_service.build_graph(db)


@router.get("/graph/path")
def graph_path(src: str, dst: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return graph_service.shortest_path(db, src, dst)


@router.get("/graph/node/{node_id}")
def graph_node(node_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    result = graph_service.neighbors(db, node_id)
    if not result:
        raise HTTPException(404, "Node not found")
    return result


@router.get("/graph/application/{app_id}")
def graph_application(app_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return graph_service.subgraph(db, app_id, depth=3)


@router.get("/graph/subnet/{subnet_id}")
def graph_subnet(subnet_id: str, db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return graph_service.subgraph(db, subnet_id, depth=2)


@router.get("/graph/risky-paths")
def risky_paths(db: Session = Depends(get_db), who=Depends(identity)):
    rbac.require(who["role"], "inventory:view")
    return graph_service.internet_to_sensitive_paths(db)
