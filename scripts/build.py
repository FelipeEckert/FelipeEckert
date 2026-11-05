"""Build the animated SVGs used by README.md.

Run from the repo root:  python scripts/build.py
Needs Pillow and fontTools (pip install pillow fonttools).
Edit the content below, re-run, commit the files in assets/.
GitHub shows SVGs as images, so everything (sprites, font) is embedded inline.
The pixel font is subset per file, so each SVG only carries the glyphs it uses.
"""
import base64
import html
import io
import random
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "assets" / "src", ROOT / "assets"

RAIN = "|'|./"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
NAVY, PANEL, BAR, EDGE, VOLT, BLUE = "#0b1324", "#0f1a2e", "#13233f", "#2b4470", "#ffcb05", "#2a75bb"
INK, MUTED = "#e8f0ff", "#a9bddf"
W = 840  # width of every section card

# ---------------------------------------------------------------- content
HEADER_LABEL = "SOFTWARE & DATA DEVELOPMENT"
HEADER_LINE = "> python · react · data products"

# **text** is drawn bright; the rest in the muted body color.
WHOAMI = [
    "I build **data products end to end**: from raw files and sensors to validated pipelines, "
    "models, web apps, and the report someone actually reads.",
    "At **Hyundai Motor Brasil** (R&D, Energy Efficiency & Data Analytics) I designed and shipped "
    "an internal analysis app (Python, Streamlit, SQLite) that cut analysis time by ~80% and became a paper at SIMEA 2026.",
    "Electrical Engineer from **Poli-USP**. Six years on the **BAJA SAE** team, where I helped build "
    "the car's telemetry data logger.",
    "Currently leveling up **SQL** and **Power BI**; next up: **Databricks**.",
    "**Portuguese** (native) · **English** (C1) · **Spanish** (B1)",
]

SKILLS = {
    "name": "FELIPE", "level": "25", "item": "Data Logger",
    "hp": ("Python", 120, 120),
    "stats": [("React", 110), ("Validation", 115), ("ML", 90), ("Data Pipelines", 125),
              ("Automation", 118), ("Agentic AI Workflow", 112)],
    "ability": "Resilience",
    "desc": ["Keeps results reliable", "when the data gets rough."],
    "next": "SQL · POWER BI · DATABRICKS",
}
STACK = ["python", "javascript", "react", "vite", "claude code", "github actions", "pandas", "numpy",
         "scikit-learn", "xgboost", "plotly", "streamlit", "jupyter", "sqlite", "git", "matlab"]
DOMAINS = ("Test and measurement data · sensor and time-series data · embedded data acquisition "
           "(STM32, CAN bus) · automotive R&D. I pick up new business domains quickly.")

PROJECTS = [
    ("finale", "One-knob mastering plugin (VST3) for music producers: C++ audio engine, loudness and "
     "tonal assistants, Catch2 tests and CI. Built Claude-first with a friend.", "c++ · juce · ci"),
    ("coastdown-analysis", "Streamlit app that automates vehicle coastdown tests (NBR 10312). "
     "~80% less analysis time. Code private.", "published at SIMEA 2026"),
    ("f1-laptime-prediction", "End-to-end ML on real F1 telemetry: FastF1, leave-one-race-out validation, "
     "XGBoost + SHAP.", "python · ml"),
    ("felipeeckert.github.io", "React + Vite site with scroll-driven canvas motion.", "web"),
]

ACHIEVEMENTS = [
    ("2026", "**1st place, Hyundai Prompt-a-thon**: an R&D Automotive Intelligence Hub on Microsoft 365 "
     "Copilot that consolidates multi-source information into executive reports."),
    ("2026", "**Paper at XXXIII SIMEA**: Data-Driven Coastdown Analysis: Automated Data Processing and "
     "Predictive Modeling for Vehicle Road Load and Energy Efficiency Assessment. J. W. P. Silva, "
     "F. A. Eckert. Blucher Engineering Proceedings, vol. 13, pp. 760–768."),
    ("2023", "**Undergraduate thesis, Poli-USP**: Sistema de aquisição de dados para protótipos off-road "
     "(data acquisition system for off-road prototypes)."),
]

