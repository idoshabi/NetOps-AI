import os
import sys

# Vercel serverless: writable SQLite lives in /tmp.
if os.getenv("VERCEL"):
    os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/netgov.db")
    os.environ.setdefault(
        "CORS_ORIGINS",
        "https://frontend-eight-sepia-68takz8tzd.vercel.app,http://localhost:5173",
    )

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI  # noqa: E402
from mangum import Mangum  # noqa: E402
from app.main import app as backend_app, bootstrap  # noqa: E402

bootstrap()

root = FastAPI()
root.mount("/api", backend_app)

handler = Mangum(root, lifespan="off")
