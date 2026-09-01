'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');

const kit = require(path.join(__dirname, '..', 'skills', 'create-slides', 'assets', 'slidekit.js'));

const IND = '8E6BE6';

function sample() {
  return kit.recordSlide(
    { eyebrow: 'SETUP FLOW 03', title: 'Two lanes', sub: 'One dies' },
    (k) => {
      k.box(0.6, 2.2, 3.4, 1.2, { rt: 'Platform' });
      k.arrowR(4.2, 2.6, 0.5, 0.4, IND);
      k.frame(5.0, 2.2, 3.4, 1.2, IND);
      k.label(0.6, 3.5, 3.4, 'SURVIVES A CRASH', IND, 9, 'center');
    });
}

test('LAYOUT is the real slide geometry', () => {
  assert.strictEqual(kit.LAYOUT.w, 13.333);
  assert.strictEqual(kit.LAYOUT.h, 7.5);
  assert.strictEqual(kit.SCALE, 100);
});

test('recordSlide captures meta and every op in order', () => {
  const s = sample();
  assert.strictEqual(s.title, 'Two lanes');
  assert.strictEqual(s.sub, 'One dies');
  assert.deepStrictEqual(s.ops.map((o) => o.op), ['box', 'arrowR', 'frame', 'label']);
});

test('bboxes are reported in inches', () => {
  const b = kit.bboxes(sample());
  assert.deepStrictEqual(b[0], { op: 'box', x: 0.6, y: 2.2, w: 3.4, h: 1.2 });
  assert.deepStrictEqual(b[1], { op: 'arrowR', x: 4.2, y: 2.6, w: 0.5, h: 0.4 });
});

test('a label gets the fixed inherited height', () => {
  const b = kit.bboxes(sample());
  assert.strictEqual(b[3].h, kit.LABEL_H);
  assert.strictEqual(kit.LABEL_H, 0.28);
});

test('renderSvg uses a viewBox matching the slide aspect ratio', () => {
  const svg = kit.renderSvg(sample());
  assert.match(svg, /viewBox="0 0 1333 750"/);
  // 1333/750 is 1.777, the real 16:9 slide. The old previews used 760x330,
  // which is 2.30:1, so a preview was a differently shaped drawing.
  assert.doesNotMatch(svg, /760 330/);
});

test('renderSvg geometry is bboxes scaled by SCALE', () => {
  const s = sample();
  const svg = kit.renderSvg(s);
  const b = kit.bboxes(s)[0];
  // Use the kit's own converter, not raw multiplication: b.y * 100 is
  // 220.00000000000003 for y=2.2, which is not what lands in the SVG.
  const u = kit._internal.u;
  assert.match(svg, new RegExp(`x="${u(b.x)}"`));
  assert.match(svg, new RegExp(`y="${u(b.y)}"`));
  assert.match(svg, new RegExp(`width="${u(b.w)}"`));
  assert.match(svg, new RegExp(`height="${u(b.h)}"`));
});

test('SVG coordinates carry no floating point noise', () => {
  const svg = kit.renderSvg(sample());
  const coords = [...svg.matchAll(/(?:x|y|width|height)="([-\d.]+)"/g)].map((m) => m[1]);
  assert.ok(coords.length > 0, 'no coordinates found to check');
  for (const c of coords) {
    assert.ok(!/\d{6,}/.test(c), `coordinate ${c} carries float noise`);
  }
});

test('renderSvg escapes text so a config cannot inject markup', () => {
  const s = kit.recordSlide({ eyebrow: 'E', title: 'T', sub: '' },
    (k) => k.label(0, 0, 3, 'a < b & c > d', IND, 9, 'left'));
  const svg = kit.renderSvg(s);
  assert.match(svg, /a &lt; b &amp; c &gt; d/);
  assert.doesNotMatch(svg, /a < b/);
});

test('an arrow renders as a polygon, never a line', () => {
  const svg = kit.renderSvg(sample());
  assert.match(svg, /<polygon/);
  assert.doesNotMatch(svg, /<line/);
  assert.doesNotMatch(svg, /stroke-dasharray/);
});

