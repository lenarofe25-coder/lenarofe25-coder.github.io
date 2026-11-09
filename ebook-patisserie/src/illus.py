"""Générateur d'illustrations originales (style « nature morte éditoriale »).

Chaque dessert est dessiné en SVG (vue 3/4, ombres douces, grain papier,
profondeur de champ) puis rendu en JPEG par Playwright.
Toutes les formes sont paramétriques : une recette = un `kind` + des couleurs.
"""
import math
import random
import zlib

W, H = 1200, 1000          # toile ; recadrée en 3:2 ou en portrait à l'affichage
HORIZON = 560              # limite mur / table

# --------------------------------------------------------------- ambiances
SCENES = {
    "creme":   dict(wall="#EFE5D6", wall2="#E6D9C5", table="#DCCBB3", table2="#CDB89C", light="#FBF5EA"),
    "rose":    dict(wall="#F1E1D9", wall2="#E8D2C8", table="#DEC6BA", table2="#CFB2A5", light="#FCF1EC"),
    "sauge":   dict(wall="#E2E3D5", wall2="#D5D7C5", table="#D4CDB9", table2="#C2B89F", light="#F5F5EC"),
    "lin":     dict(wall="#E9E2D6", wall2="#DCD3C4", table="#C9B49A", table2="#B39C80", light="#F7F2E9"),
    "cacao":   dict(wall="#3A2A22", wall2="#2E211B", table="#4A362B", table2="#3A2A21", light="#5A4234"),
    "ardoise": dict(wall="#D9D3CB", wall2="#CBC4BA", table="#5B544E", table2="#4A4440", light="#EEE9E2"),
}

C = dict(  # nuancier pâtissier
    choc="#4A2C20", choc2="#2F1B13", choc_l="#6B4232", milk="#8A5A3C", white_choc="#F2E8D2",
    sponge="#E9C98F", sponge_d="#D9AE6C", golden="#D29A4E", golden_d="#B07A35", golden_l="#E8BE7A",
    crust="#C7843F", crust_d="#9C5F2A", cream="#FBF4E4", cream2="#F3E6CB", custard="#F2D58C",
    vanilla="#F6E9C4", red="#C7353A", red_d="#93202A", rasp="#C2384F", rasp_d="#8E2238",
    straw="#D2403F", straw_l="#F08A80", lemon="#F1D867", lemon_d="#D9B83C", caramel="#B8692A",
    caramel_l="#D99A50", coffee="#B98B66", pistache="#A8B46A", mint="#6E8B5A", mint_d="#4F6B40",
    pink="#E8B5B0", rv="#9E2A2E", carrot="#C98A4E", pecan="#8B4D2A", almond="#E3C496",
    blue="#4B4F86", cherry="#7A1424", apple="#E6C46F", apple_skin="#B8452F", pear="#D8C680",
    mango="#F2B33C", passion="#E2A72E", kiwi="#8DAA3F", orange="#EE9640", plate="#FBF8F2",
    plate_s="#E8E1D4", gold="#C9A45C", coconut="#F7F3EA", oreo="#2A2420", speculoos="#B27445",
    pineapple="#F0C64A", apricot="#EE9B45", pastel_rose="#EFC1C3", pastel_pist="#C9D49A",
    pastel_lav="#C8B8D8", pastel_van="#F2E3BE", glaze_coffee="#A47551",
)


def rng(seed):
    return random.Random(seed)


def shade(hexc, f):
    """f<1 assombrit, f>1 éclaircit."""
    hexc = hexc.lstrip('#')
    r, g, b = int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16)
    if f < 1:
        r, g, b = r * f, g * f, b * f
    else:
        k = f - 1
        r, g, b = r + (255 - r) * k, g + (255 - g) * k, b + (255 - b) * k
    return "#%02X%02X%02X" % (max(0, min(255, int(r))), max(0, min(255, int(g))), max(0, min(255, int(b))))


class Svg:
    def __init__(self, seed):
        self.parts = []
        self.defs = []
        self.r = rng(seed)
        self.n = 0

    def uid(self, p="g"):
        self.n += 1
        return f"{p}{self.n}"

    def add(self, s):
        self.parts.append(s)

    # dégradé horizontal (volume cylindrique)
    def hgrad(self, col, dark=0.78, light=1.12):
        i = self.uid("hg")
        self.defs.append(
            f'<linearGradient id="{i}" x1="0" x2="1" y1="0" y2="0">'
            f'<stop offset="0" stop-color="{shade(col, dark)}"/>'
            f'<stop offset="0.38" stop-color="{shade(col, light)}"/>'
            f'<stop offset="0.62" stop-color="{col}"/>'
            f'<stop offset="1" stop-color="{shade(col, dark * 0.92)}"/></linearGradient>')
        return f"url(#{i})"

    def vgrad(self, c1, c2):
        i = self.uid("vg")
        self.defs.append(f'<linearGradient id="{i}" x1="0" x2="0" y1="0" y2="1">'
                         f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>')
        return f"url(#{i})"

    def rgrad(self, c1, c2, cx=0.4, cy=0.35):
        i = self.uid("rg")
        self.defs.append(f'<radialGradient id="{i}" cx="{cx}" cy="{cy}" r="0.75">'
                         f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></radialGradient>')
        return f"url(#{i})"


# ============================================================ primitives
def ell(cx, cy, rx, ry, fill, extra=""):
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" {extra}/>'


def poly(pts, fill, extra=""):
    return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}" {extra}/>'


def path(d, fill, extra=""):
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def shadow(cx, cy, rx, ry, op=0.28):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#2a1a10" opacity="{op}" filter="url(#blur18)"/>'


def plate(s, cx, cy, rx, ry=None, col=None, rim=True):
    ry = ry or rx * 0.34
    col = col or C["plate"]
    s.add(shadow(cx + 10, cy + ry * 0.35, rx * 1.02, ry * 0.95, 0.30))
    s.add(ell(cx, cy + 6, rx, ry, shade(col, 0.86)))
    s.add(ell(cx, cy, rx, ry, s.rgrad(shade(col, 1.04), shade(col, 0.95), 0.45, 0.3)))
    if rim:
        s.add(ell(cx, cy + ry * 0.05, rx * 0.72, ry * 0.68, shade(col, 0.965)))
        s.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*0.995}" ry="{ry*0.99}" fill="none" stroke="#ffffff" stroke-opacity="0.7" stroke-width="2"/>')


def stand(s, cx, cy, rx):
    """Présentoir à gâteau sur pied."""
    ry = rx * 0.3
    s.add(shadow(cx + 12, cy + 150, rx * 0.65, 30, 0.32))
    s.add(ell(cx, cy + 148, rx * 0.42, rx * 0.12, shade(C["plate"], 0.86)))
    s.add(ell(cx, cy + 142, rx * 0.42, rx * 0.12, C["plate"]))
    s.add(poly([(cx - 26, cy + 140), (cx + 26, cy + 140), (cx + 16, cy + 20), (cx - 16, cy + 20)], s.hgrad(C["plate"], 0.85, 1.03)))
    s.add(ell(cx, cy + 14, rx, ry, shade(C["plate"], 0.84)))
    s.add(ell(cx, cy, rx, ry, s.rgrad("#FFFFFF", shade(C["plate"], 0.95))))


def board(s, cx, cy, w, h):
    """Planche en bois (vue 3/4)."""
    wood = "#B88A5A"
    s.add(shadow(cx + 14, cy + h * 0.55, w * 0.55, h * 0.35, 0.3))
    d = 22
    pts = [(cx - w / 2 + 40, cy - h / 2), (cx + w / 2 + 40, cy - h / 2), (cx + w / 2 - 40, cy + h / 2), (cx - w / 2 - 40, cy + h / 2)]
    s.add(poly([(x, y + d) for x, y in pts], shade(wood, 0.7)))
    s.add(poly(pts, s.vgrad(shade(wood, 1.08), shade(wood, 0.92))))
    for i in range(9):
        y = cy - h / 2 + (i + 0.6) * h / 9.5
        f = (y - (cy - h / 2)) / h
        x1 = cx - w / 2 + 40 - 80 * f
        x2 = cx + w / 2 + 40 - 80 * f
        s.add(f'<path d="M{x1+10:.0f},{y:.0f} C{x1+w*0.3:.0f},{y+s.r.uniform(-4,4):.0f} {x2-w*0.3:.0f},{y+s.r.uniform(-4,4):.0f} {x2-10:.0f},{y:.0f}" stroke="{shade(wood,0.82)}" stroke-width="1.6" fill="none" opacity="0.55"/>')


def parchment(s, cx, cy, w, h, rot=-6):
    s.add(f'<g transform="rotate({rot} {cx} {cy})">')
    s.add(shadow(cx + 8, cy + 10, w * 0.5, h * 0.45, 0.18))
    jag = []
    n = 14
    for i in range(n + 1):
        jag.append((cx - w / 2 + w * i / n, cy - h / 2 + s.r.uniform(-5, 5)))
    for i in range(n + 1):
        jag.append((cx + w / 2 - w * i / n, cy + h / 2 + s.r.uniform(-5, 5)))
    s.add(poly(jag, "#F4EBDB"))
    s.add(poly(jag, "none", 'stroke="#D9CBB2" stroke-width="1.5"'))
    s.add('</g>')


def napkin(s, x, y, col="#EAD9C6", rot=12):
    s.add(f'<g transform="rotate({rot} {x} {y})" opacity="0.95">')
    s.add(f'<rect x="{x}" y="{y}" width="330" height="200" rx="6" fill="{col}"/>')
    for i in range(1, 9):
        s.add(f'<line x1="{x+i*36}" y1="{y+4}" x2="{x+i*36}" y2="{y+196}" stroke="{shade(col,0.9)}" stroke-width="1.2" opacity="0.55"/>')
    for i in range(1, 6):
        s.add(f'<line x1="{x+4}" y1="{y+i*33}" x2="{x+326}" y2="{y+i*33}" stroke="{shade(col,0.9)}" stroke-width="1.2" opacity="0.4"/>')
    s.add(f'<rect x="{x}" y="{y}" width="330" height="200" rx="6" fill="none" stroke="{shade(col,0.82)}" stroke-width="2" stroke-dasharray="7 5" transform="translate(10 10) scale(0.94)" transform-origin="{x} {y}"/>')
    s.add('</g>')


def spoon(s, x, y, rot=-20, col="#C9BBA4"):
    s.add(f'<g transform="rotate({rot} {x} {y})">')
    s.add(shadow(x + 90, y + 14, 120, 10, 0.18))
    s.add(f'<rect x="{x+30}" y="{y-6}" width="190" height="12" rx="6" fill="{s.vgrad(shade(col,1.15),shade(col,0.8))}"/>')
    s.add(ell(x, y, 42, 24, s.rgrad(shade(col, 1.2), shade(col, 0.78))))
    s.add('</g>')


def fork(s, x, y, rot=-20, col="#C9BBA4"):
    s.add(f'<g transform="rotate({rot} {x} {y})">')
    s.add(shadow(x + 110, y + 14, 140, 10, 0.18))
    g = s.vgrad(shade(col, 1.15), shade(col, 0.8))
    s.add(f'<rect x="{x+60}" y="{y-6}" width="180" height="12" rx="6" fill="{g}"/>')
    s.add(f'<path d="M{x+64},{y-12} L{x+20},{y-16} L{x-40},{y-16} L{x-40},{y+16} L{x+20},{y+16} L{x+64},{y+12} Z" fill="{g}"/>')
    for k in (-9, 0, 9):
        s.add(f'<rect x="{x-44}" y="{y+k-2.5}" width="56" height="5" fill="{shade(col,0.7)}"/>')
    s.add('</g>')


def leaf(s, x, y, size=1.0, rot=0, col=None):
    col = col or C["mint"]
    s.add(f'<g transform="translate({x} {y}) rotate({rot}) scale({size})">'
          f'<path d="M0,0 C10,-18 34,-20 46,0 C34,20 10,18 0,0 Z" fill="{col}"/>'
          f'<path d="M2,0 L42,0" stroke="{shade(col,0.7)}" stroke-width="1.5"/></g>')


def mint_sprig(s, x, y, size=1.0, rot=0):
    s.add(f'<g transform="translate({x} {y}) rotate({rot}) scale({size})">')
    s.add(f'<path d="M0,0 L-6,30" stroke="{C["mint_d"]}" stroke-width="3"/>')
    leaf(s, 0, 0, 0.9, -120)
    leaf(s, 0, 0, 0.9, -60)
    leaf(s, -3, 14, 0.8, 160)
    leaf(s, -3, 14, 0.8, 20)
    s.add('</g>')


def berry(s, x, y, kind, size=1.0):
    r = 14 * size
    if kind == "rasp":
        s.add(ell(x, y, r, r * 0.95, s.rgrad(shade(C["rasp"], 1.2), C["rasp_d"])))
        for i in range(7):
            a = i / 7 * math.tau
            s.add(f'<circle cx="{x+math.cos(a)*r*0.55:.1f}" cy="{y+math.sin(a)*r*0.5:.1f}" r="{r*0.33:.1f}" fill="{C["rasp"]}" stroke="{C["rasp_d"]}" stroke-width="1"/>')
        s.add(f'<circle cx="{x}" cy="{y}" r="{r*0.3}" fill="{shade(C["rasp"],0.75)}"/>')
        s.add(f'<circle cx="{x-r*0.35}" cy="{y-r*0.4}" r="{r*0.18}" fill="#fff" opacity="0.45"/>')
    elif kind == "blue":
        s.add(f'<circle cx="{x}" cy="{y}" r="{r*0.8}" fill="{s.rgrad(shade(C["blue"],1.25),shade(C["blue"],0.6))}"/>')
        s.add(f'<circle cx="{x+r*0.1}" cy="{y-r*0.15}" r="{r*0.2}" fill="{shade(C["blue"],0.5)}"/>')
    elif kind == "straw":      # fraise entière
        s.add(f'<path d="M{x-r},{y-r*0.4} C{x-r},{y+r*0.8} {x-r*0.2},{y+r*1.4} {x},{y+r*1.5} C{x+r*0.2},{y+r*1.4} {x+r},{y+r*0.8} {x+r},{y-r*0.4} C{x+r*0.6},{y-r*0.9} {x-r*0.6},{y-r*0.9} {x-r},{y-r*0.4} Z" fill="{s.rgrad(shade(C["straw"],1.2),C["red_d"])}"/>')
        for i in range(6):
            s.add(f'<circle cx="{x+s.r.uniform(-r*0.6,r*0.6):.1f}" cy="{y+s.r.uniform(-r*0.2,r):.1f}" r="1.6" fill="#F5DB8A"/>')
        for a in (-60, -20, 20, 60):
            leaf(s, x, y - r * 0.6, 0.35 * size, a - 90, C["mint"])
    elif kind == "straw_half":  # fraise coupée
        s.add(f'<path d="M{x-r},{y-r*0.5} C{x-r*1.05},{y+r*0.7} {x-r*0.3},{y+r*1.3} {x},{y+r*1.4} C{x+r*0.3},{y+r*1.3} {x+r*1.05},{y+r*0.7} {x+r},{y-r*0.5} Z" fill="{C["straw"]}"/>')
        s.add(f'<path d="M{x-r*0.72},{y-r*0.35} C{x-r*0.7},{y+r*0.6} {x-r*0.2},{y+r*1.05} {x},{y+r*1.12} C{x+r*0.2},{y+r*1.05} {x+r*0.7},{y+r*0.6} {x+r*0.72},{y-r*0.35} Z" fill="{C["straw_l"]}"/>')
        s.add(f'<path d="M{x},{y-r*0.3} L{x},{y+r*0.9}" stroke="#FCE3DC" stroke-width="{2*size}"/>')
        s.add(f'<rect x="{x-r}" y="{y-r*0.62}" width="{2*r}" height="{r*0.22}" fill="{C["mint"]}" rx="2"/>')
    elif kind == "cherry":
        s.add(f'<path d="M{x},{y-r*0.8} C{x+6},{y-r*2} {x+16},{y-r*2.6} {x+26},{y-r*3}" stroke="#5E6B34" stroke-width="2.5" fill="none"/>')
        s.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{s.rgrad(shade(C["cherry"],1.6),C["cherry"])}"/>')
        s.add(f'<ellipse cx="{x-r*0.35}" cy="{y-r*0.35}" rx="{r*0.25}" ry="{r*0.15}" fill="#fff" opacity="0.6"/>')
    elif kind == "currant":
        for dx, dy in ((0, 0), (12, 6), (-10, 8), (4, 14)):
            s.add(f'<circle cx="{x+dx*size}" cy="{y+dy*size}" r="{7*size}" fill="{s.rgrad("#F06A6A","#A11624")}"/>')
            s.add(f'<circle cx="{x+dx*size-2}" cy="{y+dy*size-2}" r="{2*size}" fill="#fff" opacity="0.6"/>')


def sugar_dust(s, cx, cy, rx, ry, n=220, col="#FFFFFF", op=0.85):
    out = []
    for _ in range(n):
        a = s.r.uniform(0, math.tau)
        d = math.sqrt(s.r.random())
        out.append(f'<circle cx="{cx+math.cos(a)*rx*d:.1f}" cy="{cy+math.sin(a)*ry*d:.1f}" r="{s.r.uniform(0.8,2.2):.1f}"/>')
    s.add(f'<g fill="{col}" opacity="{op}">{"".join(out)}</g>')


