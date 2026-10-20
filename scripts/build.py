"""Build the animated SVGs used by README.md.

Run from the repo root:  python scripts/build.py
Edit SKILLS / PROJECTS below, re-run, commit the files in assets/.
GitHub shows SVGs as images, so everything (sprites, font) is embedded inline.
"""
import base64
import io
import random
import textwrap
from pathlib import Path

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "assets" / "src", ROOT / "assets"

RAIN = "|'|./"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
NAVY, PANEL, EDGE, VOLT, BLUE = "#0b1324", "#0f1a2e", "#2b4470", "#ffcb05", "#2a75bb"

SKILLS = {
    "name": "FELIPE", "level": "25", "item": "Data Logger",
    "hp": ("Python", 120, 120),
    "stats": [("Pandas", 110), ("Validation", 115), ("ML", 90), ("Vehicle Data", 125), ("Automation", 118)],
    "ability": "Resilience",
    "desc": ["Keeps results reliable", "when the data gets rough."],
    "next": "SQL · POWER BI · DATABRICKS",
}

PROJECTS = [
    ("f1-laptime-prediction", "End-to-end ML on real F1 telemetry: FastF1, leave-one-race-out validation, XGBoost + SHAP.", "python · ml"),
    ("coastdown-analysis", "Streamlit app that automates vehicle coastdown tests (NBR 10312). ~80% less analysis time. Code private.", "published at SIMEA 2026"),
    ("felipeeckert.github.io", "React + Vite portfolio site with projects and experience.", "web"),
]

