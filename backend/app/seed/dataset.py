"""Single source of mock 'source-system' truth.

Each collector reads its slice from here. IDs are stable across slices so the
discovery service can wire foreign keys (a subnet -> its application, ipam range
and terraform file) just like a real correlation engine would.

This models a fictional enterprise with HR, Payroll, Identity, Finance,
Customer Platform and Data & Analytics business units across AWS / Azure / GCP.
"""

ORGANIZATION = {"id": "org-1", "name": "Acme Enterprises"}

# --------------------------------------------------------------------------- #
# CMDB slice: business units, teams, owners, applications
# --------------------------------------------------------------------------- #
BUSINESS_UNITS = [
    {"id": "bu-hr", "name": "HR", "code": "HR", "cost_center": "HR-2042", "parent_cidr": "10.42.0.0/15", "org_id": "org-1"},
    {"id": "bu-payroll", "name": "Payroll", "code": "PAY", "cost_center": "PAY-3050", "parent_cidr": "10.50.0.0/16", "org_id": "org-1"},
    {"id": "bu-identity", "name": "Identity", "code": "IDN", "cost_center": "IDN-4010", "parent_cidr": "10.60.0.0/16", "org_id": "org-1"},
    {"id": "bu-finance", "name": "Finance", "code": "FIN", "cost_center": "FIN-5001", "parent_cidr": "10.55.0.0/16", "org_id": "org-1"},
    {"id": "bu-custplat", "name": "Customer Platform", "code": "CP", "cost_center": "CP-6000", "parent_cidr": "10.80.0.0/16", "org_id": "org-1"},
    {"id": "bu-data", "name": "Data & Analytics", "code": "DA", "cost_center": "DA-7000", "parent_cidr": "10.70.0.0/16", "org_id": "org-1"},
]

TEAMS = [
    {"id": "team-hr-platform", "name": "HR Platform Team", "business_unit_id": "bu-hr"},
    {"id": "team-payroll-platform", "name": "Payroll Platform Team", "business_unit_id": "bu-payroll"},
    {"id": "team-identity", "name": "Identity Team", "business_unit_id": "bu-identity"},
    {"id": "team-custplat", "name": "Customer Platform Team", "business_unit_id": "bu-custplat"},
    {"id": "team-data", "name": "Data Platform Team", "business_unit_id": "bu-data"},
    {"id": "team-finance", "name": "Finance Systems Team", "business_unit_id": "bu-finance"},
    {"id": "team-network", "name": "Cloud Network Engineering", "business_unit_id": None},
    {"id": "team-security", "name": "Security Engineering", "business_unit_id": None},
]

OWNERS = [
    {"id": "own-hr-lead", "name": "Dana Whitfield", "email": "dana.whitfield@acme.example", "role": "requester", "team_id": "team-hr-platform"},
    {"id": "own-payroll-lead", "name": "Marcus Lee", "email": "marcus.lee@acme.example", "role": "requester", "team_id": "team-payroll-platform"},
    {"id": "own-identity-lead", "name": "Priya Nair", "email": "priya.nair@acme.example", "role": "requester", "team_id": "team-identity"},
    {"id": "own-netadmin", "name": "Sam Rivera", "email": "sam.rivera@acme.example", "role": "network_admin", "team_id": "team-network"},
    {"id": "own-secrev", "name": "Alex Chen", "email": "alex.chen@acme.example", "role": "security_reviewer", "team_id": "team-security"},
    {"id": "own-approver", "name": "Jordan Blake", "email": "jordan.blake@acme.example", "role": "approver", "team_id": "team-hr-platform"},
    {"id": "own-auditor", "name": "Robin Diaz", "email": "robin.diaz@acme.example", "role": "auditor", "team_id": "team-security"},
    {"id": "own-admin", "name": "Taylor Kim", "email": "taylor.kim@acme.example", "role": "admin", "team_id": "team-network"},
]

