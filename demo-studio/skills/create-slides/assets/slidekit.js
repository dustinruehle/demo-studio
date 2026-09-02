'use strict';
/*
  One authoring pass, two backends.

  A slide is authored once by calling the recorder helpers. The recorded ops are
  replayed by renderSvg (the flow-guide preview) and by renderPptx (the deck), so
  both artifacts derive from one coordinate space and cannot drift.

  Coordinates are inches on a 13.333 x 7.5 slide, matching pptxgenjs LAYOUT_WIDE.
  The SVG mirror uses viewBox 0 0 1333 750, the same rectangle scaled by 100.
*/

const path = require('node:path');

const LAYOUT = { w: 13.333, h: 7.5 };
const SCALE = 100;
const LABEL_H = 0.28; // inherited from the original label() helper

// brand.json is the single source for colour and type; even the library's
// own standalone-use default palette reads from it rather than hardcoding a
// second copy, so changing one value in brand.json moves it everywhere,
// including a caller that never builds its own palette object.
const _BRAND = require(path.join(__dirname, '..', '..', '..', 'shared', 'brand.json'));
const _PPTX = _BRAND.surfaces.pptx;
const _nohash = (c) => String(c || '').replace(/^#/, '');

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
    case 'box': {
      // Text colour defaults to the palette, honouring a per-op override, so
      // this stays consistent with renderPptx: neither backend may fall back
      // to a renderer default (pptxgenjs defaults to black), only to p.txt.
      const textColor = hex((o.opts && o.opts.color) || palette.txt);
      return `<rect x="${u(o.x)}" y="${u(o.y)}" width="${u(o.w)}" height="${u(o.h)}" rx="6" `
           + `fill="${fill}" stroke="${line}" stroke-width="1"/>`
           + `<text x="${u(o.x + o.w / 2)}" y="${u(o.y + o.h / 2)}" fill="${textColor}" `
           + `font-family="${palette.body}" font-size="15" text-anchor="middle" `
           + `dominant-baseline="middle">${esc(plainText(o.opts.rt))}</text>`;
    }
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
  bg: _nohash(_PPTX.bg), panel: _nohash(_PPTX.panel), border: _nohash(_PPTX.border),
  txt: _nohash(_PPTX.txt), mut: _nohash(_PPTX.mut), indigo: _nohash(_PPTX.indigo),
  body: _BRAND.fonts.body, mono: _BRAND.fonts.mono, heading: _BRAND.fonts.heading,
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
    `  <text x="60" y="52" fill="${hex(p.indigo)}" font-family="${p.mono}" `
      + `font-size="14" letter-spacing="2">${esc(slide.eyebrow)}</text>`,
    `  <text x="58" y="105" fill="${hex(p.txt)}" font-family="${p.heading}" `
      + `font-size="42" font-weight="700">${esc(slide.title)}</text>`,
    `  <text x="60" y="150" fill="${hex(p.mut)}" font-family="${p.body}" `
      + `font-size="19">${esc(slide.sub)}</text>`,
    '  ' + body,
    '</svg>',
  ].join('\n');
}

function bare(color) { return String(color || '000000').replace(/^#/, '').toUpperCase(); }

/**
 * Replay recorded slides into a pptxgenjs presentation.
 * `pres` is injected so tests can pass a stub and prove parity without the dep.
 */
function renderPptx(slides, pres, palette) {
  const p = Object.assign({}, DEFAULT_PALETTE, palette || {});
  const S = pres.ShapeType;
  for (const slide of slides) {
    const s = pres.addSlide();
    s.background = { color: bare(p.bg) };
    s.addText(slide.eyebrow, { x: 0.6, y: 0.42, w: 8, h: 0.3, fontFace: p.mono,
      fontSize: 11, color: bare(p.indigo), charSpacing: 2, margin: 0 });
    s.addText(slide.title, { x: 0.58, y: 0.72, w: 12.2, h: 0.9, fontFace: p.heading,
      fontSize: 33, bold: true, color: bare(p.txt), margin: 0 });
    s.addText(slide.sub, { x: 0.6, y: 1.62, w: 11.6, h: 0.5, fontFace: p.body,
      fontSize: 15, color: bare(p.mut), margin: 0 });

    for (const o of slide.ops) {
      switch (o.op) {
        case 'box':
          s.addText(o.opts.rt || '', {
            x: o.x, y: o.y, w: o.w, h: o.h,
            shape: S.roundRect, rectRadius: 0.06,
            fill: { color: bare(o.opts.fill || p.panel) },
            line: { color: bare(o.opts.line || p.border), width: o.opts.lw || 1 },
            align: o.opts.align || 'center',
            valign: o.opts.valign || 'middle',
            margin: o.opts.margin != null ? o.opts.margin : 6,
            // Explicit, never the pptxgenjs default (black): a dark panel with
            // black text is invisible. Honour a per-op override, else p.txt.
            color: bare(o.opts.color || p.txt),
          });
          break;
        case 'frame':
          s.addShape(S.roundRect, {
            x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.05,
            fill: { color: bare(p.bg) },
            line: { color: bare(o.color), width: 1 },
          });
          break;
        case 'arrowR':
          s.addShape(S.rightArrow, { x: o.x, y: o.y, w: o.w, h: o.h,
            fill: { color: bare(o.color) }, line: { type: 'none' } });
          break;
        case 'arrowD':
          s.addShape(S.downArrow, { x: o.x, y: o.y, w: o.w, h: o.h,
            fill: { color: bare(o.color) }, line: { type: 'none' } });
          break;
        case 'label':
          s.addText(o.text, { x: o.x, y: o.y, w: o.w, h: LABEL_H,
            fontFace: p.mono, fontSize: o.size || 9, color: bare(o.color),
            align: o.align || 'center', bold: true, charSpacing: 1, margin: 0 });
          break;
        default:
          throw new Error(`slidekit: unknown op ${o.op}`);
      }
    }
  }
  return pres;
}

module.exports = {
  LAYOUT, SCALE, LABEL_H,
  recordSlide, bboxes, renderSvg, renderPptx,
  _internal: { hex, esc, plainText, u, renderOp, DEFAULT_PALETTE },
};
