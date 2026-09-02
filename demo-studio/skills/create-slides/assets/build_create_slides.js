'use strict';
/*
  The per-engagement slide builder. Author one recordSlide block per net-new
  slide. Running this writes BOTH the deck and the preview SVGs, from the same
  coordinates, so the flow guide cannot show a different picture than the deck.

  node build_create_slides.js            -> create-slides.pptx + slide-previews.json
*/
const fs = require('node:fs');
const path = require('node:path');
const pptxgen = require('pptxgenjs');
const kit = require('./slidekit');

const brand = JSON.parse(fs.readFileSync(
  path.join(__dirname, '..', '..', '..', 'shared', 'brand.json'), 'utf8'));
const P = brand.surfaces.pptx;
// brand.json stores hex with a leading '#', pptxgenjs and the slide lint want it
// without. Normalise once, here, rather than at every call site.
const nohash = (c) => String(c).replace(/^#/, '');
const palette = {
  bg: nohash(P.bg), panel: nohash(P.panel), border: nohash(P.border),
  txt: nohash(P.txt), mut: nohash(P.mut), indigo: nohash(P.indigo),
  heading: brand.fonts.heading, body: brand.fonts.body, mono: brand.fonts.mono,
};
const IND = nohash(P.indigo), CORAL = nohash(P.coral), GREEN = nohash(P.green);

const slides = [
  kit.recordSlide(
    { eyebrow: 'SETUP FLOW 01', title: 'Two lanes, one truth',
      sub: 'Durable state survives; the live worker query does not' },
    (k) => {
      k.box(0.6, 2.4, 4.6, 1.4, { rt: 'PLATFORM LANE', fill: nohash(P.panel) });
      k.arrowR(5.5, 2.9, 0.7, 0.4, IND);
      k.box(6.5, 2.4, 4.6, 1.4, { rt: 'WORKER LANE', fill: nohash(P['coral-fill']) });
      k.label(0.6, 4.0, 4.6, 'SURVIVES A CRASH', GREEN, 9, 'center');
      k.label(6.5, 4.0, 4.6, 'GOES OFFLINE', CORAL, 9, 'center');
    }),
  // Add one recordSlide block per net-new slide.
];

const { lintSlides, formatFindings } = require('./lint_slides');
const findings = lintSlides(slides, palette);
if (findings.length) {
  console.error(`slide lint failed with ${findings.length} finding(s):`);
  console.error(formatFindings(findings));
  process.exit(1);
}

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
kit.renderPptx(slides, pres, palette);
pres.writeFile({ fileName: 'create-slides.pptx' })
  .then((f) => console.log('wrote', f));

// The preview map the flow-guide config pulls preview.body from.
const previews = {};
slides.forEach((s, i) => { previews[`slide-${i + 1}`] = kit.renderSvg(s, palette); });
fs.writeFileSync('slide-previews.json', JSON.stringify(previews, null, 2));
console.log('wrote slide-previews.json with', slides.length, 'preview(s)');
