#!/usr/bin/env python3
"""
Encontro Paranormal — mini-RPG jogável no README (tema Ordem Paranormal).

O visitante é um Agente da Ordem e enfrenta criaturas. Cada ação é uma issue
com título  rpg|<acao>  (atacar | defender | ritual | fugir | novo). Uma Action
rola os dados, aplica o resultado, regenera a cena (SVG claro/escuro) e os botões.

Sem dependências externas além do svgchip (mesma pasta).
"""

import os
import re
import json
import math
import random
import hashlib
import urllib.parse

import svgchip

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

ELEMENTS = {
    "Sangue": "#b03a3a", "Morte": "#8a8f98", "Conhecimento": "#d4a72c",
    "Energia": "#8e6fc0", "Medo": "#46607c",
}
CREATURES = [
    ("Zumbi", "Sangue"), ("Carniçal", "Sangue"), ("Sangrenta", "Sangue"),
    ("Espectro", "Morte"), ("Ceifador", "Morte"), ("Profanado", "Morte"),
    ("Membro do Outro Lado", "Conhecimento"), ("Olho Vigia", "Conhecimento"),
    ("Distorção", "Energia"), ("Tempestade Viva", "Energia"),
    ("Aberração", "Medo"), ("Sussurro do Medo", "Medo"),
]

LIGHT = {"bg": "#F4F4F2", "border": "#DDE1E6", "title": "#36567D", "text": "#2E3A48",
         "muted": "#5A6B7B", "hpbg": "#e2e5ea", "agent": "#3f7d5a"}
DARK = {"bg": "#1c2530", "border": "#2d3f57", "title": "#8aa6c8", "text": "#dfe6ee",
        "muted": "#9fb0c4", "hpbg": "#2a3a4d", "agent": "#56b886"}

BTN = {  # rótulo, cor
    "atacar": ("Atacar", "#b94a48"),
    "defender": ("Defender", "#4A6FA5"),
    "ritual": ("Ritual", "#7c5fb0"),
    "fugir": ("Fugir", "#5A6B7B"),
    "novo": ("Começar de novo", "#3f7d5a"),
}


# --------------------------------------------------------------------------- #
def new_enemy(score):
    name, elem = random.choice(CREATURES)
    hp = random.randint(8, 13) + score
    return {"name": name, "elem": elem, "hp": hp, "max": hp}


