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

## Helpers (in the template)

`slideBase(eyebrow,title,sub)`, `box(s,x,y,w,h,opts)` (rich text via `opts.rt`),
`frame(s,x,y,w,h,color)` (outline only), `arrowR/arrowD(s,x,y,w,h,color)` (block
arrows), `label(s,x,y,w,text,color,size,align)` (mono caption). Two example slide
patterns are included: "boxes + gap" and "diagram with block arrows".

## The visual-QA loop (never skip)

```bash
npm i pptxgenjs
node build_create_slides.js
python3 /mnt/skills/public/pptx/scripts/office/validate.py create-slides.pptx
python3 /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf create-slides.pptx
pdftoppm -jpeg -r 150 create-slides.pdf slide
```

Then VIEW every `slide-N.jpg`. Look for: label/arrow collisions, text touching a
frame border, low contrast, clipped content, wrapped titles. Fix coordinates and
re-render until each slide is clean. (In this codebase the classic bug was gap
labels colliding with a side frame: widen the gap or recenter the label.)

## Placement markers

A small `SETUP FLOW · NN` eyebrow on each slide helps the presenter drop it into the
right spot in the aggregate. Offer to strip these for a clean merge-ready copy.

## Read the pptx skill first

Before generating, read `/mnt/skills/public/pptx/SKILL.md`. It mandates pptxgenjs
for new decks and documents the validate/render scripts referenced above.