def scatter(s, items, area, n=8):
    """Petits éléments éparpillés sur la table (fruits, noisettes, copeaux)."""
    x0, y0, x1, y1 = area
    for _ in range(n):
        x, y = s.r.uniform(x0, x1), s.r.uniform(y0, y1)
        it = s.r.choice(items)
        if it in ("rasp", "blue", "straw", "cherry", "currant"):
            berry(s, x, y, it, s.r.uniform(0.9, 1.3))
        elif it == "almond":
            s.add(f'<ellipse cx="{x}" cy="{y}" rx="13" ry="8" fill="{C["almond"]}" transform="rotate({s.r.randint(0,180)} {x} {y})" stroke="{shade(C["almond"],0.8)}"/>')
        elif it == "hazel":
            s.add(f'<circle cx="{x}" cy="{y}" r="11" fill="{s.rgrad("#C08A55","#7A4A25")}"/>')
        elif it == "pecan":
            s.add(f'<ellipse cx="{x}" cy="{y}" rx="18" ry="10" fill="{C["pecan"]}" transform="rotate({s.r.randint(0,180)} {x} {y})"/>'
                  f'<path d="M{x-14},{y} Q{x},{y-6} {x+14},{y}" stroke="{shade(C["pecan"],0.6)}" stroke-width="2" fill="none" transform="rotate({s.r.randint(0,180)} {x} {y})"/>')
        elif it == "choc":
            w = s.r.uniform(18, 30)
            s.add(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{w*0.7:.0f}" fill="{C["choc"]}" transform="rotate({s.r.randint(-40,40)} {x} {y})" rx="2"/>')
        elif it == "chocbar":
            s.add(f'<g transform="rotate({s.r.randint(-25,25)} {x} {y})"><rect x="{x}" y="{y}" width="110" height="60" rx="3" fill="{C["choc"]}"/>'
                  + "".join(f'<rect x="{x+4+i*27}" y="{y+4}" width="23" height="24" fill="{C["choc_l"]}" opacity="0.6"/><rect x="{x+4+i*27}" y="{y+32}" width="23" height="24" fill="{C["choc_l"]}" opacity="0.6"/>' for i in range(4)) + '</g>')
        elif it == "lemon":
            s.add(f'<circle cx="{x}" cy="{y}" r="34" fill="{C["lemon"]}"/><circle cx="{x}" cy="{y}" r="28" fill="#FBF0B5"/>'
                  + "".join(f'<path d="M{x},{y} L{x+math.cos(a)*25:.1f},{y+math.sin(a)*25:.1f}" stroke="{C["lemon"]}" stroke-width="2.5"/>' for a in [i * math.tau / 8 for i in range(8)]))
        elif it == "mint":
            mint_sprig(s, x, y, 0.8, s.r.randint(-40, 40))
        elif it == "vanilla":
            s.add(f'<path d="M{x},{y} q80,-10 160,10" stroke="#3B2618" stroke-width="7" fill="none" stroke-linecap="round"/>')
        elif it == "cinnamon":
            s.add(f'<g transform="rotate({s.r.randint(-30,30)} {x} {y})"><rect x="{x}" y="{y}" width="120" height="18" rx="6" fill="#8E5631"/><rect x="{x}" y="{y+4}" width="120" height="5" fill="#6E3E21"/></g>')
        elif it == "apple":
            s.add(f'<circle cx="{x}" cy="{y}" r="46" fill="{s.rgrad("#E57D5B","#9E2F22")}"/><path d="M{x},{y-44} q4,-18 12,-24" stroke="#5B4126" stroke-width="4" fill="none"/>')
            leaf(s, x + 8, y - 54, 0.6, -30)
        elif it == "flour":
            sugar_dust(s, x, y, 70, 22, 160, "#FFFFFF", 0.7)
        elif it == "coconut":
            s.add(f'<path d="M{x},{y} q14,-10 28,0" stroke="#FFFFFF" stroke-width="4" fill="none"/>')
        elif it == "cocoa":
            sugar_dust(s, x, y, 60, 18, 120, C["choc_l"], 0.6)
        elif it == "pistachio":
            s.add(f'<ellipse cx="{x}" cy="{y}" rx="10" ry="6" fill="{C["pistache"]}"/>')
        elif it == "orange":
            s.add(f'<circle cx="{x}" cy="{y}" r="32" fill="{C["orange"]}"/><circle cx="{x}" cy="{y}" r="27" fill="#F7BB78"/>'
                  + "".join(f'<path d="M{x},{y} L{x+math.cos(a)*24:.1f},{y+math.sin(a)*24:.1f}" stroke="{C["orange"]}" stroke-width="2"/>' for a in [i * math.tau / 9 for i in range(9)]))
        elif it == "pearl":
            for _ in range(6):
                s.add(f'<circle cx="{x+s.r.uniform(-20,20):.0f}" cy="{y+s.r.uniform(-8,8):.0f}" r="4" fill="#FFFFFF"/>')
        elif it == "speculoos":
            s.add(f'<rect x="{x}" y="{y}" width="70" height="44" rx="4" fill="{C["speculoos"]}" transform="rotate({s.r.randint(-30,30)} {x} {y})"/>')
        elif it == "gold":
            s.add(f'<polygon points="{x},{y} {x+8},{y+3} {x+4},{y+9}" fill="{C["gold"]}"/>')


# ============================================================ desserts
def cylinder(s, cx, top, rx, h, side, topc, ry=None, side_pattern=None, glaze=False):
    """Gâteau entier rond. Retourne (ry)."""
    ry = ry or rx * 0.32
    s.add(f'<path d="M{cx-rx},{top} L{cx-rx},{top+h} A{rx},{ry} 0 0 0 {cx+rx},{top+h} L{cx+rx},{top} Z" fill="{s.hgrad(side)}"/>')
    if side_pattern:
        side_pattern(cx, top, rx, ry, h)
    s.add(ell(cx, top, rx, ry, s.rgrad(shade(topc, 1.08), shade(topc, 0.93))))
    if glaze:
        s.add(f'<ellipse cx="{cx-rx*0.25}" cy="{top-ry*0.25}" rx="{rx*0.45}" ry="{ry*0.22}" fill="#fff" opacity="0.22"/>')
    return ry


def drips(s, cx, top, rx, ry, col, n=16, maxlen=50):
    pts = []
    for i in range(n + 1):
        t = math.pi * i / n
        x = cx - rx * math.cos(t)
        y = top + ry * math.sin(t)
        pts.append((x, y))
    d = f"M{cx-rx},{top} "
    for i, (x, y) in enumerate(pts[1:], 1):
        L = s.r.uniform(8, maxlen) if 1 < i < n else 4
        px, py = pts[i - 1]
        mx = (px + x) / 2
        d += f"L{px:.1f},{py:.1f} Q{mx-6:.1f},{py+L:.1f} {mx:.1f},{py+L:.1f} Q{mx+6:.1f},{py+L:.1f} {x:.1f},{y:.1f} "
    d += f"L{cx+rx},{top} A{rx},{ry} 0 0 0 {cx-rx},{top} Z"
    s.add(path(d, col))


def rosettes(s, cx, top, rx, ry, col, n=10, r=16, ring=0.8):
    pts = []
    for i in range(n):
        a = math.tau * i / n
        pts.append((cx + math.cos(a) * rx * ring, top + math.sin(a) * ry * ring, math.sin(a)))
    for x, y, z in sorted(pts, key=lambda p: p[2]):
        s.add(f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r*0.7}" fill="{shade(col,0.88)}"/>')
        s.add(f'<path d="M{x-r},{y} Q{x-r*0.4},{y-r*1.9} {x},{y-r*1.6} Q{x+r*0.4},{y-r*1.9} {x+r},{y} Z" fill="{s.rgrad(shade(col,1.06),shade(col,0.88))}"/>')
        s.add(f'<path d="M{x-r*0.4},{y-r*0.2} Q{x-r*0.2},{y-r*1.2} {x},{y-r*1.5}" stroke="{shade(col,0.85)}" stroke-width="1.5" fill="none"/>')


def toppings_on_ellipse(s, cx, top, rx, ry, kinds, n=9, ring=0.6, size=1.0):
    pts = []
    for i in range(n):
        a = math.tau * i / n + s.r.uniform(-0.15, 0.15)
        rr = ring * s.r.uniform(0.85, 1.05)
        pts.append((cx + math.cos(a) * rx * rr, top + math.sin(a) * ry * rr))
    pts.append((cx, top))
    for x, y in sorted(pts, key=lambda p: p[1]):
        berry(s, x, y - 4, s.r.choice(kinds), size)


def slice_cake(s, cx, cy, layers, top="glaze", topcol=None, w=300, depth=150, rect=False, decor=None, plate_on=True):
    """Part de gâteau vue de 3/4 : face coupée visible avec les couches."""
    if plate_on:
        plate(s, cx, cy + 40, w * 0.95)
    H = sum(l[1] for l in layers)
    # points : pointe arrière gauche, coin avant droit
    T = (cx - w * 0.55, cy - 30)
    B = (cx + w * 0.45, cy + 30)
    A = (cx + w * 0.55 + (0 if rect else 30), cy - 70) if not rect else (cx + w * 0.62, cy - 52)
    Tb = (T[0] + (A[0] - B[0]), T[1] + (A[1] - B[1]))  # pour coupe rectangulaire
    top_y = -H
    # face extérieure (droite)
    side_col = layers[-1][0] if top != "glaze" else (topcol or layers[-1][0])
    s.add(shadow(cx + 20, cy + 42, w * 0.62, 26, 0.35))
    outer = [B, A, (A[0], A[1] + 0), (A[0], A[1] + H), (B[0], B[1] + H)]
    outer = [(B[0], B[1] + top_y), (A[0], A[1] + top_y), (A[0], A[1]), (B[0], B[1])]
    if rect:
        s.add(poly(outer, s.vgrad(shade(side_col, 0.9), shade(side_col, 0.7))))
        # bandes visibles sur le côté pour une coupe rectangulaire
        yb = 0
        for col, th, tex in layers:
            s.add(poly([(B[0], B[1] - yb), (A[0], A[1] - yb), (A[0], A[1] - yb - th), (B[0], B[1] - yb - th)], shade(col, 0.82)))
            yb += th
    else:
        dpath = (f"M{B[0]},{B[1]+top_y} Q{A[0]+18},{(A[1]+B[1])/2+top_y} {A[0]},{A[1]+top_y} "
                 f"L{A[0]},{A[1]} Q{A[0]+18},{(A[1]+B[1])/2} {B[0]},{B[1]} Z")
        s.add(path(dpath, s.vgrad(shade(side_col, 0.95), shade(side_col, 0.72))))
    # face coupée (vers le spectateur)
    yb = 0
    for col, th, tex in layers:
        p0 = (T[0], T[1] - yb)
        p1 = (B[0], B[1] - yb)
        q = [(T[0], T[1] - yb - th), (B[0], B[1] - yb - th), p1, p0]
        s.add(poly(q, s.vgrad(shade(col, 1.04), shade(col, 0.92))))
        texture(s, tex, col, T, B, yb, th)
        yb += th
    # dessus
    tc = topcol or layers[-1][0]
    if rect:
        tp = [(T[0], T[1] + top_y), (Tb[0], Tb[1] + top_y), (A[0], A[1] + top_y), (B[0], B[1] + top_y)]
        s.add(poly(tp, s.rgrad(shade(tc, 1.1), shade(tc, 0.95))))
    else:
        dtop = (f"M{T[0]},{T[1]+top_y} L{B[0]},{B[1]+top_y} Q{A[0]+18},{(A[1]+B[1])/2+top_y} {A[0]},{A[1]+top_y} Z")
        s.add(path(dtop, s.rgrad(shade(tc, 1.1), shade(tc, 0.95))))
    if top == "glaze":
        s.add(f'<path d="M{T[0]+40},{T[1]+top_y-4} L{B[0]-30},{B[1]+top_y-12}" stroke="#fff" stroke-opacity="0.3" stroke-width="6" stroke-linecap="round"/>')
    if decor:
        decor(s, T, B, A, top_y)
    return T, B, A, top_y


def texture(s, tex, col, T, B, yb, th):
    def lerp(t, dy):
        return (T[0] + (B[0] - T[0]) * t, T[1] + (B[1] - T[1]) * t - yb - dy)
    if tex == "sponge":
        for _ in range(int(18 * th / 20)):
            x, y = lerp(s.r.uniform(0.04, 0.96), s.r.uniform(2, th - 2))
            s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s.r.uniform(1,2.6):.1f}" fill="{shade(col,0.8)}" opacity="0.7"/>')
    elif tex == "strawberry":
        k = 7
        for i in range(k):
            x, y = lerp((i + 0.5) / k, th * 0.55)
            r = th * 0.42
            s.add(f'<path d="M{x-r},{y-r*0.9} C{x-r},{y+r*0.6} {x-r*0.3},{y+r} {x},{y+r*1.05} C{x+r*0.3},{y+r} {x+r},{y+r*0.6} {x+r},{y-r*0.9} Z" fill="{C["straw"]}"/>')
            s.add(f'<path d="M{x-r*0.6},{y-r*0.75} C{x-r*0.6},{y+r*0.4} {x-r*0.2},{y+r*0.75} {x},{y+r*0.8} C{x+r*0.2},{y+r*0.75} {x+r*0.6},{y+r*0.4} {x+r*0.6},{y-r*0.75} Z" fill="{C["straw_l"]}"/>')
    elif tex == "rasp":
        for i in range(9):
            x, y = lerp((i + 0.5) / 9, th * 0.5)
            s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{th*0.36:.1f}" fill="{C["rasp"]}"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{th*0.15:.1f}" fill="{C["rasp_d"]}"/>')
    elif tex == "cherry":
        for i in range(8):
            x, y = lerp((i + 0.5) / 8, th * 0.5)
            s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{th*0.3:.1f}" fill="{C["cherry"]}"/>')
    elif tex == "puff":
        for j in range(1, 5):
            dy = th * j / 5
            x0, y0 = lerp(0.0, dy)
            x1, y1 = lerp(1.0, dy)
            s.add(f'<path d="M{x0:.0f},{y0:.0f} Q{(x0+x1)/2:.0f},{(y0+y1)/2+s.r.uniform(-3,3):.0f} {x1:.0f},{y1:.0f}" stroke="{shade(col,0.75)}" stroke-width="1.5" fill="none"/>')
    elif tex == "crumb":
        for _ in range(26):
            x, y = lerp(s.r.uniform(0.03, 0.97), s.r.uniform(2, th - 2))
            s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s.r.uniform(1.5,3.5):.1f}" fill="{shade(col,s.r.choice([0.75,1.15]))}"/>')
    elif tex == "nuts":
        for _ in range(12):
            x, y = lerp(s.r.uniform(0.05, 0.95), s.r.uniform(3, th - 3))
            s.add(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="6" ry="3.5" fill="{C["pecan"]}"/>')
    elif tex == "chips":
        for _ in range(int(th / 2)):
            x, y = lerp(s.r.uniform(0.05, 0.95), s.r.uniform(3, th - 3))
            s.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="6" height="5" fill="{C["choc2"]}"/>')
    elif tex == "ladyfinger":
        for i in range(8):
            x, y = lerp((i + 0.5) / 8, th * 0.5)
            s.add(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{(B[0]-T[0])/18:.1f}" ry="{th*0.38:.1f}" fill="{shade(col,0.9)}"/>')
    elif tex == "carrot":
        for _ in range(30):
            x, y = lerp(s.r.uniform(0.03, 0.97), s.r.uniform(2, th - 2))
            s.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="5" height="1.6" fill="#D4632A" opacity="0.8"/>')
            if s.r.random() < 0.3:
                s.add(f'<ellipse cx="{x+8:.1f}" cy="{y:.1f}" rx="4" ry="2.5" fill="{C["pecan"]}"/>')
    elif tex == "vanilla":
        for _ in range(40):
            x, y = lerp(s.r.uniform(0.03, 0.97), s.r.uniform(2, th - 2))
            s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0.9" fill="#3B2618"/>')
    elif tex == "praline":
        for _ in range(18):
            x, y = lerp(s.r.uniform(0.05, 0.95), s.r.uniform(2, th - 2))
            s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{shade(col,0.7)}"/>')


# ----------------------------------------------- décors de dessus de part
def decor_berries(kinds, n=4, cream=None):
    def f(s, T, B, A, ty):
        pts = []
        for i in range(n):
            t = (i + 0.7) / (n + 0.4)
            x = T[0] + (B[0] - T[0]) * t * 0.85 + (A[0] - B[0]) * 0.35
            y = T[1] + (B[1] - T[1]) * t * 0.85 + (A[1] - B[1]) * 0.35 + ty
            pts.append((x, y))
        for x, y in sorted(pts, key=lambda p: p[1]):
            if cream:
                s.add(f'<ellipse cx="{x}" cy="{y-2}" rx="18" ry="11" fill="{cream}"/><path d="M{x-16},{y-2} Q{x},{y-34} {x+16},{y-2} Z" fill="{cream}"/>')
                berry(s, x, y - 26, s.r.choice(kinds), 0.85)
            else:
                berry(s, x, y - 8, s.r.choice(kinds), 1.0)
    return f


def decor_shavings(col, n=14, gold=True):
    def f(s, T, B, A, ty):
        for _ in range(n):
            t = s.r.uniform(0.15, 0.9)
            u = s.r.uniform(0.1, 0.8)
            x = T[0] + (B[0] - T[0]) * t + (A[0] - B[0]) * u
            y = T[1] + (B[1] - T[1]) * t + (A[1] - B[1]) * u + ty
            s.add(f'<path d="M{x},{y} q8,-10 18,-2 q-6,6 -18,2 Z" fill="{col}" stroke="{shade(col,0.7)}" stroke-width="1"/>')
        if gold:
            for _ in range(4):
                t = s.r.uniform(0.3, 0.8)
                x = T[0] + (B[0] - T[0]) * t + 30
                y = T[1] + (B[1] - T[1]) * t + ty - 12
                s.add(f'<polygon points="{x},{y} {x+9},{y+2} {x+5},{y+8} {x-2},{y+6}" fill="{C["gold"]}"/>')
    return f


def decor_sugar(col="#FFFFFF"):
    def f(s, T, B, A, ty):
        cx = (T[0] + A[0] + B[0]) / 3
        cy = (T[1] + A[1] + B[1]) / 3 + ty
        sugar_dust(s, cx, cy, (B[0] - T[0]) * 0.45, 30, 260, col, 0.9)
    return f


def decor_text(word, col):
    def f(s, T, B, A, ty):
        cx = (T[0] + A[0] + B[0]) / 3
        cy = (T[1] + A[1] + B[1]) / 3 + ty
        s.add(f'<text x="{cx}" y="{cy}" font-family="Pinyon Script" font-size="34" fill="{col}" text-anchor="middle" transform="skewX(-12) translate({cy*0.2} 0)">{word}</text>')
        for _ in range(3):
            x = cx + s.r.uniform(-60, 60)
            s.add(f'<polygon points="{x},{cy+14} {x+9},{cy+16} {x+5},{cy+22}" fill="{C["gold"]}"/>')
    return f


def decor_combo(*fs):
    def f(s, *a):
        for g in fs:
            g(s, *a)
    return f


# ----------------------------------------------- scènes par type
def blurred_whole(s, cx, top, rx, h, side, topc, extra=None):
    s.add('<g filter="url(#dof)" opacity="0.92">')
    stand(s, cx, top + h + 10, rx * 1.18)
    ry = cylinder(s, cx, top, rx, h, side, topc)
    if extra:
        extra(cx, top, rx, ry)
    s.add('</g>')


def k_slice(s, p):
    layers = p["layers"]
    if p.get("bg_cake", True):
        sidec = p.get("side", layers[-1][0])
        topc = p.get("topcol", layers[-1][0])

        def bgextra(cx, top, rx, ry):
            if p.get("berries"):
                toppings_on_ellipse(s, cx, top, rx, ry, p["berries"], 8, 0.62)
            if p.get("drip"):
                drips(s, cx, top, rx, ry, p["drip"], 14, 40)
        blurred_whole(s, 820, 300, 170, 150, sidec, topc, bgextra)
    deco = p.get("decor")
    slice_cake(s, 520, 640, layers, top=p.get("top", "glaze"), topcol=p.get("topcol"), w=p.get("w", 300),
               rect=p.get("rect", False), decor=deco)
    fork(s, 220, 820, -12)


def k_whole(s, p):
    """Gâteau entier sur présentoir ou plat."""
    cx, top, rx, h = 600, 400, 250, p.get("h", 150)
    if p.get("stand", True):
        stand(s, cx, top + h + 12, rx * 1.2)
    else:
        plate(s, cx, top + h + 6, rx * 1.25)
    side, topc = p["side"], p["topcol"]
    pat = p.get("pattern")

    def side_pattern(cx, top, rx, ry, h):
        if pat == "ladyfingers":
            n = 22
            for i in range(n):
                t = math.pi * (i + 0.5) / n
                x = cx - rx * math.cos(t)
                w = rx * math.pi / n * math.sin(t) * 0.92 + 2
                yb = top + h + ry * math.sin(t)
                s.add(f'<rect x="{x-w/2:.1f}" y="{top-ry*0.1+ry*math.sin(t)*0.3-28:.1f}" width="{w:.1f}" height="{yb-top+28-ry*math.sin(t)*0.3:.1f}" rx="{w/2:.1f}" fill="{shade(C["sponge"],0.96+0.1*math.sin(t))}" stroke="{shade(C["sponge"],0.82)}" stroke-width="1"/>')
            sugar_dust(s, cx, top + h * 0.3, rx, h * 0.5, 120)
            # ruban
            s.add(f'<path d="M{cx-rx},{top+h*0.55} A{rx},{ry} 0 0 0 {cx+rx},{top+h*0.55} L{cx+rx},{top+h*0.55+22} A{rx},{ry} 0 0 1 {cx-rx},{top+h*0.55+22} Z" fill="#B99B6B" opacity="0.92"/>')
        elif pat == "strawberries":
            n = 13
            for i in range(n):
                t = math.pi * (i + 0.5) / n
                x = cx - rx * math.cos(t)
                y = top + h * 0.42 + ry * math.sin(t)
                sc = 0.6 + 0.6 * math.sin(t)
                s.add(f'<g transform="translate({x:.1f} {y:.1f}) scale({sc*math.sin(t)*0.9+0.15:.2f} {sc:.2f})">')
                berry(s, 0, -10, "straw_half", 2.3)
                s.add('</g>')
        elif pat == "layers":
            for k, (col, frac) in enumerate(p.get("bands", [])):
                yy = top + h * frac
                s.add(f'<path d="M{cx-rx},{yy} A{rx},{ry} 0 0 0 {cx+rx},{yy}" stroke="{col}" stroke-width="{p.get("bandw",8)}" fill="none"/>')
        elif pat == "crosshatch":
            pass
    ry = cylinder(s, cx, top, rx, h, side, topc, side_pattern=side_pattern, glaze=p.get("glaze", False))
    if p.get("drip"):
        drips(s, cx, top, rx, ry, p["drip"], 18, 55)
        s.add(ell(cx, top, rx, ry, s.rgrad(shade(p["drip"], 1.12), shade(p["drip"], 0.9))))
    t = p.get("topping")
    if t == "berries":
        toppings_on_ellipse(s, cx, top, rx, ry, p["kinds"], 12, 0.66, 1.3)
        toppings_on_ellipse(s, cx, top, rx, ry, p["kinds"], 6, 0.3, 1.3)
    elif t == "rosettes":
        rosettes(s, cx, top, rx, ry, p.get("rcol", C["cream"]), 12, 20)
        if p.get("kinds"):
            toppings_on_ellipse(s, cx, top, rx, ry, p["kinds"], 5, 0.3, 1.3)
    elif t == "pineapple":
        for (dx, dy) in [(-120, -10), (0, -40), (120, -10), (-60, 40), (60, 40), (0, 5)]:
            x, y = cx + dx, top + dy * 0.9
            s.add(f'<ellipse cx="{x}" cy="{y}" rx="62" ry="22" fill="{C["pineapple"]}" stroke="{shade(C["caramel"],0.9)}" stroke-width="5"/>')
            s.add(f'<ellipse cx="{x}" cy="{y}" rx="16" ry="6" fill="{C["caramel"]}"/>')
            berry(s, x, y - 2, "cherry", 0.8) if False else s.add(f'<circle cx="{x}" cy="{y-2}" r="10" fill="{C["red"]}"/><circle cx="{x-3}" cy="{y-5}" r="3" fill="#fff" opacity="0.6"/>')
        s.add(f'<ellipse cx="{cx-70}" cy="{top-20}" rx="90" ry="12" fill="#fff" opacity="0.18"/>')
    elif t == "crosshatch":
        clip = s.uid("cl")
        s.defs.append(f'<clipPath id="{clip}"><ellipse cx="{cx}" cy="{top}" rx="{rx*0.96}" ry="{ry*0.94}"/></clipPath>')
        s.add(f'<g clip-path="url(#{clip})" stroke="{shade(topc,0.72)}" stroke-width="5" opacity="0.7">')
        for i in range(-8, 9):
            s.add(f'<line x1="{cx+i*40-200}" y1="{top-ry}" x2="{cx+i*40+200}" y2="{top+ry}"/>')
            s.add(f'<line x1="{cx+i*40+200}" y1="{top-ry}" x2="{cx+i*40-200}" y2="{top+ry}"/>')
        s.add('</g>')
    elif t == "cheesecake_coulis":
        s.add(ell(cx, top, rx * 0.93, ry * 0.9, s.rgrad(shade(p["coulis"], 1.2), p["coulis"])))
        s.add(f'<ellipse cx="{cx-60}" cy="{top-10}" rx="90" ry="12" fill="#fff" opacity="0.25"/>')
        toppings_on_ellipse(s, cx, top, rx, ry, p.get("kinds", ["rasp"]), 8, 0.55, 1.2)
    elif t == "sugar":
        sugar_dust(s, cx, top, rx * 0.95, ry * 0.92, 600)
    elif t == "shavings":
        for _ in range(40):
            a = s.r.uniform(0, math.tau)
            d = math.sqrt(s.r.random()) * 0.85
            x, y = cx + math.cos(a) * rx * d, top + math.sin(a) * ry * d
            s.add(f'<path d="M{x},{y} q9,-12 20,-2 q-7,7 -20,2 Z" fill="{p.get("scol",C["choc_l"])}" stroke="{shade(p.get("scol",C["choc_l"]),0.7)}"/>')
        if p.get("kinds"):
            toppings_on_ellipse(s, cx, top, rx, ry, p["kinds"], 9, 0.75, 1.2)
    elif t == "text":
        s.add(f'<text x="{cx}" y="{top+12}" font-family="Pinyon Script" font-size="58" fill="{p.get("tcol",C["gold"])}" text-anchor="middle">{p["word"]}</text>')
    elif t == "nuts":
        for _ in range(22):
            a = s.r.uniform(0, math.tau)
            d = math.sqrt(s.r.random()) * 0.85
            x, y = cx + math.cos(a) * rx * d, top + math.sin(a) * ry * d
            s.add(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="14" ry="7" fill="{p.get("ncol",C["almond"])}" stroke="{shade(p.get("ncol",C["almond"]),0.75)}" transform="rotate({s.r.randint(0,180)} {x:.0f} {y:.0f})"/>')
        sugar_dust(s, cx, top, rx * 0.9, ry * 0.85, 200)
    elif t == "choux_ring":   # saint-honoré
        rosettes(s, cx, top, rx * 0.75, ry * 0.75, C["cream"], 9, 22, 0.55)
        n = 12
        pts = []
        for i in range(n):
            a = math.tau * i / n
            pts.append((cx + math.cos(a) * rx * 0.86, top + math.sin(a) * ry * 0.86, math.sin(a)))
        for x, y, z in sorted(pts, key=lambda q: q[2]):
            s.add(f'<circle cx="{x}" cy="{y-18}" r="30" fill="{s.rgrad(C["golden_l"],C["golden_d"])}"/>')
            s.add(f'<ellipse cx="{x}" cy="{y-36}" rx="22" ry="10" fill="{C["caramel"]}"/><ellipse cx="{x-6}" cy="{y-39}" rx="8" ry="3" fill="#fff" opacity="0.4"/>')
    elif t == "fruits_mix":
        toppings_on_ellipse(s, cx, top, rx, ry, p["kinds"], 14, 0.7, 1.25)
        toppings_on_ellipse(s, cx, top, rx, ry, p["kinds"], 7, 0.35, 1.25)
    if p.get("slice_out"):
        pass


def tart_base(s, cx, top, rx, ry, crust=None, h=34):
    crust = crust or C["golden"]
    n = 34
    # bord cannelé
    s.add(f'<path d="M{cx-rx},{top} L{cx-rx},{top+h} A{rx},{ry} 0 0 0 {cx+rx},{top+h} L{cx+rx},{top} Z" fill="{s.hgrad(crust,0.75,1.1)}"/>')
    for i in range(n):
        t = math.pi * (i + 0.5) / n
        x = cx - rx * math.cos(t)
        s.add(f'<line x1="{x:.1f}" y1="{top+ry*math.sin(t)+4:.1f}" x2="{x:.1f}" y2="{top+h+ry*math.sin(t)-2:.1f}" stroke="{shade(crust,0.72)}" stroke-width="2" opacity="0.6"/>')
    s.add(ell(cx, top, rx, ry, s.rgrad(shade(crust, 1.15), crust)))
    return rx * 0.92, ry * 0.88


def k_tart(s, p):
    cx, top = 600, 560
    rx = p.get("rx", 300)
    ry = rx * 0.36
    plate(s, cx, top + 40, rx * 1.22)
    irx, iry = tart_base(s, cx, top, rx, ry, p.get("crust"))
    fill = p.get("fill", C["custard"])
    s.add(ell(cx, top + 2, irx, iry, s.rgrad(shade(fill, 1.12), shade(fill, 0.92))))
    t = p["top"]
    if t == "strawberries":
        rows = []
        for ring, n in ((0.86, 26), (0.66, 20), (0.46, 14), (0.24, 8), (0.0, 1)):
            for i in range(n):
                a = math.tau * i / n
                rows.append((cx + math.cos(a) * irx * ring, top + math.sin(a) * iry * ring))
        for x, y in sorted(rows, key=lambda q: q[1]):
            berry(s, x + s.r.uniform(-4, 4), y - 14, "straw_half", 1.45)
        s.add(f'<ellipse cx="{cx-80}" cy="{top-30}" rx="120" ry="10" fill="#fff" opacity="0.15"/>')
    elif t == "raspberries":
        rows = []
        for ring, n in ((0.85, 30), (0.66, 24), (0.47, 17), (0.28, 10), (0.08, 3)):
            for i in range(n):
                a = math.tau * i / n
                rows.append((cx + math.cos(a) * irx * ring, top + math.sin(a) * iry * ring))
        for x, y in sorted(rows, key=lambda q: q[1]):
            berry(s, x, y - 10, "rasp", 1.05)
        sugar_dust(s, cx, top, irx * 0.6, iry * 0.4, 120)
    elif t == "meringue":
        rows = []
        for ring, n in ((0.82, 24), (0.6, 18), (0.38, 12), (0.15, 5)):
            for i in range(n):
                a = math.tau * i / n + ring
                rows.append((cx + math.cos(a) * irx * ring, top + math.sin(a) * iry * ring))
        for x, y in sorted(rows, key=lambda q: q[1]):
            s.add(f'<path d="M{x-22},{y} Q{x-18},{y-34} {x+2},{y-50} Q{x+4},{y-30} {x+22},{y} Z" fill="{s.rgrad("#FFFDF6","#EADDC4",0.3,0.6)}"/>')
            s.add(f'<path d="M{x-6},{y-34} Q{x},{y-46} {x+2},{y-50} Q{x+4},{y-40} {x+6},{y-32} Z" fill="{C["caramel_l"]}" opacity="0.9"/>')
    elif t == "apples":
        for ring, n in ((0.86, 28), (0.6, 20), (0.34, 12)):
            for i in range(n):
                a = math.tau * i / n
                x = cx + math.cos(a) * irx * ring
                y = top + math.sin(a) * iry * ring
                ang = math.degrees(math.atan2(math.sin(a) * iry, math.cos(a) * irx)) + 90
                s.add(f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.0f}) scale(1 0.55)"><path d="M-26,0 Q0,-26 26,0 Q0,-12 -26,0 Z" fill="{C["apple"]}" stroke="{C["golden_d"]}" stroke-width="2"/><path d="M-24,-1 Q0,-26 24,-1" stroke="{C["apple_skin"]}" stroke-width="3" fill="none" opacity="0.7"/></g>')
        s.add(ell(cx, top, irx * 0.14, iry * 0.14, C["golden"]))
        s.add(f'<ellipse cx="{cx}" cy="{top}" rx="{irx}" ry="{iry}" fill="#F7C46A" opacity="0.18"/>')
    elif t == "chocolate":
        s.add(ell(cx, top + 2, irx, iry, s.rgrad(C["choc_l"], C["choc2"])))
        s.add(f'<path d="M{cx-irx*0.6},{top-iry*0.3} Q{cx},{top-iry*0.55} {cx+irx*0.5},{top-iry*0.25}" stroke="#fff" stroke-opacity="0.25" stroke-width="10" fill="none" stroke-linecap="round"/>')
        for _ in range(6):
            x, y = cx + s.r.uniform(-60, 80), top + s.r.uniform(-14, 14)
            s.add(f'<polygon points="{x},{y} {x+10},{y+3} {x+5},{y+10}" fill="{C["gold"]}"/>')
        sugar_dust(s, cx + irx * 0.4, top + iry * 0.35, 40, 12, 60, C["choc_l"], 0.5)
    elif t == "caramel":
        s.add(ell(cx, top + 2, irx, iry, s.rgrad(C["caramel_l"], C["caramel"])))
        s.add(f'<path d="M{cx-irx*0.6},{top-iry*0.3} Q{cx},{top-iry*0.55} {cx+irx*0.5},{top-iry*0.25}" stroke="#fff" stroke-opacity="0.3" stroke-width="10" fill="none" stroke-linecap="round"/>')
        sugar_dust(s, cx, top, irx * 0.7, iry * 0.6, 50, "#FFFFFF", 0.9)
        rows = [(cx + math.cos(a) * irx * 0.78, top + math.sin(a) * iry * 0.78) for a in [math.tau * i / 10 for i in range(10)]]
        for x, y in sorted(rows, key=lambda q: q[1]):
            s.add(f'<circle cx="{x}" cy="{y-8}" r="11" fill="{s.rgrad("#C08A55","#7A4A25")}"/>')
    elif t == "pears":
        for i in range(8):
            a = math.tau * i / 8
            x = cx + math.cos(a) * irx * 0.5
            y = top + math.sin(a) * iry * 0.5
            ang = math.degrees(math.atan2(math.sin(a) * iry, math.cos(a) * irx)) + 90
            s.add(f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang-90:.0f}) scale(1 0.6)"><path d="M-70,0 C-70,-26 -30,-30 0,-20 C30,-32 70,-36 70,0 C70,36 30,32 0,20 C-30,30 -70,26 -70,0 Z" fill="{s.rgrad("#F3E3A8",C["golden"])}"/>'
                  + "".join(f'<line x1="{-50+k*16}" y1="-18" x2="{-50+k*16}" y2="18" stroke="{C["golden_d"]}" stroke-width="1.5" opacity="0.5"/>' for k in range(7)) + '</g>')
        for _ in range(26):
            x, y = cx + s.r.uniform(-irx * 0.85, irx * 0.85), top + s.r.uniform(-iry * 0.8, iry * 0.8)
            if ((x - cx) / irx) ** 2 + ((y - top) / iry) ** 2 < 0.8:
                s.add(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="11" ry="6" fill="{C["almond"]}" stroke="{C["golden_d"]}" stroke-width="1" transform="rotate({s.r.randint(0,180)} {x:.0f} {y:.0f})"/>')
        sugar_dust(s, cx, top, irx * 0.8, iry * 0.7, 160)
    elif t == "flan":
        s.add(ell(cx, top + 2, irx, iry, s.rgrad("#E7B65E", "#B8742F")))
        for _ in range(26):
            x, y = cx + s.r.uniform(-irx * 0.8, irx * 0.8), top + s.r.uniform(-iry * 0.7, iry * 0.7)
            if ((x - cx) / irx) ** 2 + ((y - top) / iry) ** 2 < 0.75:
                s.add(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{s.r.uniform(8,26):.0f}" ry="{s.r.uniform(4,10):.0f}" fill="#7A4318" opacity="{s.r.uniform(0.3,0.7):.2f}" filter="url(#blur3)"/>')
    elif t == "walnuts":
        s.add(ell(cx, top + 2, irx, iry, s.rgrad(C["caramel_l"], C["caramel"])))
        rows = []
        for ring, n in ((0.8, 18), (0.52, 12), (0.24, 6)):
            for i in range(n):
                a = math.tau * i / n
                rows.append((cx + math.cos(a) * irx * ring, top + math.sin(a) * iry * ring))
        for x, y in sorted(rows, key=lambda q: q[1]):
            s.add(f'<g transform="translate({x:.0f} {y-6:.0f})"><ellipse rx="19" ry="11" fill="#9A6236"/><path d="M-15,0 Q-8,-8 0,0 Q8,-8 15,0 M-15,0 Q-8,8 0,0 Q8,8 15,0" stroke="#5E3618" stroke-width="2" fill="none"/></g>')
        s.add(f'<path d="M{cx-irx*0.6},{top-iry*0.3} Q{cx},{top-iry*0.55} {cx+irx*0.5},{top-iry*0.25}" stroke="#fff" stroke-opacity="0.25" stroke-width="8" fill="none"/>')
    elif t == "custard_fruit":
        toppings_on_ellipse(s, cx, top, irx, iry, p["kinds"], 14, 0.75, 1.3)
        toppings_on_ellipse(s, cx, top, irx, iry, p["kinds"], 7, 0.4, 1.3)
    elif t == "lime_coco":
        sugar_dust(s, cx, top, irx * 0.8, iry * 0.7, 300, "#FFFFFF", 0.95)
    for x, y in p.get("props", []):
        pass


def k_tatin(s, p):
    cx, top = 600, 560
    plate(s, cx, top + 50, 380)
    rx, ry = 300, 105
    s.add(f'<path d="M{cx-rx},{top} L{cx-rx+8},{top+40} A{rx},{ry} 0 0 0 {cx+rx-8},{top+40} L{cx+rx},{top} Z" fill="{s.hgrad(C["crust"],0.7,1.05)}"/>')
    s.add(ell(cx, top, rx, ry, C["caramel"]))
    rows = []
    for ring, n in ((0.75, 12), (0.38, 6), (0, 1)):
        for i in range(n):
            a = math.tau * i / n + 0.3
            rows.append((cx + math.cos(a) * rx * ring, top + math.sin(a) * ry * ring))
    for x, y in sorted(rows, key=lambda q: q[1]):
        s.add(f'<path d="M{x-42},{y+8} Q{x-40},{y-40} {x},{y-42} Q{x+40},{y-40} {x+42},{y+8} Z" fill="{s.rgrad("#E5A04E","#8A4A1A",0.4,0.25)}"/>')
        s.add(f'<path d="M{x-20},{y-28} Q{x},{y-38} {x+16},{y-28}" stroke="#fff" stroke-opacity="0.35" stroke-width="5" fill="none"/>')
    s.add(f'<path d="M{cx+rx-30},{top+30} q30,30 0,60" stroke="{C["caramel"]}" stroke-width="12" fill="none" opacity="0.8"/>')


def k_tartelettes(s, p):
    pos = [(400, 520), (790, 500), (600, 700)]
    for cx, top in sorted(pos, key=lambda q: q[1]):
        plate(s, cx, top + 30, 175)
        irx, iry = tart_base(s, cx, top, 130, 46, p.get("crust"), 26)
        s.add(ell(cx, top + 2, irx, iry, s.rgrad(shade(p.get("fill", C["vanilla"]), 1.1), p.get("fill", C["vanilla"]))))
        t = p.get("top", "swirl")
        if t == "swirl":
            for k, r in enumerate((80, 58, 36, 16)):
                y = top - k * 14
                s.add(f'<ellipse cx="{cx}" cy="{y}" rx="{r}" ry="{r*0.38+6}" fill="{s.rgrad("#FFFBEF",C["cream2"])}" stroke="{C["cream2"]}" stroke-width="2"/>')
            s.add(f'<path d="M{cx-4},{top-62} q3,-12 0,-22" stroke="{C["cream2"]}" stroke-width="6" fill="none" stroke-linecap="round"/>')
            s.add(f'<path d="M{cx-60},{top+30} q60,-30 120,-16" stroke="#3B2618" stroke-width="6" fill="none" stroke-linecap="round"/>')
        elif t == "lemon":
            s.add(ell(cx, top + 2, irx, iry, s.rgrad("#FBEA8C", C["lemon_d"])))
            s.add(f'<ellipse cx="{cx-20}" cy="{top-8}" rx="50" ry="8" fill="#fff" opacity="0.3"/>')
        elif t == "praline":
            s.add(ell(cx, top + 2, irx, iry, s.rgrad("#C79064", "#8A5530")))
            for _ in range(8):
                x, y = cx + s.r.uniform(-70, 70), top + s.r.uniform(-20, 20)
                s.add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="{s.rgrad("#C08A55","#7A4A25")}"/>')
        elif t == "berries":
            toppings_on_ellipse(s, cx, top, irx, iry, p.get("kinds", ["rasp", "blue"]), 9, 0.6, 1.0)


def k_items(s, p):
    """Biscuits / petites pièces disposés sur papier sulfurisé ou plat."""
    base = p.get("base", "parchment")
    if base == "parchment":
        parchment(s, 600, 650, 760, 360, -4)
    elif base == "plate":
        plate(s, 600, 660, 420)
    elif base == "board":
        board(s, 600, 660, 760, 330)
    item = p["item"]
    pos = p.get("pos") or [(380, 600), (560, 560), (740, 590), (460, 720), (660, 710), (840, 690), (300, 700), (920, 600)]
    k = p.get("isize", ISIZE.get(item, 1.0))
    for i, (x, y) in enumerate(sorted(pos, key=lambda q: q[1])):
        s.add(f'<g transform="translate({x} {y}) scale({k}) translate({-x} {-y})">')
        ITEMS[item](s, x, y, p, i)
        s.add('</g>')


ISIZE = dict(square=1.3, caramel=1.7, truffle=1.35, cupcake=1.3, rocher=1.3, financier=1.2, muffin=1.2, croissant=1.1,
             madeleine=1.05, linzer=1.05, macaron=1.15, painchoc=1.1, roll=1.1, beignet=1.1)


def it_cookie(s, x, y, p, i):
    col = p.get("col", C["golden"])
    pts = []
    for k in range(18):
        a = math.tau * k / 18
        r = 92 + s.r.uniform(-6, 6)
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r * 0.55))
    s.add(shadow(x + 6, y + 30, 92, 26, 0.25))
    s.add(poly([(a, b + 12) for a, b in pts], shade(col, 0.72)))
    s.add(poly(pts, s.rgrad(shade(col, 1.15), shade(col, 0.88))))
    for _ in range(9):
        cx_, cy_ = x + s.r.uniform(-60, 60), y + s.r.uniform(-30, 30)
        s.add(f'<path d="M{cx_:.0f},{cy_:.0f} l{s.r.uniform(10,18):.0f},-4 l3,{s.r.uniform(9,14):.0f} l-14,4 Z" fill="{p.get("chip",C["choc2"])}"/>')
    for _ in range(8):
        cx_, cy_ = x + s.r.uniform(-70, 70), y + s.r.uniform(-34, 34)
        s.add(f'<path d="M{cx_:.0f},{cy_:.0f} q10,-5 22,0" stroke="{shade(col,0.75)}" stroke-width="2" fill="none"/>')
    if p.get("flaky_salt"):
        sugar_dust(s, x, y, 50, 20, 14, "#FFFFFF", 0.95)
    if p.get("molten") and i == 0:
        s.add(f'<path d="M{x-50},{y-10} Q{x-20},{y+40} {x+10},{y+60} Q{x+30},{y+30} {x+40},{y-10} Z" fill="{C["choc"]}"/><path d="M{x-30},{y} q10,10 20,0" stroke="#fff" stroke-opacity="0.3" stroke-width="4" fill="none"/>')


