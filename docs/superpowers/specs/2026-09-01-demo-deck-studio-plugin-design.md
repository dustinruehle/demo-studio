# Demo Deck Studio: plugin restructure and capability upgrade

- **Date:** 2026-09-01
- **Status:** approved, ready for implementation planning
- **Baseline commit:** `0e8ba48` (verbatim extraction, no edits)

## Context

`demo-deck-studio` is a single skill shared from a colleague's Claude desktop
install and extracted byte-identical to `/Users/dan/code/skills/demo-deck-studio`
(14 files, 104K). It runs a five-stage pipeline from a discovery-call transcript to
four deliverables: a demo build spec, a deck flow guide (HTML), the net-new slides
(dark PPTX), and a presenter guide with a live-demo run-of-show (HTML).

It works, and the format generators are genuinely good. Three classes of problem
motivate this rework.

**It is really five skills in a trench coat.** One `SKILL.md` carries five
independent jobs behind one description. There is no way to ask for just the
presenter guide by name, and the description has to advertise all five outputs at
once, which weakens discovery for each.

**Its load-bearing disciplines are unenforced.** "No em dashes", "public-safe",
"traces-to", "the brand is locked", "Google-Slides-safe shapes" are documented as
prose the model must remember. `writing-skills` is explicit that regex-enforceable
constraints belong in validation, not documentation. Today the brand palette is
duplicated across three generators, and `traces` is free text nothing checks.

**It only runs in the desktop sandbox.** Verified failures on macOS / Claude Code:

| Check | Result |
|---|---|
| `build_flow_guide.py` on Python 3.12 | passes |
| `build_presenter_guide.py` on Python 3.12 | passes |
| `build_flow_guide.py` on Python 3.9 (stock macOS) | passes |
| `build_presenter_guide.py` on Python 3.9 | **SyntaxError**, line 100 |
| `/mnt/skills/public/pptx/...` (referenced 4x) | **does not exist** off-sandbox |
| `soffice`, `pdftoppm` (mandatory QA loop) | **both absent**, installable via brew |

So the PPTX deliverable, whose own reference file says "never ship without looking at
every slide", cannot be visually QA'd at all outside the desktop app.

## Goals

1. Split into a plugin of individually invocable skills, with a thin router that
   preserves the whole-pipeline path and the entry-point map.
2. Make the mechanical guardrails mechanical.
3. Author a create-slide once; render it to both PPTX and preview.
4. Give discovery a durable artifact, and make `traces-to` verifiable against it.
5. Validate the JSON configs with errors that name the offending field.
6. Run on a stock Mac, degrading loudly rather than silently when tooling is absent.

## Non-goals

- No change to the visual design of any deliverable. The generated HTML and PPTX
  should look the same; the format is the product.
- No new deliverables beyond the discovery artifact.
- Not vendoring the `pptx` skill's office scripts (they carry a large XSD tree).
- Not building a declarative slide layout engine (rejected as approach A below).

## Locked decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Plugin with a router plus five worker skills | Individually invocable; each gets its own discovery description |
| D2 | Shared layer at plugin root, referenced as `../../shared/...` | Sibling cross-references are the established convention (superpowers does this); avoids duplication across a flat skill namespace |
| D3 | Single-source slides via polymorphic helpers, not a JSON IR | Approach B below; preserves the working absolute-coordinate idiom, no layout engine |
| D4 | PPTX QA: preflight installs, degrade loudly if declined | Keeps the hard rule enforceable where tooling exists; never claims a visual pass that did not happen |
| D5 | Guardrails hard-fail the build | Mechanical constraints get validation, not prose |
| D6 | Stdlib-only Python, floor 3.9 | No `pip install` step; runs on stock macOS |
| D7 | Subagent testing for router behavior; mechanical verification elsewhere | Routing is the one genuinely behavioral question |

### Rejected alternatives

- **Approach A, declarative slide IR.** A JSON layout language rendered to both SVG
  and pptxgenjs. Cleanest in principle and would bring slides under schema
  validation, but the existing slides are bespoke diagrams on hand-tuned absolute
  coordinates while the HTML preview atoms are CSS-flow-based. Bridging them means
  building a layout engine, larger than all the rest of this work combined.
- **Approach C, author in HTML and screenshot into the PPTX.** Trivially consistent,
  but slides arrive in Google Slides as flat images rather than editable shapes,
  defeating the merge-into-the-aggregate-deck purpose.
- **Four flat skills with no router.** Loses the entry-point map and the
  cross-stage consistency rule with nowhere to live.
- **One skill with a mode argument.** All five descriptions collapse into one, so
  discovery cannot fire on "make me a presenter guide" unless the single
  description already enumerates it.

## 1. Structure

