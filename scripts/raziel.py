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
    6: "#d4cabf",    # pele pálida
    7: "#9a8a7e",    # pele (sombra)
    14: "#6d6158",   # pele (sombra profunda)
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


def _claw(g, cx, cy, up):
    # palma
    _ellipse(g, cx, cy, 3, 2, 11)
    g[min(H - 1, cy + 1)][cx] = 15
    # quatro garras se abrindo em leque
    for dx in (-3, -1, 1, 3):
        for t in range(1, 5):
            x = int(round(cx + dx + dx * 0.35 * t))
            y = cy + up * (1 + t)
            if 0 <= x < W and 0 <= y < H:
                g[y][x] = 8 if t >= 3 else 11


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
    # gola pontuda (assimétrica: ponta esquerda à frente, direita atrás/sombra)
    _poly(g, [(23, 27), (4, 2), (19, 24)], 5)
    _poly(g, [(22, 26), (10, 7), (20, 23)], 4)
    _poly(g, [(29, 27), (44, 8), (31, 23)], 4)
    _poly(g, [(29, 26), (40, 11), (31, 24)], 13)
    # sobretudo (sino levemente torcido) com luz à esquerda e sombra à direita
    _poly(g, [(13, 23), (35, 23), (47, 61), (3, 61)], 2)
    _poly(g, [(13, 23), (21, 23), (12, 60), (3, 60)], 3)
    _poly(g, [(31, 24), (35, 23), (47, 61), (33, 61)], 12)
    # mangas
    _rect(g, 9, 27, 15, 46, 2)
    _rect(g, 35, 28, 41, 47, 12)
    # placa central vermelha (deslocada à esquerda pela rotação)
    _poly(g, [(19, 25), (28, 25), (30, 46), (24, 58), (17, 46)], 4)
    _poly(g, [(21, 27), (26, 27), (27, 45), (23, 54), (20, 45)], 5)
    _poly(g, [(26, 29), (28, 30), (29, 47), (25, 52)], 13)
    # correntes douradas (dois arcos)
    for (px, py) in [(16, 31), (19, 33), (23, 34), (27, 33), (30, 31)]:
        g[py][px] = 10
    for (px, py) in [(17, 39), (20, 41), (23, 42), (26, 41), (29, 39)]:
        g[py][px] = 10
    # mãos com garras (esquerda erguida à frente, direita baixa)
    _claw(g, 11, 39, -1)
    _claw(g, 40, 51, 1)
    # cabeça pálida virada levemente à esquerda
    _ellipse(g, 23, 14, 7, 9, 6)
    _ellipse(g, 23, 14, 7, 9, 7, half="r")
    _ellipse(g, 21, 13, 5, 8, 6, half="l")
    _rect(g, 28, 9, 29, 20, 14)
    # olhos fundos + rachaduras
    for (px, py) in [(20, 11), (21, 11), (25, 11), (26, 11), (23, 7), (23, 9), (19, 13)]:
        g[py][px] = 7
    # bocarra curva com presas
    _poly(g, [(17, 16), (29, 16), (27, 21), (18, 20)], 9)
    for x in range(17, 29, 2):
        g[16][x] = 8
        g[17][x] = 8
    for x in range(18, 28, 2):
        g[20][x] = 8
        g[19][x] = 8
    # pés (passada)
    _rect(g, 13, 60, 20, 63, 2)
    _rect(g, 27, 59, 34, 63, 12)
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
