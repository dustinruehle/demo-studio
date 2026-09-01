---
name: presenter-guide
description: >-
  Use when the user wants a presenter guide, teleprompter script, speaker notes,
  or a live-demo run-of-show folded in from a runbook.
---

# Presenter Guide

Read `references/presenter-guide-format.md`. Per slide: Talking points, Say
(teleprompter, one beat per line), and Ask. Fold a demo RUNBOOK into the optional
`demo` block: cold start, the two lanes, a card per beat with the exact Ctrl-C,
plus reference/switches.

## Quickstart (per-slide points / teleprompter Say / questions + demo run-of-show)

```bash
cp assets/examples/presenter_guide.example.json my_pg.json
# edit my_pg.json: slides[] and the optional demo{} block (see references/presenter-guide-format.md)
python3 assets/build_presenter_guide.py my_pg.json presenter-guide.html
```

Apply the disciplines in `../../shared/grounding.md`.