```
demo-deck-studio/                    <- plugin root
  .claude-plugin/plugin.json
  shared/
    brand.json                       palette, fonts, act colors (ONE source)
    brand.py                         loader: emits the CSS :root block
    guardrails.py                    em dash, AI-tells, public-safe, PPTX shapes
    validate_config.py               stdlib JSON-schema walker
    pptx_tools.sh                    locate pptx skill; preflight soffice/pdftoppm
    grounding.md                     provenance discipline, referenced by all five
  skills/
    demo-deck-studio/                ROUTER
    demo-discovery/                  stages 1-4 -> discovery.json + discovery.md
    build-spec/                      stage 5    -> BUILD_SPEC.md
    deck-flow-guide/                 stage 6    -> flow-guide.html
    create-slides/                   stage 7    -> create-slides.pptx + slide SVGs
    presenter-guide/                 stage 8    -> presenter-guide.html
```

Each worker owns its own `references/` and `assets/`. Nothing that two skills need
lives inside one of them; it goes in `shared/`.

| Skill | Owns | Input | Output |
|---|---|---|---|
| `demo-deck-studio` | entry-point map, sequencing, recommend-then-lock | anything | delegation |
| `demo-discovery` | pipeline stages 1-4 | transcript(s) | `discovery.json`, `discovery.md` |
| `build-spec` | `build-spec.md`, `build_spec_template.md` | discovery + locked decisions | `BUILD_SPEC.md` |
| `deck-flow-guide` | `flow-guide-format.md`, `build_flow_guide.py` | existing deck + discovery | `flow-guide.html` |
| `create-slides` | `create-slides-pptx.md`, `slidekit.js` | slide list | `create-slides.pptx`, slide SVGs |
| `presenter-guide` | `presenter-guide-format.md`, `build_presenter_guide.py` | final deck + runbook | `presenter-guide.html` |

### Router contract

The router is thin by design. It carries the entry-point map, stage sequencing, the
recommend-then-lock hinge behavior, and handoff between stages. It **must not**
restate worker content: it names them as `demo-deck-studio:build-spec` and so on.
Per `writing-skills`, `@`-links force-load files and burn context, and duplicated
workflow text gets followed in place of the real skill.

## 2. Descriptions are the interface

Each description states only triggering conditions and **never** summarizes a
workflow. This is a documented failure mode: an agent that reads a workflow summary
in a description follows the summary and skips the skill body.

Draft triggers, to be tested for overlap:

- **router**: a call transcript is shared; "the whole thing"; "demo deck studio";
  genuinely ambiguous entry.
- **demo-discovery**: "read this transcript"; "which demo should we lead with";
  demo-fit; session design; who is in the room.
- **build-spec**: "spec the demo"; "build spec"; something to hand a coding agent.
- **deck-flow-guide**: "flow guide"; reorder or piece together a deck; which slides
  to pull.
- **create-slides**: "create slides"; net-new slides; the PPTX; slide mockups.
- **presenter-guide**: "presenter guide"; teleprompter; speaker notes; "run of
  show"; the live-demo walkthrough.

**Requirement:** no worker trigger may be a subset of the router's, or the router
swallows direct requests. Verified by the router subagent tests in section 9.

## 3. Shared layer

### brand.json

Both HTML generators already consume CSS custom properties (67 `var(--)` uses in the
flow guide, 55 in the presenter guide) over a small `:root` block, so this is a
contained change rather than a restyle:

1. Generate the `:root` block from `brand.json`.
2. Eliminate the raw hex values sitting outside `:root` (3 in `build_flow_guide.py`,
   12 in `build_presenter_guide.py`).
3. Load the same file for the JS palette constants in the PPTX backend. Node
   requires JSON natively, so no JS loader module is needed.

`brand.json` carries the light palette (guides), the dark palette (PPTX), the font
stack, and the act colors currently documented only in prose in
`presenter-guide-format.md`.

**Acceptance:** changing one hex in `brand.json` changes it in all three outputs;
no hex literal appears in any generator source.

### guardrails.py

One module, imported by every generator and runnable standalone.

| Check | Scope | Failure |
|---|---|---|
| No em dashes | every text field of every output | non-zero exit, names field |
| AI-tell filler (`seamless`, `robust`, `leverage`, `genuinely`, `delve`, `honestly`, `actually`) | prose fields | non-zero exit, names the word and field |
| Public-safe identifier gate, word-bounded and case-insensitive | all output, per-engagement list | non-zero exit, names the hit |
| No line connectors, no `prstDash`, hex without `#` | PPTX builder only | non-zero exit, names the shape |

**Division of labour.** `guardrails.py` inspects *outputs and configs*: the
generated HTML, the config JSON, and the generated `.pptx` (unzipped, checked for
connector and `prstDash` elements). The slidekit lint in section 4 inspects
*authoring* in JS, catching the same shape violations earlier with a line number in
the builder. The two overlap deliberately: the lint gives a fast, located error, the
guardrail is the gate that cannot be bypassed by hand-editing a builder.

