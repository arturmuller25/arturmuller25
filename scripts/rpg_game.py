#!/usr/bin/env python3
"""
Encontro Paranormal — mini-RPG jogável no README (tema Ordem Paranormal).

O visitante é um Agente da Ordem e enfrenta criaturas. Cada ação é uma issue
com título  rpg|<acao>  (atacar | defender | ritual | fugir | novo). Uma Action
rola os dados, aplica o resultado, regenera a cena (SVG claro/escuro) e os botões.

Sprite da criatura: se existir rpg/sprites/<Elemento>.png (de preferência 64x64,
fundo transparente), ele é embutido na cena. Senão, desenha um demônio pixel-art.
"""

import os
import re
import json
import math
import base64
import random
import hashlib
import urllib.parse

import svgchip
import raziel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "rpg")
STATE = os.path.join(GAME, "state.json")
SCENE_LIGHT = os.path.join(GAME, "scene-light.svg")
SCENE_DARK = os.path.join(GAME, "scene-dark.svg")
COMMENT = os.path.join(GAME, "_comment.md")
README = os.path.join(ROOT, "README.md")

REPO = os.environ.get("GITHUB_REPOSITORY", "arturmuller25/arturmuller25")
PROFILE_URL = f"https://github.com/{REPO.split('/')[0]}"
MARK_START = "<!-- RPG:START -->"
MARK_END = "<!-- RPG:END -->"

MAX_HP = 20
START_RITUALS = 3

# Cores vivas dos Elementos (boas em tema claro e escuro)
ELEMENTS = {
    "Sangue": "#e0352f", "Morte": "#8fa3b5", "Conhecimento": "#f4c020",
    "Energia": "#a85cff", "Medo": "#4f86d6",
}
CREATURES = [
    ("Raziel (Vampiro)", "Sangue"),
    ("Espectro", "Morte"), ("Ceifador", "Morte"), ("Profanado", "Morte"),
    ("Membro do Outro Lado", "Conhecimento"), ("Olho Vigia", "Conhecimento"),
    ("Distorção", "Energia"), ("Tempestade Viva", "Energia"),
    ("Aberração", "Medo"), ("Sussurro do Medo", "Medo"),
]

LIGHT = {"bg": "#F4F4F2", "border": "#DDE1E6", "title": "#36567D", "text": "#2E3A48",
         "muted": "#5A6B7B", "hpbg": "#e2e5ea", "agent": "#3f7d5a"}
DARK = {"bg": "#1c2530", "border": "#2d3f57", "title": "#8aa6c8", "text": "#dfe6ee",
        "muted": "#9fb0c4", "hpbg": "#2a3a4d", "agent": "#56b886"}

BTN = {
    "atacar": ("Atacar", "#c0392b"),
    "defender": ("Defender", "#4A6FA5"),
    "ritual": ("Ritual", "#7c5fb0"),
    "fugir": ("Fugir", "#5A6B7B"),
    "novo": ("Começar de novo", "#3f7d5a"),
}

# Demônio pixel-art (14x14) usado quando não há PNG. R/D/H = cor do Elemento.
DEMON = [
    ".D..........D.",
    ".R..........R.",
    "DRk........kRD",
    "kRRkkkkkkkkRRk",
    ".kRRRRRRRRRRk.",
    ".kRHRRRRRRHRk.",
    ".kyyRRRRRRyyk.",
    ".kRRRRRRRRRRk.",
    ".kRDRRRRRRDRk.",
    ".kWMWMWMWMWMk.",
    ".kMWMWMWMWMWk.",
    ".kRDRRRRRRDRk.",
    "..kRRRRRRRRk..",
    "...kRk..kRk...",
]


# --------------------------------------------------------------------------- #
# Estado
# --------------------------------------------------------------------------- #
def new_enemy(score, elem=None):
    pool = [c for c in CREATURES if c[1] == elem] if elem else CREATURES
    name, el = random.choice(pool)
    hp = random.randint(8, 13) + score
    return {"name": name, "elem": el, "hp": hp, "max": hp}