LINKS = ["linkedin", "portfolio", "researchgate", "email"]
STACK = ["python", "pandas", "numpy", "scikit-learn", "xgboost", "plotly", "streamlit", "jupyter", "sqlite", "git", "matlab"]
HEADINGS = {"whoami": "whoami", "skills": "./summary --skills", "projects": "ls ~/projects", "achievements": "cat achievements.log"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    W, H = s["w"] * scale, s["h"] * scale
    style = (f"@keyframes {cls}{{to{{transform:translateX(-{s['w'] * s['n']}px)}}}}"
             f".{cls}{{animation:{cls} {s['dur']:.2f}s steps({s['n']}) infinite}}")
    body = (f'<svg x="{x:.1f}" y="{y:.1f}" width="{W:.1f}" height="{H:.1f}" viewBox="0 0 {s["w"]} {s["h"]}" overflow="hidden">'
            f'<image class="{cls}" href="{s["uri"]}" width="{s["w"] * s["n"]}" height="{s["h"]}" '
            f'image-rendering="optimizeSpeed" style="image-rendering:pixelated"/></svg>')
    return style, body


def svg(w, h, style, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title><style>{style}'
            f'@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>{body}</svg>')


# ---------------------------------------------------------------- pixel letters
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
    CW, LH, W = 8.4, 17, 66 * 8.4
    rnd = random.Random(7)
    name, b = pixel_word("FELIPE ECKERT", 5.2, 4, W / 2, 26)
    H = b + 292
    rain_css = f"@keyframes fall{{from{{transform:translateY(-34px)}}to{{transform:translateY({H:.0f}px)}}}}"
    drops = []
    for i in range(70):
        d = rnd.uniform(1, 1.9)
        drops.append(f'<text x="{rnd.randrange(66) * CW:.1f}" y="0" fill="#5b86d6" opacity="{rnd.uniform(.25, .7):.2f}" '
                     f'style="animation:fall {d:.2f}s linear {-rnd.uniform(0, d):.2f}s infinite">{RAIN[i % 5]}</text>')
    bolt = "".join(f'<text x="{32 * CW:.1f}" y="{b + 90 + i * LH:.1f}" fill="#fff6c8" font-weight="700">{esc(l)}</text>'
                   for i, l in enumerate(["   /", "  /", " /_", "  /", " /", "'"]))
    lcss, lsvg = sprite(lux, "lux", 2 * CW, b + 78, 2.7)
    wcss, wsvg = sprite(woo, "woo", 45 * CW, b + 161, 2.7)
    style = (rain_css + lcss + wcss +
             "@keyframes fl{0%,58%,61%,63%,100%{opacity:0}59%,62%{opacity:.45}}.fl{animation:fl 7s infinite}"
             "@keyframes bo{0%,58%,64%,100%{opacity:0}59%,63%{opacity:1}}.bo{animation:bo 7s infinite}"
             "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1s step-end infinite}"
             f"text{{font-family:{MONO};white-space:pre}}")
    body = (f'<rect width="{W:.1f}" height="{H:.1f}" rx="10" fill="{NAVY}"/><g font-size="14">{"".join(drops)}{name}'
            f'<rect x="{W / 2 - 112:.1f}" y="{b + 10:.1f}" width="224" height="26" rx="4" fill="{BLUE}" stroke="{VOLT}" stroke-width="2"/>'
            f'<text x="{W / 2:.1f}" y="{b + 28:.1f}" fill="#ffffff" font-size="13" font-weight="700" letter-spacing="3" text-anchor="middle">DATA ANALYST VERSION</text>'
            f'<text x="{W / 2:.1f}" y="{b + 68:.1f}" fill="#9fb3d6" font-size="13" text-anchor="middle">&gt; python · automation · vehicle data<tspan class="cur" fill="{VOLT}"> █</tspan></text>'
            f'<g class="bo">{bolt}</g>{lsvg}'
            f'<text x="{CW:.1f}" y="{b + 266:.1f}" fill="{EDGE}">________________________________</text>{wsvg}'
            f'<text x="{42 * CW:.1f}" y="{b + 266:.1f}" fill="#3d6fae">~~ ~~~~~~~~~~~~~~~~ ~~</text></g>'
            f'<rect class="fl" width="{W:.1f}" height="{H:.1f}" rx="10" fill="#e8f0ff" opacity="0"/>')
    return svg(W, H, style, body, "Felipe Eckert, Data Analyst Version: pixel-art title in the rain with Luxray and Wooper")


# ---------------------------------------------------------------- Pokémon Platinum summary card
def summary(lucas, pory):
    S = SKILLS
    font = b64((SRC / "PixelifySans.ttf").read_bytes(), "font/ttf")

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
                 f'<rect x="352" y="{y}" width="144" height="32" fill="{"#f0f0c0" if i % 2 else "#f0f8f8"}"/>'
                 + t(228, y + 23, label, "#ffffff", "#404890", 18) + number(476, y + 24, str(v), "#505050", "#c8d0c0"))
    stripes = "".join(f'<rect x="18" y="{114 + i * 8}" width="172" height="4" fill="#e8e8b0"/>' for i in range(17))
    pcss, psvg = sprite(pory, "pory", 114, 170, 1.3)
    hp_label, hp_now, hp_max = S["hp"]
    style = (f"@font-face{{font-family:'PixelifySans';src:url({font}) format('truetype')}}"
             f"text{{font-family:'PixelifySans',{MONO};white-space:pre}}" + pcss)
    body = (
        '<g shape-rendering="crispEdges">'
        '<rect width="512" height="432" rx="8" fill="#c8d0c0"/>'
        '<path d="M0 8a8 8 0 0 1 8-8h496a8 8 0 0 1 8 8v24H0z" fill="#2068e0"/><rect x="8" width="496" height="4" fill="#4890f8"/>'
        '<rect y="32" x="208" width="304" height="34" fill="#b0b8d0"/>'
        '<rect x="208" y="66" width="304" height="222" fill="#8890f8"/></g>'
        + t(12, 24, "TRAINER SKILLS", "#ffffff", "#103878") +
        '<path d="M214 50 l8 -7 v14 z" fill="#2068e0"/>' + tabs +
        '<rect x="8" y="42" width="192" height="58" rx="8" fill="#f8f8f8" stroke="#e8d8a0" stroke-width="2"/>'
        '<path d="M8 50 a8 8 0 0 1 8 -8 h176 a8 8 0 0 1 8 8 v22 h-192 z" fill="#f8c850"/>'
        '<circle cx="26" cy="57" r="10" fill="#f8f8f8" stroke="#484038" stroke-width="2"/>'
        '<path d="M16 57 a10 10 0 0 1 20 0 z" fill="#e04848" stroke="#484038" stroke-width="2"/>'
        '<circle cx="26" cy="57" r="3" fill="#f8f8f8" stroke="#484038" stroke-width="2"/>'
        + t(44, 65, S["name"], "#ffffff", "#a87818", 21) + t(20, 93, "Lv.", "#484038", "#c8c0a8", 19)
        + number(52, 92, S["level"], "#484038", "#c8c0a8", 2.2, "start") + t(86, 92, "(age)", "#807860", "#d8d0b8", 15) +
        '<rect x="18" y="114" width="172" height="136" rx="6" fill="#f0f0c0"/>'
        f'<g shape-rendering="crispEdges">{stripes}</g>'
        f'<image href="{lucas}" x="26" y="118" width="91" height="127" image-rendering="optimizeSpeed" style="image-rendering:pixelated"/>'
        + psvg +
        '<text x="104" y="282" fill="#a8b0a0" font-size="16" text-anchor="middle" letter-spacing="3">● ▲ ■ ♥ ★ ◆</text>'
        '<g shape-rendering="crispEdges"><rect y="300" width="208" height="40" fill="#f8c850"/><rect y="340" width="208" height="44" fill="#f8f8f8"/></g>'
        + t(14, 328, "Item", "#484038", "#d8a840") + t(14, 369, S["item"], "#505050", "#c8d0c0") +
        '<rect x="216" y="66" width="296" height="54" fill="#8890f8"/>'
        + t(250, 92, hp_label, "#ffffff", "#404890") +
        '<rect x="352" y="70" width="144" height="30" rx="14" fill="#f0f8f8"/>'
        + number(478, 93, f"{hp_now}/{hp_max}", "#505050", "#c8d0c0") +
        '<rect x="356" y="104" width="138" height="12" rx="3" fill="#101820"/>'
        '<rect x="360" y="106" width="22" height="8" rx="1" fill="#e04848"/>'
        '<text x="371" y="113.5" fill="#f8f8f8" font-size="8" text-anchor="middle">HP</text>'
        f'<rect x="384" y="106" width="{106 * hp_now / hp_max:.0f}" height="8" rx="1" fill="#58d058"/>'
        f'<g shape-rendering="crispEdges">{rows}'
        '<rect x="208" y="288" width="98" height="32" fill="#6870d8"/><rect x="306" y="288" width="206" height="32" fill="#d8e0f0"/>'
        '<rect x="208" y="320" width="304" height="64" fill="#f0f8f8"/></g>'
        + t(218, 311, "Ability", "#ffffff", "#404890") + t(409, 311, S["ability"], "#505050", "#a8b0c8", 20, "middle")
        + t(220, 346, S["desc"][0], "#505050", "#c8d0c0", 18) + t(220, 374, S["desc"][1], "#505050", "#c8d0c0", 18) +
        '<g shape-rendering="crispEdges"><path d="M0 384h512v40a8 8 0 0 1-8 8H8a8 8 0 0 1-8-8z" fill="#2068e0"/>'
        '<rect y="384" width="512" height="3" fill="#4890f8"/>'
        '<rect x="112" y="403" width="122" height="12" fill="#101820"/><rect x="115" y="406" width="64" height="6" fill="#48c8f8"/></g>'
        + t(12, 415, "NEXT Lv.", "#ffffff", "#103878", 18) + t(246, 415, S["next"], "#ffffff", "#103878", 17))
    label = (f"Trainer skills, Pokémon Platinum style. {S['name']}, level {S['level']}. "
             f"{hp_label} {hp_now}; " + "; ".join(f"{a} {b}" for a, b in S["stats"])
             + f". Ability: {S['ability']}. Next level: {S['next']}.")
    return svg(512, 432, style, body, label)


