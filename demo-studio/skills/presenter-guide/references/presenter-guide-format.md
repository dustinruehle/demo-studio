# Presenter guide format

Produced by `assets/build_presenter_guide.py CONFIG.json OUT.html`. The styling is
fixed (side nav, 3-column layout, teleprompter cards, demo beat cards). You fill the
JSON. See `assets/examples/presenter_guide.example.json`.

## What it is

A slide-by-slide companion for delivering the FINAL aggregate deck:

- **Left nav**: every slide by number + short title, act-colored, with scroll-spy.
- **Per slide, three blocks:**
  - **Talking points**: the compact "what to land" brief.
  - **Say**: the teleprompter. Each beat is its own card on its own line, one
    idea per glance. This is the part users love; keep beats short and punchy.
  - **Ask & expect**: questions to pose, and ones the room will pose back.
- **Optional live-demo run-of-show** (below the last slide): cold start, the two
  lanes, a card per beat with the exact Ctrl-C, plus reference/switches.

## Config fields

Top level: `tab_title`, `nav_title`, `nav_sub`, `eyebrow`, `title`, `subtitle`,
`chips` (`[label, value]`), `legend` (`[label, value]`), `acts`, `slides`, `demo`
(optional).

`acts`: a map of `act_key -> [label, hex_color]`. The label shows in the nav (its
part before "·") and as the section eyebrow. Suggested palette: Open `#1C1526`,
Frame `#B07A00`, Model `#4C2889`, Prime `#2E7D5B`, Prove `#C0503A`, Handoff
`#6E4FC0`, Demo `#1C1526`.

Each slide: `num`, `act` (a key in `acts`), `short` (nav label), `title`,
`onscreen` (what's on the slide), `points` (list), `say` (list of teleprompter
beats), `ask` (list). All are plain strings (auto-escaped): write clean prose,
no HTML needed here.

## Demo run-of-show (`demo`)

Optional. Fold the demo RUNBOOK into this. Fields:

- `nav_divider`, `banner` (`title`, `text`), `talk_track` (opening line, one beat).
- `lanes`: list of `[name, cls, description]`; `cls` is `plat` | `work` | `""`.
  Keep PLATFORM (survives crash) and WORKER (goes offline) as the two anchors.
- `termmap`: list of `[num, command, keep_running, ctrl_c_in_beats]`. Wrap a beat
  callout in `<span class="kill">Beat 2</span>`.
- `smoke`: one-line smoke check (HTML ok).
- `beats`: list of beat cards. Each: `id` (`d1`, `d2`, ...), `badge`, `title`,
  `tag`, `accent` (`indigo` | `coral` | `green` | `amber`), optional `term` (the
  dark Ctrl-C callout, HTML ok), `rows`, optional `note`, optional `nav`.
  - `rows`: list of `[label, cls, kind, content]`. `cls` colors the label:
    `goal` | `do` | `watch` | `why`. `kind` is `single` (content = HTML string)
    or `ol` / `ul` (content = list of HTML strings). Beats 4/5-style beats can have
    multiple Do/Watch pairs: just add more rows.
- `scenarios`: list of `[button, case, shows]`.
- `switches`: list of `[title, code]` (code renders in a dark block; use `\n`).
- `switch_note`: one line under the switches.
- `troubleshooting`: list of `[title, detail]`.

Beat/demo content accepts inline HTML: `<b>`, `<code>`, `<span class="kill">`,
`&rarr;`, `&middot;`, `&#9000;` (keyboard glyph). No em dashes.

**Literal angle brackets.** `switches[].code` is treated as literal shell text and
is auto-escaped, so write placeholders like `<ns>` or `<acct>` normally. Every OTHER
demo/beat field accepts inline HTML, so for a literal `<` or `>` in those (e.g. a
`<code>` snippet showing a generic type) use `&lt;` / `&gt;`. Slide-level fields
(`title`, `onscreen`, `points`, `say`, `ask`) are always auto-escaped: write plain
prose there.

## Authoring tips

- Tune every talking point and Say beat to the ACTUAL room: name people and echo
  their quotes where it lands. Generic scripts read as generic.
- Order accents so the "money moment" beat stands out (coral).
- The guide prints cleanly (nav hidden, blocks reflow); open in a browser for the
  brand fonts.
