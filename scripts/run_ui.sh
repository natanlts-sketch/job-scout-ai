#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
exec streamlit run app/Home.py --server.port="${PORT:-8501}"
