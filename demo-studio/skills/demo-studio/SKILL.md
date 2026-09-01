---
name: demo-studio
description: >-
  Demo Studio turns a customer/discovery call transcript into a full pre-sales
  enablement set: a demo build spec, a deck FLOW GUIDE (piece an existing deck plus
  net-new "create" slides with drilldown previews, reordered for the room), the
  net-new slides as a dark Google-Slides-safe PPTX, and a companion PRESENTER GUIDE
  (per-slide talking points, a teleprompter script, and questions) with a live-demo
  run-of-show folded in from a runbook. Use this WHENEVER the user shares a call
  transcript and wants demo, deck, or enablement work; asks to build, reorder, or
  piece together a deck flow from existing slides; wants a presenter guide,
  teleprompter script, or speaker notes; wants to turn a demo runbook into a live
  walkthrough; or wants to spec a customer demo, even if they only ask for one piece
  or start midway. Also trigger on "demo studio", "flow guide", "presenter guide",
  "run of show", "create slides", and "build spec from this transcript".
---

# Demo Studio

A repeatable pipeline that takes a discovery transcript to a demo build spec, a deck
flow guide, the net-new slides (PPTX), and a presenter guide with a live-demo
run-of-show. It is built so the user can run the whole thing OR jump in at any
stage. This skill is the router: it figures out where the user is and hands off to
the right worker skill. The guide formats (navigation, the teleprompter-card
script, the 3-column layout, the from-deck/create cards with drilldown previews)
are carried as fixed, reusable generators in the worker skills, so they reproduce
identically every time.

## The stages and their workers

1. **Demo discovery** (`demo-studio:demo-discovery`) - read the transcript(s),
   map candidate demos to the stated needs, design the session, and pick v1 vs v2
   scope.
2. **Build spec** (`demo-studio:build-spec`) - write a spec a coding agent can
   execute end to end.
3. **Deck flow guide** (`demo-studio:deck-flow-guide`) - piece the deck from
   existing slides plus net-new "create" slides, reordered for the room.
4. **Create slides** (`demo-studio:create-slides`) - build the net-new slides as
   a dark, Google-Slides-safe PPTX.
5. **Presenter guide** (`demo-studio:presenter-guide`) - per-slide talking points,
   teleprompter script, and questions, with a live-demo run-of-show.

Each stage produces an artifact and feeds the next. Confirm decisions before
building; build one artifact at a time and show it before moving on.

## Entry points (start anywhere)

- "Here's a transcript" -> `demo-studio:demo-discovery`, then run the whole
  pipeline forward through build spec, deck flow guide, create slides, and
  presenter guide.
- "I know the demo, tweak it then build the deck and guides" -> go straight to
  `demo-studio:deck-flow-guide`, `demo-studio:create-slides`, and
  `demo-studio:presenter-guide`. Skip demo discovery and the build spec.
- "Just build the flow guide from this deck" -> `demo-studio:deck-flow-guide`.
- "Make the presenter guide for this final deck" -> `demo-studio:presenter-guide`
  (read the deck first).
- "Add the demo walkthrough to the guide" -> `demo-studio:presenter-guide`, demo
  section only.
- "Tweak the create slides" -> `demo-studio:create-slides` (edit
  `build_create_slides.js`, re-render).

Do not force earlier stages the user didn't ask for. Ask which stage they're at
only if it is genuinely ambiguous, then jump in there.

## Disciplines to apply throughout (do not skip)

Read `../../shared/grounding.md`. The essentials:

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
- **Design once, render many.** The create slides flow through three artifacts
  (the flow-guide previews, the PPTX, and the presenter guide). Keep them
  consistent; a change to one belongs in the generator, not a one-off patch.
- **Guardrails, held without re-litigating:** no em dashes anywhere; Google-Slides-
  safe shapes; the brand system (Fraunces / IBM Plex Sans / JetBrains Mono; indigo
  `#4C2889` with amber/green/coral accents; ink `#1C1526`, paper `#F6F4FA`);
  generic/public-safe (no customer or participant names in anything that may go
  public).

The generators are the format in each worker. Do not hand-roll the HTML or restyle
it; change the JSON, not the CSS. If the user wants a genuinely new component, add
it to the generator so it is reusable next time.

## Brand system (locked, used by all generators)

Fonts: Fraunces (headings), IBM Plex Sans (body), JetBrains Mono (labels/code).
Light guides use paper `#F6F4FA` / ink `#1C1526` / indigo `#4C2889`; the dark PPTX
uses a dark ground with lightened accents (indigo `#8E6BE6`, coral `#F0805E`, green
`#5FBE97`, amber `#E9B23A`). The generators embed this; keep it consistent so the
create slides look the same across the flow-guide preview, the PPTX, and the deck.

## Files

- `../../shared/grounding.md` - provenance, reference-wins, public-safe, no-tells,
  shared by every worker.
- `../demo-discovery/` - discovery read, demo-fit analysis, session design, and
  the v1/v2 fork.
- `../build-spec/` - the demo build spec worker (reference + template).
- `../deck-flow-guide/` - the deck flow guide worker (reference + generator).
- `../create-slides/` - the dark PPTX worker (reference + generator).
- `../presenter-guide/` - the presenter guide worker (reference + generator).

Each worker's own SKILL.md carries its quickstart command and its reference and
asset files.

## Output

Write finished artifacts to the workspace/output directory and present them. Offer
next steps (strip placement eyebrows for merge; a one-page cue card; run the spec).
