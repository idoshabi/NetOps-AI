"""In-memory property-graph projection over the relational inventory.

Builds typed nodes + edges from the ORM rows. No external graph DB required;
the abstraction (`build_graph`, `neighbors`, `shortest_path`) is Neo4j-shaped so
it can be swapped for a real graph backend later.
"""
from collections import deque
from typing import Optional
from sqlalchemy.orm import Session

from app.models import (
    BusinessUnit, Team, Owner, Application, CloudAccount, VPC, Subnet,
    Workload, SecurityGroup, FirewallRule, Route, IPAMRange, TerraformFile, RiskFinding,
)
from app.policies import cidr


def _node(id, label, type_, **props):
    return {"id": id, "label": label, "type": type_, "props": props}


def build_graph(db: Session) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []

    def edge(src, dst, rel):
        if src and dst:
            edges.append({"source": src, "target": dst, "relation": rel})

    # ----- Nodes ---------------------------------------------------------
    for bu in db.query(BusinessUnit).all():
        nodes.append(_node(bu.id, bu.name, "business_unit", code=bu.code, parent_cidr=bu.parent_cidr))
    for t in db.query(Team).all():
        nodes.append(_node(t.id, t.name, "team"))
        edge(t.business_unit_id, t.id, "has_team")
    for o in db.query(Owner).all():
        nodes.append(_node(o.id, o.name, "owner", email=o.email, role=o.role))
        edge(o.team_id, o.id, "has_member")
    for app in db.query(Application).all():
        nodes.append(_node(app.id, app.name, "application", criticality=app.criticality,
                           environment=app.environment, data_classification=app.data_classification))
        edge(app.business_unit_id, app.id, "owns")
        edge(app.team_id, app.id, "operates")
    for ca in db.query(CloudAccount).all():
        nodes.append(_node(ca.id, ca.name, "cloud_account", provider=ca.provider, region=ca.region))
    for v in db.query(VPC).all():
        nodes.append(_node(v.id, v.name, "vpc", cidr=v.cidr, environment=v.environment, region=v.region))
        edge(v.cloud_account_id, v.id, "contains")
        edge(v.owner_team_id, v.id, "owns")
    for sn in db.query(Subnet).all():
        nodes.append(_node(sn.id, sn.name, "subnet", cidr=sn.cidr, environment=sn.environment,
                           internet_facing=sn.internet_facing, owner=sn.owner,
                           terraform_managed=sn.terraform_managed))
        edge(sn.id, sn.vpc_id, "belongs_to")
        edge(sn.application_id, sn.id, "uses")
        edge(sn.ipam_range_id, sn.id, "allocated_from")
        edge(sn.terraform_file_id, sn.id, "defines")
    for w in db.query(Workload).all():
        nodes.append(_node(w.id, w.name, "workload", kind=w.type, internet_facing=w.internet_facing))
        edge(w.subnet_id, w.id, "hosts")
        edge(w.application_id, w.id, "runs_on")
    for sg in db.query(SecurityGroup).all():
        nodes.append(_node(sg.id, sg.name, "security_group"))
        edge(sg.id, sg.workload_id, "protects")
    for fw in db.query(FirewallRule).all():
        nodes.append(_node(fw.id, fw.name, "firewall_rule", action=fw.action, risk_level=fw.risk_level,
                           port=fw.port, source=fw.source_cidr, destination=fw.destination_cidr,
                           internet_facing=fw.internet_facing))
        # Connect rule to subnets it references.
        for sn in db.query(Subnet).all():
            if cidr.overlaps(fw.destination_cidr, sn.cidr):
                edge(fw.id, sn.id, "allows_to")
            if cidr.overlaps(fw.source_cidr, sn.cidr):
                edge(sn.id, fw.id, "source_of")
    for r in db.query(Route).all():
        nodes.append(_node(r.id, r.route_table, "route", destination=r.destination_cidr, target=r.target))
        edge(r.vpc_id, r.id, "routes")
    for ip in db.query(IPAMRange).all():
        nodes.append(_node(ip.id, ip.cidr, "ipam_range", type=ip.type, owner=ip.owner))
        edge(ip.parent_id, ip.id, "parent_of")
    for tf in db.query(TerraformFile).all():
        nodes.append(_node(tf.id, tf.path, "terraform_file", repo=tf.repo_path, defines=tf.defines))
    for rf in db.query(RiskFinding).all():
        nodes.append(_node(rf.id, rf.type, "risk_finding", severity=rf.severity))
        edge(rf.id, rf.asset_id, "affects")

    return {"nodes": nodes, "edges": edges,
            "stats": {"node_count": len(nodes), "edge_count": len(edges)}}


