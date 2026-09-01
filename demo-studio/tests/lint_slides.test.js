'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('path');

const base = path.join(__dirname, '..', 'skills', 'create-slides', 'assets');
const kit = require(path.join(base, 'slidekit.js'));
const { lintSlides, formatFindings } = require(path.join(base, 'lint_slides.js'));

const one = (build) => [kit.recordSlide({ eyebrow: 'E', title: 'T', sub: 'S' }, build)];

test('a clean slide produces no findings', () => {
  assert.deepStrictEqual(lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'ok' }))), []);
});

test('flags a box running off the right edge', () => {
  const f = lintSlides(one((k) => k.box(12, 1, 2, 1, { rt: 'wide' })));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'off-canvas');
  assert.match(f[0].detail, /13\.333/);
});

test('flags a box running off the bottom edge', () => {
  const f = lintSlides(one((k) => k.box(1, 7, 2, 1, { rt: 'low' })));
  assert.strictEqual(f[0].rule, 'off-canvas');
  assert.match(f[0].detail, /7\.5/);
});

test('flags a negative origin', () => {
  assert.strictEqual(lintSlides(one((k) => k.box(-0.5, 1, 2, 1, {})))[0].rule, 'off-canvas');
});

test('flags an em dash in slide text', () => {
  const f = lintSlides(one((k) => k.label(1, 1, 3, 'fast — durable', 'IND', 9, 'center')));
  assert.strictEqual(f[0].rule, 'em-dash');
});

test('flags an em dash in box rich text', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'a — b' })));
  assert.strictEqual(f[0].rule, 'em-dash');
});

test('flags a colour written with a leading hash', () => {
  const f = lintSlides(one((k) => k.frame(1, 1, 2, 1, '#8E6BE6')));
  assert.strictEqual(f[0].rule, 'hash-in-hex');
});

test('flags a zero-size shape', () => {
  assert.strictEqual(lintSlides(one((k) => k.box(1, 1, 0, 1, {})))[0].rule, 'zero-size');
});

test('findings name the slide index and the op index', () => {
  const f = lintSlides(one((k) => { k.box(1, 1, 2, 1, {}); k.box(99, 1, 2, 1, {}); }));
  assert.strictEqual(f[0].slide, 1);
  assert.strictEqual(f[0].op, 2);
});

test('formatFindings is one line per finding', () => {
  const f = lintSlides(one((k) => { k.box(99, 1, 2, 1, {}); k.frame(1, 1, 2, 1, '#FFF000'); }));
  assert.strictEqual(formatFindings(f).trim().split('\n').length, 2);
});

test('flags NaN coordinate', () => {
  const f = lintSlides(one((k) => k.box(NaN, 1, 2, 1, {})));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'invalid-coord');
  assert.match(f[0].detail, /x.*NaN/);
});

test('flags undefined coordinate', () => {
  const f = lintSlides(one((k) => k.box(1, undefined, 2, 1, {})));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'invalid-coord');
  assert.match(f[0].detail, /y.*undefined/);
});

test('flags non-finite width', () => {
  const f = lintSlides(one((k) => k.box(1, 1, Infinity, 1, {})));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'invalid-coord');
  assert.match(f[0].detail, /w.*Infinity/);
});

test('skips off-canvas check when coordinate is non-finite', () => {
  const f = lintSlides(one((k) => k.box(NaN, 1, 2, 1, {})));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'invalid-coord');
  assert.doesNotMatch(f[0].detail, /off-canvas/);
});

// A clean slide's own header text (eyebrow/title/sub is metadata on the
// slide object, not an op) was never scanned for an em dash before this
// fix; only op-level label/box text was.
const cleanHeader = () => kit.recordSlide(
  { eyebrow: 'E', title: 'T', sub: 'S' }, (k) => k.box(1, 1, 2, 1, { rt: 'ok' }));

test('flags an em dash in the eyebrow', () => {
  const f = lintSlides([kit.recordSlide(
    { eyebrow: 'fast — durable', title: 'T', sub: 'S' },
    (k) => k.box(1, 1, 2, 1, { rt: 'ok' }))]);
  assert.ok(f.some((x) => x.rule === 'em-dash' && x.op === 0),
    'expected an em-dash finding at op 0 for the eyebrow');
});

test('flags an em dash in the title', () => {
  const f = lintSlides([kit.recordSlide(
    { eyebrow: 'E', title: 'fast — durable', sub: 'S' },
    (k) => k.box(1, 1, 2, 1, { rt: 'ok' }))]);
  assert.ok(f.some((x) => x.rule === 'em-dash' && x.op === 0),
    'expected an em-dash finding at op 0 for the title');
});

test('flags an em dash in the sub', () => {
  const f = lintSlides([kit.recordSlide(
    { eyebrow: 'E', title: 'T', sub: 'fast — durable' },
    (k) => k.box(1, 1, 2, 1, { rt: 'ok' }))]);
  assert.ok(f.some((x) => x.rule === 'em-dash' && x.op === 0),
    'expected an em-dash finding at op 0 for the sub');
});

test('a clean header produces no em-dash findings at op 0', () => {
  const f = lintSlides([cleanHeader()]);
  assert.ok(!f.some((x) => x.rule === 'em-dash'));
});

test('LOW CONTRAST: catches the exact bug that shipped, black text on the dark panel', () => {
  const f = lintSlides(one(
    (k) => k.box(1, 1, 2, 1, { rt: 'x', color: '000000', fill: '241C33' })));
  const hit = f.find((x) => x.rule === 'low-contrast');
  assert.ok(hit, 'expected a low-contrast finding');
  assert.match(hit.detail, /000000/);
  assert.match(hit.detail, /241C33/);
});

test('LOW CONTRAST: a box using the default palette text-on-panel pair passes', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'ok' })));
  assert.ok(!f.some((x) => x.rule === 'low-contrast'));
});

test('LOW CONTRAST: an explicit override pair with good contrast passes', () => {
  const f = lintSlides(one(
    (k) => k.box(1, 1, 2, 1, { rt: 'ok', color: 'F4F1FB', fill: '241C33' })));
  assert.ok(!f.some((x) => x.rule === 'low-contrast'));
});

test('LOW CONTRAST: covers the header eyebrow/title/sub against the background', () => {
  const f = lintSlides([kit.recordSlide(
    { eyebrow: 'E', title: 'T', sub: 'S' },
    (k) => k.box(1, 1, 2, 1, { rt: 'ok' }))], { bg: '000000', indigo: '111111' });
  const hit = f.find((x) => x.rule === 'low-contrast' && x.op === 0);
  assert.ok(hit, 'expected a header low-contrast finding when indigo nearly matches bg');
  assert.match(hit.detail, /eyebrow/);
});

test('LOW CONTRAST: the real default palette header colours pass against the real background', () => {
  const f = lintSlides([cleanHeader()]);
  assert.ok(!f.some((x) => x.rule === 'low-contrast'));
});