APPLICATIONS = [
    {"id": "app-hr-portal", "name": "HR Portal", "business_owner": "Dana Whitfield", "technical_owner": "HR Platform Team", "team_id": "team-hr-platform", "business_unit_id": "bu-hr", "environment": "prod", "criticality": "high", "compliance_scope": "SOX", "data_classification": "internal"},
    {"id": "app-payroll-api", "name": "Payroll API", "business_owner": "Marcus Lee", "technical_owner": "Payroll Platform Team", "team_id": "team-payroll-platform", "business_unit_id": "bu-payroll", "environment": "prod", "criticality": "critical", "compliance_scope": "SOX,PCI", "data_classification": "confidential"},
    {"id": "app-identity-svc", "name": "Identity Service", "business_owner": "Priya Nair", "technical_owner": "Identity Team", "team_id": "team-identity", "business_unit_id": "bu-identity", "environment": "prod", "criticality": "critical", "compliance_scope": "SOC2", "data_classification": "confidential"},
    {"id": "app-customer-login", "name": "Customer Login", "business_owner": "Jordan Blake", "technical_owner": "Customer Platform Team", "team_id": "team-custplat", "business_unit_id": "bu-custplat", "environment": "prod", "criticality": "high", "compliance_scope": "GDPR", "data_classification": "confidential"},
    {"id": "app-data-warehouse", "name": "Data Warehouse", "business_owner": "Robin Diaz", "technical_owner": "Data Platform Team", "team_id": "team-data", "business_unit_id": "bu-data", "environment": "prod", "criticality": "high", "compliance_scope": "GDPR", "data_classification": "regulated"},
    {"id": "app-benefits-engine", "name": "Benefits Engine", "business_owner": "Dana Whitfield", "technical_owner": "HR Platform Team", "team_id": "team-hr-platform", "business_unit_id": "bu-hr", "environment": "prod", "criticality": "medium", "compliance_scope": "", "data_classification": "internal"},
]

# --------------------------------------------------------------------------- #
# Cloud slice
# --------------------------------------------------------------------------- #
CLOUD_ACCOUNTS = [
    {"id": "acct-aws-prod", "provider": "aws", "account_ref": "111122223333", "name": "AWS Production", "region": "us-east-1"},
    {"id": "acct-aws-dev", "provider": "aws", "account_ref": "444455556666", "name": "AWS NonProd", "region": "us-east-1"},
    {"id": "acct-azure", "provider": "azure", "account_ref": "sub-3f7a-eastus", "name": "Azure Shared Services", "region": "eastus"},
    {"id": "acct-gcp", "provider": "gcp", "account_ref": "gcp-data-prod", "name": "GCP Data", "region": "us-central1"},
]

VPCS = [
    {"id": "vpc-hr-dev-use1", "name": "vpc-hr-dev-use1", "cloud_account_id": "acct-aws-dev", "cidr": "10.42.0.0/16", "environment": "dev", "region": "us-east-1", "owner_team_id": "team-hr-platform", "business_unit_id": "bu-hr"},
    {"id": "vpc-hr-prod-use1", "name": "vpc-hr-prod-use1", "cloud_account_id": "acct-aws-prod", "cidr": "10.43.0.0/16", "environment": "prod", "region": "us-east-1", "owner_team_id": "team-hr-platform", "business_unit_id": "bu-hr"},
    {"id": "vpc-payroll-prod-use1", "name": "vpc-payroll-prod-use1", "cloud_account_id": "acct-aws-prod", "cidr": "10.50.0.0/16", "environment": "prod", "region": "us-east-1", "owner_team_id": "team-payroll-platform", "business_unit_id": "bu-payroll"},
    {"id": "vpc-identity-prod-use1", "name": "vpc-identity-prod-use1", "cloud_account_id": "acct-aws-prod", "cidr": "10.60.0.0/16", "environment": "prod", "region": "us-east-1", "owner_team_id": "team-identity", "business_unit_id": "bu-identity"},
    {"id": "vpc-data-prod-usc1", "name": "vpc-data-prod-usc1", "cloud_account_id": "acct-gcp", "cidr": "10.70.0.0/16", "environment": "prod", "region": "us-central1", "owner_team_id": "team-data", "business_unit_id": "bu-data"},
    {"id": "vpc-custplat-prod-use1", "name": "vpc-custplat-prod-use1", "cloud_account_id": "acct-aws-prod", "cidr": "10.80.0.0/16", "environment": "prod", "region": "us-east-1", "owner_team_id": "team-custplat", "business_unit_id": "bu-custplat"},
    {"id": "vnet-shared-services-eastus", "name": "vnet-shared-services-eastus", "cloud_account_id": "acct-azure", "cidr": "10.90.0.0/16", "environment": "prod", "region": "eastus", "owner_team_id": "team-network", "business_unit_id": None},
]

