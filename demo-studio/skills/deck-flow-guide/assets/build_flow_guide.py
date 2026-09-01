# -*- coding: utf-8 -*-
"""
build_flow_guide.py: render a deck FLOW GUIDE from a JSON config: acts of
cards, each card either a "deck" card (pull an existing slide, named explicitly)
or a "create" card (a slide that does not exist yet, with a collapsible preview
mockup). This is the "piece the deck from existing + net-new, with drilldowns"
format.

Usage:
    python3 build_flow_guide.py CONFIG.json OUT.html

The styling is fixed (it is the reusable format). Only content comes from JSON.
Card previews (create cards) carry a raw SVG/HTML mockup you author per slide;
the available mockup classes (.slide, .harness-frame, .tiles, .stack-two,
.beats, etc.) are documented in references/flow-guide-format.md.
"""
import html, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "shared"))
import brand
import guardrails
import validate_config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema_flow_guide

def esc(s): return html.escape(str(s), quote=True)

def deck_card(c):
    pg = f' <span class="pg">{c.get("deckid_pg","")}</span>' if c.get("deckid_pg") else ""
    return f'''
      <div class="card">
        <div class="seq">{c["seq"]}</div>
        <div class="body">
          <p class="title">{esc(c["title"])}</p>
          <div class="deckid"><span class="dl">{esc(c.get("deckid_label","Pull this slide"))}</span>{c.get("deckid_quote","")}{pg}</div>
          <p class="line"><span class="lbl why">Why</span><span class="txt">{c.get("why","")}</span></p>
          <div class="traces"><span class="tlbl">Traces to</span> <em>{c.get("traces","")}</em></div>
        </div>
        <span class="src deck">{esc(c.get("src_label","From deck"))}</span>
      </div>'''

def create_card(c):
    p = c.get("preview", {})
    preview = ""
    if p:
        preview = f'''
        <details class="drill">
          <summary>Preview the slide</summary>
          <p class="drillnote">{p.get("drillnote", c.get("drillnote",""))}</p>
          <div class="slide">
            <div class="s-eyebrow">{p.get("eyebrow","")}</div>
            <div class="s-title">{esc(p.get("title", c["title"]))}</div>
            <div class="s-sub">{esc(p.get("sub",""))}</div>
            <div class="s-body">{p.get("body","")}</div>
          </div>
        </details>'''
    return f'''
      <div class="card new">
        <div class="new-head">
          <div class="seq">{c["seq"]}</div>
          <p class="title">{esc(c["title"])}</p>
          <span class="src create">{esc(c.get("src_label","Create"))}</span>
        </div>
        <p class="line"><span class="lbl why">Why</span><span class="txt">{c.get("why","")}</span></p>
        <div class="traces"><span class="tlbl">Traces to</span> <em>{c.get("traces","")}</em></div>{preview}
      </div>'''