def new_state():
    return {"hp": MAX_HP, "score": 0, "best": 0, "rituals": START_RITUALS,
            "defending": False, "over": False, "last_roll": 0,
            "enemy": new_enemy(0, "Sangue"),
            "msg": "Uma criatura surge das sombras. Boa sorte, Agente."}


def load_state():
    if os.path.exists(STATE):
        try:
            s = json.load(open(STATE, encoding="utf-8"))
            for k in ("hp", "score", "best", "rituals", "enemy"):
                if k not in s:
                    raise ValueError
            return s
        except Exception:
            pass
    return new_state()


def save_state(s):
    os.makedirs(GAME, exist_ok=True)
    json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------- #
# Combate
# --------------------------------------------------------------------------- #
def _enemy_attack(s, parts):
    dano = random.randint(2, 5)
    if s["defending"]:
        dano = max(1, dano // 2)
        s["defending"] = False
        parts.append(f"defendeu e sofreu {dano}")
    else:
        parts.append(f"a criatura revidou ({dano})")
    s["hp"] -= dano


def _spawn_after_kill(s, parts):
    s["score"] += 1
    cura = random.randint(2, 5)
    s["hp"] = min(MAX_HP, s["hp"] + cura)
    parts.append(f"derrotou e recuperou {cura} de vida")
    s["enemy"] = new_enemy(s["score"])


def apply(s, action):
    if s.get("over"):
        if action == "novo":
            best = max(s.get("best", 0), s.get("score", 0))
            s.update(new_state())
            s["best"] = best
            return "Novo Agente em campo. Que os Elementos te protejam.", "Nova investida iniciada. Boa sorte!"
        return "O Agente caiu. Comece uma nova investida.", "A run anterior acabou. Clique em **Começar de novo**."

    e = s["enemy"]
    parts = ["**Você**"]

    if action == "atacar":
        roll = random.randint(1, 20)
        s["last_roll"] = roll
        if roll == 20:
            dano = random.randint(6, 9) * 2
            parts.append(f"ACERTO CRÍTICO em {e['name']} ({dano})")
        elif roll <= 3:
            dano = 0
            parts.append("errou o golpe")
        else:
            dano = random.randint(3, 7)
            parts.append(f"atingiu {e['name']} ({dano})")
        e["hp"] -= dano

    elif action == "defender":
        s["defending"] = True
        cura = random.randint(1, 3)
        s["hp"] = min(MAX_HP, s["hp"] + cura)
        parts.append(f"assume defesa e recupera {cura}")

    elif action == "ritual":
        if s["rituals"] <= 0:
            return "Sem rituais restantes nesta investida.", "Você está sem rituais; use Atacar ou Defender."
        s["rituals"] -= 1
        dano = random.randint(7, 12)
        e["hp"] -= dano
        parts.append(f"conjura um ritual em {e['name']} ({dano})")

    elif action == "fugir":
        if random.random() < 0.5:
            parts.append(f"fugiu de {e['name']}")
            s["enemy"] = new_enemy(s["score"])
            s["defending"] = False
            msg = " ".join(parts) + "."
            return msg, msg + f"\n\nContinue no [perfil]({PROFILE_URL})."
        parts.append("tentou fugir e falhou")
        _enemy_attack(s, parts)
        if s["hp"] <= 0:
            return _game_over(s)
        msg = " ".join(parts) + "."
        return msg, msg + f"\n\nContinue no [perfil]({PROFILE_URL})."
    else:
        return "Ação desconhecida.", "Ação inválida."

    if e["hp"] <= 0:
        _spawn_after_kill(s, parts)
    else:
        _enemy_attack(s, parts)
        if s["hp"] <= 0:
            return _game_over(s)

    msg = " ".join(parts) + "."
    return msg, msg + f"\n\nContinue no [perfil]({PROFILE_URL})!"


def _game_over(s):
    s["hp"] = 0
    s["over"] = True
    s["best"] = max(s.get("best", 0), s["score"])
    msg = f"O Agente tombou após derrotar {s['score']} criatura(s). Recorde: {s['best']}."
    return msg, msg + f"\n\nClique em **Começar de novo** no [perfil]({PROFILE_URL})."


# --------------------------------------------------------------------------- #
# Cores / utilidades de render
# --------------------------------------------------------------------------- #
def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(h, f):
    r, g, b = _rgb(h)
    if f <= 1:
        r, g, b = (int(r * f), int(g * f), int(b * f))
    else:
        t = f - 1
        r, g, b = (int(r + (255 - r) * t), int(g + (255 - g) * t), int(b + (255 - b) * t))
    return f"#{r:02x}{g:02x}{b:02x}"


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _short(t, n=70):
    t = re.sub(r"\*\*", "", t)
    return t if len(t) <= n else t[:n - 1] + "…"


def _bar(x, y, w, h, frac, color, pal):
    frac = max(0.0, min(1.0, frac))
    fillw = round(w * frac)
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2:.0f}" fill="{pal["hpbg"]}"/>'
    if fillw > 0:
        out += f'<rect x="{x}" y="{y}" width="{fillw}" height="{h}" rx="{h/2:.0f}" fill="{color}"/>'
    return out


