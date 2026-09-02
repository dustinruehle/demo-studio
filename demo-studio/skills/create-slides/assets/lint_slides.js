'use strict';
/*
  Author-time checks on recorded slides. These catch the mistakes that only show
  up when you finally look at a rendered image, which on a machine without
  LibreOffice may be never.
*/
const kit = require('./slidekit');

const EM_DASH = '\u2014';
const MIN_CONTRAST = 4.5; // WCAG AA for normal-size text

function textOf(o) {
  if (o.op === 'label') return String(o.text == null ? '' : o.text);
  if (o.op === 'box') return kit._internal.plainText(o.opts && o.opts.rt);
  return '';
}

function coloursOf(o) {
  const out = [];
  if (o.color != null) out.push(o.color);
  if (o.opts) {
    if (o.opts.fill != null) out.push(o.opts.fill);
    if (o.opts.line != null) out.push(o.opts.line);
  }
  return out;
}

function normHex(c) {
  return String(c || '').replace(/^#/, '').toUpperCase();
}

// WCAG relative luminance and contrast ratio, no dependency. Formula per
// https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
function srgbChannel(v) {
  const c = v / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function relativeLuminance(hex6) {
  const r = parseInt(hex6.slice(0, 2), 16) || 0;
  const g = parseInt(hex6.slice(2, 4), 16) || 0;
  const b = parseInt(hex6.slice(4, 6), 16) || 0;
  return 0.2126 * srgbChannel(r) + 0.7152 * srgbChannel(g) + 0.0722 * srgbChannel(b);
}

function contrastRatio(fg, bg) {
  const l1 = relativeLuminance(normHex(fg));
  const l2 = relativeLuminance(normHex(bg));
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Header text colours, painted directly on the slide background (p.bg) in
// both backends: renderPptx sets s.background to p.bg then paints eyebrow in
// p.indigo, title in p.txt, sub in p.mut, with no per-slide override.
function headerFields(p) {
  return [
    ['eyebrow', p.indigo],
    ['title', p.txt],
    ['sub', p.mut],
  ];
}

function lintSlides(slides, palette) {
  const p = Object.assign({}, kit._internal.DEFAULT_PALETTE, palette || {});
  const findings = [];
  slides.forEach((slide, si) => {
    const at0 = { slide: si + 1, op: 0 };
    for (const [field, color] of headerFields(p)) {
      const text = slide[field];
      if (typeof text !== 'string') continue;
      if (text.includes(EM_DASH)) {
        findings.push(Object.assign({}, at0, { rule: 'em-dash',
          detail: `${field}: use a comma or restructure` }));
      }
      const ratio = contrastRatio(color, p.bg);
      if (ratio < MIN_CONTRAST) {
        findings.push(Object.assign({}, at0, { rule: 'low-contrast',
          detail: `${field} ${normHex(color)} on ${normHex(p.bg)} is `
                + `${ratio.toFixed(2)}:1, needs ${MIN_CONTRAST}:1` }));
      }
    }

    const boxes = kit.bboxes(slide);
    slide.ops.forEach((o, oi) => {
      const b = boxes[oi];
      const at = { slide: si + 1, op: oi + 1 };

      let hasInvalidCoord = false;
      for (const field of ['x', 'y', 'w', 'h']) {
        if (!Number.isFinite(b[field])) {
          findings.push(Object.assign({}, at, { rule: 'invalid-coord',
            detail: `${field}=${b[field]}` }));
          hasInvalidCoord = true;
        }
      }

      if (!hasInvalidCoord) {
        if (b.w <= 0 || b.h <= 0) {
          findings.push(Object.assign({}, at, { rule: 'zero-size',
            detail: `${o.op} has width ${b.w} and height ${b.h}` }));
        } else if (b.x < 0 || b.y < 0
                   || b.x + b.w > kit.LAYOUT.w || b.y + b.h > kit.LAYOUT.h) {
          findings.push(Object.assign({}, at, { rule: 'off-canvas',
            detail: `${o.op} spans x ${b.x} to ${(b.x + b.w).toFixed(3)} and `
                  + `y ${b.y} to ${(b.y + b.h).toFixed(3)}, `
                  + `slide is ${kit.LAYOUT.w} by ${kit.LAYOUT.h}` }));
        }
      }

      if (textOf(o).includes(EM_DASH)) {
        findings.push(Object.assign({}, at, { rule: 'em-dash',
          detail: 'use a comma or restructure' }));
      }

      for (const c of coloursOf(o)) {
        if (typeof c === 'string' && c.startsWith('#')) {
          findings.push(Object.assign({}, at, { rule: 'hash-in-hex',
            detail: `pptxgenjs wants ${c.slice(1)}, not ${c}` }));
        }
      }

      // Both backends resolve a box's text and fill this same way (see
      // renderPptx): an explicit per-op override, else the palette default.
      // This is the exact pair that shipped black text on a near-black
      // panel, invisible to every other gate.
      if (o.op === 'box') {
        const textColor = (o.opts && o.opts.color) || p.txt;
        const bgColor = (o.opts && o.opts.fill) || p.panel;
        const ratio = contrastRatio(textColor, bgColor);
        if (ratio < MIN_CONTRAST) {
          findings.push(Object.assign({}, at, { rule: 'low-contrast',
            detail: `text ${normHex(textColor)} on ${normHex(bgColor)} is `
                  + `${ratio.toFixed(2)}:1, needs ${MIN_CONTRAST}:1` }));
        }
      }
    });
  });
  return findings;
}

function formatFindings(findings) {
  return findings
    .map((f) => `  slide ${f.slide} op ${f.op}  ${f.rule.padEnd(12)} ${f.detail}`)
    .join('\n');
}

module.exports = { lintSlides, formatFindings };