# ---------------------------------------------------------------- small pieces
def pill(text, prefix=True):
    chars = len(text) + (2 if prefix else 0)
    w, h = 22 + chars * 7.4, 28 if prefix else 26
    fg, bg, line, weight = ("#cfe0ff", PANEL, EDGE, 700) if prefix else ("#9fc3ff", "#0d1422", "#1f3253", 400)
    head = f'<tspan fill="{VOLT}">&gt; </tspan>' if prefix else ""
    body = (f'<rect x=".5" y=".5" width="{w - 1:.1f}" height="{h - 1}" rx="4" fill="{bg}" stroke="{line}"/>'
            f'<text x="{w / 2:.1f}" y="{h / 2 + 4.5:.1f}" fill="{fg}" font-size="12" font-weight="{weight}" text-anchor="middle">{head}{esc(text)}</text>')
    return svg(w, h, f"text{{font-family:{MONO};white-space:pre}}", body, text)


def heading(text):
    w, h = 840, 46
    body = (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="6" fill="{PANEL}" stroke="{EDGE}"/>'
            f'<text x="18" y="30" font-size="20" font-weight="700"><tspan fill="{VOLT}">$ </tspan><tspan fill="#e8f0ff">{esc(text)}</tspan></text>')
    return svg(w, h, f"text{{font-family:{MONO};white-space:pre}}", body, "$ " + text)