def it_sable(s, x, y, p, i):
    col = p.get("col", C["golden"])
    r = 80
    s.add(shadow(x + 6, y + 40, r, 22, 0.25))
    s.add(f'<path d="M{x-r},{y} L{x-r},{y+30} A{r},{r*0.55} 0 0 0 {x+r},{y+30} L{x+r},{y} Z" fill="{s.hgrad(col,0.75,1.05)}"/>')
    for k in range(20):
        t = math.pi * (k + 0.5) / 20
        xx = x - r * math.cos(t)
        s.add(f'<line x1="{xx:.0f}" y1="{y+r*0.55*math.sin(t)+3:.0f}" x2="{xx:.0f}" y2="{y+30+r*0.55*math.sin(t)-3:.0f}" stroke="{shade(col,0.7)}" stroke-width="1.5" opacity="0.5"/>')
    s.add(ell(x, y, r, r * 0.55, s.rgrad(shade(col, 1.1), shade(col, 0.85))))
    clip = s.uid("cl")
    s.defs.append(f'<clipPath id="{clip}"><ellipse cx="{x}" cy="{y}" rx="{r*0.8}" ry="{r*0.44}"/></clipPath>')
    s.add(f'<g clip-path="url(#{clip})" stroke="{shade(col,0.7)}" stroke-width="3">')
    for k in range(-5, 6):
        s.add(f'<line x1="{x+k*22-40}" y1="{y-50}" x2="{x+k*22+40}" y2="{y+50}"/><line x1="{x+k*22+40}" y1="{y-50}" x2="{x+k*22-40}" y2="{y+50}"/>')
    s.add('</g>')


