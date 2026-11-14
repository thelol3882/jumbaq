"""Builds docs/images/hero.svg: outlined text (an SVG in an <img> cannot load fonts), CSS animation,
and the final state as the base style, so a viewer without animation sees the finished picture."""
import re, sys, pathlib
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

F = pathlib.Path(sys.argv[1])  # node_modules/@fontsource
fonts = {
    "type": TTFont(F / "courier-prime/files/courier-prime-latin-700-normal.woff"),
    "typer": TTFont(F / "courier-prime/files/courier-prime-latin-400-normal.woff"),
    "story": TTFont(F / "literata/files/literata-latin-700-normal.woff"),
    "storyr": TTFont(F / "literata/files/literata-latin-400-normal.woff"),
    "hand": TTFont(F / "kalam/files/kalam-latin-400-normal.woff"),
}

def text(s, font, size, x, y, anchor="start", spacing=0.0):
    """Returns (path data, width). Baseline at y."""
    f = fonts[font]; gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm; k = size / upm
    adv = []; names = []
    for ch in s:
        g = cmap.get(ord(ch)) or cmap.get(ord("?")); names.append(g); adv.append(gs[g].width * k + spacing)
    w = sum(adv)
    cx = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
    d = []
    for g, a in zip(names, adv):
        pen = SVGPathPen(gs); gs[g].draw(TransformPen(pen, (k, 0, 0, -k, cx, y))); d.append(pen.getCommands()); cx += a
    return "".join(d), w

def P(s, font, size, x, y, fill, cls="", anchor="start", spacing=0.0, extra=""):
    d, w = text(s, font, size, x, y, anchor, spacing)
    d = re.sub(r"(\d+\.\d{2})\d+", r"\1", d)
    return f'<path class="{cls}" fill="{fill}" d="{d}" {extra}/>', w

W, H = 1280, 490
PAPER, DOTS, INK, MUTE, RED, BLUE, MANILA, EDGE, CARD, RULE = "#F4F3EC", "#C2C5CB", "#2B2B2B", "#55555A", "#B3261E", "#24478A", "#E3C98F", "#9A8350", "#FFFFFC", "#D7D6CE"
mark = pathlib.Path(sys.argv[2]).read_text()
mark_inner = re.search(r"<g>(.*)</g>", mark, re.S).group(1)

