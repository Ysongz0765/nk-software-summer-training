#!/usr/bin/env bash
set -euo pipefail

cp -n .env.example .env || true
python -m venv backend/.venv
backend/.venv/bin/python -m pip install -U pip
backend/.venv/bin/python -m pip install -e "backend[dev]"
npm --prefix frontend install