def it_madeleine(s, x, y, p, i):
    col = p.get("col", C["golden"])
    rot = s.r.randint(-30, 30)
    s.add(f'<g transform="rotate({rot} {x} {y})">')
    s.add(shadow(x + 5, y + 22, 85, 26, 0.25))
    if i % 2 == 0:   # face coquille
        shp = f"M{x-90},{y-10} C{x-92},{y-60} {x+80},{y-70} {x+92},{y} C{x+80},{y+50} {x-80},{y+45} {x-90},{y-10} Z"
        clip = s.uid("cl")
        s.defs.append(f'<clipPath id="{clip}"><path d="{shp}"/></clipPath>')
        s.add(f'<path d="{shp}" fill="{s.rgrad(shade(col,1.12),shade(col,0.72),0.6,0.4)}"/><g clip-path="url(#{clip})">')
        for k in range(-4, 5):
            s.add(f'<path d="M{x+80},{y} Q{x},{y+k*12} {x-80},{y+k*10-8}" stroke="{shade(col,0.68)}" stroke-width="2.5" fill="none" opacity="0.6"/>')
        s.add('</g>')
    else:            # face bosse
        s.add(f'<path d="M{x-90},{y-10} C{x-92},{y-60} {x+80},{y-70} {x+92},{y} C{x+80},{y+50} {x-80},{y+45} {x-90},{y-10} Z" fill="{s.rgrad(shade(col,1.25),shade(col,0.8),0.55,0.45)}"/>')
        s.add(f'<ellipse cx="{x+10}" cy="{y-8}" rx="40" ry="20" fill="{shade(col,1.2)}" opacity="0.7"/>')
    s.add('</g>')
    if p.get("sugar"):
        sugar_dust(s, x, y, 60, 26, 50)


def it_financier(s, x, y, p, i):
    col = p.get("col", C["golden"])
    w, h, d = 130, 34, 50
    s.add(shadow(x + 10, y + 34, 90, 20, 0.25))
    s.add(poly([(x - w / 2, y), (x + w / 2, y), (x + w / 2 - 8, y + h), (x - w / 2 + 8, y + h)], s.vgrad(shade(col, 0.95), shade(col, 0.7))))
    s.add(poly([(x - w / 2 + 14, y - d), (x + w / 2 + 14, y - d), (x + w / 2, y), (x - w / 2, y)], s.rgrad(shade(col, 1.15), shade(col, 0.85))))
    if p.get("topping") == "almonds":
        for _ in range(4):
            xx, yy = x + s.r.uniform(-40, 40), y - s.r.uniform(10, 40)
            s.add(f'<ellipse cx="{xx:.0f}" cy="{yy:.0f}" rx="10" ry="5" fill="{C["almond"]}" stroke="{C["golden_d"]}"/>')
    elif p.get("topping") == "rasp":
        berry(s, x + 4, y - 26, "rasp", 1.0)


def it_langue(s, x, y, p, i):
    rot = s.r.randint(-50, 50)
    s.add(f'<g transform="rotate({rot} {x} {y})">{shadow(x+4,y+10,110,14,0.2)}'
          f'<rect x="{x-110}" y="{y-16}" width="220" height="32" rx="16" fill="{C["golden_d"]}"/>'
          f'<rect x="{x-100}" y="{y-11}" width="200" height="22" rx="11" fill="{s.rgrad("#F2D9A0","#E3BD78")}"/></g>')


def it_linzer(s, x, y, p, i):
    col = p.get("col", C["golden_l"])
    r = 78
    s.add(shadow(x + 6, y + 30, r, 22, 0.25))
    s.add(ell(x, y + 12, r, r * 0.55, shade(col, 0.75)))
    s.add(ell(x, y, r, r * 0.55, s.rgrad(shade(col, 1.15), col)))
    s.add(f'<path d="M{x},{y+18} C{x-40},{y-6} {x-24},{y-34} {x},{y-16} C{x+24},{y-34} {x+40},{y-6} {x},{y+18} Z" fill="{s.rgrad("#E2525E",C["rasp_d"])}"/>')
    sugar_dust(s, x, y, r * 0.95, r * 0.5, 160)


def it_spritz(s, x, y, p, i):
    rot = s.r.randint(-20, 20)
    col = C["golden_l"]
    s.add(f'<g transform="rotate({rot} {x} {y})">')
    s.add(shadow(x, y + 16, 120, 18, 0.2))
    d = f"M{x-110},{y} " + " ".join(f"Q{x-110+k*44+11},{y+(-26 if k%2==0 else 26)} {x-110+k*44+22},{y} T{x-110+k*44+44},{y}" for k in range(5))
    s.add(f'<path d="{d}" stroke="{shade(col,0.75)}" stroke-width="34" fill="none" stroke-linecap="round"/>')
    s.add(f'<path d="{d}" stroke="{col}" stroke-width="26" fill="none" stroke-linecap="round"/>')
    s.add(f'<path d="{d}" stroke="{shade(col,0.8)}" stroke-width="2" fill="none" stroke-dasharray="3 6"/>')
    if i % 2 == 0:
        s.add(f'<path d="M{x+40},{y} T{x+120},{y}" stroke="{C["choc"]}" stroke-width="36" fill="none" stroke-linecap="round"/>')
    s.add('</g>')


def it_macaron(s, x, y, p, i):
    cols = p.get("cols", [C["pastel_rose"], C["pastel_pist"], C["pastel_van"], C["pastel_lav"], C["choc_l"]])
    col = cols[i % len(cols)]
    r = 62
    s.add(shadow(x + 4, y + 50, r, 16, 0.25))
    s.add(f'<path d="M{x-r},{y+20} L{x-r},{y+40} A{r},{r*0.4} 0 0 0 {x+r},{y+40} L{x+r},{y+20} Z" fill="{shade(col,0.88)}"/>')
    s.add(ell(x, y + 20, r * 0.93, r * 0.38, p.get("fill", "#F7EEDD")))
    s.add(f'<path d="M{x-r},{y} L{x-r},{y+18} A{r},{r*0.4} 0 0 0 {x+r},{y+18} L{x+r},{y} Z" fill="{s.hgrad(col,0.88,1.05)}"/>')
    s.add(f'<path d="M{x-r},{y+16} A{r},{r*0.4} 0 0 0 {x+r},{y+16}" stroke="{shade(col,0.8)}" stroke-width="4" stroke-dasharray="3 3" fill="none"/>')
    s.add(ell(x, y, r, r * 0.4, s.rgrad(shade(col, 1.1), col)))


def it_tuile(s, x, y, p, i):
    rot = s.r.randint(-30, 30)
    s.add(f'<g transform="rotate({rot} {x} {y})">{shadow(x,y+24,90,16,0.2)}'
          f'<path d="M{x-90},{y+10} Q{x},{y-40} {x+90},{y+10} Q{x},{y-14} {x-90},{y+10} Z" fill="{s.vgrad("#EFCF8F","#C88A40")}"/>')
    for _ in range(5):
        xx = x + s.r.uniform(-60, 60)
        s.add(f'<ellipse cx="{xx:.0f}" cy="{y-8:.0f}" rx="12" ry="5" fill="{C["almond"]}" stroke="{C["golden_d"]}"/>')
    s.add('</g>')


