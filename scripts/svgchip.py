#!/usr/bin/env python3
"""
Gera "pílulas" (chips/botões) em SVG no estilo do perfil: azul aço, cantos
arredondados, tipografia limpa, com ícone monocromático opcional.

`icon` (quando passado) é uma tupla (lista_de_paths, tamanho_viewbox).
"""

FILL = "#4A6FA5"
FG = "#ffffff"
HEIGHT = 30
FONT = 14
PAD_X = 13
RADIUS = 8
GAP = 8
ICON_GAP = 7
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


def _icon_group(icon, fg, height, size):
    paths, vb = icon
    isz = size * 1.3
    scale = isz / vb
    iy = (height - isz) / 2.0
    inner = "".join(f'<path d="{d}" fill="{fg}"/>' for d in paths)
    return f'<g transform="translate({PAD_X},{iy:.2f}) scale({scale:.4f})">{inner}</g>', isz


def _pill_markup(label, x, y, fill, fg, height, size, radius, icon=None):
    tw = text_width(label, size)
    ty = round(height / 2 + size * 0.34)
    if icon:
        icon_g, isz = _icon_group(icon, fg, height, size)
        w = round(PAD_X + isz + ICON_GAP + tw + PAD_X)
        tx = round(PAD_X + isz + ICON_GAP)
        text = (f'<text x="{tx}" y="{ty}" text-anchor="start" font-family="{FONT_FAMILY}" '
                f'font-size="{size}" font-weight="600" fill="{fg}">{_esc(label)}</text>')
        inner = icon_g + text
    else:
        w = round(tw + 2 * PAD_X)
        inner = (f'<text x="{w/2:.0f}" y="{ty}" text-anchor="middle" font-family="{FONT_FAMILY}" '
                 f'font-size="{size}" font-weight="600" fill="{fg}">{_esc(label)}</text>')
    return (f'<g transform="translate({x},{y})"><rect width="{w}" height="{height}" rx="{radius}" '
            f'fill="{fill}"/>{inner}</g>'), w


def pill(label, icon=None, fill=FILL, fg=FG, height=HEIGHT, size=FONT, radius=RADIUS):
    markup, w = _pill_markup(label, 0, 0, fill, fg, height, size, radius, icon)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" '
            f'viewBox="0 0 {w} {height}" role="img" aria-label="{_esc(label)}">{markup}</svg>\n')


def row(items, max_width=520, fill=FILL, fg=FG, height=HEIGHT, size=FONT, radius=RADIUS, gap=GAP):
    """`items` = lista de (label, icon) ou str."""
    norm = [(it if isinstance(it, tuple) else (it, None)) for it in items]
    sized = []
    for label, icon in norm:
        _, w = _pill_markup(label, 0, 0, fill, fg, height, size, radius, icon)
        sized.append((label, icon, w))

    lines, cur, cur_w = [], [], 0
    for label, icon, w in sized:
        if cur and cur_w + gap + w > max_width:
            lines.append(cur)
            cur, cur_w = [], 0
        cur.append((label, icon, w))
        cur_w += (gap if len(cur) > 1 else 0) + w
    if cur:
        lines.append(cur)

    line_h = height + gap
    total_h = len(lines) * line_h - gap
    width = max(sum(w for _, _, w in ln) + gap * (len(ln) - 1) for ln in lines)
    parts, y = [], 0
    for ln in lines:
        x = 0
        for label, icon, w in ln:
            markup, _ = _pill_markup(label, x, y, fill, fg, height, size, radius, icon)
            parts.append(markup)
            x += w + gap
        y += line_h
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" '
            f'viewBox="0 0 {width} {total_h}" role="img">{"".join(parts)}</svg>\n')