# terraform_file_id / ipam_range_id are wired by the discovery service.
SUBNETS = [
    {"id": "sn-hr-dev-private", "name": "hr-dev-private-1", "vpc_id": "vpc-hr-dev-use1", "cidr": "10.42.10.0/24", "environment": "dev", "region": "us-east-1", "availability_zone": "us-east-1a", "business_unit_id": "bu-hr", "application_id": "app-hr-portal", "owner": "HR Platform Team", "technical_owner": "Dana Whitfield", "cost_center": "HR-2042", "data_classification": "internal", "internet_facing": False, "source": "cloud", "terraform_managed": True, "terraform_file_id": "tf-hr-subnets", "ipam_range_id": "ipam-hr-dev-sn-10"},
    {"id": "sn-hr-dev-app", "name": "hr-dev-app-1", "vpc_id": "vpc-hr-dev-use1", "cidr": "10.42.11.0/24", "environment": "dev", "region": "us-east-1", "availability_zone": "us-east-1b", "business_unit_id": "bu-hr", "application_id": "app-hr-portal", "owner": "HR Platform Team", "technical_owner": "Dana Whitfield", "cost_center": "HR-2042", "data_classification": "internal", "internet_facing": False, "source": "cloud", "terraform_managed": True, "terraform_file_id": "tf-hr-subnets", "ipam_range_id": "ipam-hr-dev-sn-11"},
    {"id": "sn-hr-prod-private", "name": "hr-prod-private-1", "vpc_id": "vpc-hr-prod-use1", "cidr": "10.43.20.0/24", "environment": "prod", "region": "us-east-1", "availability_zone": "us-east-1a", "business_unit_id": "bu-hr", "application_id": "app-hr-portal", "owner": "HR Platform Team", "technical_owner": "Dana Whitfield", "cost_center": "HR-2042", "data_classification": "internal", "internet_facing": False, "source": "cloud", "terraform_managed": True, "terraform_file_id": "tf-hr-subnets", "ipam_range_id": "ipam-hr-prod-sn-20"},
    {"id": "sn-payroll-prod-app", "name": "payroll-prod-app-1", "vpc_id": "vpc-payroll-prod-use1", "cidr": "10.50.10.0/24", "environment": "prod", "region": "us-east-1", "availability_zone": "us-east-1a", "business_unit_id": "bu-payroll", "application_id": "app-payroll-api", "owner": "Payroll Platform Team", "technical_owner": "Marcus Lee", "cost_center": "PAY-3050", "data_classification": "confidential", "internet_facing": False, "source": "cloud", "terraform_managed": True, "terraform_file_id": "tf-payroll-subnets", "ipam_range_id": "ipam-payroll-app"},
    {"id": "sn-payroll-prod-db", "name": "payroll-prod-db-1", "vpc_id": "vpc-payroll-prod-use1", "cidr": "10.50.11.0/24", "environment": "prod", "region": "us-east-1", "availability_zone": "us-east-1b", "business_unit_id": "bu-payroll", "application_id": "app-payroll-api", "owner": "Payroll Platform Team", "technical_owner": "Marcus Lee", "cost_center": "PAY-3050", "data_classification": "confidential", "internet_facing": False, "source": "cloud", "terraform_managed": True, "terraform_file_id": "tf-payroll-subnets", "ipam_range_id": "ipam-payroll-db"},
    {"id": "sn-identity-prod-app", "name": "identity-prod-app-1", "vpc_id": "vpc-identity-prod-use1", "cidr": "10.60.10.0/24", "environment": "prod", "region": "us-east-1", "availability_zone": "us-east-1a", "business_unit_id": "bu-identity", "application_id": "app-identity-svc", "owner": "Identity Team", "technical_owner": "Priya Nair", "cost_center": "IDN-4010", "data_classification": "confidential", "internet_facing": False, "source": "cloud", "terraform_managed": True, "terraform_file_id": "tf-identity-subnets", "ipam_range_id": "ipam-identity-app"},
    {"id": "sn-data-prod-wh", "name": "data-prod-warehouse-1", "vpc_id": "vpc-data-prod-usc1", "cidr": "10.70.10.0/24", "environment": "prod", "region": "us-central1", "availability_zone": "us-central1-a", "business_unit_id": "bu-data", "application_id": "app-data-warehouse", "owner": "Data Platform Team", "technical_owner": "Robin Diaz", "cost_center": "DA-7000", "data_classification": "regulated", "internet_facing": False, "source": "cloud", "terraform_managed": True, "terraform_file_id": "tf-data-subnets", "ipam_range_id": "ipam-data-wh"},
    {"id": "sn-custplat-prod-web", "name": "custplat-prod-web-1", "vpc_id": "vpc-custplat-prod-use1", "cidr": "10.80.10.0/24", "environment": "prod", "region": "us-east-1", "availability_zone": "us-east-1a", "business_unit_id": "bu-custplat", "application_id": "app-customer-login", "owner": "Customer Platform Team", "technical_owner": "Jordan Blake", "cost_center": "CP-6000", "data_classification": "confidential", "internet_facing": True, "source": "cloud", "terraform_managed": True, "terraform_file_id": "tf-custplat-subnets", "ipam_range_id": "ipam-custplat-web"},
    # Orphan subnet: missing owner tag, not in CMDB, not terraform-managed -> risk findings
    {"id": "sn-shared-orphan", "name": "shared-orphan-1", "vpc_id": "vnet-shared-services-eastus", "cidr": "10.90.50.0/24", "environment": "prod", "region": "eastus", "availability_zone": "eastus-1", "business_unit_id": None, "application_id": None, "owner": "", "technical_owner": "", "cost_center": "", "data_classification": "unknown", "internet_facing": False, "source": "cloud", "terraform_managed": False, "terraform_file_id": None, "ipam_range_id": "ipam-shared-orphan"},
]

