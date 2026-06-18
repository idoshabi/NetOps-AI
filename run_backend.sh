#!/usr/bin/env bash
# Start the NetOps-AI backend (FastAPI) on http://localhost:8000
set -e
cd "$(dirname "$0")/backend"
python3 -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
python seed.py            # build + seed the SQLite database
uvicorn app.main:app --reload --port 8000
