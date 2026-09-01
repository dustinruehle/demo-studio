---
name: create-slides
description: >-
  Use when the user needs the net-new slides built as a dark, Google-Slides-safe
  PPTX, or wants existing create slides tweaked and re-rendered.
---

# Create Slides

Read `references/create-slides-pptx.md` and `/mnt/skills/public/pptx/SKILL.md`.
Edit `assets/build_create_slides.js` (one builder block per slide), then ALWAYS
run the render-and-inspect QA loop and view every slide image before shipping.
Google-Slides-safe: block arrows, solid borders, no connectors or dashes; no em
dashes; dark and readable.

## Quickstart (dark, Google-Slides-safe PPTX)

```bash
cp assets/build_create_slides.js my_slides.js
# edit my_slides.js: one builder block per net-new slide (see references/create-slides-pptx.md)
npm i pptxgenjs
node my_slides.js
python3 /mnt/skills/public/pptx/scripts/office/validate.py create-slides.pptx
python3 /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf create-slides.pptx
pdftoppm -jpeg -r 150 create-slides.pdf slide
# then VIEW every slide-N.jpg and fix
```

Apply the disciplines in `../../shared/grounding.md`.
