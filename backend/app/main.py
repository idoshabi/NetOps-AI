"""NetOps-AI FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import Base, engine, SessionLocal
from app.services import discovery
from app.services import subnet_request
from app.api import discovery as discovery_api
from app.api import graph as graph_api
from app.api import subnet as subnet_api
from app.api import policy as policy_api
from app.api import iac as iac_api
from app.api import assistant as assistant_api
from app.api import audit as audit_api
from app.api import dashboard as dashboard_api


def bootstrap():
    """Create tables, run discovery (loads mock inventory), seed demo requests."""
    import app.models  # noqa: F401  ensure models are registered
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from app.models import VPC
        if db.query(VPC).count() == 0:
            discovery.run_discovery(db, actor="system", role="admin")
            subnet_request.seed_sample_requests(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (discovery_api, graph_api, subnet_api, policy_api, iac_api,
          assistant_api, audit_api, dashboard_api):
    app.include_router(r.router)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs",
        "llm_provider": settings.LLM_PROVIDER,
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
