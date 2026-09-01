# Flow guide format

Produced by `assets/build_flow_guide.py CONFIG.json OUT.html`. The styling is fixed
(it is the reusable format). You fill the JSON. See
`assets/examples/flow_guide.example.json`.

## What it is

A top-down document of ACTS, each containing CARDS. A card is either:

- a **deck** card: "pull this existing slide", named explicitly so the presenter
  can find it, or
- a **create** card: a slide that does not exist yet, with a **collapsible
  preview mockup**, a one-line **why**, and a **traces to** discovery link.

The point is to reorder and piece a deck for THIS room, showing exactly what to
reuse and what to build, with the net-new slides previewed inline.

## Config fields

Top level: `tab_title`, `eyebrow`, `title`, `subtitle`, `chips` (list of
`[label, value]`), `legend` (`deck_label/deck_text/create_label/create_text`),
`acts` (list), `footer` (`title`, `cols` = list of `[heading, cls, html]` where
`cls` is `go` | `warn` | `""`).

Each act: `no`, `title`, `purpose`, `time`, `cards` (list).

**deck card:** `type:"deck"`, `seq`, `title`, `deckid_label` (default "Pull this
slide"), `deckid_quote` (the verbatim slide headline in quotes: this is how the
presenter locates it), `deckid_pg` (section + page), `why`, `traces`, `src_label`.

**create card:** `type:"create"`, `seq`, `title`, `why`, `traces`, `src_label`
(default "Create"), and `preview` = `{eyebrow, title, sub, body}` where `body` is a
raw SVG or HTML mockup of the slide.

`why` and `traces` accept inline HTML (use `<b>...</b>` for emphasis, `<code>` for
identifiers). Keep them to one line each. No em dashes.

## Traces to discovery

`traces` is **required** on every card here, unlike on a presenter-guide slide
where it is optional. Write a discovery signal id, for example `D2`, or a short
phrase if you have not run discovery for this engagement.

Add an optional top-level `discovery` field naming a `discovery.json` path
(relative paths resolve against this config's own directory). When present, the
build resolves every card's `traces` value against that record's signal ids:

- an id that does not exist (`traces: "D9"` when the record has no `D9`) is an
  `unresolved-trace` and **hard-fails the build**, naming the card and the id;
- a `traces` value with no signal id at all (free text) is `untraced` and only
  **warns**, so an engagement with no discovery record yet still builds;
- when the config has no `discovery` field, the check is skipped entirely, and
  the build prints a note saying so rather than passing silently.

See `../../demo-discovery/references/discovery-format.md` for the id format
and `../../demo-discovery/SKILL.md` to produce a `discovery.json`.

## Public-safe escape: `allow_words` and `banned_terms`

Optional top-level fields, both arrays of strings, read by the same guardrail
that scans every text field in this config:

- `banned_terms`: identifiers that must never reach the output (a real
  customer name, a codename, an internal host). Any match anywhere in the
  config, case-insensitive and word-bounded, hard-fails the build.
- `allow_words`: a documented escape for the AI-tell filter. If a listed word
  ("robust", "actually", etc.) is doing legitimate technical work here, name it
  in this list rather than rewording around a false positive.

## Authoring the create-card preview (`preview.body`)

The preview renders inside a fixed `.slide` frame (white, 16:9). For a card whose
slide will also become a real create-slide, do not hand-draw it here: build the
slide once with `demo-studio:create-slides`, which writes `slide-previews.json`
(one entry per slide, produced by `build_create_slides.js`), and paste the
matching SVG into `preview.body`. This is "design once, render many": the flow
guide, the PPTX, and any future consumer show the same drawing because they all
derive from the same slidekit coordinate space, so the mockup and the shipped
slide cannot drift apart.

**A. Inline SVG from slidekit** (the create-slides case, and any other diagram
with arrows). Use `viewBox="0 0 1333 750"` with
`preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%"`, matching
the slide's real 13.333 x 7.5in canvas at slidekit's 100x scale. For colors, use
the tokens in `../../../shared/brand.json` rather than hardcoding hex here; a
prose palette drifts the moment brand.json changes and this doc does not. Give
each SVG its own arrowhead `<marker>`s.

**B. HTML atoms** (best for a preview that is NOT also a create-slide, a quick
box-layout mockup with no matching PPTX to stay consistent with). These
classes are available inside `.s-body`:
- `.harness-frame` + `.harness-tab`: a dashed outer frame with a corner label.
- `.row3` + `.hbox` (`<b>` title, `<span>` sub): a 3-up row of boxes.
- `.innerlbl`: a small centered mono caption.
- `.gap` + `.gl` (label) + `.gt` (text): a coral "gap" band.
- `.tiles` + `.tile` (`<b>`, `<span>`): a 2x2 tile grid.
- `.stack-two` + `.agentbox`: two boxes side by side.
- `.conn` + `.backbone` (`<b>`, `<span>`) + `.expose`: connectors into a hero bar.
- `.beats` + `.beat-r` (`.bn` number, `<b>`, `<span>`): numbered beat rows.

Keep preview content light so it fits the 16:9 frame without clipping.

## Notes

- Number cards in flow order (`seq`). If you insert one, renumber the rest.
- The footer "cut list" (spine / drop-first / skip-if-known) helps the presenter
  when time is short. Keep it.
- Print: previews are collapsed `<details>` by default; expand the ones you want
  before print-to-PDF.
