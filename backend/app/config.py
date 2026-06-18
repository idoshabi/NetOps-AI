"""Application configuration."""
import os

class Settings:
    APP_NAME = "NetGraph Copilot"
    APP_DESCRIPTION = (
        "Network graph intelligence platform with LLM copilot for safe subnet governance and IaC."
    )
    VERSION = "0.1.0"
    # SQLite by default; swap DATABASE_URL for PostgreSQL in production.
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:////tmp/netgov.db" if os.getenv("VERCEL") else "sqlite:///./netgov.db",
    )
    # LLM provider: "mock" (default, offline rule-based) | "openai" | "azure" | "anthropic"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "mock-rules-v1")
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,https://netops-ai.vercel.app,https://frontend-eight-sepia-68takz8tzd.vercel.app",
    ).split(",")

settings = Settings()
