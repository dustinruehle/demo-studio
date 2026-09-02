---
name: deck-flow-guide
description: >-
  Use when someone wants a flow guide, wants an existing deck reordered or pieced
  together for a specific room, asks which slides to pull and which to build, or
  wants a cut list for when the session runs short.
---

# Deck Flow Guide

Read `references/flow-guide-format.md`. Piece the deck from existing slides plus
net-new ("create") slides in the order that serves THIS room, not deck order.
Each card either names an exact existing slide (verbatim headline, section, and
page) or is a "create" card with a collapsible mockup, a one-line why, and a
"traces to" discovery link.

## Quickstart (piece the deck: from-deck + create cards with previews)

```bash
cp assets/examples/flow_guide.example.json my_flow.json
# edit my_flow.json: acts, cards, and create-card previews (see references/flow-guide-format.md)
python3 assets/build_flow_guide.py my_flow.json flow-guide.html
```

The generator is the format. Do not hand-roll the HTML or restyle it; change the
JSON, not the CSS.

Apply the disciplines in `shared/grounding.md`.
