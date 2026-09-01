/*
  build_create_slides.js — generate the NET-NEW ("create") slides as a dark-mode
  PPTX that drops into an aggregate deck.

  This is a TEMPLATE you edit per engagement: keep the palette + helpers, then
  author one builder block per slide. Slide diagrams are bespoke, so this is code,
  not JSON.

  HARD RULES (Google-Slides-safe + brand — do not break):
    - Block-arrow autoshapes only (rightArrow / downArrow / leftRightArrow).
      NEVER use line connectors or dashed lines (prstDash) — Google Slides
      silently drops them on import.
    - Solid borders only. Hex colors WITHOUT the leading '#'.
    - No em dashes in any text. Use commas or restructure.
    - Dark background; use the lightened accents below so text stays readable.

  BUILD + VISUAL-QA LOOP (always do the visual pass, do not skip it):
    npm i pptxgenjs
    node build_create_slides.js
    python3 /mnt/skills/public/pptx/scripts/office/validate.py create-slides.pptx
    python3 /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf create-slides.pptx
    pdftoppm -jpeg -r 150 create-slides.pdf slide
    # then VIEW every slide-N.jpg, fix overlaps/label collisions/contrast, re-run.
*/

const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5

// ---- palette (dark) ----
const BG="17131F", PANEL="241C33", PANEL2="1E1830", WF="2C2247", BORDER="3A3350";
const IND="8E6BE6" /*light indigo for dark bg*/, INDB="6E4FC0" /*backbone*/;
const CORAL="F0805E", CORALFILL="2A1D1A", GREEN="5FBE97", AMBER="E9B23A";
const TXT="F4F1FB", MUT="B4AECA", FAINT="8B84A3";

// ---- fonts (brand) ----
const FH="Fraunces", FB="IBM Plex Sans", FM="JetBrains Mono";
const S = pres.ShapeType;

// ---- helpers ----
function slideBase(eyebrow, title, sub){
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText(eyebrow, {x:0.6,y:0.42,w:8,h:0.3,fontFace:FM,fontSize:11,color:IND,charSpacing:2,margin:0});
  s.addText(title,  {x:0.58,y:0.72,w:12.2,h:0.9,fontFace:FH,fontSize:33,bold:true,color:TXT,margin:0});
  s.addText(sub,    {x:0.6,y:1.62,w:11.6,h:0.5,fontFace:FB,fontSize:15,color:MUT,margin:0});
  return s;
}
// box with rich text (opts.rt is a pptxgenjs text-array); fill/line/valign/align/margin optional
function box(s, x,y,w,h, opts){
  s.addText(opts.rt || "", {
    x,y,w,h, shape:S.roundRect, rectRadius:0.06,
    fill:{color:opts.fill||PANEL},
    line:{color:opts.line||BORDER, width:opts.lw||1},
    align:opts.align||"center", valign:opts.valign||"middle",
    margin:opts.margin!=null?opts.margin:6
  });
}
// outline-only frame (fill = bg so only the border shows)
function frame(s, x,y,w,h, color){
  s.addShape(S.roundRect, {x,y,w,h, rectRadius:0.05, fill:{color:BG}, line:{color, width:1}});
}
function arrowR(s, x,y,w,h, color){ s.addShape(S.rightArrow,{x,y,w,h,fill:{color},line:{type:"none"}}); }
function arrowD(s, x,y,w,h, color){ s.addShape(S.downArrow,{x,y,w,h,fill:{color},line:{type:"none"}}); }
function label(s, x,y,w, text, color, size, align){
  s.addText(text,{x,y,w,h:0.28,fontFace:FM,fontSize:size||9,color:color||FAINT,align:align||"center",bold:true,charSpacing:1,margin:0});
}

