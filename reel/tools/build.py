# Generates index.html and compositions/*.html for the reel from the timed script.
# All on-screen Bengali text is taken from assets/transcript.json (the script's own code points).
import json, os, random, html

ROOT = os.path.join(os.path.dirname(__file__), "..")
W = json.load(open(os.path.join(ROOT, "assets", "transcript.json"), encoding="utf-8"))
TOTAL = 84.0
X = 0.35  # crossfade overlap between scenes


def T(a, b=None):
    """Exact script words a..b (inclusive) as one string."""
    b = a if b is None else b
    return " ".join(w["text"] for w in W[a:b + 1])


def t0(i):
    return W[i]["start"]


def find(seg, k=0):
    return [w for w in W if w["seg"] == seg][k]["id"]


def idx(seg, k=0):
    return int(find(seg, k)[1:])


FONT_CSS = """
@font-face{font-family:'Anek Bangla';font-weight:%(w)s;src:url('assets/fonts/anek-bangla-bengali-%(w)s-normal.woff2') format('woff2');unicode-range:U+0951-0952,U+0964-0965,U+0980-09FE,U+200C-200D,U+25CC;}
@font-face{font-family:'Anek Bangla';font-weight:%(w)s;src:url('assets/fonts/anek-bangla-latin-%(w)s-normal.woff2') format('woff2');unicode-range:U+0000-00FF,U+2000-206F;}
"""
FONTS = "".join(FONT_CSS % {"w": w} for w in (500, 700, 800))

GOLD = "#FFC46B"
MOODS = {  # background grade per scene: (centre, edge)
    "cold": ("#1d2a3a", "#05070b"),
    "dusk": ("#2a2433", "#07060a"),
    "warm": ("#3b2614", "#0a0603"),
    "glow": ("#5a3412", "#0c0703"),
}

# ---------------------------------------------------------------- line art (viewBox 0 0 500 500)
P = 'pathLength="1" class="ln"'  # a second class attr is merged in fix_cls()


def person(x, y, s=1.0, cls=""):
    return (f'<g class="{cls}"><circle {P} cx="{x}" cy="{y}" r="{22*s}"/>'
            f'<path {P} d="M{x-46*s} {y+110*s} Q{x-44*s} {y+38*s} {x} {y+36*s} Q{x+44*s} {y+38*s} {x+46*s} {y+110*s}"/></g>')


def star(x, y, r):
    return (f'<path {P} class="ln st" d="M{x} {y-r} Q{x} {y} {x+r} {y} Q{x} {y} {x} {y+r} Q{x} {y} {x-r} {y} Q{x} {y} {x} {y-r}Z"/>')


FLAME = lambda x, y, s=1: f'<path {P} class="ln fl" d="M{x} {y-70*s} C{x+38*s} {y-20*s} {x+34*s} {y+20*s} {x} {y+26*s} C{x-34*s} {y+20*s} {x-38*s} {y-20*s} {x} {y-70*s}Z"/><path {P} class="ln fl" d="M{x} {y-24*s} C{x+12*s} {y-4*s} {x+10*s} {y+10*s} {x} {y+14*s} C{x-10*s} {y+10*s} {x-12*s} {y-4*s} {x} {y-24*s}Z"/>'

