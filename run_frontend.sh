#!/usr/bin/env bash
# Start the NetOps-AI frontend (Vite dev server) on http://localhost:5173
set -e
cd "$(dirname "$0")/frontend"
npm install
npm run dev
