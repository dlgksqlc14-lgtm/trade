#!/bin/bash
cd "$(dirname "$0")"
PYTHONPATH=. .venv/bin/python scripts/trading/dashboard.py
