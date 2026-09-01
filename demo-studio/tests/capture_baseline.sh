#!/bin/bash
# Renders the example configs with the CURRENT generators and stores the output
# as golden files. Run once, before any generator is modified.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
out="$here/baseline"
mkdir -p "$out"

# The bare `python3` shim on PATH on this machine is broken (asdf, no version
# set); default to a real interpreter rather than silently failing or, worse,
# silently running something else. Override with PY=/path/to/python3 if this
# absolute path is not right for your machine.
PY="${PY:-/usr/bin/python3}"
"$PY" "$root/skills/deck-flow-guide/assets/build_flow_guide.py" \
      "$root/skills/deck-flow-guide/assets/examples/flow_guide.example.json" \
      "$out/flow-guide.html"
"$PY" "$root/skills/presenter-guide/assets/build_presenter_guide.py" \
      "$root/skills/presenter-guide/assets/examples/presenter_guide.example.json" \
      "$out/presenter-guide.html"
echo "baseline captured in $out"