Hard failure, not warnings. The AI-tell list needs a documented escape for
legitimate technical use of a listed word; the escape is an explicit allowlist entry
in the engagement config, not a flag that disables the check.

## 4. slidekit: one authoring pass, two backends

`skills/create-slides/assets/slidekit.js` keeps today's helper API exactly
(`slideBase`, `box`, `frame`, `arrowR`, `arrowD`, `label`) and adds a backend switch.

- **pptx backend**: the current pptxgenjs calls, semantics unchanged.
- **svg backend**: the same inch coordinates scaled x100 into
  `viewBox="0 0 1333 750"`, which is exactly the `LAYOUT_WIDE` 13.333 x 7.5in slide.

This fixes a real fidelity bug. Today's flow-guide previews use
`viewBox="0 0 760 330"`, an aspect ratio of 2.30:1 against the slide's actual 1.78:1,
so the "preview" of a create-slide is a differently-proportioned drawing of it. Under
slidekit both artifacts derive from one coordinate space and the mismatch cannot
recur.

**Output contract.** One run emits `create-slides.pptx` plus a slide-id to SVG map.
The flow-guide config references a slide by id for its `preview.body` instead of
re-drawing it, so a create-slide is authored once and appears consistently in the
flow guide, the PPTX, and the presenter guide.

**Lint pass** over the builder before render: off-canvas coordinates
(`x + w > 13.333`, `y + h > 7.5`), banned shape types, `#`-prefixed hex, em dashes
in slide text.

**Acceptance:** for every slide, the SVG and the PPTX shape bounding boxes agree
within rounding; the CSS-atom preview classes remain available for non-slide
mockups but are no longer used to draw create-slides.

## 5. Config validation

A stdlib-only schema walker (`shared/validate_config.py`, no `pip install`) with a
schema shipped beside each generator. Configs validate before build. Errors name the
path and the problem:

```
flow_guide.json: acts[2].cards[0].preview.title: required field missing
flow_guide.json: acts[1].cards[3].type: expected "deck" or "create", got "slide"
```

Current behavior for the same inputs is a Python traceback or a silently malformed
page.

## 6. Discovery artifact and verifiable traces-to

`demo-discovery` produces `discovery.json` plus a generated readable Markdown.
Every signal carries an id, an origin, and a grounded-or-inferred label:

```
D1  GROUNDED  "we can't tell if a worker died or the job is just slow"
              attributed to the platform lead
D2  INFERRED  healthcare claims domain, designed to exercise D1 and D4
```

This pays off twice. `traces` on flow-guide cards and presenter-guide talking points
is free text today that nothing verifies. Pointing it at a signal id makes the
skill's stated load-bearing discipline mechanically checkable: a guardrail confirms
every `traces` value resolves to a real signal and reports the ones that do not.
**Wiring.** The flow-guide and presenter-guide configs gain an optional top-level
`discovery` field naming a `discovery.json` path. When present, `traces` values are
resolved against it and unresolvable ones are reported. When absent, the check is
skipped with a stated note rather than silently passing. Free-text `traces` remains
accepted with a warning, so existing configs still build.

The artifact also lets later stages re-run without re-reading the transcript, and
gives the "did they actually say that?" source table a place to come from.

## 7. Portability

**`/mnt` path resolution.** `pptx_tools.sh` probes in order: the sandbox path
`/mnt/skills/public/pptx`, then the desktop app's skills directory, then any
`PPTX_SKILL_DIR` override. Not found means a message naming the probed locations,
not a bare `No such file or directory`.

**Render preflight.** Detects `soffice` and `pdftoppm`. If absent, offers
`brew install --cask libreoffice` and `brew install poppler`. If declined or the
install fails, the skill runs XML validation only and prints
`VISUAL QA SKIPPED - SLIDES UNVERIFIED`, which it must surface to the user rather
than reporting the deck as done. Degrade, never pretend.

**Python floor.** Fix `build_presenter_guide.py:100`, the single offending
construct: an escaped `\"` inside an f-string expression part, legal only in 3.12+.
Hoist the string to a variable before the f-string. It is the only occurrence in
either generator. Declare and test a 3.9 floor, which is strictly better than
pinning 3.12: an installed plugin runs from the user's project directory, where a
plugin-root `.tool-versions` would not apply.

## 8. Migration

Files move with `git mv` so history follows. The baseline commit `0e8ba48` stays as
the pristine reference for diffing against the colleague's original.