o = []
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
o.append('<title id="t">jumbaq</title><desc id="d">jumbaq, a detective story your kids solve by searching the room you are sitting in. The evidence tag swings in, the name is typed, and two of three suspects are crossed out in red pencil.</desc>')
css = """
.a{animation-duration:.5s;animation-fill-mode:both;animation-timing-function:cubic-bezier(.2,.8,.2,1)}
@keyframes in{from{opacity:0;transform:translateY(14px)}}
@keyframes fade{from{opacity:0}}
@keyframes swing{0%{opacity:0;transform:rotate(-38deg)}30%{opacity:1}55%{transform:rotate(14deg)}75%{transform:rotate(-6deg)}90%{transform:rotate(2deg)}}
@keyframes draw{from{stroke-dashoffset:var(--l)}}
@keyframes stamp{0%{opacity:0;transform:scale(1.7) rotate(-5deg)}100%{opacity:1;transform:scale(1) rotate(-5deg)}}
.mk{transform-origin:113px 104px;animation:swing 1.3s .1s both ease-out}
.in{animation-name:in}.fd{animation-name:fade}
.dr{stroke-dasharray:var(--l);animation:draw .55s both ease-in-out}
.st{transform-box:fill-box;transform-origin:center;transform:rotate(-5deg);animation:stamp .3s both cubic-bezier(.6,0,.9,.4)}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""
o.append(f"<style>{css}</style>")
o.append(f'<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="12" cy="12" r="1.2" fill="{DOTS}"/></pattern></defs>')
o.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/><rect width="{W}" height="{H}" fill="url(#dots)"/><rect x="56" width="1.5" height="{H}" fill="#D98A80"/>')

# mark: 64x64 source, hole at (32,11); scaled 2.3 and placed so the hole is the pivot
o.append(f'<g class="mk"><g transform="translate(39.4,78.7) scale(2.3)">{mark_inner}</g></g>')

# wordmark typed letter by letter
x = 208
for i, ch in enumerate("jumbaq"):
    p, w = P(ch, "type", 132, x, 196, RED if i == 0 else INK, "a fd", extra=f'style="animation-delay:{0.9 + i * 0.11:.2f}s;animation-duration:.01s"')
    o.append(p); x += w - 6
p, _ = P("means “riddle” in Kazakh", "hand", 26, 330, 250, BLUE, "a fd", extra='style="animation-delay:1.9s" transform="rotate(-2 330 250)"')
o.append(p)

# headline
lines = ["A detective story your kids solve", "by searching the room", "you\u2019re sitting in."]
for i, line in enumerate(lines):
    p, w = P(line, "story", 39, 84, 306 + i * 48, INK, "a in", extra=f'style="animation-delay:{2.2 + i * 0.15:.2f}s"')
    o.append(p)
_, w0 = text("you\u2019re ", "story", 39, 0, 0); _, w1 = text("sitting in.", "story", 39, 0, 0)
ux, uy = 84 + w0, 306 + 2 * 48 + 12
o.append(f'<path class="dr" d="M{ux:.0f},{uy} C{ux + w1 * 0.3:.0f},{uy - 6} {ux + w1 * 0.65:.0f},{uy + 7} {ux + w1 + 6:.0f},{uy - 2}" fill="none" stroke="{RED}" stroke-width="4.5" stroke-linecap="round" style="--l:{int(w1 + 20)};animation-delay:3s"/>')
p, _ = P("no sign-up \u00b7 first case free \u00b7 jumbaq.fun", "typer", 21, 84, 456, MUTE, "a fd", extra='style="animation-delay:3.3s"')
o.append(p)

# the case board on the right
bx, by, bw = 800, 80, 410
o.append(f'<g class="a in" style="animation-delay:2.4s"><rect x="{bx}" y="{by}" width="{bw}" height="330" fill="{CARD}" stroke="{INK}" stroke-width="2.5"/>')
o.append(f'<rect x="{bx + bw / 2 - 52}" y="{by - 15}" width="104" height="28" fill="#EBE1A9" transform="rotate(-2 {bx + bw / 2} {by})"/>')
p, _ = P("EVENING 3 OF 5", "type", 14, bx + 26, by + 44, RED, spacing=1.6); o.append(p)
p, _ = P("The Case of the", "story", 27, bx + 26, by + 82, INK); o.append(p)
p, _ = P("Missing Magic Wand", "story", 27, bx + 26, by + 114, INK); o.append(p)
p, _ = P("SUSPECTS", "typer", 13, bx + 26, by + 156, MUTE, spacing=1.6); o.append(p)
o.append(f'<rect x="{bx + 26}" y="{by + 168}" width="{bw - 52}" height="138" fill="#FBFAF5" stroke="{INK}" stroke-width="2"/>')
for i in (1, 2):
    o.append(f'<rect x="{bx + 26}" y="{by + 168 + i * 46}" width="{bw - 52}" height="1.5" fill="{RULE}"/>')
o.append("</g>")
rows = [("Pippa the Clown", "cleared", 3.6), ("Bruno the Bear", "cleared", 4.5), ("Zara the Acrobat", "still a suspect", None)]
for i, (name, note, t) in enumerate(rows):
    y = by + 168 + i * 46 + 30
    p, w = P(name, "type", 19, bx + 42, y, "#6E6E73" if t else INK, "a fd", extra='style="animation-delay:2.7s"'); o.append(p)
    p, _ = P(note, "hand", 18, bx + bw - 42, y, BLUE, "a fd", anchor="end", extra=f'style="animation-delay:{(t + 0.5) if t else 2.7}s"'); o.append(p)
    if t:
        o.append(f'<path class="dr" d="M{bx + 38},{y - 5} C{bx + 38 + w * 0.35},{y - 10} {bx + 38 + w * 0.7},{y - 1} {bx + 48 + w},{y - 7}" fill="none" stroke="{RED}" stroke-width="3" stroke-linecap="round" style="--l:{int(w + 30)};animation-delay:{t}s"/>')
# stamp
sx, sy = bx + bw - 150, by + 330 - 14
p, sw = P("CASE OPEN", "type", 17, sx + 14, sy + 25, RED, spacing=2.2)
o.append(f'<g class="st" style="animation-delay:5.4s"><rect x="{sx}" y="{sy}" width="{sw + 28}" height="38" fill="{PAPER}" stroke="{RED}" stroke-width="3"/>{p}</g>')
o.append("</svg>")
out = pathlib.Path(sys.argv[3]); out.write_text("".join(o)); print(out, out.stat().st_size // 1024, "KB")
