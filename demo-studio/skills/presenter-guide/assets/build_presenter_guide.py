# -*- coding: utf-8 -*-
"""
build_presenter_guide.py: render a companion presenter guide (side nav +
per-slide Talking points / Say-teleprompter / Ask, plus an optional live-demo
run-of-show) from a JSON config.

Usage:
    python3 build_presenter_guide.py CONFIG.json OUT.html

The styling (navigation, 3-column layout, teleprompter cards, demo beat cards)
is fixed and must not be changed; it is the reusable format. Only the CONTENT
comes from the JSON. See assets/examples/presenter_guide.example.json for the
schema by example, and references/presenter-guide-format.md for the field guide.
"""
import html, json, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "..", "..", "..", "shared"))
import brand
import guardrails
import traces as traces_mod
import validate_config
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import schema_presenter_guide

def esc(s): return html.escape(str(s), quote=True)

_DEFAULT_ACT_COLOR = brand.tokens("presenter_guide")["indigo"]

# A CSS hex colour: the value lands in a style attribute, so six digits behind
# a '#' and nothing else. The PPTX backend wants the same digits without the
# '#', which is exactly the confusion this catches.
_ACT_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def check_acts(cfg):
    """Acts rules the schema dialect cannot express. Call after enforce().

    `acts` can be declared as an object and no further: the dialect has no way
    to say "a map of act_key -> [label, colour]". build() indexes v[0] and v[1]
    straight out of the value, so a string act yielded its first two characters
    and put `style="color:n"` on the page. The act colouring was silently gone,
    with nothing raised and nothing written to stderr.
    """
    problems = []
    acts = cfg.get("acts", {})
    for key in sorted(acts):
        value = acts[key]
        where = "acts.%s" % key
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            problems.append('%s: expected [label, "#RRGGBB"], got %r'
                            % (where, value))
            continue
        label, color = value
        if not isinstance(label, str) or not label.strip():
            problems.append("%s[0]: label must not be blank, got %r"
                            % (where, label))
        if not isinstance(color, str) or not _ACT_COLOR_RE.match(color):
            problems.append('%s[1]: colour must be six hex digits behind a '
                            '"#", got %r' % (where, color))
    for i, slide in enumerate(cfg["slides"]):
        if slide["act"] not in acts:
            problems.append("slides[%d].act: %r is not a key in acts (have: %s)"
                            % (i, slide["act"], ", ".join(sorted(acts))))
    if problems:
        raise validate_config.ConfigError(
            "%d config error(s):\n%s" % (len(problems), "\n".join(problems)))