def _demon(base, x, y, size):
    cell = size / 14.0
    pal = {"k": "#160406", "D": _mix(base, 0.55), "R": base, "H": _mix(base, 1.45),
           "W": "#ece3c6", "M": "#280810", "y": "#ffce3a"}
    out = []
    for r, line in enumerate(DEMON):
        for c, ch in enumerate(line):
            col = pal.get(ch)
            if col:
                out.append(f'<rect x="{x + c*cell:.2f}" y="{y + r*cell:.2f}" '
                           f'width="{cell:.2f}" height="{cell:.2f}" fill="{col}"/>')
    return "".join(out)


def creature_svg(elem, color, size, x, y):
    png = os.path.join(GAME, "sprites", f"{elem}.png")
    if os.path.exists(png):
        b64 = base64.b64encode(open(png, "rb").read()).decode()
        uri = "data:image/png;base64," + b64
        inner = (f'<image x="{x}" y="{y}" width="{size}" height="{size}" '
                 f'image-rendering="pixelated" href="{uri}" xlink:href="{uri}" />')
    elif elem == "Sangue":
        cell = size / 64.0
        ox = x + (size - raziel.W * cell) / 2.0
        inner = raziel.markup(ox, y, cell)
    else:
        inner = _demon(color, x, y, size)
    return ('<g><animateTransform attributeName="transform" type="translate" '
            'values="0 0;0 -3;0 0" dur="2.6s" repeatCount="indefinite"/>' + inner + "</g>")