/* ===================== EXAMPLE A — "boxes + gap" layout ===================== */
/* Pattern: an outer frame (something "missing"), a row of inner boxes, a gap band. */
{
  const s = slideBase("SETUP FLOW \u00b7 04", "Your stack today",
                      "The frameworks you already build with, and the gap underneath them.");
  frame(s, 0.85,2.25,11.6,4.5, INDB);
  label(s, 1.05,2.38,6, "OUTER HARNESS \u00b7 MISSING TODAY", IND, 10, "left");
  const bw=3.45, by=2.95, bh=1.5, xs=[1.2,4.98,8.76];
  [["Framework A","graph agents"],["Framework B","agent SDK"],["Custom","hand-rolled loops"]].forEach((n,i)=>{
    box(s, xs[i],by,bw,bh,{fill:PANEL,line:IND,lw:1.25, rt:[
      {text:n[0],options:{fontFace:FH,fontSize:19,bold:true,color:TXT,breakLine:true}},
      {text:n[1],options:{fontFace:FB,fontSize:12,color:MUT}}]});
  });
  label(s, 1.2,4.62,11.1, "INNER HARNESS \u00b7 YOUR FRAMEWORKS", FAINT, 10, "center");
  box(s, 1.2,5.08,11.05,1.28,{fill:CORALFILL,line:CORAL,lw:1.25,margin:10, rt:[
    {text:"THE GAP YOU FILL BY HAND",options:{fontFace:FM,fontSize:11,bold:true,color:CORAL,charSpacing:1,breakLine:true}},
    {text:"state   \u00b7   retries   \u00b7   HITL   \u00b7   no replay",options:{fontFace:FB,fontSize:15,color:TXT}}]});
}

/* ===================== EXAMPLE B — diagram with block arrows ===================== */
/* Pattern: two side frames, inner boxes, and block-arrow relationships between. */
{
  const s = slideBase("SETUP FLOW \u00b7 07", "How it fits together", "Primitives, and how they connect.");
  frame(s, 0.5,2.25,6.2,4.5, INDB);
  label(s, 0.7,2.38,5, "YOUR ENVIRONMENT", IND, 10, "left");
  box(s, 0.92,3.45,2.35,2.35,{fill:WF,line:IND,lw:1.25, rt:[
    {text:"Primitive A",options:{fontFace:FH,fontSize:18,bold:true,color:TXT,breakLine:true}},
    {text:"durable loop",options:{fontFace:FB,fontSize:12,color:MUT}}]});
  box(s, 3.97,3.45,2.35,2.35,{fill:PANEL,line:CORAL,lw:1.25, rt:[
    {text:"Primitive B",options:{fontFace:FH,fontSize:18,bold:true,color:CORAL,breakLine:true}},
    {text:"retryable call",options:{fontFace:FB,fontSize:12,color:MUT}}]});
  arrowR(s, 3.42,4.5,0.4,0.28, IND);                 // A -> B
  label(s, 3.32,4.14,0.6, "calls", IND, 8, "center");
  box(s, 8.5,2.25,4.2,4.5,{fill:PANEL2,line:IND,lw:1.25,valign:"top",align:"left",margin:8, rt:[
    {text:"THE SERVICE",options:{fontFace:FM,fontSize:11,bold:true,color:IND,charSpacing:1}}]});
  box(s, 8.72,3.15,3.76,1.7,{fill:PANEL,line:IND,lw:1.25, rt:[
    {text:"Primitive C",options:{fontFace:FH,fontSize:18,bold:true,color:TXT,breakLine:true}},
    {text:"source of truth",options:{fontFace:FB,fontSize:12,color:MUT}}]});
  arrowR(s, 7.15,3.55,0.95,0.34, IND);               // env -> service (single head to the right)
  label(s, 6.85,3.12,1.5, "poll \u00b7 complete", IND, 9, "center");
  arrowR(s, 7.15,5.5,0.95,0.34, GREEN);              // recovery request -> service (green)
  label(s, 6.85,5.08,1.5, "get state", GREEN, 9.5, "center");
  label(s, 6.85,5.92,1.5, "replay on crash", GREEN, 9, "center");
}

/* Add more slide blocks here, one per net-new slide. Reuse the helpers.
   Common accents: indigo (default), coral (money/risk), green (recovery),
   amber (human/gate). Keep titles ~33pt, keep labels inside their gaps. */

pres.writeFile({ fileName: "create-slides.pptx" }).then(f => console.log("wrote", f));