WORKLOADS = [
    {"id": "wl-hr-portal-vm", "name": "hr-portal-web-01", "type": "vm", "subnet_id": "sn-hr-prod-private", "vpc_id": "vpc-hr-prod-use1", "application_id": "app-hr-portal", "internet_facing": False},
    {"id": "wl-payroll-api-vm", "name": "payroll-api-01", "type": "vm", "subnet_id": "sn-payroll-prod-app", "vpc_id": "vpc-payroll-prod-use1", "application_id": "app-payroll-api", "internet_facing": False},
    {"id": "wl-payroll-db", "name": "payroll-db-01", "type": "vm", "subnet_id": "sn-payroll-prod-db", "vpc_id": "vpc-payroll-prod-use1", "application_id": "app-payroll-api", "internet_facing": False},
    {"id": "wl-identity-vm", "name": "identity-svc-01", "type": "vm", "subnet_id": "sn-identity-prod-app", "vpc_id": "vpc-identity-prod-use1", "application_id": "app-identity-svc", "internet_facing": False},
    {"id": "wl-data-k8s", "name": "data-warehouse-eks", "type": "kubernetes_cluster", "subnet_id": "sn-data-prod-wh", "vpc_id": "vpc-data-prod-usc1", "application_id": "app-data-warehouse", "internet_facing": False},
    {"id": "wl-custplat-alb", "name": "custplat-public-alb", "type": "load_balancer", "subnet_id": "sn-custplat-prod-web", "vpc_id": "vpc-custplat-prod-use1", "application_id": "app-customer-login", "internet_facing": True},
    {"id": "wl-prod-igw", "name": "prod-internet-gateway", "type": "internet_gateway", "subnet_id": None, "vpc_id": "vpc-custplat-prod-use1", "application_id": None, "internet_facing": True},
    {"id": "wl-prod-natgw", "name": "hr-prod-nat-gateway", "type": "nat_gateway", "subnet_id": "sn-hr-prod-private", "vpc_id": "vpc-hr-prod-use1", "application_id": None, "internet_facing": False},
    {"id": "wl-tgw", "name": "core-transit-gateway", "type": "transit_gateway", "subnet_id": None, "vpc_id": None, "application_id": None, "internet_facing": False},
]