def it_rocher(s, x, y, p, i):
    s.add(shadow(x + 4, y + 36, 60, 14, 0.25))
    s.add(f'<path d="M{x-56},{y+30} Q{x-50},{y-50} {x},{y-60} Q{x+50},{y-50} {x+56},{y+30} Z" fill="{s.rgrad("#FFFDF6","#E8D7B4",0.4,0.3)}"/>')
    for _ in range(40):
        xx, yy = x + s.r.uniform(-44, 44), y + s.r.uniform(-48, 26)
        s.add(f'<path d="M{xx:.0f},{yy:.0f} q4,-3 8,0" stroke="#D9C49C" stroke-width="2" fill="none"/>')
    s.add(f'<path d="M{x-58},{y+18} Q{x},{y+42} {x+58},{y+18} L{x+56},{y+34} Q{x},{y+52} {x-56},{y+34} Z" fill="{C["choc"]}"/>')
    s.add(f'<path d="M{x-30},{y-20} q30,-10 50,10" stroke="#E6C793" stroke-width="5" fill="none" opacity="0.8"/>')


def it_eclair(s, x, y, p, i):
    glaze = p.get("glaze", C["choc"])
    w = 290
    rot = -14 + i * 4
    s.add(f'<g transform="rotate({rot} {x} {y})">')
    s.add(shadow(x + 10, y + 46, w / 2 + 10, 20, 0.3))
    s.add(f'<rect x="{x-w/2}" y="{y-36}" width="{w}" height="80" rx="40" fill="{s.vgrad(C["golden_l"],C["golden_d"])}"/>')
    for k in range(10):
        xx = x - w / 2 + 30 + k * 25
        s.add(f'<path d="M{xx},{y+10} l8,20" stroke="{C["crust_d"]}" stroke-width="2" opacity="0.5"/>')
    s.add(f'<rect x="{x-w/2+6}" y="{y-44}" width="{w-12}" height="44" rx="22" fill="{s.vgrad(shade(glaze,1.25),glaze)}"/>')
    s.add(f'<rect x="{x-w/2+40}" y="{y-38}" width="{w-110}" height="7" rx="3.5" fill="#fff" opacity="0.28"/>')
    if p.get("decor") == "gold":
        for k in range(4):
            xx = x - 60 + k * 36
            s.add(f'<polygon points="{xx},{y-30} {xx+9},{y-26} {xx+4},{y-20}" fill="{C["gold"]}"/>')
    elif p.get("decor") == "nuts":
        for k in range(7):
            s.add(f'<circle cx="{x-90+k*30}" cy="{y-24}" r="5" fill="{C["almond"]}"/>')
    s.add('</g>')


def it_chou(s, x, y, p, i):
    r = p.get("r", 72)
    s.add(shadow(x + 6, y + r * 0.7, r * 0.95, 16, 0.3))
    pts = []
    for k in range(22):
        a = math.tau * k / 22
        rr = r * (1 + s.r.uniform(-0.05, 0.05))
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr * 0.85))
    s.add(poly(pts, s.rgrad(C["golden_l"], C["golden_d"], 0.4, 0.3)))
    for _ in range(8):
        xx, yy = x + s.r.uniform(-r * 0.6, r * 0.6), y + s.r.uniform(-r * 0.6, r * 0.3)
        s.add(f'<path d="M{xx:.0f},{yy:.0f} q{s.r.uniform(-14,14):.0f},6 {s.r.uniform(8,20):.0f},2" stroke="{C["crust_d"]}" stroke-width="2" fill="none" opacity="0.55"/>')
    t = p.get("top")
    if t == "sugar":
        sugar_dust(s, x, y - r * 0.4, r * 0.8, r * 0.4, 140)
    elif t == "pearl":
        for _ in range(14):
            s.add(f'<circle cx="{x+s.r.uniform(-r*0.6,r*0.6):.0f}" cy="{y+s.r.uniform(-r*0.7,0):.0f}" r="{s.r.uniform(3,5):.1f}" fill="#FFFFFF" stroke="#E8E0D0"/>')
    elif t == "cream_cut" and i == 0:
        s.add(f'<path d="M{x-r},{y-4} Q{x-r*0.6},{y-r*0.6} {x-r*0.3},{y-10} Q{x},{y-r*0.7} {x+r*0.3},{y-10} Q{x+r*0.6},{y-r*0.6} {x+r},{y-4} Z" fill="{C["custard"]}"/>')
        s.add(f'<path d="M{x-r*0.95},{y-6} Q{x},{y-r*1.5} {x+r*0.95},{y-6} Q{x},{y-r*0.5} {x-r*0.95},{y-6} Z" fill="{s.rgrad(C["golden_l"],C["golden_d"])}" transform="translate(0 {-r*0.35})"/>')
        sugar_dust(s, x, y - r * 0.9, r * 0.6, r * 0.25, 80)
    elif t == "choc_sauce":
        s.add(f'<path d="M{x-r*0.8},{y-r*0.5} Q{x},{y-r*1.0} {x+r*0.8},{y-r*0.5} Q{x+r*0.7},{y} {x+r*0.6},{y+r*0.4} Q{x+r*0.4},{y-r*0.1} {x+r*0.2},{y+r*0.2} Q{x},{y-r*0.2} {x-r*0.3},{y+r*0.3} Q{x-r*0.5},{y-r*0.1} {x-r*0.8},{y-r*0.5} Z" fill="{s.vgrad(C["choc_l"],C["choc2"])}"/>')
        s.add(f'<path d="M{x-r*0.4},{y-r*0.75} q{r*0.3},-{r*0.12} {r*0.6},0" stroke="#fff" stroke-opacity="0.3" stroke-width="4" fill="none"/>')


def it_religieuse(s, x, y, p, i):
    glaze = p.get("glaze", C["glaze_coffee"])
    s.add(shadow(x + 6, y + 60, 80, 18, 0.3))
    s.add(f'<ellipse cx="{x}" cy="{y}" rx="80" ry="64" fill="{s.rgrad(C["golden_l"],C["golden_d"])}"/>')
    s.add(f'<path d="M{x-74},{y-20} Q{x},{y-90} {x+74},{y-20} Q{x+40},{y-6} {x},{y-10} Q{x-40},{y-6} {x-74},{y-20} Z" fill="{s.vgrad(shade(glaze,1.2),glaze)}"/>')
    for k in range(9):
        xx = x - 44 + k * 11
        s.add(f'<path d="M{xx},{y-56} q4,-14 8,0" fill="{C["cream2"]}" stroke="{shade(C["cream2"],0.85)}"/>')
    s.add(f'<ellipse cx="{x}" cy="{y-86}" rx="44" ry="36" fill="{s.rgrad(C["golden_l"],C["golden_d"])}"/>')
    s.add(f'<path d="M{x-40},{y-96} Q{x},{y-136} {x+40},{y-96} Q{x},{y-86} {x-40},{y-96} Z" fill="{s.vgrad(shade(glaze,1.2),glaze)}"/>')
    s.add(f'<path d="M{x-8},{y-120} q8,-14 16,0 Z" fill="{C["cream2"]}"/>')


def it_square(s, x, y, p, i):
    """Carré type brownie (cube en 3/4)."""
    layers = p["layers"]  # [(col, h, tex)]
    w, d = 120, 60
    H = sum(l[1] for l in layers)
    s.add(shadow(x + 12, y + 18, 86, 22, 0.3))
    yb = 0
    for col, h, tex in layers:
        s.add(poly([(x - w / 2, y - yb), (x + w / 2, y - yb), (x + w / 2, y - yb - h), (x - w / 2, y - yb - h)], s.vgrad(shade(col, 1.02), shade(col, 0.86))))
        s.add(poly([(x + w / 2, y - yb), (x + w / 2 + d * 0.6, y - yb - d * 0.5), (x + w / 2 + d * 0.6, y - yb - d * 0.5 - h), (x + w / 2, y - yb - h)], shade(col, 0.7)))
        for _ in range(int(h / 6)):
            xx, yy = x + s.r.uniform(-w / 2 + 6, w / 2 - 6), y - yb - s.r.uniform(3, h - 3)
            if tex == "chips":
                s.add(f'<rect x="{xx:.0f}" y="{yy:.0f}" width="9" height="6" fill="{C["choc2"]}"/>')
            elif tex == "white":
                s.add(f'<rect x="{xx:.0f}" y="{yy:.0f}" width="9" height="6" fill="{C["white_choc"]}"/>')
            elif tex == "nuts":
                s.add(f'<ellipse cx="{xx:.0f}" cy="{yy:.0f}" rx="7" ry="4" fill="{C["pecan"]}"/>')
            elif tex == "crumb":
                s.add(f'<circle cx="{xx:.0f}" cy="{yy:.0f}" r="2" fill="{shade(col,0.75)}"/>')
            elif tex == "peanut":
                s.add(f'<ellipse cx="{xx:.0f}" cy="{yy:.0f}" rx="6" ry="4" fill="#C9955A"/>')
            elif tex == "coco":
                s.add(f'<path d="M{xx:.0f},{yy:.0f} q4,-3 8,0" stroke="#D9C49C" stroke-width="2" fill="none"/>')
        yb += h
    topc = p.get("topcol", layers[-1][0])
    s.add(poly([(x - w / 2, y - H), (x + w / 2, y - H), (x + w / 2 + d * 0.6, y - H - d * 0.5), (x - w / 2 + d * 0.6, y - H - d * 0.5)], s.rgrad(shade(topc, 1.15), topc)))
    if p.get("crackle"):
        for _ in range(5):
            xx, yy = x + s.r.uniform(-40, 50), y - H - s.r.uniform(5, 25)
            s.add(f'<path d="M{xx:.0f},{yy:.0f} l14,-3 l10,4" stroke="{shade(topc,1.35)}" stroke-width="1.5" fill="none" opacity="0.7"/>')
    if p.get("topnuts"):
        s.add(f'<ellipse cx="{x+10}" cy="{y-H-16}" rx="16" ry="8" fill="{C["pecan"]}"/><path d="M{x-2},{y-H-16} q12,-6 24,0" stroke="{shade(C["pecan"],0.6)}" stroke-width="2" fill="none"/>')
    if p.get("swirl"):
        s.add(f'<path d="M{x-40},{y-H-10} q20,-14 40,-4 q20,10 50,-10" stroke="{p["swirl"]}" stroke-width="5" fill="none"/>')
    if p.get("salt"):
        sugar_dust(s, x + 15, y - H - 14, 40, 10, 12, "#FFFFFF", 1)


def it_truffle(s, x, y, p, i):
    col = p.get("col", C["choc_l"])
    s.add(shadow(x + 4, y + 32, 40, 10, 0.3))
    pts = [(x + math.cos(a) * 42 * (1 + s.r.uniform(-0.06, 0.06)), y + math.sin(a) * 38 * (1 + s.r.uniform(-0.06, 0.06))) for a in [k * math.tau / 16 for k in range(16)]]
    s.add(poly(pts, s.rgrad(shade(col, 1.15), shade(col, 0.6))))
    sugar_dust(s, x, y, 34, 30, 50, shade(col, 1.25), 0.6)


def it_caramel(s, x, y, p, i):
    s.add(f'<g transform="rotate({s.r.randint(-25,25)} {x} {y})">')
    s.add(shadow(x + 4, y + 20, 50, 12, 0.25))
    if i % 3 == 0:  # emballé
        s.add(f'<path d="M{x-70},{y-24} L{x-40},{y-14} L{x+40},{y-14} L{x+70},{y-24} L{x+70},{y+24} L{x+40},{y+14} L{x-40},{y+14} L{x-70},{y+24} Z" fill="#F7F1E4" stroke="#E2D6BE"/>')
        s.add(f'<rect x="{x-40}" y="{y-14}" width="80" height="28" fill="{C["caramel_l"]}" opacity="0.4"/>')
    else:
        s.add(poly([(x - 34, y - 10), (x + 34, y - 10), (x + 34, y + 22), (x - 34, y + 22)], s.vgrad(C["caramel_l"], C["caramel"])))
        s.add(poly([(x - 34, y - 10), (x + 34, y - 10), (x + 48, y - 28), (x - 20, y - 28)], s.rgrad("#E5AE66", C["caramel_l"])))
        s.add(f'<circle cx="{x+6}" cy="{y-20}" r="2" fill="#fff"/><circle cx="{x-8}" cy="{y-18}" r="1.6" fill="#fff"/>')
    s.add('</g>')


def it_cupcake(s, x, y, p, i):
    col = p.get("frost", C["cream"])
    s.add(shadow(x + 6, y + 70, 70, 14, 0.3))
    s.add(f'<path d="M{x-62},{y} L{x-48},{y+70} L{x+48},{y+70} L{x+62},{y} Z" fill="{s.hgrad(p.get("case","#E9D6B8"),0.8,1.05)}"/>')
    for k in range(9):
        xx = x - 56 + k * 14
        s.add(f'<line x1="{xx}" y1="{y+2}" x2="{xx+ (x-xx)*0.2:.0f}" y2="{y+68}" stroke="#C9B08C" stroke-width="1.5"/>')
    s.add(ell(x, y, 66, 20, C["sponge"]))
    for k, (r, dy) in enumerate(((64, -6), (52, -30), (38, -52), (22, -70))):
        s.add(f'<ellipse cx="{x}" cy="{y+dy}" rx="{r}" ry="{r*0.4+6}" fill="{s.rgrad(shade(col,1.06),shade(col,0.9))}"/>')
    s.add(f'<path d="M{x-6},{y-80} q6,-22 10,-4" fill="{col}"/>')
    if p.get("sprinkle"):
        for _ in range(10):
            s.add(f'<rect x="{x+s.r.uniform(-40,40):.0f}" y="{y+s.r.uniform(-60,-10):.0f}" width="7" height="2.5" fill="{C["gold"]}" transform="rotate({s.r.randint(0,180)})" transform-origin="{x} {y}"/>')
    if p.get("berry"):
        berry(s, x, y - 84, p["berry"], 1.0)


def it_muffin(s, x, y, p, i):
    s.add(shadow(x + 6, y + 70, 70, 14, 0.3))
    s.add(f'<path d="M{x-58},{y} L{x-46},{y+70} L{x+46},{y+70} L{x+58},{y} Z" fill="{s.hgrad("#F2E8D8",0.82,1.04)}"/>')
    for k in range(9):
        xx = x - 52 + k * 13
        s.add(f'<line x1="{xx}" y1="{y+2}" x2="{xx+(x-xx)*0.2:.0f}" y2="{y+68}" stroke="#D8C9AE" stroke-width="1.5"/>')
    col = p.get("col", C["golden"])
    s.add(f'<path d="M{x-74},{y+6} Q{x-82},{y-70} {x},{y-76} Q{x+82},{y-70} {x+74},{y+6} Q{x},{y+18} {x-74},{y+6} Z" fill="{s.rgrad(shade(col,1.18),shade(col,0.82),0.45,0.3)}"/>')
    for _ in range(7):
        kind = p.get("dots", "blue")
        xx, yy = x + s.r.uniform(-50, 50), y + s.r.uniform(-55, -5)
        if kind == "blue":
            berry(s, xx, yy, "blue", 0.75)
        else:
            s.add(f'<rect x="{xx:.0f}" y="{yy:.0f}" width="9" height="7" fill="{C["choc2"]}"/>')
    if p.get("sugar"):
        sugar_dust(s, x, y - 40, 50, 20, 40, "#FFFFFF", 0.95)


def it_croissant(s, x, y, p, i):
    rot = s.r.randint(-20, 20)
    s.add(f'<g transform="rotate({rot} {x} {y})">')
    s.add(shadow(x + 8, y + 50, 150, 22, 0.3))
    segs = [(-125, 28, -18), (-80, 40, -8), (-28, 52, 0), (28, 52, 0), (80, 40, 8), (125, 28, 18)]
    for dx, r, a in sorted(segs, key=lambda q: -abs(q[0])):
        cy_ = y + abs(dx) * 0.22
        s.add(f'<ellipse cx="{x+dx}" cy="{cy_}" rx="{r*0.95}" ry="{r}" fill="{s.rgrad("#E9A85A","#9C5524",0.4,0.3)}" transform="rotate({a*3} {x+dx} {cy_})"/>')
        s.add(f'<path d="M{x+dx-r*0.6},{cy_-r*0.5} Q{x+dx},{cy_+r*0.2} {x+dx+r*0.6},{cy_-r*0.5}" stroke="#7E421A" stroke-width="2" fill="none" opacity="0.5"/>')
    s.add('</g>')