def card(title, desc, foot):
    lines = textwrap.wrap(desc, 66)
    w, h = 840, 74 + 26 * len(lines) + 26
    body = (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="{PANEL}" stroke="{EDGE}"/>'
            f'<text x="22" y="40" fill="#e8f0ff" font-size="22" font-weight="700">{esc(title)}</text>'
            + "".join(f'<text x="22" y="{74 + i * 26}" fill="#9fb3d6" font-size="18">{esc(l)}</text>' for i, l in enumerate(lines))
            + f'<text x="22" y="{74 + 26 * len(lines) + 8}" fill="{VOLT}" font-size="15">{esc(foot)}</text>')
    return svg(w, h, f"text{{font-family:{MONO};white-space:pre}}", body, f"{title}: {desc}")


def footer(woo):
    w, h = 840, 120
    css, spr = sprite(woo, "woo", 24, 12, 2.6)
    body = (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="{PANEL}" stroke="{EDGE}"/>{spr}'
            f'<path d="M150 60 l16 -10 v-14 a8 8 0 0 1 8 -8 h300 a8 8 0 0 1 8 8 v44 a8 8 0 0 1 -8 8 h-300 a8 8 0 0 1 -8 -8 v-14 z" fill="{NAVY}" stroke="{EDGE}" stroke-width="2"/>'
            f'<text x="324" y="66" fill="#7fd4f0" font-size="20" text-anchor="middle">thanks for stopping by!</text>')
    return svg(w, h, css + f"text{{font-family:{MONO};white-space:pre}}", body, "Wooper says: thanks for stopping by!")


def main():
    lux, woo, pory = strip("luxray.gif"), strip("wooper.gif"), strip("porygon.gif")
    lucas = png_uri(Image.open(SRC / "lucas-laptop.png").convert("RGBA"))
    files = {"header.svg": header(lux, woo), "skills.svg": summary(lucas, pory), "footer.svg": footer(woo)}
    files |= {f"link-{n}.svg": pill(n) for n in LINKS}
    files |= {f"stack-{n}.svg": pill(n, prefix=False) for n in STACK}
    files |= {f"h-{k}.svg": heading(v) for k, v in HEADINGS.items()}
    files |= {f"project-{i + 1}.svg": card(*p) for i, p in enumerate(PROJECTS)}
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"{name:28s} {len(content) / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
