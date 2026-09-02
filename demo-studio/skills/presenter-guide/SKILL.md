---
name: presenter-guide
description: >-
  Use when someone wants a presenter guide, speaker notes, a teleprompter script,
  per-slide talking points or questions to ask and expect back, a run of show, or
  wants a demo runbook turned into a live walkthrough for delivering a deck.
---

# Presenter Guide

Write this against the FINAL aggregate deck, not a draft: slide numbers, order,
and content need to be locked first, or the guide is presenting a deck that
does not exist yet. Read `references/presenter-guide-format.md`. Per slide:
Talking points, Say (teleprompter, one beat per line), and Ask. Fold a demo
RUNBOOK into the optional `demo` block: cold start, the two lanes, a card per
beat with the exact Ctrl-C, plus reference/switches.

## Quickstart (per-slide points / teleprompter Say / questions + demo run-of-show)

```bash
cp assets/examples/presenter_guide.example.json my_pg.json
# edit my_pg.json: slides[] and the optional demo{} block (see references/presenter-guide-format.md)
python3 assets/build_presenter_guide.py my_pg.json presenter-guide.html
```

Apply the disciplines in `shared/grounding.md`.