# Small link pills: header contact links and the "open" links under some cards.
LINKS = {"linkedin": "linkedin", "portfolio": "portfolio", "researchgate": "researchgate", "email": "email",
         "finale": "finale", "coastdown-paper": "coastdown paper", "f1": "f1-laptime-prediction",
         "site": "portfolio site", "simea-paper": "simea paper", "thesis": "thesis"}

# ---------------------------------------------------------------- font
FONT_PATH = SRC / "PixelifySans.ttf"
FONT = TTFont(FONT_PATH)
CMAP, HMTX, UPM = FONT.getBestCmap(), FONT["hmtx"], FONT["head"].unitsPerEm


def text_width(s, size, bold=False):
    adv = sum(HMTX[CMAP.get(ord(c), CMAP[32])][0] for c in s) * size / UPM
    return adv * (1.06 if bold else 1)  # the 700 weight runs a little wider


def font_face(chars):
    """Pixelify Sans (variable 400-700) subset to the characters this file uses, as WOFF."""
    opts = subset.Options()
    opts.flavor, opts.layout_features, opts.notdef_outline = "woff", ["*"], True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes={ord(c) for c in chars} | {32})
    f = TTFont(FONT_PATH)
    sub.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff"
    f.save(buf)
    uri = "data:font/woff;base64," + base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'Pixelify';src:url({uri}) format('woff');font-weight:400 700}}"


PIX = f"'Pixelify',{MONO}"


# ---------------------------------------------------------------- helpers
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pesc(s):
    """Escape for pixel text; Pixelify's tilde reads as a dash, so draw it from the mono font."""
    return esc(s).replace("~", f'<tspan style="font-family:{MONO}">~</tspan>')


def b64(data, mime):
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def png_uri(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return b64(buf.getvalue(), "image/png")


def strip(gif):
    """GIF -> horizontal PNG strip, so CSS steps() can animate it (GIFs inside SVG images don't reliably animate)."""
    im = Image.open(SRC / gif)
    frames, total = [], 0
    for f in ImageSequence.Iterator(im):
        frames.append(f.convert("RGBA"))
        total += f.info.get("duration", 80) or 80
    w, h = frames[0].size
    sheet = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * w, 0))
    return {"uri": png_uri(sheet), "n": len(frames), "w": w, "h": h, "dur": total / 1000}


def sprite(s, cls, x, y, scale):
    """Animated sprite: a clipping <svg> window sliding over the strip."""
    w, h = s["w"] * scale, s["h"] * scale
    style = (f"@keyframes {cls}{{to{{transform:translateX(-{s['w'] * s['n']}px)}}}}"
             f".{cls}{{animation:{cls} {s['dur']:.2f}s steps({s['n']}) infinite}}")
    body = (f'<svg x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" viewBox="0 0 {s["w"]} {s["h"]}" overflow="hidden">'
            f'<image class="{cls}" href="{s["uri"]}" width="{s["w"] * s["n"]}" height="{s["h"]}" '
            f'image-rendering="optimizeSpeed" style="image-rendering:pixelated"/></svg>')
    return style, body


def used_chars(body):
    """Characters inside <text> elements, so the font subset covers exactly what is drawn."""
    found = "".join(re.findall(r"<text[^>]*>(.*?)</text>", body, flags=re.S))
    return set(html.unescape(re.sub(r"<[^>]+>", "", found)))


def svg(w, h, style, body, label, pixel=True):
    face = font_face(used_chars(body)) if pixel else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title><style>{face}text{{font-variant-ligatures:none;font-feature-settings:"liga" 0,"clig" 0}}{style}'
            f'@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>{body}</svg>')


def plain(s):
    return s.replace("**", "")


