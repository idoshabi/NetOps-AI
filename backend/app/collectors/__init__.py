"""Discovery collectors.

Each collector is a read-only adapter over a 'source system'. In the MVP the
source systems are mocked in ``app.seed.dataset`` but the interface
(``collect() -> dict``) matches what a real Infoblox / ServiceNow / AWS
collector would expose, so they can be swapped without touching the discovery
service.
"""
from app.collectors.cloud import CloudCollector
from app.collectors.ipam import IPAMCollector
from app.collectors.firewall import FirewallCollector
from app.collectors.cmdb import CMDBCollector
from app.collectors.terraform import TerraformCollector
from app.collectors.security import SecurityCollector

ALL_COLLECTORS = [
    CMDBCollector,       # ownership first (apps/teams/BUs)
    CloudCollector,
    IPAMCollector,
    FirewallCollector,
    TerraformCollector,
    SecurityCollector,   # derives findings from everything above
]

__all__ = [
    "CloudCollector", "IPAMCollector", "FirewallCollector",
    "CMDBCollector", "TerraformCollector", "SecurityCollector", "ALL_COLLECTORS",
]