ART = {
    "plate": f'''<ellipse {P} cx="250" cy="360" rx="175" ry="52"/><ellipse {P} cx="250" cy="356" rx="112" ry="30"/>
      <path {P} d="M60 300 L60 410 M48 300 L48 340 Q60 352 72 340 L72 300"/><path {P} d="M440 300 Q452 330 440 350 L440 410"/>
      <circle {P} class="ln dr" cx="300" cy="270" r="9"/><circle {P} class="ln dr" cx="326" cy="236" r="14"/>
      <path {P} class="ln dr" d="M300 200 Q262 196 268 160 Q250 120 294 108 Q312 72 356 92 Q396 72 418 110 Q458 120 444 160 Q452 198 410 200 Z"/>
      <path {P} class="ln dr" d="M318 140 Q356 186 394 140 Z"/>''',
    "bowl": f'''<path {P} d="M100 250 L400 250 Q392 400 250 410 Q108 400 100 250Z"/><path {P} d="M196 412 L206 440 L294 440 L304 412"/>
      <path {P} class="ln dim" d="M230 236 Q220 200 236 170 M270 236 Q282 204 266 174"/>''',
    "rain": person(250, 250, 1.3) + f'''<path {P} class="ln dim" d="M120 170 L250 90 L380 170"/><path {P} class="ln dim" d="M150 160 L150 200 M350 160 L350 190"/>'''
            + "".join(f'<path {P} class="ln rn" d="M{x} {y} L{x-14} {y+40}"/>' for x, y in [(110, 230), (160, 300), (390, 240), (420, 320), (80, 360), (340, 380), (190, 410), (450, 420), (130, 120), (400, 110), (300, 60)]),
    "elder": f'''<circle {P} cx="232" cy="170" r="30"/><path {P} d="M226 204 Q292 236 280 330 L270 420 M274 330 L230 420 M262 232 Q240 280 318 300"/>
      <path {P} d="M318 300 L338 430"/><path {P} class="ln dim" d="M90 360 L420 360 M110 360 L110 430 M400 360 L400 430"/>''',
    "child": person(150, 300, 1.05) + "".join(star(x, y, r) for x, y, r in [(300, 110, 26), (380, 170, 18), (250, 200, 14), (420, 80, 12), (340, 250, 10), (200, 120, 10), (450, 230, 14)])
             + f'<path {P} class="ln dim" d="M170 285 Q230 240 286 140"/>',
    "smile": f'''<path {P} d="M150 270 Q250 380 350 270"/><circle {P} cx="190" cy="200" r="10"/><circle {P} cx="310" cy="200" r="10"/>''',
    "candle": f'''<path {P} d="M215 270 L215 430 L285 430 L285 270 Z"/><path {P} d="M250 270 L250 250"/>{FLAME(250, 212, 1.15)}''',
    "circle": "".join(person(250 + 150 * c, 250 + 150 * s - 40, 0.7) for c, s in [(0, -1), (0.87, -0.5), (0.87, 0.5), (0, 1), (-0.87, 0.5), (-0.87, -0.5)])
              + f'<circle {P} class="ln dim" cx="250" cy="250" r="78"/>',
    "hands": f'''<path {P} d="M110 330 Q130 420 250 430 Q370 420 390 330 M110 330 Q150 320 180 350 L210 380 M390 330 Q350 320 320 350 L290 380"/>
      <path {P} d="M180 350 Q160 300 130 290 M320 350 Q340 300 370 290"/>{FLAME(250, 300, 1.2)}''',
    "logo": f'''<circle {P} cx="250" cy="250" r="200"/><path {P} d="M120 330 Q170 400 250 400 Q330 400 380 330 M120 330 Q170 320 210 360 M380 330 Q330 320 290 360"/>{FLAME(250, 260, 1.5)}''',
    "food": f'''<path {P} d="M100 270 L400 270 Q392 410 250 420 Q108 410 100 270Z"/><path {P} d="M120 270 Q250 200 380 270"/>
      <path {P} class="ln stm" d="M200 180 Q186 150 204 120 Q220 92 204 62"/><path {P} class="ln stm" d="M250 180 Q236 150 254 120 Q270 92 254 62"/><path {P} class="ln stm" d="M300 180 Q286 150 304 120 Q320 92 304 62"/>''',
    "shirt": person(150, 260, 1.0) + f'''<path {P} d="M290 200 L330 180 Q360 200 390 180 L430 200 L460 260 L430 272 L420 250 L420 400 L300 400 L300 250 L290 272 L260 260 Z"/>''',
    "care": f'''<circle {P} cx="190" cy="170" r="28"/><path {P} d="M186 202 Q240 236 232 320 L224 420 M228 320 L190 420 M220 232 Q206 280 270 296 L284 420"/>
      <path {P} class="ln ht" d="M350 230 C350 200 390 190 400 222 C410 190 450 200 450 230 C450 270 400 300 400 300 C400 300 350 270 350 230Z"/>''',
    "house": f'''<path {P} d="M90 250 L250 110 L410 250"/><path {P} d="M130 220 L130 420 L370 420 L370 220"/><path {P} d="M220 420 L220 330 L280 330 L280 420"/>
      <path {P} class="ln ht" d="M160 270 C160 254 180 248 186 264 C192 248 212 254 212 270 C212 290 186 304 186 304 C186 304 160 290 160 270Z"/><path {P} class="ln dim" d="M310 130 L310 180 L340 180 L340 156"/>''',
    "work": f'''<circle {P} cx="300" cy="230" r="70"/><circle {P} cx="300" cy="230" r="26"/>'''
            + "".join(f'<path {P} d="M{300+70*c:.0f} {230+70*s:.0f} L{300+96*c:.0f} {230+96*s:.0f}"/>' for c, s in [(1, 0), (0.71, 0.71), (0, 1), (-0.71, 0.71), (-1, 0), (-0.71, -0.71), (0, -1), (0.71, -0.71)])
            + f'<path {P} d="M90 430 L190 330 M160 300 L220 360 L240 340 L180 280 Z"/><path {P} class="ln dim" d="M60 440 L440 440"/>',
    "fund": f'''<path {P} d="M170 230 L170 410 Q170 430 190 430 L310 430 Q330 430 330 410 L330 230 M160 230 L340 230 M190 200 L310 200 L310 230 M190 200 L190 230"/>
      <path {P} class="ln ht" d="M220 320 C220 300 246 292 250 314 C254 292 280 300 280 320 C280 346 250 366 250 366 C250 366 220 346 220 320Z"/>
      <path {P} class="ln fan" d="M250 200 Q160 120 60 90"/><path {P} class="ln fan" d="M250 200 Q200 90 160 30"/><path {P} class="ln fan" d="M250 200 Q260 90 250 20"/><path {P} class="ln fan" d="M250 200 Q300 90 340 30"/><path {P} class="ln fan" d="M250 200 Q340 120 440 90"/>''',
    "ripple": f'''<circle {P} class="ln cn" cx="250" cy="150" r="22"/><path {P} class="ln cn" d="M250 128 L250 172"/>'''
              + "".join(f'<ellipse {P} class="ln rp" cx="250" cy="330" rx="{r}" ry="{r*0.3:.0f}"/>' for r in (30, 80, 140, 200, 240)),
    "lanterns": "".join(f'<path {P} class="ln lt" d="M{x-26} {y} L{x+26} {y} L{x+34} {y+70} L{x-34} {y+70} Z M{x} {y} L{x} {y-30}"/>' for x, y in [(70, 300), (160, 250), (250, 220), (340, 250), (430, 300)])
                + "".join(FLAME(x, y + 48, 0.32) for x, y in [(70, 300), (160, 250), (250, 220), (340, 250), (430, 300)]),
    "reach": f'''<path {P} d="M40 470 L120 360 Q140 330 170 330 L200 330 M120 360 Q150 300 190 290 L215 285 M200 330 L218 312"/>
      <path {P} d="M460 470 L380 360 Q360 330 330 330 L300 330 M380 360 Q350 300 310 290 L285 285 M300 330 L282 312"/>
      <path {P} class="ln ht" d="M195 190 C195 150 245 140 250 182 C255 140 305 150 305 190 C305 240 250 270 250 270 C250 270 195 240 195 190Z"/>''',
    "people": "".join(person(x, y, s) for x, y, s in [(80, 270, 0.75), (165, 240, 0.85), (250, 220, 1.0), (335, 240, 0.85), (420, 270, 0.75)])
              + f'<path {P} class="ln dim" d="M40 420 L460 420"/>',
}

