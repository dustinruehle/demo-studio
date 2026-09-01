'use strict';
/*
  One authoring pass, two backends.

  A slide is authored once by calling the recorder helpers. The recorded ops are
  replayed by renderSvg (the flow-guide preview) and by renderPptx (the deck), so
  both artifacts derive from one coordinate space and cannot drift.

  Coordinates are inches on a 13.333 x 7.5 slide, matching pptxgenjs LAYOUT_WIDE.
  The SVG mirror uses viewBox 0 0 1333 750, the same rectangle scaled by 100.
*/

const LAYOUT = { w: 13.333, h: 7.5 };
const SCALE = 100;
const LABEL_H = 0.28; // inherited from the original label() helper

function hex(color) {
  const c = String(color || '000000').replace(/^#/, '');
  return '#' + c.toUpperCase();
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Rich text may be a plain string or a pptxgenjs text array. Flatten for SVG.
function plainText(rt) {
  if (rt == null) return '';
  if (typeof rt === 'string') return rt;
  if (Array.isArray(rt)) return rt.map((r) => (r && r.text) || '').join('');
  return String(rt.text || '');
}

function recorder(ops) {
  return {
    box(x, y, w, h, opts) { ops.push({ op: 'box', x, y, w, h, opts: opts || {} }); },
    frame(x, y, w, h, color) { ops.push({ op: 'frame', x, y, w, h, color }); },
    arrowR(x, y, w, h, color) { ops.push({ op: 'arrowR', x, y, w, h, color }); },
    arrowD(x, y, w, h, color) { ops.push({ op: 'arrowD', x, y, w, h, color }); },
    label(x, y, w, text, color, size, align) {
      ops.push({ op: 'label', x, y, w, h: LABEL_H, text, color, size, align });
    },
  };
}

function recordSlide(meta, build) {
  const ops = [];
  build(recorder(ops));
  return { eyebrow: meta.eyebrow, title: meta.title, sub: meta.sub, ops };
}

/** Geometry in inches. The single source both backends position from. */
function bboxes(slide) {
  return slide.ops.map((o) => ({
    op: o.op, x: o.x, y: o.y, w: o.w, h: o.h == null ? LABEL_H : o.h,
  }));
}

// Inches to SVG user units. Rounds to 2dp because JS floats are not exact:
// 2.2 * 100 is 220.00000000000003 and 0.28 * 100 is 28.000000000000004, which
// would litter every coordinate in the output. 2dp is far finer than a pixel here.
function u(inches) { return Math.round(inches * SCALE * 100) / 100; }

// Exact for op geometry, rounded for the canvas: u(13.333) is 1333.3000000000002
// in floating point, which would make the viewBox unreadable and untestable.
function viewBoxDim(inches) { return Math.round(inches * SCALE); }

// Block arrows as polygons. Never a <line>: Google Slides drops connectors, and
// the SVG must show what the deck will actually contain.
function arrowRightPoints(x, y, w, h) {
  const shaftH = h * 0.45, headW = Math.min(w * 0.4, h);
  const top = y + (h - shaftH) / 2;
  return [
    [x, top], [x + w - headW, top], [x + w - headW, y],
    [x + w, y + h / 2], [x + w - headW, y + h], [x + w - headW, top + shaftH],
    [x, top + shaftH],
  ].map(([px, py]) => `${u(px)},${u(py)}`).join(' ');
}

function arrowDownPoints(x, y, w, h) {
  const shaftW = w * 0.45, headH = Math.min(h * 0.4, w);
  const left = x + (w - shaftW) / 2;
  return [
    [left, y], [left + shaftW, y], [left + shaftW, y + h - headH],
    [x + w, y + h - headH], [x + w / 2, y + h], [x, y + h - headH],
    [left, y + h - headH],
  ].map(([px, py]) => `${u(px)},${u(py)}`).join(' ');
}

function renderOp(o, palette) {
  const fill = hex((o.opts && o.opts.fill) || palette.panel);
  const line = hex((o.opts && o.opts.line) || palette.border);
  switch (o.op) {
    case 'box':
      return `<rect x="${u(o.x)}" y="${u(o.y)}" width="${u(o.w)}" height="${u(o.h)}" rx="6" `
           + `fill="${fill}" stroke="${line}" stroke-width="1"/>`
           + `<text x="${u(o.x + o.w / 2)}" y="${u(o.y + o.h / 2)}" fill="${hex(palette.txt)}" `
           + `font-family="${palette.body}" font-size="15" text-anchor="middle" `
           + `dominant-baseline="middle">${esc(plainText(o.opts.rt))}</text>`;
    case 'frame':
      return `<rect x="${u(o.x)}" y="${u(o.y)}" width="${u(o.w)}" height="${u(o.h)}" rx="5" `
           + `fill="none" stroke="${hex(o.color)}" stroke-width="1"/>`;
    case 'arrowR':
      return `<polygon points="${arrowRightPoints(o.x, o.y, o.w, o.h)}" fill="${hex(o.color)}"/>`;
    case 'arrowD':
      return `<polygon points="${arrowDownPoints(o.x, o.y, o.w, o.h)}" fill="${hex(o.color)}"/>`;
    case 'label': {
      const anchor = o.align === 'left' ? 'start' : o.align === 'right' ? 'end' : 'middle';
      const tx = o.align === 'left' ? o.x : o.align === 'right' ? o.x + o.w : o.x + o.w / 2;
      return `<text x="${u(tx)}" y="${u(o.y + LABEL_H / 2)}" fill="${hex(o.color)}" `
           + `font-family="${palette.mono}" font-size="${(o.size || 9) * 1.3}" `
           + `font-weight="700" letter-spacing="1" text-anchor="${anchor}" `
           + `dominant-baseline="middle">${esc(o.text)}</text>`;
    }
    default:
      throw new Error(`slidekit: unknown op ${o.op}`);
  }
}

const DEFAULT_PALETTE = {
  bg: '17131F', panel: '241C33', border: '3A3350', txt: 'F4F1FB',
  mut: 'B4AECA', body: 'IBM Plex Sans', mono: 'JetBrains Mono', heading: 'Fraunces',
};

/** Render one slide to a standalone SVG string for a flow-guide preview. */
function renderSvg(slide, palette) {
  const p = Object.assign({}, DEFAULT_PALETTE, palette || {});
  const body = slide.ops.map((o) => renderOp(o, p)).join('\n  ');
  return [
    `<svg viewBox="0 0 ${viewBoxDim(LAYOUT.w)} ${viewBoxDim(LAYOUT.h)}" `
      + `preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%" `
      + `xmlns="http://www.w3.org/2000/svg">`,
    `  <rect x="0" y="0" width="${viewBoxDim(LAYOUT.w)}" height="${viewBoxDim(LAYOUT.h)}" fill="${hex(p.bg)}"/>`,
    `  <text x="60" y="52" fill="${hex('8E6BE6')}" font-family="${p.mono}" `
      + `font-size="14" letter-spacing="2">${esc(slide.eyebrow)}</text>`,
    `  <text x="58" y="105" fill="${hex(p.txt)}" font-family="${p.heading}" `
      + `font-size="42" font-weight="700">${esc(slide.title)}</text>`,
    `  <text x="60" y="150" fill="${hex(p.mut)}" font-family="${p.body}" `
      + `font-size="19">${esc(slide.sub)}</text>`,
    '  ' + body,
    '</svg>',
  ].join('\n');
}

module.exports = {
  LAYOUT, SCALE, LABEL_H,
  recordSlide, bboxes, renderSvg,
  _internal: { hex, esc, plainText, u, renderOp, DEFAULT_PALETTE },
};