SECURITY_GROUPS = [
    {"id": "sg-custplat-web", "name": "custplat-web-sg", "vpc_id": "vpc-custplat-prod-use1", "workload_id": "wl-custplat-alb",
     "rules": [{"direction": "ingress", "cidr": "0.0.0.0/0", "port": "443", "protocol": "tcp", "action": "allow"}]},
    {"id": "sg-payroll-db", "name": "payroll-db-sg", "vpc_id": "vpc-payroll-prod-use1", "workload_id": "wl-payroll-db",
     "rules": [{"direction": "ingress", "cidr": "10.90.0.0/16", "port": "5432", "protocol": "tcp", "action": "allow"}]},
    {"id": "sg-hr-portal", "name": "hr-portal-sg", "vpc_id": "vpc-hr-prod-use1", "workload_id": "wl-hr-portal-vm",
     "rules": [{"direction": "ingress", "cidr": "10.43.0.0/16", "port": "443", "protocol": "tcp", "action": "allow"}]},
]

# --------------------------------------------------------------------------- #
# Firewall / network slice
# --------------------------------------------------------------------------- #
FIREWALL_RULES = [
    {"id": "fw-101", "name": "customer-portal-public-https", "source_cidr": "0.0.0.0/0", "destination_cidr": "10.80.10.0/24", "port": "443", "protocol": "tcp", "action": "allow", "owner": "Customer Platform Team", "risk_level": "high", "zone": "dmz", "internet_facing": True, "direction": "north-south", "description": "Public HTTPS ingress to customer portal load balancer."},
    {"id": "fw-102", "name": "shared-to-payroll-db", "source_cidr": "10.90.0.0/16", "destination_cidr": "10.50.11.0/24", "port": "5432", "protocol": "tcp", "action": "allow", "owner": "Cloud Network Engineering", "risk_level": "high", "zone": "internal", "internet_facing": False, "direction": "east-west", "description": "Broad shared-services access to the payroll database subnet."},
    {"id": "fw-103", "name": "hr-dev-to-prod-https", "source_cidr": "10.42.0.0/16", "destination_cidr": "10.43.0.0/16", "port": "443", "protocol": "tcp", "action": "allow", "owner": "HR Platform Team", "risk_level": "medium", "zone": "internal", "internet_facing": False, "direction": "east-west", "description": "HR dev environment access to HR prod over HTTPS."},
    {"id": "fw-104", "name": "identity-to-payroll-https", "source_cidr": "10.60.10.0/24", "destination_cidr": "10.50.10.0/24", "port": "443", "protocol": "tcp", "action": "allow", "owner": "Identity Team", "risk_level": "low", "zone": "internal", "internet_facing": False, "direction": "east-west", "description": "Identity service calls Payroll API over HTTPS."},
    {"id": "fw-105", "name": "any-ssh-to-shared", "source_cidr": "0.0.0.0/0", "destination_cidr": "10.90.50.0/24", "port": "22", "protocol": "tcp", "action": "allow", "owner": "", "risk_level": "high", "zone": "internal", "internet_facing": True, "direction": "north-south", "description": "Overly broad 0.0.0.0/0 SSH access to shared services subnet (no owner)."},
    {"id": "fw-106", "name": "internal-to-data-warehouse", "source_cidr": "10.0.0.0/8", "destination_cidr": "10.70.10.0/24", "port": "443", "protocol": "tcp", "action": "allow", "owner": "Data Platform Team", "risk_level": "medium", "zone": "internal", "internet_facing": False, "direction": "east-west", "description": "Broad internal RFC1918 access to the data warehouse."},
]

ROUTES = [
    {"id": "rt-hr-prod-default", "route_table": "rtb-hr-prod", "destination_cidr": "0.0.0.0/0", "target": "nat_gateway", "vpc_id": "vpc-hr-prod-use1", "description": "HR prod egress via NAT gateway."},
    {"id": "rt-custplat-default", "route_table": "rtb-custplat-prod", "destination_cidr": "0.0.0.0/0", "target": "internet_gateway", "vpc_id": "vpc-custplat-prod-use1", "description": "Customer portal public egress/ingress via IGW."},
    {"id": "rt-payroll-shared", "route_table": "rtb-payroll-prod", "destination_cidr": "10.90.0.0/16", "target": "transit_gateway", "vpc_id": "vpc-payroll-prod-use1", "description": "Payroll to shared services via transit gateway."},
    {"id": "rt-data-internal", "route_table": "rtb-data-prod", "destination_cidr": "10.0.0.0/8", "target": "transit_gateway", "vpc_id": "vpc-data-prod-usc1", "description": "Data warehouse internal connectivity via transit gateway."},
]