# ---------------------------------------------------------------- scenes
# beats: (local-start, art key or None, [headline lines], highlight index list, extra classes)
SC = []


def scene(sid, start, end, mood, beats, chapter=None, end_mood=None, extra=""):
    SC.append(dict(id=sid, start=start, end=end, mood=mood, beats=beats, chapter=chapter, end_mood=end_mood, extra=extra))


# times are absolute here; converted to local below
scene("s01", 0.0, 5.80, "cold", [
    (0.0, "plate", [T(0, 1), T(2, 4)], [0]),
    (t0(idx(1)) - 0.1, None, [T(idx(1) + 2, idx(1) + 3), T(idx(1) + 4, idx(1) + 5)], [1]),
])
scene("s02", 5.80, 12.60, "cold", [
    (t0(idx(2)) - 0.05, "bowl", [T(idx(2), idx(2) + 1)], [0]),
    (t0(idx(3)) - 0.05, "rain", [T(idx(3), idx(3) + 1)], [0]),
    (t0(idx(4)) - 0.05, "elder", [T(idx(4) + 1, idx(4) + 3), T(idx(4) + 7, idx(4) + 9)], [1]),
])
scene("s03", 12.60, 18.55, "dusk", [
    (t0(idx(5)) - 0.05, "child", [T(idx(5) + 2, idx(5) + 3), T(idx(5) + 5, idx(5) + 7)], [1]),
    (t0(idx(6)) - 0.05, "child", [T(idx(6) + 3, idx(6) + 5)], [0], "dark"),
])
scene("s04", 18.55, 27.25, "dusk", [
    (t0(idx(7)) - 0.05, "smile", [T(idx(7) + 1, idx(7) + 4)], [0]),
    (t0(idx(8)) - 0.05, "candle", [T(idx(8) + 2, idx(8) + 4)], [0], "ignite"),
    (t0(idx(9)) - 0.05, "circle", [T(idx(9) + 1, idx(9) + 5)], [0]),
    (t0(idx(10)) - 0.05, "hands", [T(idx(10) + 2, idx(10) + 3)], [0]),
], end_mood="warm")
scene("s05", 27.25, 29.45, "glow", [
    (t0(idx(11)) - 0.02, "logo", [T(idx(11), idx(11) + 1), T(idx(11) + 2)], [0], "brand"),
])
scene("s06", 29.45, 31.90, "warm", [
    (t0(idx(12)) - 0.05, "icons", [T(idx(12) + 2, idx(12) + 4)], [0]),
])
scene("s07", 31.90, 34.95, "warm", [(t0(idx(13)) - 0.05, "food", [T(idx(13) + 5, idx(13) + 6)], [0])], chapter="০১")
scene("s08", 34.95, 38.90, "warm", [(t0(idx(14)) - 0.05, "shirt", [T(idx(14), idx(14) + 1)], [0], "chips")], chapter="০২")
scene("s09", 38.90, 42.35, "warm", [(t0(idx(15)) - 0.05, "care", [T(idx(15) + 1, idx(15) + 2), T(idx(15) + 3, idx(15) + 6)], [1])], chapter="০৩")
scene("s10", 42.35, 46.55, "warm", [(t0(idx(16)) - 0.05, "house", [T(idx(16) + 7, idx(16) + 9)], [0])], chapter="০৪")
scene("s11", 46.55, 51.25, "warm", [(t0(idx(17)) - 0.05, "work", [T(idx(17) + 7, idx(17) + 9)], [0])], chapter="০৫")
scene("s12", 51.25, 58.30, "glow", [
    (t0(idx(18)) - 0.05, "fund", [T(idx(18) + 3, idx(18) + 4)], [0]),
    (t0(idx(19)) - 0.05, "fund", [T(idx(19) + 2, idx(19) + 4)], [0], "spread"),
    (t0(idx(19) + 6) - 0.05, None, [T(idx(19) + 6, idx(19) + 7), T(idx(19) + 8, idx(19) + 9)], [1]),
])
scene("s13", 58.30, 64.10, "dusk", [
    (t0(idx(20)) - 0.05, "ripple", [T(idx(20), idx(20) + 1)], [0], "dropwait"),
    (t0(idx(21)) - 0.05, "ripple", [T(idx(21) + 1, idx(21) + 2)], [0], "drop"),
    (t0(idx(21) + 8) - 0.05, "ripple", [T(idx(21) + 8, idx(21) + 10)], [0], "waves"),
], end_mood="glow")
scene("s14", 64.10, 69.05, "warm", [
    (t0(idx(22)) - 0.05, "lanterns", [T(idx(22))], [0], "lights"),
    (t0(idx(24)) - 0.05, None, [T(idx(24), idx(24) + 3)], [0]),
])
scene("s15", 69.05, 71.30, "glow", [(t0(idx(25)) - 0.05, "reach", [T(idx(25) + 2, idx(25) + 4)], [0])])
scene("s16", 71.30, 75.85, "warm", [
    (t0(idx(26)) - 0.05, "people", [T(idx(26), idx(26) + 2)], [], "stack"),
], end_mood="glow")
scene("s17", 75.85, TOTAL, "glow", [
    (t0(idx(27)) - 0.05, "logo", [T(idx(27), idx(27) + 1), T(idx(27) + 2)], [0], "endcard"),
])