def it_painchoc(s, x, y, p, i):
    w, h = 200, 70
    rot = s.r.randint(-12, 12)
    s.add(f'<g transform="rotate({rot} {x} {y})">{shadow(x+8,y+42,115,18,0.3)}')
    s.add(f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="22" fill="{s.vgrad("#E5A257","#9E5826")}"/>')
    for k in range(4):
        s.add(f'<path d="M{x-w/2+10},{y-h/2+14+k*13} Q{x},{y-h/2+8+k*13} {x+w/2-10},{y-h/2+14+k*13}" stroke="#7E421A" stroke-width="1.6" fill="none" opacity="0.45"/>')
    for dy in (-12, 12):
        s.add(f'<rect x="{x-w/2-8}" y="{y+dy-6}" width="16" height="12" rx="3" fill="{C["choc"]}"/>')
    s.add(f'<rect x="{x-60}" y="{y-h/2+6}" width="120" height="6" rx="3" fill="#fff" opacity="0.2"/></g>')


def it_chausson(s, x, y, p, i):
    rot = s.r.randint(-15, 15)
    s.add(f'<g transform="rotate({rot} {x} {y})">{shadow(x+6,y+50,120,20,0.3)}')
    s.add(f'<path d="M{x-120},{y+30} Q{x-120},{y-80} {x},{y-84} Q{x+120},{y-80} {x+120},{y+30} Q{x},{y+56} {x-120},{y+30} Z" fill="{s.rgrad("#ECB466","#A3602A",0.45,0.35)}"/>')
    for k in range(-3, 4):
        s.add(f'<path d="M{x},{y-50} Q{x+k*18},{y-20} {x+k*30},{y+20}" stroke="#86461C" stroke-width="2" fill="none" opacity="0.55"/>')
    s.add(f'<path d="M{x-118},{y+30} Q{x},{y+56} {x+118},{y+30}" stroke="#86461C" stroke-width="4" stroke-dasharray="6 8" fill="none" opacity="0.6"/></g>')


def it_roll(s, x, y, p, i):
    """Cinnamon roll vu de dessus 3/4."""
    r = 78
    s.add(shadow(x + 6, y + 30, r, 18, 0.25))
    s.add(f'<path d="M{x-r},{y} L{x-r},{y+26} A{r},{r*0.6} 0 0 0 {x+r},{y+26} L{x+r},{y} Z" fill="{s.hgrad("#D79A55",0.75,1.05)}"/>')
    s.add(ell(x, y, r, r * 0.6, s.rgrad("#ECC283", "#C88A4A")))
    d = ""
    for k in range(80):
        t = k / 79 * 3.2 * math.tau
        rr = 6 + k / 79 * (r - 10)
        d += ("M" if k == 0 else "L") + f"{x+math.cos(t)*rr:.1f},{y+math.sin(t)*rr*0.6:.1f} "
    s.add(f'<path d="{d}" stroke="#8E5631" stroke-width="5" fill="none"/>')
    if p.get("icing"):
        s.add(f'<path d="M{x-60},{y-10} q20,-24 40,0 t40,0 t40,0" stroke="#FFFDF5" stroke-width="9" fill="none" stroke-linecap="round" opacity="0.92"/>')


def it_beignet(s, x, y, p, i):
    r = 70
    s.add(shadow(x + 6, y + r * 0.6, r, 16, 0.3))
    s.add(ell(x, y, r, r * 0.78, s.rgrad("#E8B06A", "#B26A2C", 0.4, 0.3)))
    s.add(f'<ellipse cx="{x}" cy="{y+4}" rx="{r}" ry="9" fill="#F4DDB1" opacity="0.9"/>')
    sugar_dust(s, x, y - 14, r * 0.85, r * 0.55, 260)
    if i == 0:
        s.add(f'<path d="M{x+r*0.6},{y-2} q16,6 20,18 q-8,6 -22,-4 Z" fill="{C["rasp"]}"/>')


def it_chouquette(s, x, y, p, i):
    p2 = dict(p)
    p2["r"] = 44
    p2["top"] = "pearl"
    it_chou(s, x, y, p2, i)


def it_bread_slice(s, x, y, p, i):
    """Tranche de cake debout (pour les loafs)."""
    col = p.get("crumb", C["sponge"])
    s.add(f'<g transform="rotate({p.get("rot",-8)} {x} {y})">')
    s.add(shadow(x + 6, y + 110, 80, 14, 0.28))
    s.add(f'<path d="M{x-72},{y+110} L{x-72},{y-30} Q{x-70},{y-92} {x},{y-98} Q{x+70},{y-92} {x+72},{y-30} L{x+72},{y+110} Z" fill="{p.get("crustc",C["crust"])}"/>')
    s.add(f'<path d="M{x-64},{y+104} L{x-64},{y-28} Q{x-62},{y-84} {x},{y-88} Q{x+62},{y-84} {x+64},{y-28} L{x+64},{y+104} Z" fill="{s.rgrad(shade(col,1.08),shade(col,0.94))}"/>')
    if p.get("marble"):
        s.add(f'<path d="M{x-64},{y+40} C{x-30},{y-30} {x+10},{y+80} {x+64},{y-10} L{x+64},{y+30} C{x+20},{y+100} {x-20},{y+20} {x-64},{y+80} Z" fill="{C["choc_l"]}"/>')
        s.add(f'<path d="M{x-40},{y-60} C{x-10},{y-20} {x+20},{y-80} {x+50},{y-40} C{x+20},{y-50} {x},{y-10} {x-40},{y-60} Z" fill="{C["choc_l"]}"/>')
    for _ in range(40):
        xx, yy = x + s.r.uniform(-56, 56), y + s.r.uniform(-70, 96)
        s.add(f'<circle cx="{xx:.0f}" cy="{yy:.0f}" r="{s.r.uniform(1,2.4):.1f}" fill="{shade(col,0.78)}" opacity="0.65"/>')
    if p.get("seeds"):
        for _ in range(30):
            s.add(f'<circle cx="{x+s.r.uniform(-56,56):.0f}" cy="{y+s.r.uniform(-70,96):.0f}" r="1.3" fill="#2B2B33"/>')
    if p.get("bits"):
        for _ in range(10):
            s.add(f'<ellipse cx="{x+s.r.uniform(-50,50):.0f}" cy="{y+s.r.uniform(-60,90):.0f}" rx="6" ry="4" fill="{p["bits"]}"/>')
    s.add('</g>')


def k_loaf(s, p):
    board(s, 600, 650, 820, 330)
    x, y, w, h, d = 520, 600, 420, 130, 110
    crust = p.get("crust", C["crust"])
    s.add(shadow(x + 20, y + 30, 260, 34, 0.32))
    # face avant
    s.add(f'<path d="M{x-w/2},{y} L{x-w/2+10},{y-h} L{x+w/2-10},{y-h} L{x+w/2},{y} Z" fill="{s.vgrad(shade(crust,1.05),shade(crust,0.75))}"/>')
    # dessus bombé
    s.add(f'<path d="M{x-w/2+10},{y-h} Q{x-w/2+30},{y-h-60} {x-w/2+10+d*0.7},{y-h-d*0.45-30} L{x+w/2-10+d*0.7},{y-h-d*0.45-30} Q{x+w/2+10},{y-h-50} {x+w/2-10},{y-h} Z" fill="{s.rgrad(shade(crust,1.2),shade(crust,0.85),0.5,0.4)}"/>')
    s.add(f'<path d="M{x-w/2+70},{y-h-30} Q{x},{y-h-70} {x+w/2-30},{y-h-38}" stroke="{shade(crust,0.65)}" stroke-width="7" fill="none" stroke-linecap="round"/>')
    s.add(f'<path d="M{x-w/2+76},{y-h-36} Q{x},{y-h-74} {x+w/2-36},{y-h-44}" stroke="{shade(crust,1.35)}" stroke-width="3" fill="none"/>')
    # face coupée (droite)
    col = p.get("crumb", C["sponge"])
    fx = x + w / 2
    face = [(fx, y), (fx - 10, y - h), (fx - 10 + d * 0.7, y - h - d * 0.45), (fx + d * 0.7, y - d * 0.45)]
    s.add(poly(face, s.rgrad(shade(col, 1.08), shade(col, 0.92))))
    if p.get("marble"):
        s.add(f'<path d="M{fx},{y-40} C{fx+30},{y-90} {fx+40},{y-30} {fx+70},{y-100} L{fx+70},{y-70} C{fx+40},{y-10} {fx+20},{y-70} {fx},{y-10} Z" fill="{C["choc_l"]}"/>')
    if p.get("glaze"):
        g = p["glaze"]
        s.add(f'<path d="M{x-w/2+10},{y-h-4} Q{x-w/2+30},{y-h-62} {x-w/2+10+d*0.7},{y-h-d*0.45-32} L{x+w/2-10+d*0.7},{y-h-d*0.45-32} Q{x+w/2+10},{y-h-52} {x+w/2-10},{y-h-4} '
              + " ".join(f"L{x+w/2-10-k*40},{y-h+ (s.r.uniform(10,40) if k%2 else 0):.0f}" for k in range(1, 10)) + " Z\" fill=\"" + g + "\"/>")
        if p.get("zest"):
            for _ in range(20):
                xx, yy = x + s.r.uniform(-w / 2 + 40, w / 2), y - h - s.r.uniform(30, 70)
                s.add(f'<path d="M{xx:.0f},{yy:.0f} q6,-3 12,0" stroke="{p["zest"]}" stroke-width="3" fill="none"/>')
    if p.get("banana"):
        s.add(f'<path d="M{x-w/2+40},{y-h-50} Q{x},{y-h-110} {x+w/2-20},{y-h-56} Q{x},{y-h-80} {x-w/2+40},{y-h-50} Z" fill="#E9C46A" stroke="#A9772E" stroke-width="3"/>')
    if p.get("sugar"):
        sugar_dust(s, x + 40, y - h - 40, w * 0.4, 30, 200)
    # tranches
    sp = dict(p)
    it_bread_slice(s, 880, 640, dict(sp, rot=10), 0)
    it_bread_slice(s, 790, 700, dict(sp, rot=-6), 1)


def k_bread(s, p):
    board(s, 600, 650, 860, 340)
    kind = p["bread"]
    col_hi, col_lo = "#E9A85A", "#8E4A1C"
    if kind == "brioche":
        x, y = 560, 620
        s.add(shadow(x + 20, y + 20, 260, 30, 0.3))
        s.add(f'<path d="M{x-220},{y} L{x-210},{y-80} L{x+210},{y-80} L{x+220},{y} Z" fill="{s.vgrad("#C7782E","#8A4718")}"/>')
        for k in range(6):
            bx = x - 180 + k * 72
            s.add(f'<ellipse cx="{bx}" cy="{y-100}" rx="48" ry="52" fill="{s.rgrad("#E8A456","#9A531F",0.4,0.3)}"/>')
            s.add(f'<ellipse cx="{bx-12}" cy="{y-124}" rx="16" ry="9" fill="#fff" opacity="0.25"/>')
        if p.get("pearl"):
            for _ in range(40):
                s.add(f'<circle cx="{x+s.r.uniform(-210,210):.0f}" cy="{y-100+s.r.uniform(-40,10):.0f}" r="3.5" fill="#fff"/>')
        it_bread_slice(s, 860, 680, dict(crumb="#F6DEAA", crustc="#B5662A", rot=8), 0)
    elif kind == "tressee":
        x, y = 580, 640
        s.add(shadow(x + 20, y + 20, 300, 34, 0.3))
        for k in range(9):
            bx = x - 260 + k * 64
            for side in (-1, 1):
                s.add(f'<ellipse cx="{bx+side*14}" cy="{y-50+side*18}" rx="52" ry="34" transform="rotate({side*35} {bx+side*14} {y-50+side*18})" fill="{s.rgrad(col_hi,col_lo,0.4,0.3)}" stroke="#7A3E16" stroke-width="1.5"/>')
        for _ in range(60):
            s.add(f'<circle cx="{x+s.r.uniform(-260,260):.0f}" cy="{y-50+s.r.uniform(-40,30):.0f}" r="3.5" fill="#fff"/>')
    elif kind == "painlait":
        for k, (x, y) in enumerate([(380, 600), (600, 580), (820, 600), (490, 720), (710, 720)]):
            s.add(shadow(x + 10, y + 40, 110, 18, 0.3))
            s.add(f'<ellipse cx="{x}" cy="{y}" rx="110" ry="54" fill="{s.rgrad("#E8A456","#9A531F",0.45,0.3)}"/>')
            for j in range(-3, 4):
                s.add(f'<path d="M{x+j*26-8},{y-34} l14,-10 l2,14" fill="#F6DEAA"/>')
            for _ in range(12):
                s.add(f'<circle cx="{x+s.r.uniform(-80,80):.0f}" cy="{y+s.r.uniform(-34,-4):.0f}" r="3.5" fill="#fff"/>')
    elif kind == "suisse":
        for k, (x, y) in enumerate([(430, 600), (770, 590), (600, 730)]):
            s.add(f'<g transform="rotate({[-8,6,-2][k]} {x} {y})">{shadow(x+8,y+46,140,18,0.3)}')
            s.add(f'<rect x="{x-140}" y="{y-50}" width="280" height="100" rx="20" fill="{s.vgrad("#E8A456","#9E5826")}"/>')
            s.add(f'<rect x="{x-140}" y="{y-6}" width="280" height="22" fill="{C["custard"]}"/>')
            for j in range(9):
                s.add(f'<rect x="{x-126+j*30}" y="{y-2}" width="10" height="8" fill="{C["choc2"]}"/>')
            for _ in range(14):
                s.add(f'<circle cx="{x+s.r.uniform(-120,120):.0f}" cy="{y-36+s.r.uniform(-6,6):.0f}" r="3" fill="#fff"/>')
            s.add('</g>')
    elif kind == "babka":
        x, y = 560, 640
        s.add(shadow(x + 20, y + 20, 260, 30, 0.3))
        s.add(f'<path d="M{x-220},{y} L{x-210},{y-100} L{x+210},{y-100} L{x+220},{y} Z" fill="{s.vgrad("#B9732F","#7E4318")}"/>')
        for k in range(7):
            bx = x - 190 + k * 63
            s.add(f'<ellipse cx="{bx}" cy="{y-118}" rx="46" ry="34" transform="rotate({25 if k%2 else -25} {bx} {y-118})" fill="{s.rgrad("#E3A25A","#9A531F")}"/>')
            s.add(f'<path d="M{bx-30},{y-120} q30,-20 60,4" stroke="{C["choc"]}" stroke-width="10" fill="none"/>')
        s.add(f'<path d="M{x-200},{y-140} L{x+200},{y-140}" stroke="#D99E4F" stroke-width="5" opacity="0.5"/>')
        it_bread_slice(s, 870, 690, dict(crumb="#F1D29A", crustc="#A35D27", rot=8, marble=True), 0)


def k_glass(s, p):
    """Verrine / coupe / bol avec couches."""
    kind = p.get("glass", "tumbler")
    positions = p.get("pos", [(470, 470), (760, 520)] if kind != "bowl" else [(600, 520)])
    for gi, (x, y) in enumerate(positions):
        sc = 1.0 if gi == 0 else 0.86
        draw_glass(s, x, y, p, kind, sc)
    for prop in p.get("props", []):
        pass


def draw_glass(s, x, y, p, kind, sc):
    layers = p["layers"]  # bas -> haut : (col, h, tex)
    if kind == "tumbler":
        rx, ry, H = 110 * sc, 30 * sc, 260 * sc
        bottom = y + H / 2
        s.add(shadow(x + 14, bottom + 10, rx * 1.2, 22, 0.32))
        yb = bottom
        for col, h, tex in layers:
            h *= sc
            s.add(f'<path d="M{x-rx+6},{yb-h} L{x-rx+6},{yb} A{rx-6},{ry-2} 0 0 0 {x+rx-6},{yb} L{x+rx-6},{yb-h} Z" fill="{s.hgrad(col,0.85,1.06)}"/>')
            gtex(s, tex, col, x, yb, h, rx - 8, ry)
            yb -= h
        topc = layers[-1][0]
        s.add(ell(x, yb, rx - 6, ry - 2, s.rgrad(shade(topc, 1.08), shade(topc, 0.95))))
        topdeco(s, p, x, yb, rx - 6, ry - 2, sc)
        top = bottom - H
        s.add(f'<path d="M{x-rx},{top} L{x-rx},{bottom} A{rx},{ry} 0 0 0 {x+rx},{bottom} L{x+rx},{top}" fill="none" stroke="#FFFFFF" stroke-opacity="0.75" stroke-width="3"/>')
        s.add(f'<ellipse cx="{x}" cy="{top}" rx="{rx}" ry="{ry}" fill="none" stroke="#FFFFFF" stroke-opacity="0.8" stroke-width="3"/>')
        s.add(f'<rect x="{x-rx+16}" y="{top+20}" width="10" height="{H-50}" rx="5" fill="#fff" opacity="0.35"/>')
        s.add(f'<rect x="{x+rx-34}" y="{top+30}" width="5" height="{H-80}" rx="3" fill="#fff" opacity="0.25"/>')
    elif kind == "coupe":
        rx, ry = 140 * sc, 36 * sc
        top = y - 40 * sc
        depth = 120 * sc
        s.add(shadow(x + 10, y + 230 * sc, 100 * sc, 18, 0.3))
        s.add(ell(x, y + 225 * sc, 85 * sc, 22 * sc, "#F4F1EA", 'stroke="#fff" stroke-width="2" opacity="0.7"'))
        s.add(f'<rect x="{x-7*sc}" y="{y+60*sc}" width="{14*sc}" height="{165*sc}" fill="#EDE8DE" opacity="0.6"/>')
        col = layers[-1][0]
        s.add(f'<path d="M{x-rx},{top} Q{x-rx},{top+depth+40*sc} {x},{top+depth+40*sc} Q{x+rx},{top+depth+40*sc} {x+rx},{top} Z" fill="{s.hgrad(col,0.8,1.06)}"/>')
        if len(layers) > 1:
            s.add(f'<path d="M{x-rx*0.8},{top+depth*0.75} Q{x},{top+depth+30*sc} {x+rx*0.8},{top+depth*0.75} Q{x},{top+depth*1.25} {x-rx*0.8},{top+depth*0.75} Z" fill="{layers[0][0]}"/>')
        s.add(ell(x, top, rx, ry, s.rgrad(shade(col, 1.1), shade(col, 0.92))))
        topdeco(s, p, x, top, rx, ry, sc)
        s.add(f'<path d="M{x-rx},{top} Q{x-rx},{top+depth+40*sc} {x},{top+depth+40*sc} Q{x+rx},{top+depth+40*sc} {x+rx},{top}" fill="none" stroke="#fff" stroke-opacity="0.7" stroke-width="3"/>')
        s.add(f'<path d="M{x-rx+20},{top+20} Q{x-rx+24},{top+depth} {x-30},{top+depth+20}" stroke="#fff" stroke-opacity="0.35" stroke-width="8" fill="none"/>')
    elif kind in ("bowl", "jar"):
        rx, ry = 230 * sc, 64 * sc
        top = y
        depth = 150 * sc
        bc = p.get("bowlcol", "#F4EFE6")
        s.add(shadow(x + 14, top + depth + 20, rx * 0.9, 26, 0.32))
        s.add(f'<path d="M{x-rx},{top} Q{x-rx*0.95},{top+depth*1.1} {x},{top+depth*1.15} Q{x+rx*0.95},{top+depth*1.1} {x+rx},{top} Z" fill="{s.hgrad(bc,0.82,1.04)}"/>')
        col = layers[-1][0]
        s.add(ell(x, top, rx, ry, shade(bc, 0.9)))
        s.add(ell(x, top + 6, rx * 0.94, ry * 0.88, s.rgrad(shade(col, 1.1), shade(col, 0.9))))
        topdeco(s, p, x, top + 6, rx * 0.94, ry * 0.88, sc)
        s.add(f'<ellipse cx="{x}" cy="{top}" rx="{rx}" ry="{ry}" fill="none" stroke="{shade(bc,1.1)}" stroke-width="5"/>')
    elif kind == "plate_dome":   # panna cotta / crème caramel démoulée
        plate(s, x, y + 120, 300)
        col = layers[-1][0]
        topcol = p.get("topcol", col)
        s.add(f'<path d="M{x-120},{y+110} L{x-90},{y} L{x+90},{y} L{x+120},{y+110} Z" fill="{s.hgrad(col,0.85,1.08)}"/>')
        s.add(f'<ellipse cx="{x}" cy="{y+110}" rx="120" ry="30" fill="{shade(col,0.85)}"/>')
        s.add(ell(x, y, 90, 24, topcol))
        if p.get("sauce"):
            s.add(f'<path d="M{x-90},{y} Q{x-100},{y+40} {x-110},{y+80} Q{x-80},{y+50} {x-60},{y+70} Q{x-40},{y+30} {x},{y+60} Q{x+30},{y+20} {x+70},{y+80} Q{x+90},{y+40} {x+90},{y} Z" fill="{p["sauce"]}" opacity="0.95"/>')
            s.add(f'<ellipse cx="{x}" cy="{y+138}" rx="200" ry="40" fill="{p["sauce"]}" opacity="0.85"/>')
            s.add(f'<path d="M{x-120},{y+110} L{x+120},{y+110}" stroke="{shade(col,0.9)}" stroke-width="2"/>')
        topdeco(s, p, x, y, 90, 24, 0.8)
    elif kind == "ile":
        rx, ry = 260, 80
        bc = "#F4EFE6"
        s.add(shadow(x + 14, y + 110, rx * 0.9, 26, 0.32))
        s.add(f'<path d="M{x-rx},{y} Q{x-rx*0.9},{y+120} {x},{y+124} Q{x+rx*0.9},{y+120} {x+rx},{y} Z" fill="{s.hgrad(bc,0.82,1.04)}"/>')
        s.add(ell(x, y, rx, ry, shade(bc, 0.9)))
        s.add(ell(x, y + 8, rx * 0.93, ry * 0.85, s.rgrad("#FBEFC8", "#EED48F")))
        for _ in range(30):
            s.add(f'<circle cx="{x+s.r.uniform(-180,180):.0f}" cy="{y+s.r.uniform(-30,40):.0f}" r="1" fill="#3B2618"/>')
        s.add(f'<path d="M{x-120},{y+10} Q{x-130},{y-90} {x},{y-96} Q{x+130},{y-90} {x+120},{y+10} Q{x},{y+30} {x-120},{y+10} Z" fill="{s.rgrad("#FFFFFF","#E9E2D2",0.4,0.3)}"/>')
        for k in range(10):
            s.add(f'<path d="M{x-100+k*20},{y-80+s.r.uniform(-10,10):.0f} C{x-40+k*8},{y-20} {x+k*10},{y-110} {x+60-k*14},{y-30}" stroke="{C["caramel"]}" stroke-width="2.5" fill="none"/>')
        for _ in range(10):
            s.add(f'<ellipse cx="{x+s.r.uniform(-80,80):.0f}" cy="{y-s.r.uniform(60,90):.0f}" rx="8" ry="4" fill="{C["almond"]}" stroke="{C["golden"]}"/>')


def gtex(s, tex, col, x, yb, h, rx, ry):
    if not tex:
        return
    for _ in range(int(rx / 4)):
        xx = x + s.r.uniform(-rx + 6, rx - 6)
        yy = yb - s.r.uniform(4, max(5, h - 4)) + ry * 0.6
        if tex == "crumb":
            s.add(f'<circle cx="{xx:.0f}" cy="{yy:.0f}" r="{s.r.uniform(2,4):.1f}" fill="{shade(col,s.r.choice([0.7,1.15]))}"/>')
        elif tex == "fruit":
            s.add(f'<circle cx="{xx:.0f}" cy="{yy:.0f}" r="{s.r.uniform(5,9):.1f}" fill="{s.r.choice([C["rasp"],C["straw"],C["blue"]])}" opacity="0.85"/>')
        elif tex == "mango":
            s.add(f'<rect x="{xx:.0f}" y="{yy:.0f}" width="12" height="10" fill="{C["mango"]}" opacity="0.9"/>')
        elif tex == "biscuit":
            s.add(f'<rect x="{xx:.0f}" y="{yy:.0f}" width="14" height="8" fill="{shade(col,0.8)}"/>')
        elif tex == "vanilla":
            s.add(f'<circle cx="{xx:.0f}" cy="{yy:.0f}" r="1" fill="#3B2618"/>')
        elif tex == "rice":
            s.add(f'<ellipse cx="{xx:.0f}" cy="{yy:.0f}" rx="4" ry="2" fill="#FFFFFF" opacity="0.9"/>')


def topdeco(s, p, x, y, rx, ry, sc):
    t = p.get("top")
    if t == "cocoa":
        sugar_dust(s, x, y, rx * 0.95, ry * 0.9, 500, C["choc_l"], 0.9)
    elif t == "shavings":
        for _ in range(16):
            xx, yy = x + s.r.uniform(-rx * 0.6, rx * 0.6), y + s.r.uniform(-ry * 0.5, ry * 0.5)
            s.add(f'<path d="M{xx:.0f},{yy:.0f} q8,-10 18,-2 q-6,6 -18,2 Z" fill="{C["choc_l"]}" stroke="{C["choc2"]}" stroke-width="1"/>')
    elif t == "cream_berry":
        s.add(f'<ellipse cx="{x}" cy="{y-6}" rx="{rx*0.5}" ry="{ry*0.6}" fill="{C["cream"]}"/><path d="M{x-rx*0.45},{y-6} Q{x},{y-60*sc} {x+rx*0.45},{y-6} Z" fill="{s.rgrad("#FFFFFF",C["cream2"])}"/>')
        berry(s, x, y - 50 * sc, p.get("berry", "rasp"), 1.1 * sc)
        if p.get("mint"):
            mint_sprig(s, x + 18, y - 56 * sc, 0.7 * sc, 30)
    elif t == "berries":
        toppings_on_ellipse(s, x, y, rx, ry, p.get("kinds", ["rasp", "blue"]), 7, 0.55, 1.1 * sc)
    elif t == "speculoos":
        for _ in range(20):
            xx, yy = x + s.r.uniform(-rx * 0.8, rx * 0.8), y + s.r.uniform(-ry * 0.6, ry * 0.6)
            s.add(f'<rect x="{xx:.0f}" y="{yy:.0f}" width="9" height="6" fill="{C["speculoos"]}"/>')
        s.add(f'<rect x="{x-10}" y="{y-60*sc}" width="{70*sc}" height="{48*sc}" rx="4" fill="{C["speculoos"]}" transform="rotate(-20 {x} {y})"/>')
    elif t == "oreo":
        for _ in range(16):
            xx, yy = x + s.r.uniform(-rx * 0.8, rx * 0.8), y + s.r.uniform(-ry * 0.6, ry * 0.6)
            s.add(f'<rect x="{xx:.0f}" y="{yy:.0f}" width="9" height="6" fill="{C["oreo"]}"/>')
    elif t == "passion":
        s.add(ell(x, y, rx * 0.95, ry * 0.9, s.rgrad("#F7C64B", "#E09A1E")))
        for _ in range(16):
            s.add(f'<circle cx="{x+s.r.uniform(-rx*0.7,rx*0.7):.0f}" cy="{y+s.r.uniform(-ry*0.6,ry*0.6):.0f}" r="4" fill="#2B1A10"/>')
        mint_sprig(s, x, y - 10, 0.7 * sc, 10)
    elif t == "coulis":
        s.add(ell(x, y, rx * 0.95, ry * 0.9, s.rgrad(shade(C["rasp"], 1.2), C["rasp"])))
        berry(s, x - 10, y - 10, "rasp", 1.0 * sc)
        mint_sprig(s, x + 20, y - 14, 0.6 * sc, 30)
    elif t == "kinder":
        s.add(ell(x, y, rx * 0.95, ry * 0.9, s.rgrad("#8A5A3C", "#5E3A26")))
        for k in range(3):
            s.add(f'<rect x="{x-50+k*30}" y="{y-34*sc}" width="{22*sc}" height="{36*sc}" rx="3" fill="{C["milk"]}" stroke="{C["white_choc"]}" stroke-width="3" transform="rotate({-10+k*10} {x} {y})"/>')
    elif t == "fruit_salad":
        for _ in range(26):
            xx, yy = x + s.r.uniform(-rx * 0.75, rx * 0.75), y + s.r.uniform(-ry * 0.6, ry * 0.6)
            kind = s.r.choice(["orange", "kiwi", "straw", "blue", "mango", "rasp"])
            if kind == "orange":
                s.add(f'<path d="M{xx:.0f},{yy:.0f} q14,-16 30,0 Z" fill="{C["orange"]}"/>')
            elif kind == "kiwi":
                s.add(f'<ellipse cx="{xx:.0f}" cy="{yy:.0f}" rx="18" ry="11" fill="{C["kiwi"]}" stroke="#6B5434"/><ellipse cx="{xx:.0f}" cy="{yy:.0f}" rx="6" ry="4" fill="#F2EBC9"/>')
            elif kind == "mango":
                s.add(f'<rect x="{xx:.0f}" y="{yy:.0f}" width="18" height="14" fill="{C["mango"]}" rx="2"/>')
            else:
                berry(s, xx, yy, kind, 0.9)
        mint_sprig(s, x + 30, y - 20, 0.8, 20)
    elif t == "scoops":
        for k, (dx, dy) in enumerate([(-70, 10), (70, 10), (0, -30)]):
            col = p.get("scoop", C["rasp"])
            xx, yy = x + dx * sc, y + dy * sc
            pts = [(xx + math.cos(a) * 80 * sc * (1 + s.r.uniform(-0.06, 0.06)), yy + math.sin(a) * 66 * sc * (1 + s.r.uniform(-0.04, 0.08))) for a in [i * math.tau / 20 for i in range(20)]]
            s.add(poly(pts, s.rgrad(shade(col, 1.2), shade(col, 0.82), 0.35, 0.3)))
            for _ in range(6):
                s.add(f'<path d="M{xx+s.r.uniform(-50,40):.0f},{yy+s.r.uniform(-30,30):.0f} q10,-4 20,0" stroke="{shade(col,0.8)}" stroke-width="2" fill="none"/>')
        mint_sprig(s, x + 20, y - 80 * sc, 0.8, 10)
    elif t == "rice":
        for _ in range(60):
            s.add(f'<ellipse cx="{x+s.r.uniform(-rx*0.8,rx*0.8):.0f}" cy="{y+s.r.uniform(-ry*0.6,ry*0.6):.0f}" rx="5" ry="2.5" fill="#FFFFFF" opacity="0.9"/>')
        s.add(f'<path d="M{x-60},{y+10} q60,-30 140,-10" stroke="#3B2618" stroke-width="6" fill="none" stroke-linecap="round"/>')
        sugar_dust(s, x + 30, y, 40, 10, 60, "#8E5631", 0.6)
    elif t == "zest":
        for _ in range(14):
            xx, yy = x + s.r.uniform(-rx * 0.6, rx * 0.6), y + s.r.uniform(-ry * 0.5, ry * 0.5)
            s.add(f'<path d="M{xx:.0f},{yy:.0f} q6,-4 12,0" stroke="{p.get("zest",C["lemon_d"])}" stroke-width="3" fill="none"/>')
        if p.get("biscuit"):
            s.add(f'<rect x="{x+rx*0.2}" y="{y-40*sc}" width="{80*sc}" height="{30*sc}" rx="15" fill="{C["golden_l"]}" transform="rotate(-25 {x} {y})"/>')
    elif t == "caramel":
        s.add(ell(x, y, rx * 0.95, ry * 0.9, s.rgrad(C["caramel_l"], C["caramel"])))
    elif t == "cream":
        s.add(f'<ellipse cx="{x}" cy="{y-4}" rx="{rx*0.85}" ry="{ry*0.75}" fill="{C["cream"]}"/>')


def k_ramekin(s, p):
    kind = p["ram"]
    if kind == "brulee":
        for gi, (x, y, sc) in enumerate([(470, 560, 1.0), (800, 520, 0.8)]):
            rx, ry, h = 190 * sc, 62 * sc, 90 * sc
            plate(s, x, y + h + 10, rx * 1.35) if gi == 0 else None
            s.add(f'<path d="M{x-rx},{y} L{x-rx},{y+h} A{rx},{ry} 0 0 0 {x+rx},{y+h} L{x+rx},{y} Z" fill="{s.hgrad("#F6F2EA",0.8,1.04)}"/>')
            for k in range(24):
                t = math.pi * (k + 0.5) / 24
                xx = x - rx * math.cos(t)
                s.add(f'<line x1="{xx:.0f}" y1="{y+ry*math.sin(t)+6:.0f}" x2="{xx:.0f}" y2="{y+h+ry*math.sin(t)-4:.0f}" stroke="#D8D0C2" stroke-width="2.5"/>')
            s.add(ell(x, y, rx, ry, "#EFE9DD"))
            s.add(ell(x, y + 4, rx * 0.88, ry * 0.84, s.rgrad("#E0A04E", "#A9611F")))
            for _ in range(12):
                xx, yy = x + s.r.uniform(-rx * 0.6, rx * 0.6), y + s.r.uniform(-ry * 0.5, ry * 0.5)
                s.add(f'<ellipse cx="{xx:.0f}" cy="{yy:.0f}" rx="{s.r.uniform(8,20)*sc:.0f}" ry="{s.r.uniform(3,7)*sc:.0f}" fill="#6E3810" opacity="0.5" filter="url(#blur3)"/>')
            s.add(f'<ellipse cx="{x-rx*0.3}" cy="{y-ry*0.25}" rx="{rx*0.35}" ry="{ry*0.15}" fill="#fff" opacity="0.3"/>')
            if gi == 0:
                s.add(f'<path d="M{x-20},{y-10} l20,12 l-6,14 l24,10" stroke="#5A2E0E" stroke-width="2.5" fill="none"/>')
        spoon(s, 300, 830, -15)
    elif kind == "fondant":
        x, y = 560, 560
        plate(s, x, y + 90, 330)
        s.add(f'<path d="M{x-120},{y+80} L{x-110},{y-10} L{x+110},{y-10} L{x+120},{y+80} Z" fill="{s.hgrad(C["choc"],0.7,1.15)}"/>')
        s.add(ell(x, y - 10, 110, 32, s.rgrad(C["choc_l"], C["choc"])))
        sugar_dust(s, x, y - 10, 100, 28, 240, "#FFFFFF", 0.9)
        s.add(f'<path d="M{x+60},{y+40} Q{x+120},{y+60} {x+180},{y+110} Q{x+120},{y+140} {x+40},{y+110} Z" fill="{s.vgrad(C["choc_l"],C["choc2"])}"/>')
        s.add(f'<path d="M{x+80},{y+80} q40,10 70,30" stroke="#fff" stroke-opacity="0.3" stroke-width="5" fill="none"/>')
        s.add(f'<ellipse cx="{x-200}" cy="{y+110}" rx="46" ry="20" fill="#FFFBF0"/><path d="M{x-246},{y+110} Q{x-200},{y+60} {x-154},{y+110} Z" fill="#FFFBF0"/>')
        berry(s, x - 150, y + 130, "rasp", 1.1)
        berry(s, x - 240, y + 140, "rasp", 1.0)
        fork(s, 860, 820, -18)
    elif kind in ("clafoutis", "crumble", "gratin", "apples_baked"):
        x, y = 600, 560
        rx, ry, h = 330, 120, 70
        dish = p.get("dish", "#F3EEE5")
        s.add(shadow(x + 18, y + h + 40, rx * 1.05, 40, 0.35))
        s.add(f'<path d="M{x-rx},{y} L{x-rx+18},{y+h} A{rx-18},{ry-8} 0 0 0 {x+rx-18},{y+h} L{x+rx},{y} Z" fill="{s.hgrad(dish,0.8,1.04)}"/>')
        s.add(ell(x, y, rx, ry, shade(dish, 1.02)))
        s.add(ell(x, y + 6, rx * 0.88, ry * 0.82, shade(dish, 0.88)))
        fx, fy, frx, fry = x, y + 10, rx * 0.86, ry * 0.78
        if kind == "clafoutis":
            s.add(ell(fx, fy, frx, fry, s.rgrad("#F3C978", "#C98A3A")))
            for _ in range(22):
                xx, yy = fx + s.r.uniform(-frx * 0.8, frx * 0.8), fy + s.r.uniform(-fry * 0.7, fry * 0.7)
                if ((xx - fx) / frx) ** 2 + ((yy - fy) / fry) ** 2 < 0.75:
                    s.add(f'<circle cx="{xx:.0f}" cy="{yy:.0f}" r="15" fill="{s.rgrad("#A5283A",C["cherry"])}"/><circle cx="{xx-4:.0f}" cy="{yy-5:.0f}" r="4" fill="#fff" opacity="0.4"/>')
            sugar_dust(s, fx, fy, frx * 0.8, fry * 0.7, 300)
        elif kind == "crumble":
            s.add(ell(fx, fy, frx, fry, C["apple_skin"]))
            for _ in range(260):
                a = s.r.uniform(0, math.tau)
                d = math.sqrt(s.r.random()) * 0.92
                xx, yy = fx + math.cos(a) * frx * d, fy + math.sin(a) * fry * d
                s.add(f'<circle cx="{xx:.0f}" cy="{yy:.0f}" r="{s.r.uniform(6,13):.0f}" fill="{s.r.choice(["#D9A35C","#C98A40","#E8BE7A","#B87830"])}"/>')
            for _ in range(8):
                a = s.r.uniform(0, math.tau)
                s.add(f'<ellipse cx="{fx+math.cos(a)*frx*0.95:.0f}" cy="{fy+math.sin(a)*fry*0.95:.0f}" rx="16" ry="7" fill="#8E3A1A" opacity="0.8"/>')
            s.add(f'<ellipse cx="{x+80}" cy="{y-30}" rx="70" ry="26" fill="#FFF8E8"/><path d="M{x+14},{y-30} Q{x+80},{y-100} {x+146},{y-30} Z" fill="{s.rgrad("#FFFFFF","#F2E6CC")}"/>')
            for k in range(3):
                s.add(f'<path d="M{x+30+k*30},{y-50} q12,-20 20,0" stroke="#E9DCC0" stroke-width="2" fill="none"/>')
        elif kind == "gratin":
            s.add(ell(fx, fy, frx, fry, s.rgrad("#F7D68E", "#D9A04A")))
            for _ in range(20):
                xx, yy = fx + s.r.uniform(-frx * 0.75, frx * 0.75), fy + s.r.uniform(-fry * 0.6, fry * 0.6)
                if ((xx - fx) / frx) ** 2 + ((yy - fy) / fry) ** 2 < 0.7:
                    berry(s, xx, yy, s.r.choice(["rasp", "blue", "straw_half"]), 1.0)
            for _ in range(14):
                xx, yy = fx + s.r.uniform(-frx * 0.7, frx * 0.7), fy + s.r.uniform(-fry * 0.6, fry * 0.6)
                s.add(f'<ellipse cx="{xx:.0f}" cy="{yy:.0f}" rx="22" ry="8" fill="#A9611F" opacity="0.35" filter="url(#blur3)"/>')
        elif kind == "apples_baked":
            s.add(ell(fx, fy, frx, fry, s.rgrad("#C9793A", "#7E3A14")))
            for (dx, dy) in [(-150, -10), (0, -30), (150, -10), (-75, 40), (75, 40)]:
                xx, yy = fx + dx, fy + dy
                s.add(f'<path d="M{xx-70},{yy} C{xx-76},{yy-90} {xx+76},{yy-90} {xx+70},{yy} C{xx+60},{yy+44} {xx-60},{yy+44} {xx-70},{yy} Z" fill="{s.rgrad("#E1704C","#8E2A1A",0.35,0.3)}"/>')
                s.add(f'<ellipse cx="{xx}" cy="{yy-52}" rx="30" ry="10" fill="#E4B55E"/>')
                s.add(f'<path d="M{xx},{yy-58} q4,-22 10,-30" stroke="#5B3A1E" stroke-width="5" fill="none"/>')
                s.add(f'<ellipse cx="{xx-30}" cy="{yy-30}" rx="10" ry="18" fill="#fff" opacity="0.25"/>')
        spoon(s, 260, 840, -18)
    elif kind == "souffle":
        for gi, (x, y, sc) in enumerate([(500, 560, 1.0), (810, 500, 0.75)]):
            rx, ry, h = 150 * sc, 46 * sc, 150 * sc
            s.add(shadow(x + 10, y + h + 20, rx * 1.1, 20, 0.3))
            s.add(f'<path d="M{x-rx},{y} L{x-rx},{y+h} A{rx},{ry} 0 0 0 {x+rx},{y+h} L{x+rx},{y} Z" fill="{s.hgrad("#F6F2EA",0.8,1.04)}"/>')
            for k in range(22):
                t = math.pi * (k + 0.5) / 22
                xx = x - rx * math.cos(t)
                s.add(f'<line x1="{xx:.0f}" y1="{y+ry*math.sin(t)+6:.0f}" x2="{xx:.0f}" y2="{y+h+ry*math.sin(t)-4:.0f}" stroke="#D8D0C2" stroke-width="2.5"/>')
            s.add(ell(x, y, rx, ry, "#EFE9DD"))
            s.add(f'<path d="M{x-rx*0.95},{y} L{x-rx*0.9},{y-90*sc} A{rx*0.9},{ry} 0 0 1 {x+rx*0.9},{y-90*sc} L{x+rx*0.95},{y} Z" fill="{s.hgrad("#EBB967",0.8,1.08)}"/>')
            s.add(ell(x, y - 90 * sc, rx * 0.9, ry, s.rgrad("#F4D08A", "#C98A3A")))
            s.add(f'<path d="M{x-rx*0.5},{y-90*sc} q{rx*0.5},{ry*0.6} {rx},0" stroke="#A9611F" stroke-width="3" fill="none" opacity="0.6"/>')
            sugar_dust(s, x, y - 90 * sc, rx * 0.8, ry * 0.8, 200)
        scatter(s, ["lemon"], (880, 700, 1000, 780), 1)


def k_choux(s, p):
    base = p.get("base", "plate")
    if base == "plate":
        plate(s, 600, 650, 440)
    else:
        parchment(s, 600, 660, 780, 360, -3)
    item = p["item"]
    pos = p.get("pos")
    if item == "paris_brest":
        x, y = 600, 590
        s.add(shadow(x + 10, y + 60, 300, 40, 0.3))
        for layer, dy in (("bottom", 40), ("cream", 0), ("top", -46)):
            n = 18
            pts = []
            for i in range(n):
                a = math.tau * i / n
                pts.append((x + math.cos(a) * 220, y + dy + math.sin(a) * 76, math.sin(a)))
            for xx, yy, z in sorted(pts, key=lambda q: q[2]):
                if layer == "cream":
                    s.add(f'<path d="M{xx-34},{yy+6} Q{xx-30},{yy-46} {xx},{yy-50} Q{xx+30},{yy-46} {xx+34},{yy+6} Z" fill="{s.rgrad("#E7C79A","#B98552")}"/>')
                    s.add(f'<path d="M{xx-20},{yy-6} Q{xx},{yy-40} {xx+18},{yy-8}" stroke="#A97546" stroke-width="2" fill="none"/>')
                else:
                    s.add(f'<ellipse cx="{xx}" cy="{yy}" rx="62" ry="{34 if layer=="bottom" else 40}" fill="{s.rgrad(C["golden_l"],C["golden_d"],0.4,0.3)}"/>')
            if layer == "top":
                for _ in range(40):
                    a = s.r.uniform(0, math.tau)
                    s.add(f'<ellipse cx="{x+math.cos(a)*220+s.r.uniform(-30,30):.0f}" cy="{y+dy+math.sin(a)*76-14+s.r.uniform(-12,12):.0f}" rx="10" ry="5" fill="{C["almond"]}" stroke="{C["golden_d"]}" stroke-width="1"/>')
                for _ in range(3):
                    sugar_dust(s, x, y + dy - 10, 260, 90, 300)
        return
    if item == "saint_honore":
        k_whole(s, dict(side=C["golden_d"], topcol=C["golden"], h=50, stand=False, topping="choux_ring"))
        return
    ITEMS[item](s, 0, 0, p, -1) if False else None
    pos = pos or {"eclair": [(560, 560), (620, 680)], "religieuse": [(470, 620), (760, 600)],
                  "chou": [(470, 600), (700, 560), (620, 710)], "profiterole": [(500, 620), (690, 600), (600, 700)],
                  "chouquette": [(350, 600), (480, 560), (620, 590), (760, 560), (880, 620), (420, 700), (570, 720), (720, 710), (850, 730)]}[item]
    if item == "profiterole":
        s.add(f'<ellipse cx="600" cy="660" rx="260" ry="70" fill="{C["choc"]}" opacity="0.85"/>')
    k = p.get("isize", ISIZE.get(item, 1.0))
    for i, (x, y) in enumerate(sorted(pos, key=lambda q: q[1])):
        s.add(f'<g transform="translate({x} {y}) scale({k}) translate({-x} {-y})">')
        ITEMS[item](s, x, y, p, i)
        s.add('</g>')
    if item == "profiterole":
        s.add(f'<path d="M780,620 Q800,560 900,500" stroke="{C["choc"]}" stroke-width="0"/>')


def k_pavlova(s, p):
    x, y = 600, 580
    plate(s, x, y + 90, 400)
    s.add(shadow(x + 10, y + 70, 290, 40, 0.25))
    blobs = []
    for i in range(30):
        a = math.tau * i / 30
        blobs.append((x + math.cos(a) * 250, y + 10 + math.sin(a) * 78, s.r.uniform(48, 64)))
    for bx, by, r in sorted(blobs, key=lambda q: q[1]):
        s.add(f'<ellipse cx="{bx:.0f}" cy="{by:.0f}" rx="{r:.0f}" ry="{r*0.9:.0f}" fill="{s.rgrad("#FFFDF8", "#E6D9BF", 0.35, 0.3)}"/>')
        s.add(f'<path d="M{bx-r*0.5:.0f},{by-r*0.2:.0f} q{r*0.4:.0f},-{r*0.5:.0f} {r*0.8:.0f},-{r*0.1:.0f}" stroke="#E2D2B4" stroke-width="2" fill="none"/>')
    s.add(ell(x, y - 30, 245, 72, s.rgrad("#FFFFFF", "#F1E8D6")))
    for k in range(18):
        a = math.tau * k / 18
        xx, yy = x + math.cos(a) * 200, y - 34 + math.sin(a) * 56
        s.add(f'<path d="M{xx-30:.0f},{yy+4:.0f} Q{xx:.0f},{yy-40:.0f} {xx+30:.0f},{yy+4:.0f} Z" fill="{s.rgrad("#FFFFFF", "#F3EBDB")}"/>')
    s.add(ell(x, y - 46, 200, 56, s.rgrad("#FFFFFF", "#F7F0E2")))
    toppings_on_ellipse(s, x, y - 56, 200, 56, p.get("kinds", ["rasp", "blue", "straw", "currant"]), 14, 0.65, 1.3)
    toppings_on_ellipse(s, x, y - 56, 200, 56, p.get("kinds", ["rasp", "blue", "straw"]), 6, 0.25, 1.3)
    if p.get("passion"):
        s.add(f'<path d="M{x-70},{y-50} q40,-10 80,6 q-30,24 -80,-6 Z" fill="#F2B33C"/>')
        for _ in range(6):
            s.add(f'<circle cx="{x-60+s.r.uniform(0,60):.0f}" cy="{y-46+s.r.uniform(-4,6):.0f}" r="3" fill="#2B1A10"/>')
    mint_sprig(s, x + 40, y - 110, 1.0, 10)


def k_fruits(s, p):
    kind = p["fruit"]
    if kind == "pears":
        k_glass(s, dict(glass="bowl", layers=[("#C9772E", 50, None)], pos=[(600, 600)], bowlcol="#EDE6DA"))
        for k, (x, y) in enumerate([(480, 560), (620, 520), (740, 570)]):
            s.add(f'<path d="M{x},{y-160} C{x-30},{y-150} {x-34},{y-90} {x-54},{y-40} C{x-80},{y+20} {x-50},{y+60} {x},{y+60} C{x+50},{y+60} {x+80},{y+20} {x+54},{y-40} C{x+34},{y-90} {x+30},{y-150} {x},{y-160} Z" fill="{s.rgrad(p.get("pcol","#E8C26E"),shade(p.get("pcol","#C78C3A"),0.75),0.35,0.4)}"/>')
            s.add(f'<path d="M{x},{y-158} q4,-24 14,-34" stroke="#5B3A1E" stroke-width="5" fill="none"/>')
            s.add(f'<ellipse cx="{x-22}" cy="{y-30}" rx="10" ry="30" fill="#fff" opacity="0.25"/>')
        s.add('<path d="M640,640 q80,-14 160,10" stroke="#3B2618" stroke-width="7" fill="none" stroke-linecap="round"/>')
        scatter(s, ["cinnamon"], (850, 720, 950, 780), 1)
    elif kind == "apricots":
        k_ramekin(s, dict(ram="gratin", dish="#E9DFD1")) if False else None
        x, y = 600, 580
        rx, ry, h = 330, 120, 60
        s.add(shadow(x + 18, y + h + 40, rx, 40, 0.35))
        s.add(f'<path d="M{x-rx},{y} L{x-rx+16},{y+h} A{rx-16},{ry-8} 0 0 0 {x+rx-16},{y+h} L{x+rx},{y} Z" fill="{s.hgrad("#3E3A36",0.8,1.15)}"/>')
        s.add(ell(x, y, rx, ry, "#4A4540"))
        s.add(ell(x, y + 6, rx * 0.9, ry * 0.84, s.rgrad("#D98B3A", "#8E4A1A")))
        rows = []
        for ring, n in ((0.66, 10), (0.25, 4)):
            for i in range(n):
                a = math.tau * i / n
                rows.append((x + math.cos(a) * rx * 0.86 * ring, y + 6 + math.sin(a) * ry * 0.8 * ring))
        for xx, yy in sorted(rows, key=lambda q: q[1]):
            s.add(f'<ellipse cx="{xx}" cy="{yy}" rx="48" ry="30" fill="{s.rgrad("#FBC373",C["apricot"])}"/><ellipse cx="{xx}" cy="{yy-2}" rx="20" ry="11" fill="#D86A28"/><ellipse cx="{xx-14}" cy="{yy-10}" rx="10" ry="5" fill="#fff" opacity="0.4"/>')
        for k in range(3):
            xx = x - 150 + k * 140
            s.add(f'<path d="M{xx},{y-10} l90,-20" stroke="#4F6B40" stroke-width="3"/>')
            for j in range(9):
                s.add(f'<path d="M{xx+j*10},{y-10-j*2.2} l-6,-12 M{xx+j*10},{y-10-j*2.2} l6,10" stroke="#4F6B40" stroke-width="2.5"/>')
        spoon(s, 260, 840, -18)


ITEMS = dict(cookie=it_cookie, sable=it_sable, madeleine=it_madeleine, financier=it_financier, langue=it_langue,
             linzer=it_linzer, spritz=it_spritz, macaron=it_macaron, tuile=it_tuile, rocher=it_rocher,
             eclair=it_eclair, chou=it_chou, religieuse=it_religieuse, profiterole=it_chou, square=it_square,
             truffle=it_truffle, caramel=it_caramel, cupcake=it_cupcake, muffin=it_muffin, croissant=it_croissant,
             painchoc=it_painchoc, chausson=it_chausson, roll=it_roll, beignet=it_beignet, chouquette=it_chouquette)

KINDS = dict(slice=k_slice, whole=k_whole, tart=k_tart, tatin=k_tatin, tartelettes=k_tartelettes, items=k_items,
             loaf=k_loaf, bread=k_bread, glass=k_glass, ramekin=k_ramekin, choux=k_choux, pavlova=k_pavlova,
             fruits=k_fruits)


def background(s, scene):
    sc = SCENES[scene]
    s.add(f'<rect x="-20" y="-20" width="{W+40}" height="{HORIZON+20}" fill="{s.rgrad(sc["light"], sc["wall2"], 0.3, 0.2)}"/>')
    s.add(f'<rect y="{HORIZON}" width="{W}" height="{H-HORIZON}" fill="{s.vgrad(sc["table"], sc["table2"])}"/>')
    s.add(f'<rect y="{HORIZON-2}" width="{W}" height="8" fill="#000" opacity="0.06" filter="url(#blur3)"/>')
    # lumière de fenêtre diffuse
    s.add(f'<polygon points="0,0 520,0 900,{H} 200,{H}" fill="#FFFFFF" opacity="{0.05 if scene!="cacao" else 0.04}"/>')


ZOOM = dict(slice=1.4, whole=1.3, tart=1.25, tatin=1.3, tartelettes=1.3, items=1.3, loaf=1.3, bread=1.3,
            glass=1.45, ramekin=1.3, choux=1.3, pavlova=1.3, fruits=1.3)


def render(slug, spec):
    s = Svg(zlib.crc32(slug.encode()))
    scene = spec.get("scene", "creme")
    background(s, scene)
    bg = "".join(s.parts)
    s.parts = []
    z = spec.get("zoom", ZOOM.get(spec["kind"], 1.25))
    s.add(f'<g transform="translate(600 {spec.get("cy",600)}) scale({z}) translate(-600 -620)">')
    nap = spec.get("napkin")
    if nap:
        napkin(s, *nap)
    for sc_ in spec.get("scatter_back", []):
        scatter(s, sc_[0], sc_[1], sc_[2])
    KINDS[spec["kind"]](s, spec)
    for sc_ in spec.get("scatter", []):
        scatter(s, sc_[0], sc_[1], sc_[2])
    s.add('</g>')
    # vignette + grain papier
    s.add(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    s.add(f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.16"/>')
    defs = "".join(s.defs)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
<filter id="blur18" filterUnits="userSpaceOnUse" x="-300" y="-300" width="{W+600}" height="{H+600}"><feGaussianBlur stdDeviation="18"/></filter>
<filter id="blur3"><feGaussianBlur stdDeviation="3"/></filter>
<filter id="dof" filterUnits="userSpaceOnUse" x="-300" y="-300" width="{W+600}" height="{H+600}"><feGaussianBlur stdDeviation="5"/></filter>
<filter id="grain" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="table" tableValues="0 0.9"/></feComponentTransfer></filter>
<filter id="wobble" filterUnits="userSpaceOnUse" x="-20" y="-20" width="{W+40}" height="{H+40}"><feTurbulence type="fractalNoise" baseFrequency="0.015" numOctaves="2" seed="7"/><feDisplacementMap in="SourceGraphic" scale="5"/></filter>
<radialGradient id="vig" cx="0.5" cy="0.5" r="0.75"><stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#2a1a10" stop-opacity="0.28"/></radialGradient>
{defs}
</defs>
{bg}<g>{"".join(s.parts)}</g>
</svg>'''
