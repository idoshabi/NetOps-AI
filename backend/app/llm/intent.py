"""Lightweight intent classifier for the assistant.

Keyword/rule based for the MVP. Returns an intent key and a confidence label.
A real deployment would replace this with an LLM function-calling router; the
return shape stays the same.
"""
import re

# Ordered: first matching pattern wins.
QA_PATTERNS = [
    ("owner_lookup", r"who owns|owner of|which team owns|owns (the )?subnet|owns (the )?vpc"),
    ("request_denied", r"why was.*(denied|rejected)|reason.*denied|explain.*denied"),
    ("approvals_required", r"approval|approvers|sign-?off|who needs to approve"),
    ("internet_facing_prod", r"internet[- ]facing.*(prod|production)|production.*internet"),
    ("risky_paths", r"risky paths|internet to|blast radius|reach.*(payroll|identity|sensitive)|exposed to the internet"),
    ("broad_rules", r"broad (access|rule)|0\.0\.0\.0/0|overly broad|wide open"),
    ("missing_owner", r"missing owner|untagged|missing.*tag"),
    ("unknown_assets", r"unknown asset|missing cmdb|not in cmdb|unmapped"),
    ("terraform_for_vpc", r"terraform.*(define|defines|file).*vpc|which terraform"),
    ("suggest_subnet", r"suggest.*subnet|available subnet for|recommend.*cidr|find.*subnet for"),
    ("cidr_available", r"is.*available|can i (create|use)|cidr available"),
    ("app_for_vpc", r"which app|what app.*using|application.*using.*vpc"),
]

# IaC proposal verbs.
IAC_PATTERNS = [
    r"\bcreate\b", r"\bgenerate\b", r"\bpropose\b", r"\badd (a |the )?(tag|owner|cost)",
    r"\bprovision\b", r"\bnew (private |dev |prod )?subnet\b", r"terraform (for|pr)",
    r"\bsuggest a safer\b", r"\bremove (broad|0\.0\.0\.0)",
]


def classify(text: str) -> dict:
    low = (text or "").lower().strip()
    if not low:
        return {"intent": "clarify", "mode": "qa", "confidence": "low"}

    # IaC proposal intent (mode 2). "suggest an available subnet" is read-only.
    suggest_readonly = "suggest" in low and "subnet" in low and "safer" not in low and "create" not in low
    if not suggest_readonly:
        for pat in IAC_PATTERNS:
            if re.search(pat, low):
                return {"intent": "iac_proposal", "mode": "iac", "confidence": "high"}

    for intent, pat in QA_PATTERNS:
        if re.search(pat, low):
            return {"intent": intent, "mode": "qa", "confidence": "high"}

    return {"intent": "general_qa", "mode": "qa", "confidence": "medium"}
