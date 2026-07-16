#!/usr/bin/env bash
set -euo pipefail

echo "Start backend: cd backend && .venv/bin/python -m uvicorn app.main:app --reload"
echo "Start frontend: cd frontend && npm run dev"
echo "Start MySQL: docker compose up mysql"
