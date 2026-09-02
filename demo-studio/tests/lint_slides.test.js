'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');

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

// BAD COLOUR: parseInt(...) || 0 used to turn any malformed value into black
// channels, and coloursOf only ever checked for a leading '#'. A colour must
// be exactly six hex digits after any leading '#', or it must be caught here
// rather than silently rendering as black (or crashing pptxgenjs).

test('flags a three-digit hex shorthand with no leading hash', () => {
  const f = lintSlides(one((k) => k.frame(1, 1, 2, 1, 'FFF')));
  assert.strictEqual(f[0].rule, 'bad-colour');
});

test('flags a CSS colour name', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'x', fill: 'red' })));
  assert.ok(f.some((x) => x.rule === 'bad-colour'), 'expected a bad-colour finding for fill: red');
});

test('the exact bug: a malformed color and an invalid fill both get caught', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'x', color: 'FFF', fill: 'red' })));
  const bad = f.filter((x) => x.rule === 'bad-colour');
  assert.strictEqual(bad.length, 2, 'expected both color and fill to be flagged');
});

test('flags a malformed opts.line', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'x', line: 'blue' })));
  assert.ok(f.some((x) => x.rule === 'bad-colour'), 'expected a bad-colour finding for line: blue');
});

test('flags a malformed opts.color (box text colour)', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'x', color: 'ZZZZZZ' })));
  assert.ok(f.some((x) => x.rule === 'bad-colour'), 'expected a bad-colour finding for opts.color');
});

test('opts.color with a leading hash is covered by hash-in-hex too', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, 1, { rt: 'x', color: '#8E6BE6' })));
  assert.ok(f.some((x) => x.rule === 'hash-in-hex'), 'opts.color was not covered by hash-in-hex before this fix');
});

test('a well-formed six-digit colour with no hash produces no colour findings', () => {
  assert.deepStrictEqual(lintSlides(one((k) => k.frame(1, 1, 2, 1, '8E6BE6'))), []);
});

test('a well-formed colour with a leading hash is only flagged hash-in-hex, not bad-colour', () => {
  const f = lintSlides(one((k) => k.frame(1, 1, 2, 1, '#8E6BE6')));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'hash-in-hex');
});

test('flags a zero-size shape', () => {
  assert.strictEqual(lintSlides(one((k) => k.box(1, 1, 0, 1, {})))[0].rule, 'zero-size');
});

// A negative width was previously caught by the same `b.w <= 0` branch as an
// exactly-zero width and mislabelled zero-size. The two are different bugs
// (a negative dimension cannot come from an empty box; it comes from a
// swapped or miscomputed coordinate) and now get different rule names.
test('flags a negative-width shape as invalid-size, not zero-size', () => {
  const f = lintSlides(one((k) => k.box(1, 1, -1, 1, {})));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'invalid-size');
});

test('flags a negative-height shape as invalid-size', () => {
  const f = lintSlides(one((k) => k.box(1, 1, 2, -1, {})));
  assert.strictEqual(f.length, 1);
  assert.strictEqual(f[0].rule, 'invalid-size');
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

// WCAG AA has two tiers and this deck spans both. Gating everything at 4.5
// rejects the brand's own accent on 18pt box text; gating everything at 3
// lets an unreadable 9pt label through. These pin both directions.

test('box text takes the large-text tier, so a brand accent passes', () => {
  const s = one((k) => k.box(1, 2, 4, 1, { rt: 'X', fill: '241C33', color: '8E6BE6' }));
  const f = lintSlides(s).filter((x) => x.rule === 'low-contrast');
  assert.deepStrictEqual(f, [], 'brand indigo on the panel is 4.19:1, fine at the 3:1 large tier');
});

test('box text still catches the black-on-near-black that shipped', () => {
  const s = one((k) => k.box(1, 2, 4, 1, { rt: 'X', fill: '241C33', color: '000000' }));
  const f = lintSlides(s).filter((x) => x.rule === 'low-contrast');
  assert.strictEqual(f.length, 1);
  assert.match(f[0].detail, /needs 3:1/);
});

test('a label takes the normal tier, being small and only 9pt', () => {
  const s = one((k) => k.label(1, 2, 4, 'LBL', '3A3350', 9, 'center'));
  const f = lintSlides(s).filter((x) => x.rule === 'low-contrast');
  assert.strictEqual(f.length, 1, 'a near-invisible label must be caught');
  assert.match(f[0].detail, /needs 4\.5:1/);
});

test('a legible label passes', () => {
  const s = one((k) => k.label(1, 2, 4, 'LBL', 'F4F1FB', 9, 'center'));
  assert.deepStrictEqual(lintSlides(s).filter((x) => x.rule === 'low-contrast'), []);
});
