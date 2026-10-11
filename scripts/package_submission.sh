#!/usr/bin/env bash
# Builds Capstone_Project_<Name>.zip from tracked files plus the deliverable docs.
set -euo pipefail
NAME="${1:-Dani_Chakiath_Varghese}"
OUT="Capstone_Project_${NAME}.zip"
rm -f "$OUT"
git ls-files -z -- . ':!:guardian.db' ':!:*.zip' ':!:demo/*.pptx' ':!:docs/deliverables' | xargs -0 zip -q "$OUT"
echo "$OUT"
