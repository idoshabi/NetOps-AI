"""Mock Infoblox/BlueCat-style IPAM collector."""
from app.collectors.base import BaseCollector
from app.seed import dataset


class IPAMCollector(BaseCollector):
    name = "ipam"
    source_system = "infoblox-mock"

    def collect(self) -> dict:
        return {"ipam_ranges": dataset.IPAM_RANGES}