def new_state():
    return {"hp": MAX_HP, "score": 0, "best": 0, "rituals": START_RITUALS,
            "defending": False, "over": False, "last_roll": 0, "enemy": new_enemy(0),
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
    """Aplica a ação e devolve (mensagem, comentario_issue)."""
    if s.get("over"):
        if action == "novo":
            best = max(s.get("best", 0), s.get("score", 0))
            s.update(new_state())
            s["best"] = best
            return "Novo Agente em campo. Que os Elementos te protejam.", "Nova investida iniciada. Boa sorte!"
        return "O Agente caiu. Comece uma nova investida.", "A run anterior acabou — clique em **Começar de novo**."

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
            return "Sem rituais restantes nesta investida.", "Você está sem rituais — use Atacar ou Defender."
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
        else:
            parts.append("tentou fugir e falhou")
            _enemy_attack(s, parts)
            if s["hp"] <= 0:
                return _game_over(s)
            msg = " ".join(parts) + "."
            return msg, msg + f"\n\nContinue no [perfil]({PROFILE_URL})."
    else:
        return "Ação desconhecida.", "Ação inválida."

    # criatura morreu?
    if e["hp"] <= 0:
        _spawn_after_kill(s, parts)
    else:
        if action != "defender":
            _enemy_attack(s, parts)
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
    return msg, msg + "\n\nClique em **Começar de novo** no [perfil](" + PROFILE_URL + ")."


# --------------------------------------------------------------------------- #
# Sprites pixel-art (12x12). X = cor do Elemento, e = olho claro, p = pupila
SPRITES = {
    "Sangue": ["....XXXX....", "..XXXXXXXX..", ".XXXXXXXXXX.", "XXXXXXXXXXXX",
               "XXeeXXXXeeXX", "XXeeXXXXeeXX", "XXXXXXXXXXXX", "XXXXXXXXXXXX",
               "XXXXXXXXXXXX", ".XXXXXXXXXX.", "X.XX.XX.XX.X", "............"],
    "Morte": ["....XXXX....", "..XXXXXXXX..", ".XXXXXXXXXX.", "XXXXXXXXXXXX",
              "XXeeXXXXeeXX", "XXeeXXXXeeXX", "XXXXXXXXXXXX", "XXXXXXXXXXXX",
              "XXXXXXXXXXXX", "XXXXXXXXXXXX", "X.XX.XX.XX.X", ".X..X..X..X."],
    "Conhecimento": ["............", "...XXXXXX...", ".XXXXXXXXXX.", "XXXXXXXXXXXX",
                     "XXXeeeeeeXXX", "XXeepppppeXX", "XXeepppppeXX", "XXXeeeeeeXXX",
                     "XXXXXXXXXXXX", ".XXXXXXXXXX.", "...XXXXXX...", "............"],
    "Energia": [".....XXX....", "....XXX.....", "...XXX......", "..XXXXXX....",
                "....XXX.....", "...XXXXX....", "..XXXXXXX...", ".....XXX....",
                "....XXX.....", "...XXX......", "..XXX.......", "............"],
    "Medo": ["...XXXXXX...", "..XXXXXXXX..", ".XXXXXXXXXX.", ".XXXXXXXXXX.",
             ".XXeXXXXeXX.", ".XXeXXXXeXX.", ".XXXXXXXXXX.", ".XXXXXXXXXX.",
             ".XXXXXXXXXX.", ".XXXXXXXXXX.", ".X.XXXX.X.X.", "............"],
}


def _bar(x, y, w, h, frac, color, pal):
    frac = max(0.0, min(1.0, frac))
    fillw = round(w * frac)
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2:.0f}" fill="{pal["hpbg"]}"/>'
    if fillw > 0:
        out += f'<rect x="{x}" y="{y}" width="{fillw}" height="{h}" rx="{h/2:.0f}" fill="{color}"/>'
    return out


def sprite_svg(elem, color, cell, x, y):
    grid = SPRITES.get(elem, SPRITES["Sangue"])
    pal = {"X": color, "e": "#f4f4f2", "p": "#16202b"}
    rects = []
    for r, line in enumerate(grid):
        for c, ch in enumerate(line):
            col = pal.get(ch)
            if col:
                rects.append(f'<rect x="{x + c*cell:.0f}" y="{y + r*cell:.0f}" '
                             f'width="{cell}" height="{cell}" fill="{col}"/>')
    return ('<g><animateTransform attributeName="transform" type="translate" '
            'values="0 0;0 -3;0 0" dur="2.6s" repeatCount="indefinite"/>' + "".join(rects) + "</g>")


def d20_svg(n, cx, cy, r):
    pts = [(cx + r * math.cos(math.radians(60 * k - 90)),
            cy + r * math.sin(math.radians(60 * k - 90))) for k in range(6)]
    hexp = "M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    tri = [(cx, cy - r * 0.6), (cx - r * 0.52, cy + r * 0.34), (cx + r * 0.52, cy + r * 0.34)]
    trip = "M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in tri) + " Z"
    label = str(n) if n else "20"
    fs = r * 0.6
    return ('<g><animateTransform attributeName="transform" type="rotate" '
            f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="0.7s" repeatCount="1" fill="freeze"/>'
            f'<path d="{hexp}" fill="#3a4f6a" stroke="#9fb0c4" stroke-width="1.6" stroke-linejoin="round"/>'
            f'<path d="{trip}" fill="#4A6FA5" stroke="#9fb0c4" stroke-width="1"/>'
            f'<text x="{cx}" y="{cy + fs*0.35:.1f}" text-anchor="middle" '
            f'font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" font-size="{fs:.0f}" '
            f'font-weight="800" fill="#ffffff">{label}</text></g>')


