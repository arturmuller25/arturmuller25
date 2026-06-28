#!/usr/bin/env python3
"""
Pixel-art procedural do Raziel (Vampiro) — Ordem Paranormal.

Pose em 3/4 (levemente de lado), com sombreado em camadas, gola vermelha
pontuda, cabeça pálida com sorriso de presas, sobretudo preto/vermelho com
correntes douradas e mãos com garras. Contorno automático e run-length nas
linhas para não gerar milhares de <rect>.
"""

W, H = 52, 64

PALETTE = {
    1: "#0c0a0c",    # contorno
    2: "#181219",    # sobretudo (preto)
    3: "#2a2230",    # sobretudo (luz, lado iluminado)
    12: "#0e0a11",   # sobretudo (sombra profunda, lado afastado)
    4: "#5d141b",    # vermelho escuro
    5: "#a3262e",    # vermelho vivo
    13: "#3a0d12",   # vermelho (sombra)
    6: "#cf9389",    # pele avermelhada
    7: "#9c5a52",    # pele (sombra)
    14: "#6e3a35",   # pele (sombra profunda)
    8: "#efe6cc",    # presas / osso
    9: "#160610",    # bocarra
    10: "#cda24a",   # corrente dourada
    11: "#dccfc3",   # garra / mão
    15: "#a99e92",   # garra (sombra)
}


def _grid():
    return [[0] * W for _ in range(H)]


def _rect(g, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            g[y][x] = c


def _ellipse(g, cx, cy, rx, ry, c, half=None):
    for y in range(H):
        for x in range(W):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                if half == "r" and x < cx:
                    continue
                if half == "l" and x > cx:
                    continue
                g[y][x] = c


def _poly(g, pts, c):
    ys = [p[1] for p in pts]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        xs = []
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            for x in range(int(round(xs[j])), int(round(xs[j + 1])) + 1):
                if 0 <= x < W:
                    g[y][x] = c


def _fist(g, cx, cy):
    # punho fechado (dedos juntos)
    _ellipse(g, cx, cy, 4, 3, 11)
    _rect(g, cx - 3, cy - 1, cx + 3, cy + 2, 11)
    # vincos entre os dedos
    for dx in (-2, 0, 2):
        if 0 <= cx + dx < W:
            g[cy][cx + dx] = 15
    # pequenas pontas de garra na base do punho
    for dx in (-3, -1, 1, 3):
        x, y = cx + dx, cy + 3
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = 8


def _outline(g, c=1):
    add = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and g[ny][nx] not in (0, c):
                        add.append((x, y))
                        break
    for x, y in add:
        g[y][x] = c


def _paint():
    g = _grid()
    cx = 26
    # sobretudo (sino) com luz à esquerda e sombra à direita
    _poly(g, [(15, 23), (37, 23), (48, 61), (4, 61)], 2)
    _poly(g, [(15, 23), (24, 23), (14, 60), (4, 60)], 3)
    _poly(g, [(28, 23), (37, 23), (48, 61), (38, 61)], 12)
    # mangas
    _rect(g, 9, 27, 15, 48, 2)
    _rect(g, 37, 27, 43, 48, 12)
    # --- GOLA (por cima do sobretudo) ---
    # faixa atrás do pescoço (liga os dois lados)
    _poly(g, [(17, 16), (35, 16), (33, 21), (19, 21)], 4)
    # lapelas: assentam nos ombros, abraçam o pescoço e sobem nas laterais
    _poly(g, [(11, 30), (8, 11), (13, 10), (18, 17), (21, 31)], 5)
    _poly(g, [(41, 30), (44, 11), (39, 10), (34, 17), (31, 31)], 5)
    _poly(g, [(11, 30), (8, 11), (11, 15), (15, 30)], 4)     # dobra externa esq
    _poly(g, [(41, 30), (44, 11), (41, 15), (37, 30)], 4)    # dobra externa dir
    _poly(g, [(18, 17), (21, 31), (19, 31), (16, 18)], 4)    # vinco interno esq
    _poly(g, [(34, 17), (31, 31), (33, 31), (36, 18)], 4)    # vinco interno dir
    # placa central vermelha (no V da gola, abertura do sobretudo)
    _poly(g, [(22, 30), (30, 30), (31, 47), (26, 58), (21, 47)], 4)
    _poly(g, [(24, 31), (28, 31), (28, 46), (26, 54), (24, 46)], 5)
    # correntes douradas
    for (px, py) in [(20, 34), (23, 36), (26, 37), (29, 36), (32, 34)]:
        g[py][px] = 10
    for (px, py) in [(21, 42), (24, 44), (26, 45), (28, 44), (31, 42)]:
        g[py][px] = 10
    # mãos: punhos fechados
    _fist(g, 12, 48)
    _fist(g, 40, 48)
    # cabeça (emerge da gola), luz à esquerda
    _ellipse(g, cx, 14, 7, 9, 6)
    _ellipse(g, cx, 14, 7, 9, 7, half="r")
    _ellipse(g, cx - 1, 13, 6, 8, 6, half="l")
    for (px, py) in [(cx - 3, 11), (cx - 2, 11), (cx + 2, 11), (cx + 3, 11), (cx, 7), (cx, 9)]:
        g[py][px] = 7
    # bocarra com presas
    _rect(g, cx - 6, 16, cx + 6, 20, 9)
    for x in range(cx - 6, cx + 7, 2):
        g[16][x] = 8
        g[17][x] = 8
    for x in range(cx - 5, cx + 6, 2):
        g[20][x] = 8
        g[19][x] = 8
    # pés
    _rect(g, 16, 60, 23, 63, 2)
    _rect(g, 29, 60, 36, 63, 12)
    _outline(g)
    return g


_CACHE = None


def markup(ox, oy, cell):
    global _CACHE
    if _CACHE is None:
        _CACHE = _paint()
    g = _CACHE
    out = []
    for y in range(H):
        x = 0
        while x < W:
            c = g[y][x]
            if c == 0:
                x += 1
                continue
            run = 1
            while x + run < W and g[y][x + run] == c:
                run += 1
            out.append(f'<rect x="{ox + x*cell:.2f}" y="{oy + y*cell:.2f}" '
                       f'width="{run*cell:.2f}" height="{cell:.2f}" fill="{PALETTE[c]}"/>')
            x += run
    return "".join(out)