ICON_ROW = ["food", "shirt", "care", "house", "work"]


def bokeh(rng, n, warm):
    out = []
    for i in range(n):
        x, y = rng.uniform(-40, 1080), rng.uniform(150, 1900)
        r = rng.uniform(14, 70)
        a = rng.uniform(0.05, 0.22)
        col = "255,196,107" if warm else "150,185,230"
        out.append(f'<i class="bk" style="left:{x:.0f}px;top:{y:.0f}px;width:{2*r:.0f}px;height:{2*r:.0f}px;'
                   f'background:radial-gradient(circle,rgba({col},{a:.2f}) 0%,rgba({col},{a*0.4:.2f}) 45%,rgba({col},0) 70%)"></i>')
    return "".join(out)


def headline_html(sid, bi, lines, hi, start, dur, extra):
    spans = []
    for li, ln in enumerate(lines):
        cls = "hl gold" if li in hi else "hl"
        spans.append(f'<span class="{cls}">{html.escape(ln)}</span>')
    cls = "head" + (" brand" if extra in ("brand", "endcard") else "")
    return (f'<div id="{sid}-h{bi}" class="clip {cls}" data-start="{start:.2f}" data-duration="{dur:.2f}" data-track-index="3" '
            f'data-layout-allow-overflow>{"".join(spans)}</div>')