def runs(s):
    """'a **b**: c' -> [[(piece, bright), ...], ...]: one list per word, so 'b' + ':' stay glued."""
    words, cur = [], []
    for i, part in enumerate(s.split("**")):
        for k, chunk in enumerate(part.split(" ")):
            if k and cur:
                words.append(cur)
                cur = []
            if chunk:
                cur.append((chunk, i % 2 == 1))
    if cur:
        words.append(cur)
    return words


def wrap(s, size, width):
    lines, line, lw = [], [], 0.0
    space = text_width(" ", size)
    for word in runs(s):
        ww = sum(text_width(t, size, b) for t, b in word)
        if line and lw + space + ww > width:
            lines.append(line)
            line, lw = [], 0.0
        lw += (space if line else 0) + ww
        line.append(word)
    if line:
        lines.append(line)
    return lines


def rich_line(x, y, words, size, base=MUTED, bright=INK):
    """One <text> per line; bright pieces become bold tspans."""
    spans = []
    for i, word in enumerate(words):
        for k, (t, b) in enumerate(word):
            t = (" " if i and not k else "") + t
            if spans and spans[-1][1] == b:
                spans[-1][0] += t
            else:
                spans.append([t, b])
    parts = [f'<tspan fill="{bright}" font-weight="700">{pesc(t)}</tspan>' if b else pesc(t) for t, b in spans]
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{base}" font-size="{size}">{"".join(parts)}</text>'


def cursor(x, y, fill=VOLT, px=2.4):
    """Pokémon menu cursor: a small pixel triangle pointing right."""
    rows = ["#..", "##.", "###", "##.", "#.."]
    cells = "".join(f'<rect x="{x + k * px:.1f}" y="{y + r * px:.1f}" width="{px + .2:.1f}" height="{px + .2:.1f}" fill="{fill}"/>'
                    for r, row in enumerate(rows) for k, c in enumerate(row) if c == "#")
    return f'<g shape-rendering="crispEdges">{cells}</g>'


def window(h, title):
    """Section card frame: one rounded panel with a title strip."""
    return (f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="10" fill="{PANEL}" stroke="{EDGE}" stroke-width="2"/>'
            f'<path d="M2 11a9 9 0 0 1 9-9h{W - 22}a9 9 0 0 1 9 9v41H2z" fill="{BAR}"/>'
            f'<rect x="2" y="52" width="{W - 4}" height="2" fill="{EDGE}"/>'
            f'<text x="24" y="35" fill="{VOLT}" font-size="22" font-weight="700">{pesc(title)}</text>')


PAD_X, TOP = 26, 92  # left padding and first baseline under the title strip


# ---------------------------------------------------------------- pixel letters (header title)
GLYPH = {
    "F": ["######", "######", "##....", "#####.", "#####.", "##....", "##....", "##...."],
    "E": ["######", "######", "##....", "#####.", "#####.", "##....", "######", "######"],
    "L": ["##....", "##....", "##....", "##....", "##....", "##....", "######", "######"],
    "I": ["####", ".##.", ".##.", ".##.", ".##.", ".##.", ".##.", "####"],
    "P": ["#####.", "######", "##..##", "##..##", "######", "#####.", "##....", "##...."],
    "C": [".#####", "######", "##....", "##....", "##....", "##....", "######", ".#####"],
    "K": ["##..##", "##.##.", "####..", "###...", "###...", "####..", "##.##.", "##..##"],
    "R": ["#####.", "######", "##..##", "##..##", "#####.", "####..", "##.##.", "##..##"],
    "T": ["######", "######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."],
}
DIGITS = {
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."], "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"], "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."], "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."], "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."], "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
}


def rect(x, y, s, fill):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{s + .3:.1f}" height="{s + .3:.1f}" fill="{fill}"/>'