def d20_svg(cx, cy, r, roll):
    s3 = 0.866
    T = (cx, cy - r); UR = (cx + s3 * r, cy - 0.5 * r); LR = (cx + s3 * r, cy + 0.5 * r)
    B = (cx, cy + r); LL = (cx - s3 * r, cy + 0.5 * r); UL = (cx - s3 * r, cy - 0.5 * r)
    I1 = (cx, cy - 0.34 * r); I2 = (cx - 0.56 * r, cy + 0.32 * r); I3 = (cx + 0.56 * r, cy + 0.32 * r)
    center = str(roll) if roll else "20"
    # tons do mais claro (topo, recebe luz) ao mais escuro (base) -> volume + contraste
    faces = [
        ((T, UL, I1), "#f0463d", "18", False), ((T, I1, UR), "#f0463d", "4", False),
        ((UL, I2, I1), "#e03a33", "2", False), ((UR, I1, I3), "#e03a33", "14", False),
        ((UL, LL, I2), "#bf2d27", "12", False), ((UR, I3, LR), "#bf2d27", "6", False),
        ((LL, B, I2), "#8c201c", "10", False), ((I3, B, LR), "#8c201c", "16", False),
        ((I2, B, I3), "#6a1413", "8", False), ((I1, I2, I3), "#ff6f66", center, True),
    ]
    edge = "#260606"
    ff = "'Segoe UI',Helvetica,Arial,sans-serif"
    polys, nums = [], []
    for verts, shade, num, is_c in faces:
        pts = " ".join(f"{vx:.1f},{vy:.1f}" for vx, vy in verts)
        polys.append(f'<polygon points="{pts}" fill="{shade}" stroke="{edge}" '
                     f'stroke-width="{r*0.045:.1f}" stroke-linejoin="round"/>')
        nx = sum(v[0] for v in verts) / 3
        ny = sum(v[1] for v in verts) / 3
        if not is_c:
            nx += (cx - nx) * 0.12
            ny += (cy - ny) * 0.12
        fs = r * 0.46 if is_c else r * 0.27
        col = "#ffffff" if is_c else "#ffe2de"
        wt = 800 if is_c else 700
        nums.append(f'<text x="{nx:.1f}" y="{ny + fs*0.35:.1f}" text-anchor="middle" '
                    f'font-family="{ff}" font-size="{fs:.1f}" font-weight="{wt}" fill="{col}">{num}</text>')
    spec = (f'<polygon points="{T[0]:.1f},{T[1]:.1f} {UL[0]:.1f},{UL[1]:.1f} {I1[0]:.1f},{I1[1]:.1f}" fill="#ffffff" opacity="0.18"/>'
            f'<polygon points="{T[0]:.1f},{T[1]:.1f} {I1[0]:.1f},{I1[1]:.1f} {UR[0]:.1f},{UR[1]:.1f}" fill="#ffffff" opacity="0.09"/>')
    shadow = f'<ellipse cx="{cx}" cy="{cy + r + 5:.0f}" rx="{r*0.82:.0f}" ry="{r*0.16:.0f}" fill="#000000" opacity="0.22"/>'
    rot = ('<g><animateTransform attributeName="transform" type="rotate" '
           f'values="0 {cx} {cy};360 {cx} {cy};360 {cx} {cy}" keyTimes="0;0.1;1" '
           'dur="6s" repeatCount="indefinite"/>'
           + "".join(polys) + spec + "".join(nums) + "</g>")
    return shadow + rot


def render_scene(s, pal):
    w, h = 520, 258
    e = s["enemy"]
    ecol = ELEMENTS.get(e["elem"], "#e0352f")
    ff = "'Segoe UI',Helvetica,Arial,sans-serif"
    parts = [
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{pal["bg"]}" stroke="{pal["border"]}"/>',
        f'<text x="24" y="34" font-family="{ff}" font-size="17" font-weight="700" fill="{pal["title"]}">Encontro Paranormal</text>',
        f'<line x1="24" y1="46" x2="496" y2="46" stroke="{pal["border"]}"/>',
        f'<circle cx="30" cy="66" r="6" fill="{ecol}"/>',
        f'<text x="44" y="71" font-family="{ff}" font-size="15" font-weight="600" fill="{pal["text"]}">{_esc(e["name"])}</text>',
        f'<text x="344" y="71" text-anchor="end" font-family="{ff}" font-size="11" fill="{pal["muted"]}">{max(0,e["hp"])}/{e["max"]} HP</text>',
        _bar(24, 80, 320, 12, e["hp"] / max(1, e["max"]), ecol, pal),
        f'<text x="24" y="108" font-family="{ff}" font-size="11" fill="{pal["muted"]}">Elemento: {e["elem"]}</text>',
        f'<text x="24" y="138" font-family="{ff}" font-size="15" font-weight="600" fill="{pal["text"]}">Agente da Ordem</text>',
        f'<text x="344" y="138" text-anchor="end" font-family="{ff}" font-size="11" fill="{pal["muted"]}">{max(0,s["hp"])}/{MAX_HP} HP</text>',
        _bar(24, 147, 320, 12, s["hp"] / MAX_HP, pal["agent"], pal),
        f'<text x="24" y="178" font-family="{ff}" font-size="11" fill="{pal["muted"]}">Derrotadas: {s["score"]}   ·   Recorde: {s["best"]}   ·   Rituais: {s["rituals"]}</text>',
        f'<text x="24" y="210" font-family="{ff}" font-size="12.5" fill="{pal["text"]}">{_esc(_short(s["msg"]))}</text>',
        creature_svg(e["elem"], ecol, 104, 372, 44),
        d20_svg(424, 200, 40, s.get("last_roll", 0)),
        f'<text x="424" y="252" text-anchor="middle" font-family="{ff}" font-size="9.5" fill="{pal["muted"]}">rolagem do d20</text>',
    ]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Encontro Paranormal">'
            f'{"".join(parts)}</svg>\n')