def build_scene(s, rng):
    sid, dur = s["id"], s["end"] - s["start"] + (X if s["end"] < TOTAL else 0)
    c1, c2 = MOODS[s["mood"]]
    warm = s["mood"] in ("warm", "glow")
    beats = [(b[0] - s["start"], *b[1:]) for b in s["beats"]]
    js, body = [], []
    # scene entrance (crossfade over previous scene) + camera push
    js.append(f'tl.fromTo("#{sid}-in",{{opacity:{0 if sid != "s01" else 1}}},{{opacity:1,duration:{X},ease:"sine.inOut"}},0);')
    js.append(f'tl.fromTo("#{sid}-cam",{{scale:1.0,y:0}},{{scale:1.07,y:-18,duration:{dur:.2f},ease:"none"}},0);')
    js.append(f'tl.fromTo("#{sid}-rays",{{rotation:-8,opacity:{0.35 if warm else 0.18}}},{{rotation:10,opacity:{0.6 if warm else 0.25},duration:{dur:.2f},ease:"none"}},0);')
    js.append(f'tl.fromTo("#{sid}-bk .bk",{{y:0}},{{y:(i)=>-40-(i%5)*22,x:(i)=>((i%3)-1)*18,duration:{dur:.2f},ease:"none"}},0);')
    if s["end_mood"]:
        e1, e2 = MOODS[s["end_mood"]]
        js.append(f'tl.fromTo("#{sid}-warm",{{opacity:0}},{{opacity:1,duration:{dur*0.6:.2f},ease:"sine.inOut"}},{dur*0.35:.2f});')
        body.append(f'<div id="{sid}-warm" class="bg" style="background:radial-gradient(120% 75% at 50% 42%,{e1} 0%,{e2} 78%)"></div>')
    if s["chapter"]:
        body.append(f'<div id="{sid}-ch" class="clip chap" data-start="0" data-duration="{dur:.2f}" data-track-index="4"><span class="chn">{s["chapter"]}</span><span class="chl"></span></div>')
        js.append(f'tl.fromTo("#{sid}-ch .chn",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},0.1);')
        js.append(f'tl.fromTo("#{sid}-ch .chl",{{scaleX:0}},{{scaleX:1,duration:0.7,ease:"power3.out"}},0.2);')
    arts = []
    for bi, b in enumerate(beats):
        st, art, lines, hi = b[0], b[1], b[2], b[3]
        extra = b[4] if len(b) > 4 else ""
        st = max(st, 0.0)
        nxt = beats[bi + 1][0] if bi + 1 < len(beats) else dur
        hd = nxt - st
        body.append(headline_html(sid, bi, lines, hi, st, hd, extra))
        hsel = f"#{sid}-h{bi} .hl"
        if extra in ("brand", "endcard"):
            js.append(f'tl.fromTo("{hsel}",{{opacity:0,scale:1.25}},{{opacity:1,scale:1,duration:0.7,ease:"expo.out",stagger:0.18}},{st + 0.05:.2f});')
        elif sid == "s01" and bi == 0:
            js.append(f'tl.fromTo("{hsel}",{{opacity:1,y:0,scale:0.96}},{{opacity:1,y:0,scale:1,duration:1.2,ease:"power2.out"}},0);')
        else:
            js.append(f'tl.fromTo("{hsel}",{{opacity:0,y:60,scale:0.92}},{{opacity:1,y:0,scale:1,duration:0.55,ease:"power3.out",stagger:0.16}},{st:.2f});')
        if bi + 1 == len(beats) and s["end"] < TOTAL:
            js.append(f'tl.to("{hsel}",{{opacity:0,duration:0.25,ease:"power2.in"}},{dur - X - 0.2:.2f});')
        if hd > 0.5 and bi + 1 < len(beats):
            js.append(f'tl.to("{hsel}",{{opacity:0,y:-40,duration:0.22,ease:"power2.in"}},{nxt - 0.24:.2f});')
        if art:
            arts.append((bi, art, st, extra))
    # art layers: an art keeps showing until a beat brings another art
    for k, (bi, art, st, extra) in enumerate(arts):
        nxt_art = next((a[2] for a in arts[k + 1:] if a[1] != art), dur)
        if art == "icons":
            inner = "".join(f'<svg class="ico" viewBox="0 0 500 500" style="left:{45+i*202}px">{ART[a]}</svg>' for i, a in enumerate(ICON_ROW))
            body.append(f'<div id="{sid}-a{bi}" class="clip artrow" data-start="{st:.2f}" data-duration="{nxt_art-st:.2f}" data-track-index="2">{inner}</div>')
            js.append(f'tl.fromTo("#{sid}-a{bi} .ico",{{opacity:0,y:50}},{{opacity:1,y:0,duration:0.5,stagger:0.22,ease:"back.out(1.6)"}},{st+0.1:.2f});')
            js.append(f'tl.fromTo("#{sid}-a{bi} .ln",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.9,stagger:0.03,ease:"power2.inOut"}},{st+0.1:.2f});')
            continue
        if k > 0 and arts[k - 1][1] == art:
            # same drawing continues: only the effect changes
            fx_art(js, f"#{sid}-a{owner}", extra, st)
            continue
        owner = bi
        body.append(f'<div id="{sid}-a{bi}" class="clip art {extra}" data-start="{st:.2f}" data-duration="{nxt_art-st:.2f}" data-track-index="2">'
                    f'<svg viewBox="0 0 500 500">{ART[art]}</svg></div>')
        sel = f"#{sid}-a{bi}"
        a0 = 1 if (sid == "s01" and st == 0) else 0
        d0 = 0.25 if a0 else 1
        js.append(f'tl.fromTo("{sel} svg",{{opacity:{a0},scale:0.94}},{{opacity:1,scale:1,duration:0.45,ease:"power2.out"}},{st:.2f});')
        js.append(f'tl.fromTo("{sel} .ln",{{strokeDashoffset:{d0}}},{{strokeDashoffset:0,duration:{1.3 if extra not in ("brand","endcard") else 1.0},stagger:0.05,ease:"power2.inOut"}},{st:.2f});')
        if nxt_art < dur:
            js.append(f'tl.to("{sel} svg",{{opacity:0,scale:1.04,duration:0.22,ease:"power2.in"}},{nxt_art-0.24:.2f});')
        fx_art(js, sel, extra, st)
    if sid == "s17":
        for n, seg in enumerate((28, 30)):
            i0 = idx(seg); i1 = max(i for i, w in enumerate(W) if w["seg"] == seg + (1 if seg == 28 else 0))
            txt = T(i0, i1)
            cls = "tag" if n == 0 else "mot"
            st2 = t0(i0) - s["start"] - 0.05
            body.append(f'<div id="{sid}-{cls}" class="clip {cls}" data-start="{st2:.2f}" data-duration="{dur-st2:.2f}" data-track-index="4"><span class="in">{html.escape(txt)}</span></div>')
            js.append(f'tl.fromTo("#{sid}-{cls} .in",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.6,ease:"power3.out"}},{st2:.2f});')
        if True:
            # the second half of the tagline lights up on its own words
            pass
    # chips for street-children scene
    if any(len(b) > 4 and b[4] == "chips" for b in beats):
        i0 = idx(14)
        chips = [(i0 + 2, i0 + 2), (i0 + 3, i0 + 3), (i0 + 5, i0 + 6)]
        cs = "".join(f'<span class="chip" id="{sid}-c{n}">{html.escape(T(a, b).rstrip(","))}</span>' for n, (a, b) in enumerate(chips))
        body.append(f'<div id="{sid}-chips" class="clip chips" data-start="0" data-duration="{dur:.2f}" data-track-index="4">{cs}</div>')
        for n, (a, b) in enumerate(chips):
            js.append(f'tl.fromTo("#{sid}-c{n}",{{opacity:0,scale:0.6,y:20}},{{opacity:1,scale:1,y:0,duration:0.35,ease:"back.out(2)"}},{t0(a)-s["start"]-0.03:.2f});')
    # words that stack in the community scene
    if any(len(b) > 4 and b[4] == "stack" for b in beats):
        i0 = idx(26)
        ws = [(i0 + 3, i0 + 3), (i0 + 4, i0 + 4), (i0 + 6, i0 + 6)]
        cs = "".join(f'<span class="stk" id="{sid}-k{n}">{html.escape(T(a, b).rstrip(","))}</span>' for n, (a, b) in enumerate(ws))
        body.append(f'<div id="{sid}-stack" class="clip stack" data-start="0" data-duration="{dur:.2f}" data-track-index="4">{cs}</div>')
        for n, (a, b) in enumerate(ws):
            js.append(f'tl.fromTo("#{sid}-k{n}",{{opacity:0,y:40,scale:1.2}},{{opacity:1,y:0,scale:1,duration:0.4,ease:"power3.out"}},{t0(a)-s["start"]-0.03:.2f});')
    if sid == "s16":
        # each person lights up in turn
        js.append(f'tl.fromTo("#{sid}-a0 g",{{opacity:0.25}},{{opacity:1,duration:0.4,stagger:0.45,ease:"sine.out"}},0.6);')
    return f"""<template>
<style>
{FONTS}
#root{{position:absolute;inset:0;overflow:hidden;font-family:'Anek Bangla',sans-serif;}}
#{sid}-in{{position:absolute;inset:0;}}
#root .bg{{position:absolute;inset:0;}}
#{sid}-cam{{position:absolute;inset:0;transform-origin:50% 46%;}}
#{sid}-rays{{position:absolute;left:-460px;top:-560px;width:2000px;height:2000px;transform-origin:50% 50%;
  background:repeating-conic-gradient(from 0deg at 50% 50%,rgba(255,206,140,0.10) 0deg 4deg,rgba(255,206,140,0) 4deg 13deg);
  -webkit-mask:radial-gradient(circle at 50% 50%,#000 0%,rgba(0,0,0,0.5) 30%,transparent 62%);mask:radial-gradient(circle at 50% 50%,#000 0%,rgba(0,0,0,0.5) 30%,transparent 62%);}}
#root .bk{{position:absolute;border-radius:50%;}}
#root .art{{position:absolute;left:230px;top:545px;width:620px;height:620px;}}
#root .art.brand,#root .art.endcard{{left:300px;top:230px;width:480px;height:480px;}}
#root .art svg{{width:100%;height:100%;overflow:visible;}}
#root .artrow{{position:absolute;left:0;top:760px;width:1080px;height:220px;}}
#root .ico{{position:absolute;top:0;width:200px;height:200px;overflow:visible;}}
#root .ln{{fill:none;stroke:{GOLD};stroke-width:7;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1 1;filter:url(#{sid}-glow);}}
#root .ico .ln{{stroke-width:12;}}
#root .ln.dim{{stroke:rgba(255,196,107,0.45);stroke-width:5;}}
#root .art.cold .ln{{stroke:#cfe0f5;}}
#root .head{{position:absolute;left:90px;right:90px;top:250px;height:330px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}}
#root .hl{{display:block;font-weight:800;font-size:112px;line-height:1.22;color:#fff;letter-spacing:-0.005em;
  text-shadow:0 6px 30px rgba(0,0,0,0.55),0 0 2px rgba(0,0,0,0.6);}}
#root .hl.gold{{color:#FFC46B;text-shadow:0 0 38px rgba(255,170,60,0.55),0 6px 26px rgba(0,0,0,0.5);}}
#root .head.brand{{top:730px;height:280px;}}
#root .head.brand .hl{{font-size:104px;}}
#root .chap{{position:absolute;left:0;right:0;top:200px;height:60px;display:flex;align-items:center;justify-content:center;gap:22px;}}
#root .chn{{font-weight:700;font-size:46px;color:#FFC46B;letter-spacing:0.08em;}}
#root .chl{{display:block;width:120px;height:4px;background:linear-gradient(90deg,#FFC46B,rgba(255,196,107,0));transform-origin:0 50%;}}
#root .chips{{position:absolute;left:60px;right:60px;top:560px;display:flex;flex-wrap:wrap;justify-content:center;gap:18px;}}
#root .chip{{display:inline-block;padding:12px 30px 8px;border-radius:60px;border:3px solid rgba(255,196,107,0.85);background:rgba(20,12,4,0.55);color:#FFE3B5;font-weight:700;font-size:50px;}}
#root .stack{{position:absolute;left:0;right:0;top:470px;display:flex;justify-content:center;gap:26px;}}
#root .tag{{position:absolute;left:60px;right:60px;top:1035px;text-align:center;font-weight:700;font-size:66px;color:#FFE3B5;}}
#root .mot{{position:absolute;left:60px;right:60px;top:1150px;text-align:center;font-weight:800;font-size:92px;color:#FFC46B;text-shadow:0 0 36px rgba(255,170,60,0.55);}}
#root .tag .in,#root .mot .in{{display:inline-block;}}
#root .stk{{font-weight:800;font-size:70px;color:#FFC46B;text-shadow:0 0 30px rgba(255,170,60,0.5);}}
{s["extra"]}
</style>
<div id="root" data-composition-id="{sid}" data-width="1080" data-height="1920">
<svg width="0" height="0" style="position:absolute"><defs><filter id="{sid}-glow" x="-50%" y="-50%" width="200%" height="200%">
<feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs></svg>
<div id="{sid}-in">
<div class="bg" style="background:radial-gradient(120% 75% at 50% 42%,{c1} 0%,{c2} 78%)"></div>
{body.pop(0) if s["end_mood"] else ""}
<div id="{sid}-cam">
<div id="{sid}-rays"></div>
<div id="{sid}-bk">{bokeh(rng, 16, warm)}</div>
{"".join(body)}
</div></div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["{sid}"] = tl;
</script>
</template>
"""


