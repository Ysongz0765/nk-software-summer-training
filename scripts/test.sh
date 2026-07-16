#!/usr/bin/env bash
set -euo pipefail

backend/.venv/bin/python -m pytest backend/tests
npm --prefix frontend run type-check
