"""Standalone seeding script: `python seed.py` (re)builds the database.

Drops and recreates tables, runs discovery, and seeds demo subnet requests.
"""
import os
from app.db.database import Base, engine, SessionLocal
import app.models  # noqa: F401
from app.services import discovery, subnet_request


def main(reset: bool = True):
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run = discovery.run_discovery(db, actor="system", role="admin")
        subnet_request.seed_sample_requests(db)
        print("Discovery complete. Loaded:")
        for table, n in run["counts"].items():
            print(f"  {table:20s} {n}")
        from app.models import SubnetRequest
        print("\nSeeded demo subnet requests:")
        for r in db.query(SubnetRequest).all():
            print(f"  {r.id:14s} {r.requested_cidr:18s} {r.status}")
    finally:
        db.close()


if __name__ == "__main__":
    main(reset=os.getenv("NETGOV_RESET", "1") == "1")
