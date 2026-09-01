---
name: demo-deck-studio
description: >-
  Demo Deck Studio turns a customer/discovery call transcript into a full pre-sales
  enablement set: a demo build spec, a deck FLOW GUIDE (piece an existing deck plus
  net-new "create" slides with drilldown previews, reordered for the room), the
  net-new slides as a dark Google-Slides-safe PPTX, and a companion PRESENTER GUIDE
  (per-slide talking points, a teleprompter script, and questions) with a live-demo
  run-of-show folded in from a runbook. Use this WHENEVER the user shares a call
  transcript and wants demo, deck, or enablement work; asks to build, reorder, or
  piece together a deck flow from existing slides; wants a presenter guide,
  teleprompter script, or speaker notes; wants to turn a demo runbook into a live
  walkthrough; or wants to spec a customer demo, even if they only ask for one piece
  or start midway. Also trigger on "demo deck studio", "deck studio", "flow guide",
  "presenter guide", "run of show", "create slides", and "build spec from this
  transcript".
---

# Demo Deck Studio

A repeatable pipeline that takes a discovery transcript to a demo build spec, a deck
flow guide, the net-new slides (PPTX), and a presenter guide with a live-demo
run-of-show. It is built so the user can run the whole thing OR jump in at any
stage. The guide formats (navigation, the teleprompter-card script, the 3-column
layout, the from-deck/create cards with drilldown previews) are carried as fixed,
reusable generators so they reproduce identically every time.

## First: figure out where the user is, then jump in

Read `references/pipeline.md` for the full method and the entry-point map. In short:

- **Whole thing** ("here's a transcript") -> run all stages.
- **Mid-pipeline** ("I know the demo, tweak it then build the deck and guides") ->
  go straight to the deck flow guide, create slides, and presenter guide.
- **One artifact** ("just the presenter guide for this deck", "add the demo
  walkthrough", "reorder this deck into a flow") -> do that stage.

Do not force earlier stages the user didn't ask for. Ask which stage only if it is
genuinely ambiguous.

## The four deliverables and how to build each

1. **Demo build spec** -> read `references/build-spec.md`; fill
   `assets/build_spec_template.md`. Non-negotiables: name the skills/refs to read
   with "reference wins", a preflight that installs prereqs, a definition-of-done
   gate whose tests loop until green, mock-by-default, generic/public-safe, pinned
   pre-release versions.

2. **Deck flow guide** -> read `references/flow-guide-format.md`. Author a JSON
   config (copy `assets/examples/flow_guide.example.json`) and run:
   `python3 assets/build_flow_guide.py CONFIG.json OUT.html`.
   Each card either names an exact existing slide (verbatim headline + section +
   page) or is a "create" card with a collapsible mockup, a one-line why, and a
   "traces to" discovery link. Reorder for the room, not deck order.

3. **Create slides (dark PPTX)** -> read `references/create-slides-pptx.md` and
   `/mnt/skills/public/pptx/SKILL.md`. Edit `assets/build_create_slides.js` (one
   builder block per slide), then ALWAYS run the render-and-inspect QA loop and view
   every slide image before shipping. Google-Slides-safe: block arrows, solid
   borders, no connectors or dashes; no em dashes; dark + readable.

4. **Presenter guide + live-demo run-of-show** -> read
   `references/presenter-guide-format.md`. Author a JSON config (copy
   `assets/examples/presenter_guide.example.json`) and run:
   `python3 assets/build_presenter_guide.py CONFIG.json OUT.html`.
   Per slide: Talking points / Say (teleprompter, one beat per line) / Ask. Fold a
   demo RUNBOOK into the optional `demo` block: cold start, the two lanes, a card
   per beat with the exact Ctrl-C, plus reference/switches.

The generators are the format. Do not hand-roll the HTML or restyle it — change the
JSON, not the CSS. If the user wants a genuinely new component, add it to the
generator so it is reusable next time.

## Disciplines to apply throughout (do not skip)

Read `references/grounding.md`. The essentials:

- **Grounded vs inferred.** Quote what the customer said; label what you designed.
  When asked "did they say that?", answer with a source table.
- **Traces-to.** Every flow-guide card and every talking point traces to a
  discovery signal or a demo beat.
- **Reference wins.** Verify SDK/API names, versions, URLs against the authoritative
  reference, not memory. Mark unverified items as "verify".
- **Recommend, then lock.** Commit to a recommendation; get the user to lock a small
  set of decisions before you build the artifact.
- **Render-and-inspect QA.** Never ship a PPTX without rendering it to images and
  looking at every slide.
- **Guardrails, held without re-litigating:** no em dashes anywhere; Google-Slides-
  safe shapes; the brand system (Fraunces / IBM Plex Sans / JetBrains Mono; indigo
  `#4C2889` with amber/green/coral accents; ink `#1C1526`, paper `#F6F4FA`);
  generic/public-safe (no customer or participant names in anything that may go
  public).

## Brand system (locked, used by all generators)

Fonts: Fraunces (headings), IBM Plex Sans (body), JetBrains Mono (labels/code).
Light guides use paper `#F6F4FA` / ink `#1C1526` / indigo `#4C2889`; the dark PPTX
uses a dark ground with lightened accents (indigo `#8E6BE6`, coral `#F0805E`, green
`#5FBE97`, amber `#E9B23A`). The generators embed this; keep it consistent so the
create slides look the same across the flow-guide preview, the PPTX, and the deck.

## Files

- `QUICKSTART.md` — the exact copy-edit-run commands for all four deliverables.
- `references/pipeline.md` — the 8 stages + entry-point map + disciplines.
- `references/grounding.md` — provenance, reference-wins, public-safe, no-tells.
- `references/flow-guide-format.md` — flow-guide fields + mockup classes.
- `references/presenter-guide-format.md` — presenter-guide fields + demo block.
- `references/create-slides-pptx.md` — dark PPTX rules + the QA loop.
- `references/build-spec.md` — build-spec non-negotiables + structure.
- `assets/build_flow_guide.py`, `assets/build_presenter_guide.py` — the generators.
- `assets/build_create_slides.js` — the PPTX template (edit per engagement).
- `assets/build_spec_template.md` — the spec skeleton.
- `assets/examples/*.json` — copy these as your starting configs.

## Output

Write finished artifacts to the workspace/output directory and present them. Offer
next steps (strip placement eyebrows for merge; a one-page cue card; run the spec).