# --------------------------------------------------------------------------- #
# README + botões
# --------------------------------------------------------------------------- #
def gen_buttons():
    os.makedirs(GAME, exist_ok=True)
    for key, (label, color) in BTN.items():
        with open(os.path.join(GAME, f"btn-{key}.svg"), "w", encoding="utf-8") as f:
            f.write(svgchip.pill(label, fill=color, height=36, size=15))


def issue_link(action):
    title = urllib.parse.quote(f"rpg|{action}")
    body = urllib.parse.quote("Apenas envie esta issue (Submit new issue) para realizar a ação. "
                              "O resultado aparece no perfil em alguns segundos.")
    return f"https://github.com/{REPO}/issues/new?title={title}&body={body}"


def btn_md(key):
    base = f"https://raw.githubusercontent.com/{REPO}/main/rpg"
    return f"[![{BTN[key][0]}]({base}/btn-{key}.svg)]({issue_link(key)})"


def build_section(s, ver):
    base = f"https://raw.githubusercontent.com/{REPO}/main/rpg"
    out = ['<div align="center">\n\n', "<picture>\n",
           f'<source media="(prefers-color-scheme: dark)" srcset="{base}/scene-dark.svg?v={ver}" />\n',
           f'<img src="{base}/scene-light.svg?v={ver}" width="520" alt="Encontro Paranormal" />\n',
           "</picture>\n\n"]
    if s.get("over"):
        out.append(btn_md("novo") + "\n\n")
    else:
        out.append(" ".join(btn_md(k) for k in ("atacar", "defender", "ritual", "fugir")) + "\n\n")
    out.append("</div>\n")
    return "".join(out)


def inject(section):
    c = open(README, encoding="utf-8").read()
    block = MARK_START + "\n" + section + MARK_END
    if MARK_START in c and MARK_END in c:
        c = re.sub(re.escape(MARK_START) + ".*?" + re.escape(MARK_END), lambda _: block, c, flags=re.S)
    else:
        c = c.rstrip() + "\n\n" + block + "\n"
    open(README, "w", encoding="utf-8").write(c)


def write_comment(t):
    os.makedirs(GAME, exist_ok=True)
    open(COMMENT, "w", encoding="utf-8").write(t or "")


def main():
    s = load_state()
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    title = os.environ.get("ISSUE_TITLE", "").strip().lower()
    comment = ""

    if event == "issues" and title.startswith("rpg|"):
        action = title.split("|", 1)[1].strip()
        msg, comment = apply(s, action)
        s["msg"] = msg

    gen_buttons()
    os.makedirs(GAME, exist_ok=True)
    light = render_scene(s, LIGHT)
    open(SCENE_LIGHT, "w", encoding="utf-8").write(light)
    open(SCENE_DARK, "w", encoding="utf-8").write(render_scene(s, DARK))
    ver = hashlib.md5(light.encode()).hexdigest()[:8]
    inject(build_section(s, ver))
    save_state(s)
    write_comment(comment)
    print("OK rpg:", "hp", s["hp"], "score", s["score"], "over", s.get("over"))


if __name__ == "__main__":
    main()
