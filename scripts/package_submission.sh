#!/usr/bin/env bash
# Builds Capstone_Project_<Name>.zip from tracked and non-ignored source files.
set -euo pipefail
NAME="${1:-Dani_Chakiath_Varghese}"
OUT="Capstone_Project_${NAME}.zip"
rm -f "$OUT"
git ls-files -co --exclude-standard -z -- . ':!:guardian.db' ':!:*.zip' ':!:**/__pycache__/*' ':!:demo/*.pptx' ':!:docs/deliverables' | xargs -0 zip -q "$OUT"
echo "$OUT"
