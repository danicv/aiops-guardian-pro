#!/usr/bin/env bash
set -euo pipefail
curl -sS -X POST http://localhost:8000/api/investigations -H 'Content-Type: application/json' -d '{"query":"Why is checkout-api failing after today\u0027s production deployment?","application":"checkout-api","environment":"prod","namespace":"default"}' | python -m json.tool
