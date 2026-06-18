#!/usr/bin/env python3
"""
Gera "pílulas" (chips/botões) em SVG no estilo do perfil.

`icon` (quando passado) é uma tupla (markup_interno, vb_w, vb_h):
  - markup_interno: conteúdo SVG já pronto (paths com fill definido)
  - vb_w, vb_h: dimensões do viewBox de origem (para escalar corretamente)
"""

FILL = "#4A6FA5"
FG = "#ffffff"
HEIGHT = 30
FONT = 14
PAD_X = 13
RADIUS = 8
GAP = 8
ICON_GAP = 8
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


def _icon_group(icon, height, size):
    inner, vbw, vbh = icon
    box = size * 1.42
    scale = box / max(vbw, vbh)
    iw, ih = vbw * scale, vbh * scale
    iy = (height - ih) / 2.0
    return f'<g transform="translate({PAD_X},{iy:.2f}) scale({scale:.4f})">{inner}</g>', iw


def _pill_markup(label, x, y, fill, fg, height, size, radius, icon, stroke):
    tw = text_width(label, size)
    ty = round(height / 2 + size * 0.34)
    if icon:
        icon_g, iw = _icon_group(icon, height, size)
        w = round(PAD_X + iw + ICON_GAP + tw + PAD_X)
        tx = round(PAD_X + iw + ICON_GAP)
        text = (f'<text x="{tx}" y="{ty}" text-anchor="start" font-family="{FONT_FAMILY}" '
                f'font-size="{size}" font-weight="600" fill="{fg}">{_esc(label)}</text>')
        inner = icon_g + text
    else:
        w = round(tw + 2 * PAD_X)
        inner = (f'<text x="{w/2:.0f}" y="{ty}" text-anchor="middle" font-family="{FONT_FAMILY}" '
                 f'font-size="{size}" font-weight="600" fill="{fg}">{_esc(label)}</text>')
    sk = f' stroke="{stroke}"' if stroke else ""
    return (f'<g transform="translate({x},{y})"><rect width="{w}" height="{height}" rx="{radius}" '
            f'fill="{fill}"{sk}/>{inner}</g>'), w


def pill(label, icon=None, fill=FILL, fg=FG, height=HEIGHT, size=FONT, radius=RADIUS, stroke=None):
    markup, w = _pill_markup(label, 0.5, 0.5, fill, fg, height - 1, size, radius, icon, stroke)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w+1}" height="{height}" '
            f'viewBox="0 0 {w+1} {height}" role="img" aria-label="{_esc(label)}">{markup}</svg>\n')


def row(items, max_width=520, fill=FILL, fg=FG, height=HEIGHT, size=FONT, radius=RADIUS, gap=GAP, stroke=None):
    """`items` = lista de (label, icon) ou str."""
    norm = [(it if isinstance(it, tuple) else (it, None)) for it in items]
    sized = []
    for label, icon in norm:
        _, w = _pill_markup(label, 0, 0, fill, fg, height, size, radius, icon, stroke)
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
    width = max(sum(w for _, _, w in ln) + gap * (len(ln) - 1) for ln in lines) + 1
    parts, y = [], 0.5
    for ln in lines:
        x = 0.5
        for label, icon, w in ln:
            markup, _ = _pill_markup(label, x, y, fill, fg, height - 1, size, radius, icon, stroke)
            parts.append(markup)
            x += w + gap
        y += line_h
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" '
            f'viewBox="0 0 {width} {total_h}" role="img">{"".join(parts)}</svg>\n')