def fx_art(js, sel, extra, st):
    if extra == "dark":  # dream fades: stars go out one by one
        js.append(f'tl.to("{sel} .st",{{opacity:0.12,duration:0.35,stagger:0.18,ease:"power2.in"}},{st+0.2:.2f});')
        js.append(f'tl.to("{sel} svg",{{filter:"saturate(0.2) brightness(0.7)",duration:1.2}},{st:.2f});')
    if extra == "ignite":
        js.append(f'tl.fromTo("{sel} .fl",{{scale:0.2,transformOrigin:"50% 100%"}},{{scale:1,duration:0.6,ease:"back.out(2.5)"}},{st+0.55:.2f});')
    if extra == "spread":
        js.append(f'tl.fromTo("{sel} .fan",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:1.4,stagger:0.12,ease:"power2.out"}},{st:.2f});')
    if extra == "dropwait":
        js.append(f'tl.set("{sel} .rp",{{opacity:0}},{st:.2f});')
    if extra == "drop":
        js.append(f'tl.fromTo("{sel} .cn",{{y:-60}},{{y:180,duration:0.6,ease:"power2.in"}},{st+0.6:.2f});')
        js.append(f'tl.to("{sel} .cn",{{opacity:0,duration:0.15}},{st+1.2:.2f});')
        js.append(f'tl.fromTo("{sel} .rp",{{opacity:0,scale:0.3,transformOrigin:"250px 330px"}},{{opacity:1,scale:1,duration:1.6,stagger:0.25,ease:"sine.out"}},{st+1.2:.2f});')
    if extra == "waves":
        js.append(f'tl.to("{sel} .rp",{{scale:1.9,strokeWidth:9,duration:1.8,stagger:0.1,ease:"power2.out"}},{st:.2f});')
    if extra == "lights":
        js.append(f'tl.fromTo("{sel} .fl",{{opacity:0}},{{opacity:1,duration:0.3,stagger:0.5,ease:"power2.out"}},{st+0.9:.2f});')