def build(cfg):
    ACT = {k:(v[0], v[1]) for k,v in cfg.get("acts", {}).items()}
    slides = cfg["slides"]

    # ---- nav (slides) ----
    nav_items=[]
    for s in slides:
        label, color = ACT.get(s["act"], (s["act"], _DEFAULT_ACT_COLOR))
        nav_items.append(
          f'<a class="navitem" href="#s{s["num"]}" data-target="s{s["num"]}">'
          f'<span class="navnum">{int(s["num"]):02d}</span>'
          f'<span class="navtxt">{esc(s["short"])}</span>'
          f'<span class="navact" style="color:{color}">{esc(label.split("·")[0].strip())}</span>'
          f'</a>')
    nav_html="\n".join(nav_items)

    # ---- slide sections ----
    sections=[]
    for s in slides:
        label, color = ACT.get(s["act"], (s["act"], _DEFAULT_ACT_COLOR))
        points="".join(f'<li>{esc(p)}</li>' for p in s.get("points",[]))
        say="".join(f'<div class="beat">{esc(b)}</div>' for b in s.get("say",[]))
        ask="".join(f'<div class="qcard">{esc(a)}</div>' for a in s.get("ask",[]))
        sections.append(f'''
    <section class="slide" id="s{s['num']}">
      <div class="s-head">
        <div class="s-eyebrow" style="color:{color}">{esc(label)}</div>
        <div class="s-titlerow"><span class="s-num">{int(s['num']):02d}</span><h2 class="s-title">{esc(s['title'])}</h2></div>
        <div class="s-onscreen"><span class="oslbl">On screen</span>{esc(s.get('onscreen',''))}</div>
      </div>
      <div class="s-grid">
        <div class="col-points"><div class="blocklbl points">Talking points</div><ul class="points">{points}</ul></div>
        <div class="col-say"><div class="blocklbl say">Say <span class="tele">teleprompter</span></div><div class="beats">{say}</div></div>
        <div class="col-ask"><div class="blocklbl ask">Ask &amp; expect</div>{ask}</div>
      </div>
    </section>''')
    sections_html="\n".join(sections)

    # ---- optional demo run-of-show ----
    demo_nav_html=""; demo_sections_html=""
    demo=cfg.get("demo")
    if demo:
        def r_rows(rows):
            out=[]
            for row in rows:
                lbl,cls,kind,content = row
                if kind in ('ol','ul'):
                    items="".join(f"<li>{it}</li>" for it in content)
                    body=f"<{kind}>{items}</{kind}>"
                else:
                    extra=" whytext" if cls=="why" else ""
                    body=f'<div class="single{extra}">{content}</div>'
                out.append(f'<div class="bc-row"><span class="bc-lbl {cls}">{lbl}</span><div>{body}</div></div>')
            return "".join(out)
        def r_beat(b):
            term=f'<div class="term-action">{b["term"]}</div>' if b.get("term") else ""
            note=f'<div class="bc-note">{b["note"]}</div>' if b.get("note") else ""
            tag=f'<span class="bc-tag">{b["tag"]}</span>' if b.get("tag") else ""
            return ('<section class="navsec beatsec" id="'+b["id"]+'">'
                    '<div class="beatcard accent-'+b.get("accent","indigo")+'">'
                    '<div class="bc-head"><span class="bc-badge">'+b["badge"]+'</span>'
                    '<h3 class="bc-title">'+b["title"]+'</h3>'+tag+'</div>'+term+
                    '<div class="bc-body">'+r_rows(b["rows"])+'</div>'+note+'</div></section>')

        beats=demo.get("beats",[])
        demo_beats_html="\n".join(r_beat(b) for b in beats)

        navdefs=[('demo', demo.get("intro_nav","Cold start &amp; lanes"))]
        for b in beats:
            navdefs.append((b["id"], b.get("nav", b["badge"]+" &middot; "+b["title"])))
        navdefs.append(('dref', demo.get("ref_nav","Reference &amp; switches")))
        def dnn(i):
            if i=='demo': return '&#9654;'
            if i=='dref': return 'R'
            d=i[1:] if i.startswith('d') else i
            return d if d.isdigit() else '&bull;'
        demo_nav_html='<div class="navdiv">'+demo.get("nav_divider","Live demo &middot; run of show")+'</div>\n'+"\n".join(
          f'<a class="navitem" href="#{i}" data-target="{i}"><span class="navnum">{dnn(i)}</span><span class="navtxt">{t}</span></a>'
          for (i,t) in navdefs)

        # intro (cold start + lanes + termmap + smoke)
        _muted_style = ' style="color:var(--muted)"'
        lanes="".join(
          f'<div class="lane {cls}"><span class="ln"{_muted_style if not cls else ""}>{name}</span><p>{desc}</p></div>'
          for (name,cls,desc) in demo.get("lanes",[]))
        def _kc(k): return "yes" if str(k).strip().lower().startswith("yes") else ""
        termmap="".join(
          f'<tr><td><b>{n}</b></td><td><code>{c}</code></td><td class="{_kc(k)}">{k}</td><td>{x}</td></tr>'
          for (n,c,k,x) in demo.get("termmap",[]))
        banner=demo.get("banner",{})
        demo_intro=('<section class="navsec" id="demo">'
          '<div class="demobanner"><div class="eyebrow">'+demo.get("nav_divider","Live demo &middot; run of show")+'</div>'
          '<h2>'+banner.get("title","Live demo")+'</h2><p>'+banner.get("text","")+'</p></div>')
        if demo.get("talk_track"):
            demo_intro+='<h3 class="demo-h">Opening talk track</h3><div class="beats"><div class="beat">'+demo["talk_track"]+'</div></div>'
        if demo.get("lanes"):
            demo_intro+='<h3 class="demo-h">What you are pointing at</h3><div class="lanes">'+lanes+'</div>'
        if demo.get("termmap"):
            demo_intro+=('<h3 class="demo-h">Cold start &middot; terminal map</h3>'
              '<table class="termmap"><thead><tr><th>#</th><th>Command</th><th>Keep running</th><th>Ctrl-C in beats</th></tr></thead><tbody>'+termmap+'</tbody></table>')
        if demo.get("smoke"):
            demo_intro+='<div class="smoke">'+demo["smoke"]+'</div>'
        demo_intro+='</section>'

        # reference (scenarios + switches + troubleshooting)
        scen="".join(f'<tr><td><b>{a}</b></td><td><code>{b}</code></td><td>{c}</td></tr>' for (a,b,c) in demo.get("scenarios",[]))
        switches="".join(f'<div class="switchblock"><div class="sw-t">{t}</div><pre>{esc(code)}</pre></div>' for (t,code) in demo.get("switches",[]))
        trouble="".join(f'<div class="trouble"><b>{t}:</b> {d}</div>' for (t,d) in demo.get("troubleshooting",[]))
        demo_ref='<section class="navsec" id="dref"><div class="s-titlerow"><span class="s-num">R</span><h2 class="s-title">'+demo.get("ref_title","Reference &amp; switches")+'</h2></div>'
        if demo.get("scenarios"):
            demo_ref+=('<h3 class="demo-h">Scenario buttons</h3><table class="scenariotable"><thead><tr><th>Button</th><th>Case / profile</th><th>Shows</th></tr></thead><tbody>'+scen+'</tbody></table>')
        if demo.get("switches"):
            demo_ref+='<h3 class="demo-h">Switches</h3><div class="switchwrap">'+switches+'</div>'
            if demo.get("switch_note"):
                demo_ref+='<p class="swnote">'+demo["switch_note"]+'</p>'
        if demo.get("troubleshooting"):
            demo_ref+='<h3 class="demo-h">Troubleshooting</h3><div class="troublelist">'+trouble+'</div>'
        demo_ref+='</section>'
        demo_sections_html=demo_intro+"\n"+demo_beats_html+"\n"+demo_ref

    chips="".join(f'<span class="chip"><b>{esc(a)}:</b> {esc(b)}</span>' for (a,b) in cfg.get("chips",[]))
    legend="".join(f'<span><b>{esc(a)}</b> {esc(b)}</span>' for (a,b) in cfg.get("legend",[]))

    doc = f"""<!DOCTYPE html>
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
<div class="shell">
  <aside class="side">
    <h1>{esc(cfg.get("nav_title","Presenter Guide"))}</h1>
    <div class="sub">{esc(cfg.get("nav_sub",""))}</div>
    <nav class="nav">
{nav_html}
{demo_nav_html}
    </nav>
  </aside>
  <main class="main">
    <div class="masthead">
      <div class="eyebrow">{esc(cfg.get("eyebrow","Companion presenter guide"))}</div>
      <h1>{esc(cfg["title"])}</h1>
      <p class="lede">{esc(cfg.get("subtitle",""))}</p>
      <div class="chips">{chips}</div>
      <div class="legend">{legend}</div>
    </div>
{sections_html}
{demo_sections_html}
  </main>
</div>
<a class="backtop" href="#top">&#8593; top</a>
<span id="top"></span>
<script>{JS}</script>
</body>
</html>"""
    return doc