| From | To |
|---|---|
| `SKILL.md` | `skills/demo-deck-studio/SKILL.md`, reduced to the router |
| `references/pipeline.md` | router, minus the per-stage detail that moves to workers |
| `references/grounding.md` | `shared/grounding.md` |
| `references/build-spec.md` | `skills/build-spec/references/` |
| `references/flow-guide-format.md` | `skills/deck-flow-guide/references/` |
| `references/presenter-guide-format.md` | `skills/presenter-guide/references/` |
| `references/create-slides-pptx.md` | `skills/create-slides/references/` |
| `assets/build_flow_guide.py` | `skills/deck-flow-guide/assets/` |
| `assets/build_presenter_guide.py` | `skills/presenter-guide/assets/` |
| `assets/build_create_slides.js` | `skills/create-slides/assets/`, split with `slidekit.js` |
| `assets/build_spec_template.md` | `skills/build-spec/assets/` |
| `assets/examples/*.json` | beside their owning generator |
| `QUICKSTART.md` | split: each worker gets its own copy-edit-run block |

The brand and guardrail work happens after the move, so diffs stay readable.

## 9. Verification

### Mechanical

| # | Check |
|---|---|
| V1 | Both generators run on Python 3.9 and 3.12 |
| V2 | Generated HTML for the example configs differs from baseline only in ways reviewed and intended; diff every change, do not assume |
| V3 | Seeded em dash, AI-tell, and banned identifier each fail the build with a message naming the field |
| V4 | Malformed configs are rejected with a path-naming error, never a traceback |
| V5 | Changing one hex in `brand.json` propagates to all three outputs |
| V6 | Per slide, SVG and PPTX bounding boxes agree within rounding |
| V7 | A `traces` value with no matching signal id is reported |
| V8 | With `soffice`/`pdftoppm` removed from PATH, the skill emits the unverified banner and does not report success |
| V9 | Every `SKILL.md` has valid frontmatter, and no description summarizes a workflow |

V2 is the safety net for the non-goal that visual output must not change. Capture
baseline renders from `0e8ba48` before any edit. Byte-identity is the wrong bar:
regenerating `:root` from `brand.json` may reorder tokens, and the slide-preview
aspect-ratio fix changes previews on purpose. The bar is that every diff is
deliberate and reviewed.

### Subagent (authorized, router behavior only)

| # | Scenario | Expect |
|---|---|---|
| R1 | "Here's a call transcript" plus a transcript | router fires, offers the full pipeline |
| R2 | "Make me a presenter guide for this deck" | `presenter-guide` fires directly, no discovery stage forced |
| R3 | "Reorder this deck for a security-team audience" | `deck-flow-guide` fires |
| R4 | "Add the demo walkthrough to the guide" | `presenter-guide`, demo block only |
| R5 | Ambiguous: "help me with a customer demo" | router asks which stage rather than guessing |
| R6 | Mid-pipeline: "I know the demo, build the deck and guides" | stages 6-8, skips 1-5 |

R2 and R6 are the ones the current monolith cannot get right by construction, since
there is only one description to match on.

## 10. Suggested implementation order

Each phase leaves the skill working and independently verifiable, so the work can
stop at a phase boundary without leaving a half-migrated tree.

| Phase | Work | Gate |
|---|---|---|
| 0 | Capture baseline renders from `0e8ba48` | outputs archived for V2 |
| 1 | Portability fixes in place: 3.9 SyntaxError, `/mnt` probe, render preflight | V1, V8 |
| 2 | `git mv` restructure into the plugin, no content edits beyond splitting | V9, V2 |
| 3 | Shared layer: `brand.json`, `guardrails.py`, `validate_config.py` | V3, V4, V5 |
| 4 | `slidekit.js` and the two backends | V6 |
| 5 | `demo-discovery` artifact and the traces-to check | V7 |
| 6 | Router description tuning | R1-R6 |

Phase 1 before phase 2 is deliberate: fixing the known breakage while the tree is
still small keeps those diffs readable, and it means the restructure can be verified
against a generator that actually runs.

## 11. Risks and open questions

- **Description overlap** is the main risk to the whole design. If the router's
  triggers are too broad it swallows direct worker requests; too narrow and the
  whole-pipeline path stops firing. R1-R6 exist to tune this, and it may take
  iteration after real use.
- **The AI-tell filter will produce false positives.** "actually" and "robust" have
  legitimate technical uses. The allowlist escape needs to be easy or the check gets
  disabled wholesale.
- **`brand.json` cannot capture everything.** Some styling is structural (spacing,
  radii, layout) and stays in the CSS. The line between token and structure needs a
  stated rule, or the file becomes a dumping ground.
- **Baseline-identical output (V2) may conflict with the aspect-ratio fix.** Slide
  previews are *supposed* to change shape. V2 must be scoped to the guide chrome,
  with slide previews explicitly exempt and reviewed by eye.
- **Open:** does the plugin get installed via a local marketplace entry, or do the
  skills get symlinked into `~/.claude/skills/`? Affects nothing in the design but
  needs an answer before the skills are usable outside this repo.
