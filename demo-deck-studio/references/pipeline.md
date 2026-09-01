# Pipeline — transcript to demo, deck, and guides

The full method. Each stage produces an artifact and feeds the next. The user can
enter at ANY stage (see "Entry points"). Confirm decisions before building; build
one artifact at a time and show it before moving on.

## The stages

1. **Discovery read.** Read the call transcript(s). Identify the real technical
   buyer versus low-fit contacts. Pull: their stack/frameworks, stated pains
   (quote them), constraints (security, regulated, air-gapped), deployment reality
   (cloud vs self-host), who will be in the room, and any productization thesis.
   Separate what was *said* from what you *infer*.

2. **Demo-fit analysis.** Map candidate out-of-the-box demos to the stated needs,
   with a one-line "why" each, and say which to lead with and which to skip. Name
   the audience's familiarity so you can right-size depth (skip a product pitch if
   they already know it).

3. **Session design.** Decide pitch-or-no-pitch, cloud-primary vs local, and draft
   a time-boxed beat sheet (for example 60 min) before touching architecture. Pick
   the demo domain from THEIR heavy verticals, not a default.

4. **v1 vs v2 fork (for multi-demo stories).** v1 = one narrative/domain with the
   OOTB demos themed and sequenced (cheap, robust, independent failure surfaces).
   v2 = one fused build (higher fidelity, higher risk; only with a POC/commitment).
   Default to v1 for a first session.

5. **Build spec.** Write a spec a coding agent can execute. See `build-spec.md`.
   Non-negotiables: name the skills/refs to read, "reference wins" over the spec,
   a preflight that installs prereqs on a fresh machine, a definition-of-done gate
   with tests that loop until green, generic/public-safe, and a mock-by-default
   switch. Pin pre-release versions and flag them.

6. **Deck assembly — flow guide.** Piece the deck from existing slides + net-new
   ("create") slides in the order that serves THIS room (not deck order). Produce
   the FLOW GUIDE (see `flow-guide-format.md`): each card names the exact source
   slide (verbatim headline + section + page) or is a "create" card with a
   collapsible mockup, a one-line "why", and a "traces to" link back to discovery.

7. **Create slides (PPTX).** Build the net-new slides as a dark, Google-Slides-safe
   PPTX for the aggregate deck (see `create-slides-pptx.md`). Always run the
   render-and-inspect visual QA loop.

8. **Presenter guide + live-demo run-of-show.** For the FINAL aggregate deck,
   build the presenter guide (see `presenter-guide-format.md`): per-slide Talking
   points / Say-teleprompter / Ask. Then fold the demo RUNBOOK into a live
   run-of-show section (cold start, the two lanes, a card per beat with the exact
   Ctrl-C, plus reference/switches).

## Entry points (start anywhere)

- "Here's a transcript" -> stage 1, run the whole pipeline.
- "I know the demo, tweak it then build the deck + guides" -> stages 6 to 8 (and
  edit the create-slides in stage 7). Skip 1 to 5.
- "Just build the flow guide from this deck" -> stage 6.
- "Make the presenter guide for this final deck" -> stage 8 (read the deck first).
- "Add the demo walkthrough to the guide" -> stage 8, demo section only.
- "Tweak the create slides" -> stage 7 (edit `build_create_slides.js`, re-render).

Ask which stage they're at if it isn't obvious; then jump in there.

## Disciplines that make it hold up (apply throughout)

- **Grounding and provenance.** Map every claim back to the source. Label
  grounded-versus-inferred when you design a domain or scenario. See
  `grounding.md`.
- **Recommend, then lock.** At each hinge, commit to a recommendation and ask the
  user to lock a small set of decisions before building.
- **Render-and-inspect QA.** Never ship a PPTX without rendering it to images and
  looking at every slide.
- **Guardrails held without re-litigating:** Google-Slides-safe shapes (block
  arrows, solid borders, no connectors/dashes), no em dashes anywhere, the locked
  brand system, generic/public-safe (no customer or participant names in anything
  that may go public).
- **Design once, render many.** The create slides flow through three artifacts
  (flow-guide previews, the PPTX, the presenter guide). Keep them consistent.
