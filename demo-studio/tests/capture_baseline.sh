#!/bin/bash
# Renders the example configs with the CURRENT generators and stores the output
# as golden files. Run once, before any generator is modified.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
out="$here/baseline"
mkdir -p "$out"

PY="${PY:-python3}"
"$PY" "$root/skills/deck-flow-guide/assets/build_flow_guide.py" \
      "$root/skills/deck-flow-guide/assets/examples/flow_guide.example.json" \
      "$out/flow-guide.html"
"$PY" "$root/skills/presenter-guide/assets/build_presenter_guide.py" \
      "$root/skills/presenter-guide/assets/examples/presenter_guide.example.json" \
      "$out/presenter-guide.html"
echo "baseline captured in $out"
