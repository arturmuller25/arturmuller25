#!/usr/bin/env python3
"""
Gera "pílulas" (chips/botões) em SVG no estilo do perfil: azul aço, cantos
arredondados, tipografia limpa. Usado para contato, stack e lances do xadrez,
deixando tudo no mesmo visual dos cards.
"""

FILL = "#4A6FA5"
FG = "#ffffff"
HEIGHT = 30
FONT = 14
PAD_X = 13
RADIUS = 8
GAP = 8
FONT_FAMILY = "'Segoe UI',Helvetica,Arial,sans-serif"


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_width(s, size=FONT):
    w = 0.0
    for ch in s:
        if ch in "iIlj.,'!|:;":
            w += 0.30
        elif ch in "ftrJ()[]/ ":
            w += 0.42
        elif ch in "mMW":
            w += 0.92
        elif ch.isupper():
            w += 0.68
        else:
            w += 0.55
    return w * size


def _pill_markup(label, x, y, fill, fg, height, size, radius):
    w = round(text_width(label, size) + 2 * PAD_X)
    ty = round(y + height / 2 + size * 0.34)
    return (
        f'<g transform="translate({x},{y})">'
        f'<rect width="{w}" height="{height}" rx="{radius}" fill="{fill}"/>'
        f'<text x="{w/2:.0f}" y="{ty-y}" text-anchor="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{size}" font-weight="600" fill="{fg}">{_esc(label)}</text>'
        f'</g>'
    ), w


def pill(label, fill=FILL, fg=FG, height=HEIGHT, size=FONT, radius=RADIUS):
    """Uma pílula isolada (para botões clicáveis)."""
    markup, w = _pill_markup(label, 0, 0, fill, fg, height, size, radius)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" '
        f'viewBox="0 0 {w} {height}" role="img" aria-label="{_esc(label)}">{markup}</svg>\n'
    )


def row(labels, max_width=480, fill=FILL, fg=FG, height=HEIGHT, size=FONT,
        radius=RADIUS, gap=GAP):
    """Uma faixa de pílulas com quebra de linha automática."""
    lines, cur, cur_w = [], [], 0
    for lab in labels:
        w = round(text_width(lab, size) + 2 * PAD_X)
        if cur and cur_w + gap + w > max_width:
            lines.append(cur)
            cur, cur_w = [], 0
        cur.append((lab, w))
        cur_w += (gap if len(cur) > 1 else 0) + w
    if cur:
        lines.append(cur)

    line_h = height + gap
    total_h = len(lines) * line_h - gap
    width = max(sum(w for _, w in ln) + gap * (len(ln) - 1) for ln in lines)
    parts, y = [], 0
    for ln in lines:
        x = 0
        for lab, w in ln:
            markup, _ = _pill_markup(lab, x, y, fill, fg, height, size, radius)
            parts.append(markup)
            x += w + gap
        y += line_h
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" '
        f'viewBox="0 0 {width} {total_h}" role="img">{"".join(parts)}</svg>\n'
    )
