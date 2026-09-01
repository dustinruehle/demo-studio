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