CSS = brand.root_block("presenter_guide") + r'''
*{box-sizing:border-box;}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%;}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:16px;line-height:1.5;}
a{color:inherit;text-decoration:none;}

/* layout */
.shell{display:grid;grid-template-columns:264px 1fr;}
/* sidebar */
.side{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;border-right:1px solid var(--line);background:#fff;padding:22px 14px 40px;}
.side h1{font-family:"Fraunces",serif;font-weight:600;font-size:19px;line-height:1.1;margin:2px 6px 2px;}
.side .sub{font-size:11.5px;color:var(--muted);margin:0 6px 16px;}
.nav{display:flex;flex-direction:column;gap:2px;}
.navitem{display:grid;grid-template-columns:26px 1fr auto;gap:8px;align-items:center;padding:7px 8px;border-radius:7px;font-size:13px;color:var(--ink);}
.navitem:hover{background:var(--indigo-tint);}
.navitem.active{background:var(--indigo);color:#fff;}
.navitem.active .navnum,.navitem.active .navact{color:#fff !important;}
.navnum{font-family:"JetBrains Mono",monospace;font-size:11.5px;font-weight:700;color:var(--indigo);}
.navtxt{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.navact{font-family:"JetBrains Mono",monospace;font-size:8.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;}

/* content */
.main{padding:36px clamp(20px,4vw,56px) 90px;max-width:1080px;}
.masthead{border-bottom:1px solid var(--line);padding-bottom:22px;margin-bottom:8px;}
.eyebrow{font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--indigo);font-weight:500;}
.masthead h1{font-family:"Fraunces",serif;font-weight:600;font-size:clamp(30px,4.4vw,44px);line-height:1.05;margin:.25em 0 .3em;}
.masthead .lede{font-size:16px;color:var(--muted);max-width:70ch;margin:0 0 16px;}
.chips{display:flex;flex-wrap:wrap;gap:8px;}
.chip{font-family:"JetBrains Mono",monospace;font-size:11.5px;background:var(--indigo-tint);color:var(--indigo-ink);padding:6px 11px;border-radius:999px;}
.chip b{font-weight:700;}
.legend{display:flex;flex-wrap:wrap;gap:16px;margin-top:14px;font-size:13px;color:var(--muted);}
.legend span b{color:var(--ink);}

/* slide section */
.slide{padding:34px 0 30px;border-bottom:1px solid var(--line);scroll-margin-top:14px;}
.s-eyebrow{font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;}
.s-titlerow{display:flex;align-items:baseline;gap:12px;margin:4px 0 8px;}
.s-num{font-family:"JetBrains Mono",monospace;font-weight:700;font-size:20px;color:var(--indigo);}
.s-title{font-family:"Fraunces",serif;font-weight:600;font-size:clamp(23px,3vw,30px);line-height:1.08;margin:0;}
.s-onscreen{font-size:13.5px;color:var(--muted);background:#fff;border:1px solid var(--line);border-radius:8px;padding:9px 12px;}
.s-onscreen .oslbl{font-family:"JetBrains Mono",monospace;font-size:9.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--faint);margin-right:8px;}

.s-grid{display:grid;grid-template-columns:1fr 1.35fr 1fr;gap:18px;margin-top:18px;}
.blocklbl{font-family:"JetBrains Mono",monospace;font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:8px;}
.blocklbl.points{color:var(--indigo);}
.blocklbl.say{color:var(--green);}
.blocklbl.ask{color:var(--coral);}
.tele{font-family:"IBM Plex Sans",sans-serif;font-size:9.5px;font-weight:600;letter-spacing:.04em;text-transform:none;color:var(--faint);background:var(--green-tint);padding:2px 7px;border-radius:999px;}

ul.points{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:9px;}
ul.points li{position:relative;padding-left:16px;font-size:14px;color:var(--ink);line-height:1.4;}
ul.points li::before{content:"";position:absolute;left:0;top:8px;width:6px;height:6px;border-radius:50%;background:var(--indigo);}

/* teleprompter beats */
.beats{display:flex;flex-direction:column;gap:8px;}
.beat{background:#fff;border:1px solid var(--line);border-left:3px solid var(--green);border-radius:8px;padding:11px 14px;font-size:16px;line-height:1.45;color:var(--ink);}

/* questions */
.qcard{background:var(--coral-tint);border:1px solid var(--coral-border);border-radius:8px;padding:10px 12px;font-size:13.5px;color:var(--ink);line-height:1.4;margin-bottom:8px;}

.backtop{position:fixed;right:18px;bottom:18px;background:var(--indigo);color:#fff;font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;letter-spacing:.06em;padding:9px 12px;border-radius:8px;opacity:.9;}

@media (max-width:1000px){
  .shell{grid-template-columns:1fr;}
  .side{position:static;height:auto;border-right:none;border-bottom:1px solid var(--line);}
  .side{max-height:none;}
  .nav{display:grid;grid-template-columns:1fr 1fr;}
  .s-grid{grid-template-columns:1fr;}
}
@media print{
  .side,.backtop{display:none;}
  .shell{grid-template-columns:1fr;}
  .slide{break-inside:avoid;}
  .s-grid{grid-template-columns:1fr 1fr;}
}


.navdiv{font-family:"JetBrains Mono",monospace;font-size:9.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);padding:14px 8px 6px;border-top:1px solid var(--line);margin-top:10px;}
.demobanner{background:var(--indigo);color:#fff;border-radius:12px;padding:22px 24px;margin:6px 0 18px;}
.demobanner .eyebrow{color:var(--on-dark);}
.demobanner h2{font-family:"Fraunces",serif;font-weight:600;font-size:28px;margin:.2em 0 .3em;color:#fff;}
.demobanner p{margin:0;color:var(--on-dark-body);font-size:14px;max-width:72ch;}
.demo-h{font-family:"JetBrains Mono",monospace;font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--indigo);margin:22px 0 9px;}
.lanes{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:4px 0;}
.lane{background:#fff;border:1px solid var(--line);border-radius:9px;padding:12px 14px;}
.lane .ln{font-family:"JetBrains Mono",monospace;font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;}
.lane.plat{border-left:3px solid var(--indigo);} .lane.plat .ln{color:var(--indigo);}
.lane.work{border-left:3px solid var(--coral);} .lane.work .ln{color:var(--coral-ink);}
.lane p{margin:5px 0 0;font-size:13px;color:var(--muted);line-height:1.4;}
.termmap,.scenariotable{width:100%;border-collapse:collapse;font-size:13px;margin:4px 0;}
.termmap th,.termmap td,.scenariotable th,.scenariotable td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);}
.termmap th,.scenariotable th{font-family:"JetBrains Mono",monospace;font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);font-weight:700;}
.termmap code,.scenariotable code,.trouble code,.bc-row code,.bc-note code,.smoke code{font-family:"JetBrains Mono",monospace;font-size:12px;background:var(--indigo-tint);padding:1px 5px;border-radius:4px;color:var(--indigo-ink);}
.termmap .yes{color:var(--green);font-weight:600;} .termmap .kill{color:var(--coral);font-weight:700;}
.smoke{background:var(--green-tint);border:1px solid var(--green-border);border-radius:8px;padding:11px 13px;font-size:13.5px;color:var(--green-ink);margin:12px 0;line-height:1.5;}
.smoke b{color:var(--ink);}
.beatsec{scroll-margin-top:14px;padding:8px 0;}
.beatcard{background:#fff;border:1px solid var(--line);border-left:4px solid var(--indigo);border-radius:11px;padding:18px 20px;margin:0 0 8px;}
.beatcard.accent-coral{border-left-color:var(--coral);}
.beatcard.accent-green{border-left-color:var(--green);}
.beatcard.accent-amber{border-left-color:var(--amber);}
.bc-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:4px;}
.bc-badge{font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;letter-spacing:.05em;color:#fff;background:var(--indigo);padding:4px 9px;border-radius:6px;}
.accent-coral .bc-badge{background:var(--coral);} .accent-green .bc-badge{background:var(--green);} .accent-amber .bc-badge{background:var(--amber);}
.bc-title{font-family:"Fraunces",serif;font-weight:600;font-size:21px;margin:0;flex:1;}
.bc-tag{font-family:"JetBrains Mono",monospace;font-size:9.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);background:var(--paper);border:1px solid var(--line);padding:4px 9px;border-radius:999px;}
.term-action{font-family:"JetBrains Mono",monospace;font-size:12.5px;background:var(--term-bg);color:var(--term-fg);border-radius:8px;padding:10px 13px;margin:8px 0 12px;line-height:1.5;}
.term-action code{background:rgba(255,255,255,.14);padding:1px 5px;border-radius:4px;color:#fff;}
.term-action b{color:var(--term-accent);}
.bc-row{display:grid;grid-template-columns:78px 1fr;gap:12px;padding:8px 0;border-top:1px solid var(--line);}
.bc-row:first-child{border-top:none;}
.bc-lbl{font-family:"JetBrains Mono",monospace;font-size:9.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;padding-top:3px;}
.bc-lbl.goal{color:var(--muted);} .bc-lbl.do{color:var(--indigo);} .bc-lbl.watch{color:var(--green);} .bc-lbl.why{color:var(--coral);}
.bc-row ol,.bc-row ul{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:5px;font-size:14px;}
.bc-row li{line-height:1.45;}
.bc-row .single{font-size:14px;line-height:1.45;}
.bc-row .single.whytext{font-weight:500;}
.bc-note{font-size:12.5px;color:var(--muted);background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:9px 12px;margin-top:11px;line-height:1.5;}
.bc-note b{color:var(--ink);}
.switchwrap{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:6px 0;}
.switchblock{background:var(--term-bg);border-radius:9px;padding:13px 15px;}
.switchblock .sw-t{font-family:"JetBrains Mono",monospace;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--on-dark);margin-bottom:8px;}
.switchblock pre{margin:0;font-family:"JetBrains Mono",monospace;font-size:11.5px;color:var(--on-dark-pre);white-space:pre-wrap;line-height:1.55;}
.swnote{font-size:12.5px;color:var(--muted);margin:10px 0 0;line-height:1.5;}
.troublelist{display:flex;flex-direction:column;gap:8px;margin-top:4px;}
.trouble{background:#fff;border:1px solid var(--line);border-radius:8px;padding:9px 12px;font-size:13px;line-height:1.45;}
.trouble b{color:var(--ink);}
@media(max-width:1000px){ .lanes,.switchwrap{grid-template-columns:1fr;} .bc-row{grid-template-columns:1fr;} .bc-lbl{padding-top:0;} }
'''
JS  = r'''
const items=[...document.querySelectorAll('.navitem')];
const map=new Map(items.map(a=>[a.dataset.target,a]));
const secs=[...document.querySelectorAll('section[id]')];
function setActive(){
  const line=120; let best=null;
  const atBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 2;
  if(atBottom){ best=secs[secs.length-1]; }
  else { for(const s of secs){ if(s.getBoundingClientRect().top-line<=0) best=s; } }
  if(!best) best=secs[0];
  if(!best) return;
  items.forEach(i=>i.classList.remove('active'));
  const a=map.get(best.id); if(a){a.classList.add('active'); a.scrollIntoView({block:'nearest'});}
}
let tick=false;
addEventListener('scroll',()=>{if(!tick){tick=true;requestAnimationFrame(()=>{setActive();tick=false;});}},{passive:true});
addEventListener('load',setActive); setActive();
'''

def main():
    here=os.path.dirname(os.path.realpath(__file__))
    cfg_path = sys.argv[1] if len(sys.argv)>1 else os.path.join(here,"examples","presenter_guide.example.json")
    out_path = sys.argv[2] if len(sys.argv)>2 else "presenter-guide.html"
    cfg=validate_config.load_config(cfg_path)

    validate_config.enforce(cfg, schema_presenter_guide.SCHEMA, name=os.path.basename(cfg_path))

    check_acts(cfg)

    allowlist = cfg.get("allow_words", ())
    banned = cfg.get("banned_terms", ())
    guardrails.enforce(guardrails.check_tree(cfg, allowlist=allowlist, banned=banned))

    traces_mod.resolve_and_report(cfg, cfg_path)

    open(out_path,"w").write(build(cfg))
    print("wrote", out_path, "with", len(cfg["slides"]), "slides",
          "+ demo" if cfg.get("demo") else "")


if __name__ == "__main__":
    try:
        main()
    except (validate_config.ConfigError, guardrails.GuardrailError) as err:
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)