def pixel_word(word, px, arch, cx, top):
    """Pokémon-logo style: yellow fill, blue outline, navy drop shadow; letters step up toward the middle."""
    cells, x, n = {}, 0, len(word)
    for i, ch in enumerate(word):
        if ch == " ":
            x += 4
            continue
        g, t = GLYPH[ch], (i / (n - 1)) * 2 - 1
        dy = round(arch * t * t)
        for r, row in enumerate(g):
            for k, c in enumerate(row):
                if c == "#":
                    cells[(x + k, r + dy)] = r
        x += len(g[0]) + 2
    w = x - 2
    outline = set(cells)
    for (cx_, cy_) in cells:
        outline |= {(cx_ + dx, cy_ + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    shadow = {(a + sx, b + sy) for (a, b) in outline for sx, sy in ((1, 1), (1, 2), (0, 2))} - outline
    ox, oy = cx - w * px / 2, top + px
    out = [rect(ox + a * px, oy + b * px, px, "#13234a") for a, b in sorted(shadow)]
    out += [rect(ox + a * px, oy + b * px, px, BLUE) for a, b in sorted(outline - set(cells))]
    out += [rect(ox + a * px, oy + b * px, px, "#fff3a0" if r == 0 else "#e0a400" if r >= 6 else VOLT) for (a, b), r in sorted(cells.items())]
    bottom = oy + (max(b for _, b in outline) + 3) * px
    return f'<g shape-rendering="crispEdges">{"".join(out)}</g>', bottom


def number(x, base, s, fill, shade, px=2.2, align="end"):
    adv = 6 * px
    x0 = x - (len(s) * adv - px) if align == "end" else x
    y0 = base - 7 * px
    a, b = [], []
    for i, ch in enumerate(s):
        for r, row in enumerate(DIGITS[ch]):
            for k, c in enumerate(row):
                if c == "#":
                    X, Y = x0 + i * adv + k * px, y0 + r * px
                    a.append(f'<rect x="{X + px:.1f}" y="{Y + px:.1f}" width="{px}" height="{px}" fill="{shade}"/>')
                    b.append(f'<rect x="{X:.1f}" y="{Y:.1f}" width="{px}" height="{px}" fill="{fill}"/>')
    return f'<g shape-rendering="crispEdges">{"".join(a + b)}</g>'


# ---------------------------------------------------------------- header
def header(lux, woo):
    CW, LH, HW = 8.4, 17, 66 * 8.4
    rnd = random.Random(7)
    name, b = pixel_word("FELIPE ECKERT", 5.2, 4, HW / 2, 26)
    H = b + 292
    rain_css = f"@keyframes fall{{from{{transform:translateY(-34px)}}to{{transform:translateY({H:.0f}px)}}}}"
    drops = []
    for i in range(70):
        d = rnd.uniform(1, 1.9)
        drops.append(f'<text class="m" x="{rnd.randrange(66) * CW:.1f}" y="0" fill="#5b86d6" opacity="{rnd.uniform(.25, .7):.2f}" '
                     f'style="animation:fall {d:.2f}s linear {-rnd.uniform(0, d):.2f}s infinite">{RAIN[i % 5]}</text>')
    bolt = "".join(f'<text class="m" x="{32 * CW:.1f}" y="{b + 90 + i * LH:.1f}" fill="#fff6c8" font-weight="700">{esc(l)}</text>'
                   for i, l in enumerate(["   /", "  /", " /_", "  /", " /", "'"]))
    lcss, lsvg = sprite(lux, "lux", 2 * CW, b + 78, 2.7)
    wcss, wsvg = sprite(woo, "woo", 45 * CW, b + 161, 2.7)
    label_w = text_width(HEADER_LABEL, 15, True) + 15 * 0.18 * len(HEADER_LABEL) + 36
    style = (rain_css + lcss + wcss +
             "@keyframes fl{0%,58%,61%,63%,100%{opacity:0}59%,62%{opacity:.45}}.fl{animation:fl 7s infinite}"
             "@keyframes bo{0%,58%,64%,100%{opacity:0}59%,63%{opacity:1}}.bo{animation:bo 7s infinite}"
             "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1s step-end infinite}"
             f"text{{font-family:{PIX};white-space:pre}}text.m{{font-family:{MONO}}}")
    body = (f'<rect width="{HW:.1f}" height="{H:.1f}" rx="10" fill="{NAVY}"/><g font-size="14">{"".join(drops)}{name}'
            f'<rect x="{HW / 2 - label_w / 2:.1f}" y="{b + 9:.1f}" width="{label_w:.1f}" height="28" rx="4" fill="{BLUE}" stroke="{VOLT}" stroke-width="2"/>'
            f'<text x="{HW / 2:.1f}" y="{b + 28:.1f}" fill="#ffffff" font-size="15" font-weight="700" letter-spacing="2.7" text-anchor="middle">{esc(HEADER_LABEL)}</text>'
            f'<text x="{HW / 2:.1f}" y="{b + 68:.1f}" fill="#9fb3d6" font-size="16" text-anchor="middle">{esc(HEADER_LINE)}<tspan class="cur" fill="{VOLT}"> _</tspan></text>'
            f'<g class="bo">{bolt}</g>{lsvg}'
            f'<text class="m" x="{CW:.1f}" y="{b + 266:.1f}" fill="{EDGE}">________________________________</text>{wsvg}'
            f'<text class="m" x="{42 * CW:.1f}" y="{b + 266:.1f}" fill="#3d6fae">~~ ~~~~~~~~~~~~~~~~ ~~</text></g>'
            f'<rect class="fl" width="{HW:.1f}" height="{H:.1f}" rx="10" fill="#e8f0ff" opacity="0"/>')
    return svg(HW, H, style, body, f"Felipe Eckert, {HEADER_LABEL.title().replace('&', '&')}: pixel-art title in the rain with Luxray and Wooper")


# ---------------------------------------------------------------- Pokémon Platinum summary card
def summary(lucas, pory):
    """Returns (style, body, height) for a 512-wide trainer card drawn at the origin."""
    S = SKILLS
    n = len(S["stats"])
    sy = 32 * (n - 5)  # extra height for stat rows beyond the original five
    vx = 414          # value boxes start here, leaving room for long stat names

    def t(x, y, s, fill, shade, size=20, anchor="start"):
        return (f'<text x="{x + 2}" y="{y + 2}" fill="{shade}" font-size="{size}" text-anchor="{anchor}">{esc(s)}</text>'
                f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" text-anchor="{anchor}">{esc(s)}</text>')

    tabs = ""
    for i, c in enumerate(["#58c060", "#40b8d0", "#e04848", "#f07890", "#d068e0", "#f0d040", "#f0a8b8", "#b0a888"]):
        on = i == 2
        tabs += (f'<rect x="{222 + i * 36}" y="{34 if on else 38}" width="32" height="{28 if on else 24}" rx="3" fill="{c}" '
                 f'stroke="#ffffff" stroke-width="{3 if on else 1}"/>'
                 f'<rect x="{230 + i * 36}" y="{44 if on else 46}" width="16" height="8" rx="1" fill="#ffffff" opacity=".85"/>')
    rows = ""
    for i, (label, v) in enumerate(S["stats"]):
        y = 120 + i * 32
        rows += (f'<rect x="216" y="{y}" width="296" height="32" fill="{"#8890f8" if i % 2 else "#6870d8"}"/>'
                 f'<rect x="{vx}" y="{y}" width="{496 - vx}" height="32" fill="{"#f0f0c0" if i % 2 else "#f0f8f8"}"/>'
                 + t(226, y + 22, label, "#ffffff", "#404890", 17) + number(484, y + 24, str(v), "#505050", "#c8d0c0"))
    stripes = "".join(f'<rect x="18" y="{114 + i * 8}" width="172" height="4" fill="#e8e8b0"/>' for i in range(17 + sy // 8))
    pcss, psvg = sprite(pory, "pory", 114, 170 + sy, 1.3)
    hp_label, hp_now, hp_max = S["hp"]
    H = 432 + sy
    body = (
        '<g shape-rendering="crispEdges">'
        f'<rect width="512" height="{H}" rx="8" fill="#c8d0c0"/>'
        '<path d="M0 8a8 8 0 0 1 8-8h496a8 8 0 0 1 8 8v24H0z" fill="#2068e0"/><rect x="8" width="496" height="4" fill="#4890f8"/>'
        '<rect y="32" x="208" width="304" height="34" fill="#b0b8d0"/>'
        f'<rect x="208" y="66" width="304" height="{222 + sy}" fill="#8890f8"/></g>'
        + t(12, 24, "TRAINER SKILLS", "#ffffff", "#103878") +
        '<path d="M214 50 l8 -7 v14 z" fill="#2068e0"/>' + tabs +
        '<rect x="8" y="42" width="192" height="58" rx="8" fill="#f8f8f8" stroke="#e8d8a0" stroke-width="2"/>'
        '<path d="M8 50 a8 8 0 0 1 8 -8 h176 a8 8 0 0 1 8 8 v22 h-192 z" fill="#f8c850"/>'
        '<circle cx="26" cy="57" r="10" fill="#f8f8f8" stroke="#484038" stroke-width="2"/>'
        '<path d="M16 57 a10 10 0 0 1 20 0 z" fill="#e04848" stroke="#484038" stroke-width="2"/>'
        '<circle cx="26" cy="57" r="3" fill="#f8f8f8" stroke="#484038" stroke-width="2"/>'
        + t(44, 65, S["name"], "#ffffff", "#a87818", 21) + t(20, 93, "Lv.", "#484038", "#c8c0a8", 19)
        + number(52, 92, S["level"], "#484038", "#c8c0a8", 2.2, "start") + t(86, 92, "(age)", "#807860", "#d8d0b8", 15) +
        f'<rect x="18" y="114" width="172" height="{136 + sy}" rx="6" fill="#f0f0c0"/>'
        f'<g shape-rendering="crispEdges">{stripes}</g>'
        f'<image href="{lucas}" x="26" y="{118 + sy}" width="91" height="127" image-rendering="optimizeSpeed" style="image-rendering:pixelated"/>'
        + psvg +
        f'<text x="104" y="{282 + sy}" fill="#a8b0a0" font-size="16" text-anchor="middle" letter-spacing="3" class="m">● ▲ ■ ♥ ★ ◆</text>'
        f'<g shape-rendering="crispEdges"><rect y="{300 + sy}" width="208" height="40" fill="#f8c850"/><rect y="{340 + sy}" width="208" height="44" fill="#f8f8f8"/></g>'
        + t(14, 328 + sy, "Item", "#484038", "#d8a840") + t(14, 369 + sy, S["item"], "#505050", "#c8d0c0") +
        '<rect x="216" y="66" width="296" height="54" fill="#8890f8"/>'
        + t(250, 92, hp_label, "#ffffff", "#404890") +
        '<rect x="352" y="70" width="144" height="30" rx="14" fill="#f0f8f8"/>'
        + number(478, 93, f"{hp_now}/{hp_max}", "#505050", "#c8d0c0") +
        '<rect x="356" y="104" width="138" height="12" rx="3" fill="#101820"/>'
        '<rect x="360" y="106" width="22" height="8" rx="1" fill="#e04848"/>'
        '<text x="371" y="113.5" fill="#f8f8f8" font-size="8" text-anchor="middle">HP</text>'
        f'<rect x="384" y="106" width="{106 * hp_now / hp_max:.0f}" height="8" rx="1" fill="#58d058"/>'
        f'<g shape-rendering="crispEdges">{rows}'
        f'<rect x="208" y="{288 + sy}" width="98" height="32" fill="#6870d8"/><rect x="306" y="{288 + sy}" width="206" height="32" fill="#d8e0f0"/>'
        f'<rect x="208" y="{320 + sy}" width="304" height="64" fill="#f0f8f8"/></g>'
        + t(218, 311 + sy, "Ability", "#ffffff", "#404890") + t(409, 311 + sy, S["ability"], "#505050", "#a8b0c8", 20, "middle")
        + t(220, 346 + sy, S["desc"][0], "#505050", "#c8d0c0", 18) + t(220, 374 + sy, S["desc"][1], "#505050", "#c8d0c0", 18) +
        f'<g shape-rendering="crispEdges"><path d="M0 {384 + sy}h512v40a8 8 0 0 1-8 8H8a8 8 0 0 1-8-8z" fill="#2068e0"/>'
        f'<rect y="{384 + sy}" width="512" height="3" fill="#4890f8"/>'
        f'<rect x="112" y="{403 + sy}" width="122" height="12" fill="#101820"/><rect x="115" y="{406 + sy}" width="64" height="6" fill="#48c8f8"/></g>'
        + t(12, 415 + sy, "NEXT Lv.", "#ffffff", "#103878", 18) + t(246, 415 + sy, S["next"], "#ffffff", "#103878", 17))
    return pcss, body, H


# ---------------------------------------------------------------- section cards
def whoami_card():
    size, lh, gap = 18, 27, 12
    x_text, width = PAD_X + 22, W - PAD_X - 22 - 30
    out, y = [], TOP
    for item in WHOAMI:
        lines = wrap(item, size, width)
        out.append(cursor(PAD_X, y - 12))
        for i, words in enumerate(lines):
            out.append(rich_line(x_text, y + i * lh, words, size))
        y += len(lines) * lh + gap
    h = y - gap - lh + 34
    body = window(h, "Who am I") + "".join(out)
    return svg(W, h, f"text{{font-family:{PIX};white-space:pre}}", body, "Who am I. " + " ".join(plain(s) for s in WHOAMI))


def chips(items, x0, y0, width, size=15):
    """Flow layout of small pixel chips; returns (svg, bottom y)."""
    x, y, out, ch = x0, y0, [], 28
    for it in items:
        w = text_width(it, size) + 22
        if x + w > x0 + width:
            x, y = x0, y + ch + 8
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{ch}" rx="4" fill="#0d1422" stroke="#1f3253" stroke-width="1.5"/>'
                   f'<text x="{x + w / 2:.1f}" y="{y + 19:.1f}" fill="#9fc3ff" font-size="{size}" text-anchor="middle">{esc(it)}</text>')
        x += w + 8
    return "".join(out), y + ch


def skills_card(lucas, pory):
    pcss, card, ch = summary(lucas, pory)
    y = 76
    body = [f'<g transform="translate({(W - 512) / 2:.0f} {y})">{card}</g>']
    y += ch + 40
    body.append(f'<text x="{PAD_X}" y="{y}" fill="{VOLT}" font-size="18" font-weight="700">Stack</text>')
    c, y = chips(STACK, PAD_X, y + 14, W - 2 * PAD_X)
    body.append(c)
    y += 40
    body.append(f'<text x="{PAD_X}" y="{y}" fill="{VOLT}" font-size="18" font-weight="700">Domains</text>')
    y += 30
    for i, words in enumerate(wrap(DOMAINS, 18, W - 2 * PAD_X)):
        body.append(rich_line(PAD_X, y + i * 27, words, 18))
        last = y + i * 27
    h = last + 34
    S = SKILLS
    label = ("Skills. Trainer skills card, Pokémon Platinum style: "
             f"{S['hp'][0]} {S['hp'][1]}; " + "; ".join(f"{a} {b}" for a, b in S["stats"])
             + f". Ability: {S['ability']}. Next level: {S['next']}. Stack: {', '.join(STACK)}. Domains: {DOMAINS}")
    style = (f"text{{font-family:{PIX};white-space:pre}}text.m{{font-family:{MONO}}}" + pcss)
    return svg(W, h, style, window(h, "Skills") + "".join(body), label)


def projects_card():
    out, y = [], TOP - 2
    for i, (name, desc, tag) in enumerate(PROJECTS):
        if i:
            out.append(f'<g shape-rendering="crispEdges">' + "".join(
                f'<rect x="{PAD_X + k * 10}" y="{y - 30}" width="5" height="2" fill="{EDGE}"/>' for k in range((W - 2 * PAD_X) // 10)) + "</g>")
        out.append(cursor(PAD_X, y - 13))
        out.append(f'<text x="{PAD_X + 22}" y="{y}" fill="{INK}" font-size="21" font-weight="700">{esc(name)}</text>')
        y += 30
        for words in wrap(desc, 18, W - 2 * PAD_X - 22 - 10):
            out.append(rich_line(PAD_X + 22, y, words, 18))
            y += 26
        out.append(f'<text x="{PAD_X + 22}" y="{y + 2}" fill="{VOLT}" font-size="16">{esc(tag)}</text>')
        y += 62
    h = y - 62 + 30
    label = "Projects. " + " ".join(f"{n}: {d} ({t})." for n, d, t in PROJECTS)
    return svg(W, h, f"text{{font-family:{PIX};white-space:pre}}", window(h, "Projects") + "".join(out), label)


def achievements_card():
    size, lh, gap = 18, 27, 18
    x_text, width = PAD_X + 78, W - PAD_X - 78 - 30
    out, y = [], TOP
    for year, text in ACHIEVEMENTS:
        out.append(f'<text x="{PAD_X}" y="{y}" fill="{VOLT}" font-size="18" font-weight="700">[{year}]</text>')
        lines = wrap(text, size, width)
        for i, words in enumerate(lines):
            out.append(rich_line(x_text, y + i * lh, words, size))
        y += len(lines) * lh + gap
    h = y - gap - lh + 34
    label = "Achievements. " + " ".join(f"[{yr}] {plain(t)}" for yr, t in ACHIEVEMENTS)
    return svg(W, h, f"text{{font-family:{PIX};white-space:pre}}", window(h, "Achievements") + "".join(out), label)


# ---------------------------------------------------------------- small pieces
def pill(text):
    size = 15
    w, h = text_width("> " + text, size, True) + 26, 30
    body = (f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2}" rx="5" fill="{PANEL}" stroke="{EDGE}" stroke-width="2"/>'
            f'<text x="{w / 2:.1f}" y="{h / 2 + 5:.1f}" fill="#cfe0ff" font-size="{size}" font-weight="700" text-anchor="middle">'
            f'<tspan fill="{VOLT}">&gt; </tspan>{esc(text)}</text>')
    return svg(w, h, f"text{{font-family:{PIX};white-space:pre}}", body, text)


def footer(woo):
    h = 120
    css, spr = sprite(woo, "woo", 24, 12, 2.6)
    body = (f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="10" fill="{PANEL}" stroke="{EDGE}" stroke-width="2"/>{spr}'
            f'<path d="M150 60 l16 -10 v-14 a8 8 0 0 1 8 -8 h300 a8 8 0 0 1 8 8 v44 a8 8 0 0 1 -8 8 h-300 a8 8 0 0 1 -8 -8 v-14 z" fill="{NAVY}" stroke="{EDGE}" stroke-width="2"/>'
            f'<text x="324" y="67" fill="#7fd4f0" font-size="22" text-anchor="middle">thanks for stopping by!</text>')
    return svg(W, h, css + f"text{{font-family:{PIX};white-space:pre}}", body, "Wooper says: thanks for stopping by!")


def main():
    lux, woo, pory = strip("luxray.gif"), strip("wooper.gif"), strip("porygon.gif")
    lucas = png_uri(Image.open(SRC / "lucas-laptop.png").convert("RGBA"))
    files = {
        "header.svg": header(lux, woo),
        "whoami.svg": whoami_card(),
        "skills.svg": skills_card(lucas, pory),
        "projects.svg": projects_card(),
        "achievements.svg": achievements_card(),
        "footer.svg": footer(woo),
    }
    files |= {f"link-{k}.svg": pill(v) for k, v in LINKS.items()}
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"{name:28s} {len(content) / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
