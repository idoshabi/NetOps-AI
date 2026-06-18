"""Mock firewall / network device collector."""
from app.collectors.base import BaseCollector
from app.seed import dataset


class FirewallCollector(BaseCollector):
    name = "firewall"
    source_system = "panorama-mock"

    def collect(self) -> dict:
        # Routes are also surfaced by the cloud collector; firewall device
        # owns rule data. Discovery upserts so duplicates are harmless.
        return {"firewall_rules": dataset.FIREWALL_RULES}
