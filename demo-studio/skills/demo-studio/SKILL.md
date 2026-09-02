---
name: demo-studio
description: >-
  Use when someone shares a customer or discovery call transcript and wants demo
  or enablement work, when they ask for the whole pre-sales set for an upcoming
  session, when they name several pieces to build or want to resume the pipeline
  partway with earlier stages already settled, when they say "demo studio", or
  when they want demo help but it is not clear which piece they need. Not for a
  request that names exactly one artifact: that has its own skill.
---

# Demo Studio

Router for the pre-sales pipeline. Figure out where the user is, then hand off.
Do not do the work here, and do not force a stage nobody asked for.

## Entry points

| They say | Go to |
|---|---|
| "Here's a transcript" | `demo-discovery`, then onward |
| "Which demo should we lead with" | `demo-discovery` |
| "Spec the demo" | `build-spec` |
| "Piece the deck for this room" | `deck-flow-guide` |
| "Build the net-new slides" | `create-slides` |
| "Make the presenter guide" | `presenter-guide` |
| "I know the demo, build the deck and guides" | `deck-flow-guide`, `create-slides`, `presenter-guide` |
| Genuinely unclear | Ask which stage. Do not guess. |

Worker names above are bare on purpose. Installed as a plugin they are addressed
`demo-studio:build-spec` and so on; symlinked into a personal skills directory they
are addressed `build-spec`. The bare name is the identity in both cases, so use it
and let the prefix resolve.

## Sequencing

Full run: discovery, build spec, flow guide, create slides, presenter guide.
Build one artifact at a time and show it before starting the next.

## Recommend, then lock

At each hinge, commit to a recommendation and get a small set of decisions locked
before building. Do not present an exhaustive menu.

## Design once, render many

The create slides flow through three artifacts: the flow-guide previews, the
PPTX, and the presenter guide. Build a net-new slide once with
`create-slides` and keep it consistent across all three rather
than redrawing it per artifact.

## Disciplines

Read `shared/grounding.md`. Provenance, reference wins, public safe, no
AI tells. The mechanical rules are enforced by `shared/guardrails.py`, so a
violation fails the build rather than needing to be remembered.
