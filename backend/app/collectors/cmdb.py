"""Mock ServiceNow-style CMDB collector: ownership, apps, teams, BUs."""
from app.collectors.base import BaseCollector
from app.seed import dataset


class CMDBCollector(BaseCollector):
    name = "cmdb"
    source_system = "servicenow-mock"

    def collect(self) -> dict:
        return {
            "organizations": [dataset.ORGANIZATION],
            "business_units": dataset.BUSINESS_UNITS,
            "teams": dataset.TEAMS,
            "owners": dataset.OWNERS,
            "applications": dataset.APPLICATIONS,
        }