# --------------------------------------------------------------------------- #
# IPAM slice
# --------------------------------------------------------------------------- #
IPAM_RANGES = [
    {"id": "ipam-hr-super", "cidr": "10.42.0.0/15", "parent_id": None, "type": "parent", "business_unit_id": "bu-hr", "environment": "", "region": "us-east-1", "owner": "HR Platform Team", "dns_zone": "hr.acme.internal", "dhcp_leases": 0},
    {"id": "ipam-hr-dev", "cidr": "10.42.0.0/16", "parent_id": "ipam-hr-super", "type": "allocated", "business_unit_id": "bu-hr", "environment": "dev", "region": "us-east-1", "owner": "HR Platform Team", "dns_zone": "hr-dev.acme.internal", "dhcp_leases": 120},
    {"id": "ipam-hr-prod", "cidr": "10.43.0.0/16", "parent_id": "ipam-hr-super", "type": "allocated", "business_unit_id": "bu-hr", "environment": "prod", "region": "us-east-1", "owner": "HR Platform Team", "dns_zone": "hr-prod.acme.internal", "dhcp_leases": 64},
    {"id": "ipam-hr-dev-sn-10", "cidr": "10.42.10.0/24", "parent_id": "ipam-hr-dev", "type": "allocated", "business_unit_id": "bu-hr", "environment": "dev", "region": "us-east-1", "owner": "HR Platform Team", "dns_zone": "", "dhcp_leases": 48},
    {"id": "ipam-hr-dev-sn-11", "cidr": "10.42.11.0/24", "parent_id": "ipam-hr-dev", "type": "allocated", "business_unit_id": "bu-hr", "environment": "dev", "region": "us-east-1", "owner": "HR Platform Team", "dns_zone": "", "dhcp_leases": 30},
    {"id": "ipam-hr-dev-avail-18", "cidr": "10.42.18.0/24", "parent_id": "ipam-hr-dev", "type": "available", "business_unit_id": "bu-hr", "environment": "dev", "region": "us-east-1", "owner": "HR Platform Team", "dns_zone": "", "dhcp_leases": 0},
    {"id": "ipam-hr-reserved", "cidr": "10.42.250.0/24", "parent_id": "ipam-hr-dev", "type": "reserved", "business_unit_id": "bu-hr", "environment": "dev", "region": "us-east-1", "owner": "HR Platform Team", "dns_zone": "", "dhcp_leases": 0},
    {"id": "ipam-hr-prod-sn-20", "cidr": "10.43.20.0/24", "parent_id": "ipam-hr-prod", "type": "allocated", "business_unit_id": "bu-hr", "environment": "prod", "region": "us-east-1", "owner": "HR Platform Team", "dns_zone": "", "dhcp_leases": 22},
    {"id": "ipam-payroll", "cidr": "10.50.0.0/16", "parent_id": None, "type": "parent", "business_unit_id": "bu-payroll", "environment": "prod", "region": "us-east-1", "owner": "Payroll Platform Team", "dns_zone": "payroll.acme.internal", "dhcp_leases": 0},
    {"id": "ipam-payroll-app", "cidr": "10.50.10.0/24", "parent_id": "ipam-payroll", "type": "allocated", "business_unit_id": "bu-payroll", "environment": "prod", "region": "us-east-1", "owner": "Payroll Platform Team", "dns_zone": "", "dhcp_leases": 40},
    {"id": "ipam-payroll-db", "cidr": "10.50.11.0/24", "parent_id": "ipam-payroll", "type": "allocated", "business_unit_id": "bu-payroll", "environment": "prod", "region": "us-east-1", "owner": "Payroll Platform Team", "dns_zone": "", "dhcp_leases": 12},
    {"id": "ipam-identity", "cidr": "10.60.0.0/16", "parent_id": None, "type": "parent", "business_unit_id": "bu-identity", "environment": "prod", "region": "us-east-1", "owner": "Identity Team", "dns_zone": "identity.acme.internal", "dhcp_leases": 0},
    {"id": "ipam-identity-app", "cidr": "10.60.10.0/24", "parent_id": "ipam-identity", "type": "allocated", "business_unit_id": "bu-identity", "environment": "prod", "region": "us-east-1", "owner": "Identity Team", "dns_zone": "", "dhcp_leases": 35},
    {"id": "ipam-data", "cidr": "10.70.0.0/16", "parent_id": None, "type": "parent", "business_unit_id": "bu-data", "environment": "prod", "region": "us-central1", "owner": "Data Platform Team", "dns_zone": "data.acme.internal", "dhcp_leases": 0},
    {"id": "ipam-data-wh", "cidr": "10.70.10.0/24", "parent_id": "ipam-data", "type": "allocated", "business_unit_id": "bu-data", "environment": "prod", "region": "us-central1", "owner": "Data Platform Team", "dns_zone": "", "dhcp_leases": 18},
    {"id": "ipam-custplat", "cidr": "10.80.0.0/16", "parent_id": None, "type": "parent", "business_unit_id": "bu-custplat", "environment": "prod", "region": "us-east-1", "owner": "Customer Platform Team", "dns_zone": "portal.acme.internal", "dhcp_leases": 0},
    {"id": "ipam-custplat-web", "cidr": "10.80.10.0/24", "parent_id": "ipam-custplat", "type": "allocated", "business_unit_id": "bu-custplat", "environment": "prod", "region": "us-east-1", "owner": "Customer Platform Team", "dns_zone": "", "dhcp_leases": 26},
    {"id": "ipam-shared", "cidr": "10.90.0.0/16", "parent_id": None, "type": "parent", "business_unit_id": None, "environment": "prod", "region": "eastus", "owner": "Cloud Network Engineering", "dns_zone": "shared.acme.internal", "dhcp_leases": 0},
    {"id": "ipam-shared-orphan", "cidr": "10.90.50.0/24", "parent_id": "ipam-shared", "type": "allocated", "business_unit_id": None, "environment": "prod", "region": "eastus", "owner": "", "dns_zone": "", "dhcp_leases": 5},
]