import re
def fix_cls(h):
    return re.sub(r'class="ln" class="ln ([^"]*)"', r'class="ln \1"', h)


rng = random.Random(7)
os.makedirs(os.path.join(ROOT, "compositions"), exist_ok=True)
for s in SC:
    open(os.path.join(ROOT, "compositions", s["id"] + ".html"), "w", encoding="utf-8").write(fix_cls(build_scene(s, rng)))

# ---------------------------------------------------------------- captions
SKIP_SEGS = {11, 27, 28, 29, 30}  # brand and end card already show these exact lines large
groups, cur = [], []
for w in W:
    if w["seg"] in SKIP_SEGS:
        continue
    if cur and (w["seg"] != cur[-1]["seg"] or len(cur) >= 3 or cur[-1]["text"].endswith((",", "।"))):
        groups.append(cur); cur = []
    cur.append(w)
groups.append(cur)
cap_body, cap_js = [], []
for gi, g in enumerate(groups):
    st = max(g[0]["start"] - 0.08, 0.1)
    nxt = groups[gi + 1][0]["start"] - 0.08 if gi + 1 < len(groups) else TOTAL
    en = min(g[-1]["end"] + 0.35, nxt)
    spans = "".join(f'<span class="cw" id="cw{w["id"][1:]}">{html.escape(w["text"])}</span> ' for w in g)
    cap_body.append(f'<div id="cg{gi}" class="clip cg" data-start="{st:.2f}" data-duration="{en-st:.2f}" data-track-index="0"><div class="cgi">{spans.strip()}</div></div>')
    cap_js.append(f'tl.fromTo("#cg{gi} .cgi",{{opacity:0,y:24,scale:0.96}},{{opacity:1,y:0,scale:1,duration:0.18,ease:"power2.out"}},{st:.2f});')
    for w in g:
        sel = f'#cw{w["id"][1:]}'
        cap_js.append(f'tl.fromTo("{sel}",{{color:"#ffffff",scale:1}},{{color:"#FFC46B",scale:1.08,duration:0.08,ease:"power1.out"}},{w["start"]:.3f});')
        if w is not g[-1]:
            cap_js.append(f'tl.to("{sel}",{{color:"#ffffff",scale:1,duration:0.1}},{w["end"]:.3f});')
    cap_js.append(f'tl.to("#cg{gi} .cgi",{{opacity:0,duration:0.12,ease:"power2.in"}},{en-0.12:.2f});')
open(os.path.join(ROOT, "compositions", "captions.html"), "w", encoding="utf-8").write(f"""<template>
<style>
{FONTS}
#root{{position:absolute;inset:0;font-family:'Anek Bangla',sans-serif;}}
#root .cg{{position:absolute;left:0;right:0;top:1170px;height:170px;display:flex;align-items:center;justify-content:center;}}
#root .cgi{{max-width:880px;text-align:center;font-weight:700;font-size:78px;line-height:1.18;color:#fff;
  padding:10px 34px 4px;border-radius:26px;background:rgba(6,4,2,0.38);}}
#root .cw{{display:inline-block;margin:0 0.13em;transform-origin:50% 70%;text-shadow:0 4px 18px rgba(0,0,0,0.75);}}
</style>
<div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(cap_body)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cap_js)}
window.__timelines["captions"] = tl;
</script>
</template>
""")

