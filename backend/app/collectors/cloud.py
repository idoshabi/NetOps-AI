"""Mock AWS/Azure/GCP cloud inventory collector."""
from app.collectors.base import BaseCollector
from app.seed import dataset


class CloudCollector(BaseCollector):
    name = "cloud"
    source_system = "aws/azure/gcp-mock"

    def collect(self) -> dict:
        return {
            "cloud_accounts": dataset.CLOUD_ACCOUNTS,
            "vpcs": dataset.VPCS,
            "subnets": dataset.SUBNETS,
            "workloads": dataset.WORKLOADS,
            "security_groups": dataset.SECURITY_GROUPS,
            "routes": dataset.ROUTES,
        }
