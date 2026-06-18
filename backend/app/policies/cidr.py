"""Shared CIDR / IP math helpers used by the policy engine and IPAM logic."""
import ipaddress
from typing import Optional


def parse(cidr: str) -> Optional[ipaddress.IPv4Network]:
    try:
        return ipaddress.ip_network(cidr, strict=False)
    except (ValueError, TypeError):
        return None


def overlaps(a: str, b: str) -> bool:
    na, nb = parse(a), parse(b)
    if na is None or nb is None:
        return False
    return na.overlaps(nb)


def contains(parent: str, child: str) -> bool:
    """True if `child` is fully inside `parent`."""
    np, nc = parse(parent), parse(child)
    if np is None or nc is None:
        return False
    return nc.subnet_of(np) if nc.prefixlen >= np.prefixlen else False


def prefix_size(cidr: str) -> int:
    n = parse(cidr)
    return n.num_addresses if n else 0


def suggest_next_available(parent_cidr: str, prefixlen: int, taken: list[str]) -> Optional[str]:
    """Return the first /prefixlen subnet of parent that does not overlap taken."""
    parent = parse(parent_cidr)
    if parent is None or prefixlen < parent.prefixlen:
        return None
    taken_nets = [parse(c) for c in taken if parse(c)]
    for candidate in parent.subnets(new_prefix=prefixlen):
        if not any(candidate.overlaps(t) for t in taken_nets):
            return str(candidate)
    return None
