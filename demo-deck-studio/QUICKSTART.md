# Quickstart

Four deliverables, one loop each: copy an example, edit the content, run the
generator, open the HTML (or render the PPTX and look at it).

## Flow guide (piece the deck: from-deck + create cards with previews)
```bash
cp assets/examples/flow_guide.example.json my_flow.json
# edit my_flow.json — acts, cards, and create-card previews (see references/flow-guide-format.md)
python3 assets/build_flow_guide.py my_flow.json flow-guide.html
```

## Presenter guide (per-slide points / teleprompter Say / questions + demo run-of-show)
```bash
cp assets/examples/presenter_guide.example.json my_pg.json
# edit my_pg.json — slides[] and the optional demo{} block (see references/presenter-guide-format.md)
python3 assets/build_presenter_guide.py my_pg.json presenter-guide.html
```

## Create slides (dark, Google-Slides-safe PPTX)
```bash
cp assets/build_create_slides.js my_slides.js
# edit my_slides.js — one builder block per net-new slide (see references/create-slides-pptx.md)
npm i pptxgenjs
node my_slides.js
python3 /mnt/skills/public/pptx/scripts/office/validate.py create-slides.pptx
python3 /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf create-slides.pptx
pdftoppm -jpeg -r 150 create-slides.pdf slide      # then VIEW every slide-N.jpg and fix
```

## Build spec (hand to a coding agent)
```bash
cp assets/build_spec_template.md BUILD_SPEC.md
# fill it in (see references/build-spec.md)
```

Then present the finished files. Rules that always apply: no em dashes; block-arrow
autoshapes only in the PPTX; brand fonts (Fraunces / IBM Plex Sans / JetBrains Mono);
generic/public-safe. Change the JSON, not the CSS — the format is the point.
