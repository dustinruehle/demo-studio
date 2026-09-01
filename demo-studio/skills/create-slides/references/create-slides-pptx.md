# Create slides (dark PPTX)

Build the net-new slides as a dark-mode PPTX that drops into the aggregate deck.
Template: `assets/build_create_slides.js` (edit per engagement; slide diagrams are
bespoke, so this is code, not JSON).

## Hard rules (do not break)

- **Google-Slides-safe:** block-arrow autoshapes only (`rightArrow`, `downArrow`,
  `leftRightArrow`). NEVER line connectors or dashed lines (`prstDash`): Google
  Slides silently drops them on import. Solid borders only. Hex without `#`.
- **Dark + readable:** dark background, lightened accents (the palette in the
  template). Check contrast in the render.
- **No em dashes** in any slide text.
- **Brand fonts:** Fraunces (headings), IBM Plex Sans (body), JetBrains Mono
  (labels). The render machine may lack them and show fallbacks: that is fine for
  layout QA; the file names them correctly.

## Helpers (the kit API, in `slidekit.js`)

The template authors through `assets/slidekit.js`, not local per-file helpers.
One call records one slide:

```js
const kit = require('./slidekit');
kit.recordSlide({ eyebrow, title, sub }, (k) => {
  k.box(x, y, w, h, opts);      // rich text via opts.rt; opts.fill/line/lw/
                                 // align/valign/margin/color all optional
  k.frame(x, y, w, h, color);   // outline only, fill is the background
  k.arrowR(x, y, w, h, color);  // block arrow, never a connector
  k.arrowD(x, y, w, h, color);
  k.label(x, y, w, text, color, size, align);  // mono caption
});
```

`k` has no `s` (slide) parameter: the recorder only captures ops, it does not
touch pptxgenjs. `kit.renderPptx(slides, pres, palette)` and
`kit.renderSvg(slide, palette)` replay those ops into the deck and the preview
SVG respectively, from the one coordinate space, so the two cannot drift.
`kit.bboxes(slide)` returns the recorded geometry in inches, for tests. Two
example slide patterns are included in `build_create_slides.js`: "boxes + gap"
and "diagram with block arrows".

## The visual-QA loop (never skip)

Run these commands from `skills/create-slides/` (this skill's own directory),
the same working directory the Quickstart in `SKILL.md` uses.

```bash
. ../../shared/pptx_tools.sh
PPTX_SKILL="$(find_pptx_skill)" || exit 1
render_preflight || echo "proceeding without visual QA, deck is UNVERIFIED"

node assets/build_create_slides.js
python3 "$PPTX_SKILL/scripts/office/validate.py" create-slides.pptx
python3 "$PPTX_SKILL/scripts/office/soffice.py" --headless --convert-to pdf create-slides.pptx
pdftoppm -jpeg -r 150 create-slides.pdf slide      # then VIEW every slide-N.jpg
```

Then VIEW every `slide-N.jpg`. Look for: label/arrow collisions, text touching a
frame border, low contrast, clipped content, wrapped titles. Fix coordinates and
re-render until each slide is clean. (In this codebase the classic bug was gap
labels colliding with a side frame: widen the gap or recenter the label.)

## Placement markers

A small `SETUP FLOW · NN` eyebrow on each slide helps the presenter drop it into the
right spot in the aggregate. Offer to strip these for a clean merge-ready copy.

## Read the pptx skill first

Before generating, read the pptx skill's SKILL.md at the path `find_pptx_skill`
resolves. It mandates pptxgenjs for new decks and documents the validate/render
scripts referenced above.
