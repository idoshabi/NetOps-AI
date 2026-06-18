"""Shared pytest fixtures: an isolated in-memory DB seeded via discovery."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
import app.models  # noqa: F401
from app.services import discovery, subnet_request


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    s = Session()
    discovery.run_discovery(s, actor="test", role="admin")
    subnet_request.seed_sample_requests(s)
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client():
    """FastAPI TestClient against a fresh seeded app (uses default sqlite file)."""
    import os
    os.environ["DATABASE_URL"] = "sqlite:///./netgov_test.db"
    from fastapi.testclient import TestClient
    from app.db.database import Base, engine
    Base.metadata.drop_all(bind=engine)
    from app.main import app
    with TestClient(app) as c:
        yield c