test('colours are accepted with or without a leading hash', () => {
  const a = kit.renderSvg(kit.recordSlide({ eyebrow: '', title: '', sub: '' },
    (k) => k.frame(0, 0, 1, 1, '8E6BE6')));
  const b = kit.renderSvg(kit.recordSlide({ eyebrow: '', title: '', sub: '' },
    (k) => k.frame(0, 0, 1, 1, '#8E6BE6')));
  assert.match(a, /#8E6BE6/);
  assert.match(b, /#8E6BE6/);
});

// A stub standing in for pptxgenjs, recording what the backend asks for.
function stubPres() {
  const slides = [];
  return {
    ShapeType: { roundRect: 'roundRect', rightArrow: 'rightArrow', downArrow: 'downArrow' },
    slides,
    addSlide() {
      const s = { texts: [], shapes: [], background: null };
      s.addText = (text, opts) => s.texts.push({ text, opts });
      s.addShape = (type, opts) => s.shapes.push({ type, opts });
      slides.push(s);
      return s;
    },
  };
}

test('renderPptx emits one slide per recorded slide', () => {
  const pres = stubPres();
  kit.renderPptx([sample(), sample()], pres);
  assert.strictEqual(pres.slides.length, 2);
});

test('PARITY: every op has the same bbox in both backends', () => {
  const s = sample();
  const pres = stubPres();
  kit.renderPptx([s], pres);
  // renderPptx always emits exactly three header texts first (eyebrow, title,
  // sub). Skip them structurally: filtering by coordinate does not work, because
  // the header sits at x 0.58 and 0.6, inside the range real ops occupy.
  const HEADER_TEXTS = 3;
  const placed = pres.slides[0].texts.slice(HEADER_TEXTS)
    .concat(pres.slides[0].shapes)
    .map((e) => e.opts);
  const boxes = kit.bboxes(s);
  assert.strictEqual(placed.length, boxes.length,
    'the PPTX backend placed a different number of elements than there are ops');
  // Ops are compared by bbox membership, not index: box/label become texts and
  // frame/arrow become shapes, so the concatenated order is not the op order.
  const key = (o) => `${o.x},${o.y},${o.w},${o.h}`;
  const placedKeys = new Set(placed.map(key));
  boxes.forEach((b) => {
    assert.ok(placedKeys.has(key(b)),
      `op ${b.op} bbox ${key(b)} was not placed by the PPTX backend`);
  });
});

test('PARITY: the SVG places the same geometry, scaled', () => {
  const s = sample();
  const svg = kit.renderSvg(s);
  for (const b of kit.bboxes(s)) {
    if (b.op !== 'box' && b.op !== 'frame') continue;
    const u = kit._internal.u;
    assert.match(svg, new RegExp(`x="${u(b.x)}"[^>]*width="${u(b.w)}"`),
      `${b.op} geometry missing from the SVG`);
  }
});

test('the PPTX backend uses block arrows, never connectors', () => {
  const pres = stubPres();
  kit.renderPptx([sample()], pres);
  const types = pres.slides[0].shapes.map((s) => s.type);
  assert.ok(types.includes('rightArrow'));
  assert.ok(!types.some((t) => /onnector|^line$/.test(t)));
});

test('the PPTX backend never emits a dashed line', () => {
  const pres = stubPres();
  kit.renderPptx([sample()], pres);
  const all = JSON.stringify(pres.slides[0]);
  assert.doesNotMatch(all, /prstDash|dashType|"dash"/);
});

test('the PPTX backend strips the leading hash from colours', () => {
  const pres = stubPres();
  kit.renderPptx([kit.recordSlide({ eyebrow: '', title: '', sub: '' },
    (k) => k.frame(1, 1, 2, 2, '#8E6BE6'))], pres);
  const line = pres.slides[0].shapes.find((s) => s.opts.line);
  assert.strictEqual(line.opts.line.color, '8E6BE6');
});

test('the PPTX backend gives box text an explicit colour, never the pptxgenjs default', () => {
  const pres = stubPres();
  kit.renderPptx([sample()], pres);
  const boxText = pres.slides[0].texts.find((t) => t.opts.shape === pres.ShapeType.roundRect);
  assert.ok(boxText, 'no box text found');
  assert.strictEqual(boxText.opts.color, kit._internal.DEFAULT_PALETTE.txt,
    'box text must default to the palette text colour, not fall through to black');
});

test('the PPTX backend honours a per-box colour override', () => {
  const pres = stubPres();
  kit.renderPptx([kit.recordSlide({ eyebrow: '', title: '', sub: '' },
    (k) => k.box(1, 1, 2, 2, { rt: 'x', color: '#8E6BE6' }))], pres);
  const boxText = pres.slides[0].texts.find((t) => t.opts.shape === pres.ShapeType.roundRect);
  assert.strictEqual(boxText.opts.color, '8E6BE6');
});

test('the SVG box text uses the same colour rule as the PPTX backend', () => {
  const svg = kit.renderSvg(kit.recordSlide({ eyebrow: '', title: '', sub: '' },
    (k) => k.box(1, 1, 2, 2, { rt: 'x', color: '#8E6BE6' })));
  assert.match(svg, /<text[^>]*fill="#8E6BE6"[^>]*>x<\/text>/,
    'box text overriding colour must be painted with the override, not the default palette text colour');
});