# --------------------------------------------------------------------------- #
# Terraform / IaC slice
# --------------------------------------------------------------------------- #
TERRAFORM_MODULES = [
    {"id": "tfm-network-baseline", "name": "network-baseline", "repo_path": "git@github.com:acme/infra-network.git", "description": "Baseline VPC + routing module."},
    {"id": "tfm-subnet", "name": "subnet-provisioning", "repo_path": "git@github.com:acme/infra-network.git", "description": "Standard subnet provisioning module with tagging policy."},
]

TERRAFORM_FILES = [
    {"id": "tf-hr-subnets", "path": "network/hr/subnets.tf", "repo_path": "git@github.com:acme/infra-network.git", "module_id": "tfm-subnet", "defines": "subnet", "owner": "HR Platform Team", "state_resources": ["sn-hr-dev-private", "sn-hr-dev-app", "sn-hr-prod-private"]},
    {"id": "tf-hr-vpc", "path": "network/hr/vpc.tf", "repo_path": "git@github.com:acme/infra-network.git", "module_id": "tfm-network-baseline", "defines": "vpc", "owner": "HR Platform Team", "state_resources": ["vpc-hr-dev-use1", "vpc-hr-prod-use1"]},
    {"id": "tf-payroll-subnets", "path": "network/payroll/subnets.tf", "repo_path": "git@github.com:acme/infra-network.git", "module_id": "tfm-subnet", "defines": "subnet", "owner": "Payroll Platform Team", "state_resources": ["sn-payroll-prod-app", "sn-payroll-prod-db"]},
    {"id": "tf-identity-subnets", "path": "network/identity/subnets.tf", "repo_path": "git@github.com:acme/infra-network.git", "module_id": "tfm-subnet", "defines": "subnet", "owner": "Identity Team", "state_resources": ["sn-identity-prod-app"]},
    {"id": "tf-data-subnets", "path": "network/data/subnets.tf", "repo_path": "git@github.com:acme/infra-network.git", "module_id": "tfm-subnet", "defines": "subnet", "owner": "Data Platform Team", "state_resources": ["sn-data-prod-wh"]},
    {"id": "tf-custplat-subnets", "path": "network/custplat/subnets.tf", "repo_path": "git@github.com:acme/infra-network.git", "module_id": "tfm-subnet", "defines": "subnet", "owner": "Customer Platform Team", "state_resources": ["sn-custplat-prod-web"]},
]