def build(cfg):
    acts=[]
    for a in cfg["acts"]:
        cards="".join(deck_card(c) if c.get("type")=="deck" else create_card(c) for c in a["cards"])
        acts.append(f'''
  <section class="act">
    <div class="rail">
      <div class="act-no">{esc(a["no"])}</div>
      <div class="act-title">{esc(a["title"])}</div>
      <p class="act-purpose">{esc(a.get("purpose",""))}</p>
      <div class="act-time">{esc(a.get("time",""))}</div>
    </div>
    <div class="cards">{cards}
    </div>
  </section>''')
    acts_html="\n".join(acts)

    chips="".join(f'<span class="chip"><b>{esc(a)}:</b> {esc(b)}</span>' for (a,b) in cfg.get("chips",[]))
    lg=cfg.get("legend",{})
    legend=(f'<div class="item"><span class="tag deck">{esc(lg.get("deck_label","From deck"))}</span> {esc(lg.get("deck_text",""))}</div>'
            f'<div class="item"><span class="tag create">{esc(lg.get("create_label","Create"))}</span> {esc(lg.get("create_text",""))}</div>')

    foot=""
    f=cfg.get("footer")
    if f:
        cols="".join(f'<div class="cut {cls}"><p class="k">{esc(k)}</p><p>{txt}</p></div>' for (k,cls,txt) in f.get("cols",[]))
        foot=f'<div class="foot"><h2>{esc(f.get("title",""))}</h2><div class="cutgrid">{cols}</div></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(cfg.get("tab_title", cfg["title"]))}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">{esc(cfg.get("eyebrow",""))}</div>
    <h1>{esc(cfg["title"])}</h1>
    <p class="lede">{esc(cfg.get("subtitle",""))}</p>
    <div class="meta">{chips}</div>
    <div class="legend">{legend}</div>
  </header>
{acts_html}
{foot}
</div>
</body>
</html>"""

CSS = brand.root_block("flow_guide") + r'''
  *{box-sizing:border-box;}
  html{-webkit-text-size-adjust:100%;}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:16px;line-height:1.5;}
  .wrap{max-width:1080px;margin:0 auto;padding:40px 28px 72px;}

  .eyebrow{font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--indigo);font-weight:500;}
  h1{font-family:"Fraunces",serif;font-weight:600;font-size:clamp(34px,5vw,52px);line-height:1.04;letter-spacing:-.01em;margin:.28em 0 .3em;color:var(--ink);}
  .lede{font-size:17px;color:var(--muted);max-width:64ch;margin:0 0 26px;}

  .meta{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px;}
  .chip{font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.04em;background:var(--indigo-tint);color:var(--indigo-ink);padding:6px 11px;border-radius:999px;white-space:nowrap;}
  .chip b{font-weight:700;}

  .legend{display:flex;flex-wrap:wrap;gap:18px;align-items:center;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:14px 0;margin:0 0 6px;}
  .legend .item{display:flex;align-items:center;gap:9px;font-size:14px;color:var(--muted);}
  .tag{font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:4px 9px;border-radius:5px;}
  .tag.deck{background:var(--indigo);color:#fff;}
  .tag.create{background:var(--coral);color:#fff;}

  .act{display:grid;grid-template-columns:210px 1fr;gap:28px;padding:34px 0 8px;border-top:1px solid var(--line);}
  .act:first-of-type{border-top:none;}
  .act-no{font-family:"Fraunces",serif;font-weight:600;font-size:15px;color:var(--indigo);letter-spacing:.02em;}
  .act-title{font-family:"Fraunces",serif;font-weight:600;font-size:23px;line-height:1.12;margin:2px 0 8px;color:var(--ink);}
  .act-purpose{font-size:13.5px;color:var(--muted);margin:0 0 10px;}
  .act-time{font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.04em;color:var(--green);font-weight:500;}

  .cards{display:flex;flex-direction:column;gap:12px;}

  .card{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--indigo);border-radius:9px;padding:15px 17px;display:grid;grid-template-columns:34px 1fr auto;gap:14px;align-items:start;}
  .seq{font-family:"JetBrains Mono",monospace;font-weight:700;font-size:16px;color:var(--indigo);padding-top:1px;}
  .body{min-width:0;}
  .title{font-weight:600;font-size:16.5px;line-height:1.25;margin:0 0 6px;letter-spacing:-.005em;}

  .deckid{font-family:"JetBrains Mono",monospace;font-size:11.5px;line-height:1.4;color:var(--indigo-ink);background:var(--indigo-tint);border-radius:6px;padding:7px 10px;margin:0 0 8px;}
  .deckid .dl{display:block;font-size:9.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--indigo);margin-bottom:2px;}
  .deckid .pg{color:var(--muted);}

  .line{font-size:14px;color:var(--ink);margin:0 0 8px;display:flex;gap:8px;align-items:baseline;}
  .lbl{font-family:"JetBrains Mono",monospace;font-size:9.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;padding-top:1px;white-space:nowrap;}
  .lbl.why{color:var(--indigo);}
  .line .txt{color:var(--muted);}
  .line .txt b{color:var(--ink);font-weight:600;}

  .traces{display:flex;gap:8px;align-items:baseline;background:var(--green-tint);border-radius:6px;padding:7px 10px;font-size:13px;color:var(--green-ink);}
  .traces .tlbl{font-family:"JetBrains Mono",monospace;font-size:9.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;white-space:nowrap;padding-top:1px;}
  .traces .tlbl::before{content:"\21B3";margin-right:4px;}
  .traces em{font-style:normal;color:var(--ink);}

  .src{font-family:"JetBrains Mono",monospace;font-size:10.5px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;white-space:nowrap;padding:5px 9px;border-radius:5px;align-self:start;}
  .src.deck{background:var(--indigo);color:#fff;}
  .src.create{background:var(--coral);color:#fff;}

  .card.new{display:block;background:var(--coral-tint);border:1px dashed var(--coral);border-left:3px solid var(--coral);}
  .new-head{display:flex;align-items:center;gap:12px;margin:0 0 8px;}
  .new-head .seq{color:var(--coral-ink);padding:0;}
  .new-head .title{margin:0;flex:1;}
  .card.new .line .lbl.why{color:var(--coral-ink);}

  details.drill{margin-top:10px;border-top:1px dashed var(--drill-line);padding-top:10px;}
  details.drill summary{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:7px;font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--coral-ink);user-select:none;}
  details.drill summary::-webkit-details-marker{display:none;}
  details.drill summary::before{content:"\25B8";transition:transform .15s ease;font-size:11px;}
  details.drill[open] summary::before{transform:rotate(90deg);}
  details.drill summary:hover{color:var(--drill-hover);}
  .drillnote{font-size:12px;color:var(--muted);margin:4px 0 12px 18px;}

  .slide{background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:0 8px 26px -14px rgba(28,21,38,.28);aspect-ratio:16/9;padding:22px 26px;display:flex;flex-direction:column;overflow:hidden;}
  .s-eyebrow{font-family:"JetBrains Mono",monospace;font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--coral-ink);font-weight:700;}
  .s-title{font-family:"Fraunces",serif;font-weight:600;font-size:clamp(18px,3.2vw,25px);line-height:1.08;margin:3px 0 3px;color:var(--ink);}
  .s-sub{font-size:12.5px;color:var(--muted);margin:0 0 12px;}
  .s-body{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:10px;}

  .harness-frame{border:1.5px dashed var(--indigo);border-radius:9px;padding:12px;position:relative;}
  .harness-tab{position:absolute;top:-9px;left:12px;background:#fff;padding:0 7px;font-family:"JetBrains Mono",monospace;font-size:9px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--indigo);}
  .row3{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;}
  .hbox{background:var(--indigo-tint);border:1px solid var(--hbox-border);border-radius:7px;padding:9px 8px;text-align:center;}
  .hbox b{display:block;font-size:13px;color:var(--indigo-ink);}
  .hbox span{font-size:10.5px;color:var(--muted);}
  .innerlbl{font-family:"JetBrains Mono",monospace;font-size:9px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);text-align:center;margin:2px 0 0;}
  .gap{margin-top:11px;background:var(--coral-tint);border:1px dashed var(--coral);border-radius:7px;padding:9px 11px;text-align:center;}
  .gap .gl{font-family:"JetBrains Mono",monospace;font-size:9px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--coral-ink);display:block;margin-bottom:3px;}
  .gap .gt{font-size:12px;color:var(--ink);}

  .tiles{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
  .tile{background:var(--paper);border:1px solid var(--line);border-left:3px solid var(--indigo);border-radius:7px;padding:9px 11px;}
  .tile b{font-family:"Fraunces",serif;font-size:14.5px;color:var(--ink);}
  .tile span{display:block;font-size:11.5px;color:var(--muted);margin-top:1px;line-height:1.35;}
  .loopnote{font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:.05em;color:var(--green-ink);text-align:center;margin-top:2px;}

  .stack-two{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
  .agentbox{background:#fff;border:1.5px solid var(--indigo);border-radius:8px;padding:10px;text-align:center;}
  .agentbox b{font-size:13.5px;color:var(--indigo-ink);}
  .agentbox span{font-size:10.5px;color:var(--muted);}
  .conn{height:14px;display:flex;justify-content:space-around;}
  .conn i{width:1.5px;background:var(--indigo);opacity:.5;display:block;}
  .backbone{background:var(--indigo);color:#fff;border-radius:8px;padding:11px;text-align:center;}
  .backbone b{font-family:"Fraunces",serif;font-size:15px;letter-spacing:.01em;}
  .backbone span{display:block;font-size:10.5px;opacity:.85;margin-top:2px;}
  .expose{text-align:center;font-size:11.5px;color:var(--muted);margin-top:8px;font-style:italic;}

  .beats{display:flex;flex-direction:column;gap:7px;}
  .beat-r{display:grid;grid-template-columns:22px 1fr;gap:10px;align-items:baseline;background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:7px 10px;}
  .beat-r .bn{font-family:"JetBrains Mono",monospace;font-weight:700;font-size:12px;color:var(--coral-ink);}
  .beat-r b{font-size:13px;color:var(--ink);}
  .beat-r span{font-size:11.5px;color:var(--muted);}

  .foot{margin-top:38px;border-top:2px solid var(--ink);padding-top:22px;}
  .foot h2{font-family:"Fraunces",serif;font-weight:600;font-size:20px;margin:0 0 14px;}
  .cutgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
  .cut{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 15px;}
  .cut .k{font-family:"JetBrains Mono",monospace;font-size:10.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--indigo);margin:0 0 7px;}
  .cut p{margin:0;font-size:13.5px;color:var(--muted);line-height:1.45;}
  .cut .path{color:var(--ink);font-weight:600;}
  .cut.warn .k{color:var(--coral-ink);}
  .cut.go .k{color:var(--green);}

  a{color:var(--indigo);}

  @media (max-width:720px){
    .act{grid-template-columns:1fr;gap:14px;}
    .act-title{font-size:20px;margin:0;}
    .card{grid-template-columns:28px 1fr;}
    .card .src{grid-column:2;justify-self:start;margin-top:2px;}
    .cutgrid{grid-template-columns:1fr;}
    .tiles,.row3,.stack-two{grid-template-columns:1fr;}
  }
  @media print{
    body{background:#fff;}
    .wrap{padding:0;max-width:100%;}
    .card,.cut,.act{break-inside:avoid;}
  }'''

def main():
    here=os.path.dirname(os.path.abspath(__file__))
    cfg_path = sys.argv[1] if len(sys.argv)>1 else os.path.join(here,"examples","flow_guide.example.json")
    out_path = sys.argv[2] if len(sys.argv)>2 else "flow-guide.html"
    cfg=json.load(open(cfg_path))

    validate_config.enforce(cfg, schema_flow_guide.SCHEMA, name=os.path.basename(cfg_path))

    for ai, act in enumerate(cfg["acts"]):
        for ci, card in enumerate(act.get("cards", [])):
            where = "acts[%d].cards[%d]" % (ai, ci)
            if card["type"] == "deck" and not card.get("deckid_quote"):
                raise validate_config.ConfigError(
                    "%s: a deck card needs deckid_quote, the verbatim slide headline"
                    % where)
            if card["type"] == "create" and not card.get("preview"):
                raise validate_config.ConfigError(
                    "%s: a create card needs a preview block" % where)

    allowlist = cfg.get("allow_words", ())
    banned = cfg.get("banned_terms", ())
    guardrails.enforce(guardrails.check_tree(cfg, allowlist=allowlist, banned=banned))
    open(out_path,"w").write(build(cfg))
    n=sum(len(a["cards"]) for a in cfg["acts"])
    print("wrote", out_path, "with", len(cfg["acts"]), "acts and", n, "cards")


if __name__ == "__main__":
    try:
        main()
    except (validate_config.ConfigError, guardrails.GuardrailError) as err:
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)
