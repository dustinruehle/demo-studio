# Flow guide format

Produced by `assets/build_flow_guide.py CONFIG.json OUT.html`. The styling is fixed
(it is the reusable format). You fill the JSON. See
`assets/examples/flow_guide.example.json`.

## What it is

A top-down document of ACTS, each containing CARDS. A card is either:

- a **deck** card — "pull this existing slide", named explicitly so the presenter
  can find it, or
- a **create** card — a slide that does not exist yet, with a **collapsible
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
slide"), `deckid_quote` (the verbatim slide headline in quotes — this is how the
presenter locates it), `deckid_pg` (section + page), `why`, `traces`, `src_label`.

**create card:** `type:"create"`, `seq`, `title`, `why`, `traces`, `src_label`
(default "Create"), and `preview` = `{eyebrow, title, sub, body}` where `body` is a
raw SVG or HTML mockup of the slide.

`why` and `traces` accept inline HTML (use `<b>...</b>` for emphasis, `<code>` for
identifiers). Keep them to one line each. No em dashes.

## Authoring the create-card preview (`preview.body`)

The preview renders inside a fixed `.slide` frame (white, 16:9). Two ways to draw:

**A. Inline SVG** (best for diagrams with arrows). Use `viewBox="0 0 760 330"` and
`preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%"`. Brand colors:
indigo `#4C2889`, coral `#E2664A`, green `#3B8C6E`, ink `#1C1526`, muted `#6A6478`,
tint `#EFEAF6`. Give each SVG its own arrowhead `<marker>`s. (This mirrors the PPTX
diagram; keep them visually consistent.)

**B. HTML atoms** (best for box layouts). These classes are available inside
`.s-body`:
- `.harness-frame` + `.harness-tab` — a dashed outer frame with a corner label.
- `.row3` + `.hbox` (`<b>` title, `<span>` sub) — a 3-up row of boxes.
- `.innerlbl` — a small centered mono caption.
- `.gap` + `.gl` (label) + `.gt` (text) — a coral "gap" band.
- `.tiles` + `.tile` (`<b>`, `<span>`) — a 2x2 tile grid.
- `.stack-two` + `.agentbox` — two boxes side by side.
- `.conn` + `.backbone` (`<b>`, `<span>`) + `.expose` — connectors into a hero bar.
- `.beats` + `.beat-r` (`.bn` number, `<b>`, `<span>`) — numbered beat rows.

Keep preview content light so it fits the 16:9 frame without clipping.

## Notes

- Number cards in flow order (`seq`). If you insert one, renumber the rest.
- The footer "cut list" (spine / drop-first / skip-if-known) helps the presenter
  when time is short. Keep it.
- Print: previews are collapsed `<details>` by default; expand the ones you want
  before print-to-PDF.
