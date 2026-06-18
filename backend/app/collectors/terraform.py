"""Mock Terraform state / IaC file collector."""
from app.collectors.base import BaseCollector
from app.seed import dataset


class TerraformCollector(BaseCollector):
    name = "terraform"
    source_system = "git+tfstate-mock"

    def collect(self) -> dict:
        return {
            "terraform_modules": dataset.TERRAFORM_MODULES,
            "terraform_files": dataset.TERRAFORM_FILES,
        }
