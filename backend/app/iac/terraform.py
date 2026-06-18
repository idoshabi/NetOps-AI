"""Terraform code generation for subnet provisioning (mock, never applied)."""
import re


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")


def resource_name(application: str, environment: str, suffix: str = "private_1") -> str:
    return f"{_slug(application)}_{_slug(environment)}_{suffix}"


def vpc_var(vpc: str) -> str:
    return f"var.{_slug(vpc)}_id"


def render_subnet(req) -> tuple[str, str]:
    """Return (file_path, terraform_code) for a subnet request-like object."""
    # normalize access for dict or object
    def g(k, d=""):
        return getattr(req, k, d) if hasattr(req, k) else req.get(k, d)

    application = g("application")
    environment = g("environment", "dev")
    cidr = g("requested_cidr")
    vpc = g("vpc")
    region = g("region", "us-east-1")
    az = f"{region}a"
    owner = g("owner")
    cost_center = g("cost_center")
    data_class = g("data_classification", "internal")
    bu = _slug(g("business_unit"))
    res = resource_name(application, environment)
    name_tag = f"{_slug(application)}-{_slug(environment)}-private-1".replace("_", "-")

    code = f'''resource "aws_subnet" "{res}" {{
  vpc_id            = {vpc_var(vpc)}
  cidr_block        = "{cidr}"
  availability_zone = "{az}"

  tags = {{
    Name               = "{name_tag}"
    Environment        = "{environment}"
    Application        = "{_slug(application)}"
    Owner              = "{owner}"
    CostCenter         = "{cost_center}"
    DataClassification = "{data_class}"
    BusinessUnit       = "{bu}"
    ManagedBy          = "terraform"
  }}
}}
'''
    file_path = f"network/{bu or 'shared'}/subnets.tf"
    return file_path, code


def render_diff(file_path: str, code: str) -> str:
    """Produce a unified-diff style addition for the PR preview."""
    lines = code.rstrip("\n").split("\n")
    body = "\n".join(f"+{l}" for l in lines)
    return (
        f"--- a/{file_path}\n"
        f"+++ b/{file_path}\n"
        f"@@ subnet allocation @@\n"
        f"{body}\n"
    )