def render_scene(s, pal):
    w, h = 500, 214
    e = s["enemy"]
    ecol = ELEMENTS.get(e["elem"], "#b03a3a")
    ff = "'Segoe UI',Helvetica,Arial,sans-serif"
    parts = [
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{pal["bg"]}" stroke="{pal["border"]}"/>',
        f'<text x="24" y="32" font-family="{ff}" font-size="16" font-weight="700" fill="{pal["title"]}">Encontro Paranormal</text>',
        f'<line x1="24" y1="42" x2="476" y2="42" stroke="{pal["border"]}"/>',
        # inimigo (esquerda)
        f'<circle cx="30" cy="60" r="6" fill="{ecol}"/>',
        f'<text x="44" y="65" font-family="{ff}" font-size="15" font-weight="600" fill="{pal["text"]}">{_esc(e["name"])}</text>',
        f'<text x="384" y="65" text-anchor="end" font-family="{ff}" font-size="11" fill="{pal["muted"]}">{max(0,e["hp"])}/{e["max"]} HP</text>',
        _bar(24, 74, 360, 11, e["hp"] / max(1, e["max"]), ecol, pal),
        f'<text x="24" y="100" font-family="{ff}" font-size="11" fill="{pal["muted"]}">Elemento: {e["elem"]}</text>',
        # agente (esquerda)
        f'<text x="24" y="128" font-family="{ff}" font-size="15" font-weight="600" fill="{pal["text"]}">Agente da Ordem</text>',
        f'<text x="384" y="128" text-anchor="end" font-family="{ff}" font-size="11" fill="{pal["muted"]}">{max(0,s["hp"])}/{MAX_HP} HP</text>',
        _bar(24, 137, 360, 11, s["hp"] / MAX_HP, pal["agent"], pal),
        f'<text x="24" y="166" font-family="{ff}" font-size="11" fill="{pal["muted"]}">Derrotadas: {s["score"]}   ·   Recorde: {s["best"]}   ·   Rituais: {s["rituals"]}</text>',
        f'<text x="24" y="196" font-family="{ff}" font-size="12.5" fill="{pal["text"]}">{_esc(_short(s["msg"]))}</text>',
        # direita: sprite da criatura + d20
        sprite_svg(e["elem"], ecol, 6, 406, 50),
        d20_svg(s.get("last_roll", 0), 446, 150, 22),
        f'<text x="446" y="188" text-anchor="middle" font-family="{ff}" font-size="9" fill="{pal["muted"]}">último d20</text>',
    ]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="Encontro Paranormal">{"".join(parts)}</svg>\n')


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _short(t, n=68):
    t = re.sub(r"\*\*", "", t)
    return t if len(t) <= n else t[:n - 1] + "…"


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


def btn_md(key, ver):
    label = BTN[key][0]
    base = f"https://raw.githubusercontent.com/{REPO}/main/rpg"
    return f"[![{label}]({base}/btn-{key}.svg)]({issue_link(key)})"


def build_section(s):
    ver = hashlib.md5(json.dumps(s, sort_keys=True).encode()).hexdigest()[:8]
    base = f"https://raw.githubusercontent.com/{REPO}/main/rpg"
    out = ['<div align="center">\n\n']
    out.append("<picture>\n")
    out.append(f'<source media="(prefers-color-scheme: dark)" srcset="{base}/scene-dark.svg?v={ver}" />\n')
    out.append(f'<img src="{base}/scene-light.svg?v={ver}" width="500" alt="Encontro Paranormal" />\n')
    out.append("</picture>\n\n")
    if s.get("over"):
        out.append(btn_md("novo", ver) + "\n\n")
    else:
        out.append(" ".join(btn_md(k, ver) for k in ("atacar", "defender", "ritual", "fugir")) + "\n\n")
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
    open(SCENE_LIGHT, "w", encoding="utf-8").write(render_scene(s, LIGHT))
    open(SCENE_DARK, "w", encoding="utf-8").write(render_scene(s, DARK))
    inject(build_section(s))
    save_state(s)
    write_comment(comment)
    print("OK rpg:", "hp", s["hp"], "score", s["score"], "over", s.get("over"))


if __name__ == "__main__":
    main()