def _adjacency(graph: dict) -> dict:
    adj: dict[str, list[tuple[str, str]]] = {}
    for e in graph["edges"]:
        adj.setdefault(e["source"], []).append((e["target"], e["relation"]))
        adj.setdefault(e["target"], []).append((e["source"], e["relation"]))  # undirected for pathing
    return adj


def neighbors(db: Session, node_id: str) -> dict:
    graph = build_graph(db)
    node = next((n for n in graph["nodes"] if n["id"] == node_id), None)
    if node is None:
        return {}
    related_edges = [e for e in graph["edges"] if e["source"] == node_id or e["target"] == node_id]
    related_ids = {e["source"] for e in related_edges} | {e["target"] for e in related_edges}
    related_ids.discard(node_id)
    related = [n for n in graph["nodes"] if n["id"] in related_ids]
    return {"node": node, "edges": related_edges, "related": related}


def shortest_path(db: Session, src: str, dst: str) -> dict:
    graph = build_graph(db)
    adj = _adjacency(graph)
    if src not in adj or dst not in adj:
        return {"found": False, "path": [], "hops": 0}
    prev: dict[str, tuple[str, str]] = {}
    q = deque([src])
    seen = {src}
    while q:
        cur = q.popleft()
        if cur == dst:
            break
        for nxt, rel in adj.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                prev[nxt] = (cur, rel)
                q.append(nxt)
    if dst not in seen:
        return {"found": False, "path": [], "hops": 0}
    chain, node = [], dst
    while node != src:
        parent, rel = prev[node]
        chain.append({"from": parent, "to": node, "relation": rel})
        node = parent
    chain.reverse()
    by_id = {n["id"]: n for n in graph["nodes"]}
    return {"found": True, "hops": len(chain), "path": chain,
            "nodes": [by_id[src]] + [by_id[c["to"]] for c in chain]}


def subgraph(db: Session, root_id: str, depth: int = 2) -> dict:
    """BFS-limited subgraph around a node (used for app/subnet focus views)."""
    graph = build_graph(db)
    adj = _adjacency(graph)
    if root_id not in {n["id"] for n in graph["nodes"]}:
        return {"nodes": [], "edges": []}
    keep = {root_id}
    frontier = {root_id}
    for _ in range(depth):
        nxt = set()
        for node in frontier:
            for neighbor, _rel in adj.get(node, []):
                if neighbor not in keep:
                    nxt.add(neighbor)
        keep |= nxt
        frontier = nxt
    nodes = [n for n in graph["nodes"] if n["id"] in keep]
    edges = [e for e in graph["edges"] if e["source"] in keep and e["target"] in keep]
    return {"nodes": nodes, "edges": edges, "root": root_id}


def internet_to_sensitive_paths(db: Session) -> list[dict]:
    """Find risky paths: internet-facing firewall rules that reach sensitive BUs."""
    results = []
    sensitive_subnets = (
        db.query(Subnet)
        .filter(Subnet.business_unit_id.in_(["bu-payroll", "bu-identity", "bu-data", "bu-custplat"]))
        .all()
    )
    for fw in db.query(FirewallRule).filter(FirewallRule.internet_facing == True).all():  # noqa: E712
        for sn in sensitive_subnets:
            if cidr.overlaps(fw.destination_cidr, sn.cidr):
                results.append({
                    "firewall_rule": fw.id, "rule_name": fw.name, "source": fw.source_cidr,
                    "target_subnet": sn.id, "target_cidr": sn.cidr, "risk_level": fw.risk_level,
                })
    return results