# ---------------------------------------------------------------- finishing layer: vignette + light leak + letterbox fades
open(os.path.join(ROOT, "compositions", "finish.html"), "w", encoding="utf-8").write(f"""<template>
<style>
#root{{position:absolute;inset:0;pointer-events:none;}}
#fin-vig{{position:absolute;inset:0;background:radial-gradient(110% 70% at 50% 45%,rgba(0,0,0,0) 55%,rgba(0,0,0,0.6) 100%);}}
#fin-leak{{position:absolute;left:-300px;top:-200px;width:900px;height:900px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,170,80,0.22) 0%,rgba(255,120,40,0.08) 40%,rgba(255,120,40,0) 70%);}}
#fin-fade{{position:absolute;inset:0;background:#000;}}
</style>
<div id="root" data-composition-id="finish" data-width="1080" data-height="1920">
<div id="fin-leak" data-layout-ignore></div><div id="fin-vig" data-layout-ignore></div><div id="fin-fade" data-layout-ignore></div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
tl.fromTo("#fin-leak",{{x:0,y:0,opacity:0.5}},{{x:700,y:1300,opacity:1,duration:{TOTAL},ease:"none"}},0);
tl.fromTo("#fin-fade",{{opacity:0}},{{opacity:0,duration:0.01}},0);
tl.to("#fin-fade",{{opacity:1,duration:1.0,ease:"sine.in"}},{TOTAL-1.05});
window.__timelines["finish"] = tl;
</script>
</template>
""")

# ---------------------------------------------------------------- index
hosts = []
for n, s in enumerate(SC):
    dur = s["end"] - s["start"] + (X if s["end"] < TOTAL else 0)
    hosts.append(f'<div id="{s["id"]}" data-composition-id="{s["id"]}" data-composition-src="compositions/{s["id"]}.html" data-start="{s["start"]:.2f}" '
                 f'data-duration="{dur:.2f}" data-track-index="{1 + n % 2}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:{n+1}"></div>')

SFX = [  # (file, picture time, peak offset in file, volume)
    ("whoosh", SC[1]["start"] + 0.1, 0.162, 0.32),
    ("whoosh-short", SC[2]["start"] + 0.1, 0.162, 0.26),
    ("whoosh", SC[3]["start"] + 0.1, 0.162, 0.26),
    ("sparkle", t0(idx(8)) + 0.55, 0.027, 0.30),
    ("riser", t0(idx(11)) - 0.02, 3.472, 0.22),
    ("impact-bass-1", t0(idx(11)) + 0.03, 0.073, 0.55),
    ("whoosh-short", SC[5]["start"] + 0.1, 0.162, 0.26),
] + [(("whoosh", "whoosh-short")[k % 2], SC[6 + k]["start"] + 0.1, 0.162, 0.24) for k in range(5)] + [
    ("pop", t0(idx(14) + 2) - 0.03, 0.12, 0.30),
    ("pop", t0(idx(14) + 3) - 0.03, 0.12, 0.26),
    ("pop", t0(idx(14) + 5) - 0.03, 0.12, 0.30),
    ("whoosh", SC[11]["start"] + 0.1, 0.162, 0.26),
    ("sparkle", t0(idx(19)) + 0.1, 0.027, 0.24),
    ("whoosh-short", SC[12]["start"] + 0.1, 0.162, 0.24),
    ("impact-bass-2", t0(idx(21)) + 1.2, 1.986, 0.30),
    ("whoosh", SC[13]["start"] + 0.1, 0.162, 0.24),
    ("sparkle", t0(idx(22)) + 0.9, 0.027, 0.22),
    ("whoosh-short", SC[14]["start"] + 0.1, 0.162, 0.24),
    ("whoosh", SC[15]["start"] + 0.1, 0.162, 0.24),
    ("whoosh-cinematic", SC[16]["start"] + 0.1, 2.503, 0.30),
    ("sparkle", t0(idx(27)) + 0.1, 0.027, 0.26),
]
import subprocess
DUR = {f: round(float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',os.path.join(ROOT,'assets','sfx',f+'.mp3')])) - 0.01, 2) for f in {x[0] for x in SFX}}
aud = []
for k, (f, at, pk, vol) in enumerate(SFX):
    st = round(at - pk + 1 / 30, 3)
    ln = DUR[f]
    aud.append(f'<audio id="sfx{k}" class="clip" src="assets/sfx/{f}.mp3" data-start="{st}" data-duration="{ln}" data-track-index="{11 + k}" data-volume="{vol}"></audio>')

open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(f"""<!doctype html>
<html lang="bn">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#05070b; }}
#root {{ position:relative; width:1080px; height:1920px; background:#05070b; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
{chr(10).join(hosts)}
<div id="finish" data-composition-id="finish" data-composition-src="compositions/finish.html" data-start="0" data-duration="{TOTAL}" data-track-index="3" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:50"></div>
<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{TOTAL}" data-track-index="4" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:60"></div>
<audio id="voice" class="clip" src="assets/voice.mp3" data-start="0" data-track-index="10" data-volume="1"></audio>
{chr(10).join(aud)}
</div>
<script>
window.__timelines["main"] = gsap.timeline({{ paused: true }});
</script>
</body>
</html>
""")
print("scenes", len(SC), "caption groups", len(groups), "sfx", len(SFX))
