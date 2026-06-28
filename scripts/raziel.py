#!/usr/bin/env python3
"""
Pixel-art procedural do Raziel, o Vampiro de Sangue (Ordem Paranormal).

Pinta a figura numa grade 52x64 (cabeça pálida com sorriso de presas, gola
vermelha pontuda, sobretudo preto/vermelho com correntes douradas, garras),
faz um contorno automático e devolve markup SVG (com run-length nas linhas
para não gerar milhares de <rect>).
"""

W, H = 52, 64

PALETTE = {
    1: "#0c0a0c",   # contorno
    2: "#181219",   # sobretudo (preto)
    3: "#241d2b",   # sobretudo (luz)
    4: "#5d141b",   # vermelho escuro
    5: "#a3262e",   # vermelho vivo
    6: "#d2c8bf",   # pele pálida
    7: "#8c8079",   # pele (sombra)
    8: "#efe6cc",   # presas / osso
    9: "#160610",   # bocarra
    10: "#c9a24a",  # corrente dourada
    11: "#dccfc3",  # garra
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
    # gola vermelha pontuda (atrás da cabeça)
    _poly(g, [(24, 27), (7, 5), (21, 23)], 5)
    _poly(g, [(28, 27), (45, 5), (31, 23)], 5)
    _poly(g, [(23, 26), (12, 9), (21, 22)], 4)
    _poly(g, [(29, 26), (40, 9), (31, 22)], 4)
    # sobretudo (sino)
    _poly(g, [(15, 23), (37, 23), (49, 61), (3, 61)], 2)
    _poly(g, [(15, 23), (25, 23), (16, 60), (4, 60)], 3)   # luz no lado esquerdo
    # mangas
    _rect(g, 10, 27, 16, 47, 2)
    _rect(g, 36, 27, 42, 47, 2)
    # placa central vermelha
    _poly(g, [(22, 25), (30, 25), (32, 46), (26, 59), (20, 46)], 4)
    _poly(g, [(24, 27), (28, 27), (29, 45), (26, 55), (23, 45)], 5)
    # correntes douradas (dois arcos)
    for (px, py) in [(19, 31), (22, 33), (26, 34), (30, 33), (33, 31)]:
        g[py][px] = 10
    for (px, py) in [(20, 39), (23, 41), (26, 42), (29, 41), (32, 39)]:
        g[py][px] = 10
    # mãos com garras
    _ellipse(g, 13, 49, 4, 4, 11)
    _ellipse(g, 39, 49, 4, 4, 11)
    for (px, py) in [(9, 52), (11, 53), (13, 53), (15, 53), (37, 53), (39, 53), (41, 53), (43, 52)]:
        g[py][px] = 11
    # cabeça pálida
    _ellipse(g, 26, 14, 7, 9, 6)
    _ellipse(g, 26, 14, 7, 9, 7, half="r")
    _ellipse(g, 25, 13, 6, 8, 6, half="l")
    # olhos fundos + rachaduras
    for (px, py) in [(23, 11), (24, 11), (28, 11), (29, 11), (26, 7), (26, 9)]:
        g[py][px] = 7
    # bocarra com presas
    _rect(g, 20, 16, 32, 20, 9)
    for x in range(20, 33, 2):      # presas de cima
        g[16][x] = 8
        if 16 + 1 < H:
            g[17][x] = 8
    for x in range(21, 33, 2):      # presas de baixo
        g[20][x] = 8
        g[19][x] = 8
    # pés
    _rect(g, 17, 60, 24, 63, 2)
    _rect(g, 28, 60, 35, 63, 2)
    _outline(g)
    return g


_CACHE = None


def markup(ox, oy, cell):
    """Devolve <rect>s posicionados (run-length por linha) para a figura."""
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