# --------------------------------------------------------------------------- #
# Security findings (static; the security collector also derives more)
# --------------------------------------------------------------------------- #
STATIC_RISK_FINDINGS = [
    {"id": "rf-portal-exposure", "type": "internet_exposure", "severity": "high", "asset_type": "subnet", "asset_id": "sn-custplat-prod-web", "description": "Production subnet hosts an internet-facing load balancer reachable from 0.0.0.0/0:443.", "recommendation": "Confirm WAF + rate limiting; restrict source ranges where possible."},
    {"id": "rf-broad-ssh", "type": "broad_access", "severity": "high", "asset_type": "firewall_rule", "asset_id": "fw-105", "description": "Firewall rule fw-105 allows 0.0.0.0/0 SSH (22) to the shared services subnet.", "recommendation": "Replace 0.0.0.0/0 with a bastion or named admin CIDR; require security approval."},
    {"id": "rf-shared-to-payroll", "type": "broad_access", "severity": "high", "asset_type": "firewall_rule", "asset_id": "fw-102", "description": "Firewall rule fw-102 allows the entire shared-services /16 to reach the payroll database.", "recommendation": "Scope source to the specific payroll app subnet 10.50.10.0/24."},
]

# --------------------------------------------------------------------------- #
# Sample subnet requests (demo scenarios). Policy is evaluated at seed time.
# --------------------------------------------------------------------------- #
SAMPLE_REQUESTS = [
    {   # CIDR overlap -> denied
        "id": "req-overlap", "requester_name": "Dana Whitfield", "requester_email": "dana.whitfield@acme.example",
        "team": "HR Platform Team", "application": "HR Portal", "business_unit": "HR", "environment": "dev",
        "requested_cidr": "10.42.10.128/25", "vpc": "vpc-hr-dev-use1", "cloud_provider": "aws", "region": "us-east-1",
        "business_justification": "Additional dev capacity for HR Portal feature testing.",
        "data_classification": "internal", "internet_exposure_required": False,
        "expected_traffic_pattern": "east-west", "cost_center": "HR-2042", "owner": "HR Platform Team",
        "technical_owner": "Dana Whitfield", "seed_status": "evaluate",
    },
    {   # Valid dev request -> allowed
        "id": "req-valid", "requester_name": "Dana Whitfield", "requester_email": "dana.whitfield@acme.example",
        "team": "HR Platform Team", "application": "Benefits Engine", "business_unit": "HR", "environment": "dev",
        "requested_cidr": "10.42.18.0/24", "vpc": "vpc-hr-dev-use1", "cloud_provider": "aws", "region": "us-east-1",
        "business_justification": "New private subnet for Benefits Engine dev microservices.",
        "data_classification": "internal", "internet_exposure_required": False,
        "expected_traffic_pattern": "east-west", "cost_center": "HR-2042", "owner": "HR Platform Team",
        "technical_owner": "Dana Whitfield", "seed_status": "evaluate",
    },
    {   # Production request -> requires two approvals
        "id": "req-prod-two", "requester_name": "Dana Whitfield", "requester_email": "dana.whitfield@acme.example",
        "team": "HR Platform Team", "application": "Benefits Engine", "business_unit": "HR", "environment": "prod",
        "requested_cidr": "10.43.40.0/24", "vpc": "vpc-hr-prod-use1", "cloud_provider": "aws", "region": "us-east-1",
        "business_justification": "Production subnet for Benefits Engine blue/green deployment.",
        "data_classification": "internal", "internet_exposure_required": False,
        "expected_traffic_pattern": "east-west", "cost_center": "HR-2042", "owner": "HR Platform Team",
        "technical_owner": "Dana Whitfield", "seed_status": "evaluate",
    },
    {   # Internet-facing prod -> requires security review
        "id": "req-internet", "requester_name": "Jordan Blake", "requester_email": "jordan.blake@acme.example",
        "team": "Customer Platform Team", "application": "Customer Login", "business_unit": "Customer Platform",
        "environment": "prod", "requested_cidr": "10.80.20.0/24", "vpc": "vpc-custplat-prod-use1",
        "cloud_provider": "aws", "region": "us-east-1",
        "business_justification": "New internet-facing subnet for customer login edge nodes.",
        "data_classification": "confidential", "internet_exposure_required": True,
        "expected_traffic_pattern": "north-south", "cost_center": "CP-6000", "owner": "Customer Platform Team",
        "technical_owner": "Jordan Blake", "seed_status": "evaluate",
    },
]
