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
    11: "#dccfc3",   # mão
    15: "#a99e92",   # mão (sombra)
    16: "#48121a",   # ombreira (vermelho bem escuro, distinto da gola)
    17: "#6b1c24",   # ombreira (luz)
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
    # punho fechado, liso e uniforme (sem pixels avulsos)
    _ellipse(g, cx, cy, 4, 4, 11)
    _ellipse(g, cx + 1, cy + 1, 3, 3, 15)   # sombra suave
    _ellipse(g, cx - 1, cy - 1, 2, 2, 11)   # leve luz


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
    _poly(g, [(15, 24), (37, 24), (48, 61), (4, 61)], 2)
    _poly(g, [(15, 24), (24, 24), (14, 60), (4, 60)], 3)
    _poly(g, [(28, 24), (37, 24), (48, 61), (38, 61)], 12)
    # mangas
    _rect(g, 9, 32, 15, 50, 2)
    _rect(g, 37, 32, 43, 50, 12)
    # GOLA (um pouco mais baixa): leque atrás da cabeça, borda vermelha + interior escuro
    _poly(g, [(13, 26), (10, 6), (19, 11), (26, 14), (33, 11), (42, 6), (39, 26)], 5)
    _poly(g, [(16, 25), (13, 9), (20, 13), (26, 16), (32, 13), (39, 9), (36, 25)], 4)
    # OMBREIRAS (pauldrons) — vermelho ESCURO, distinto da gola, com luz/sombra e franja
    _ellipse(g, 12, 28, 6, 4, 16)
    _ellipse(g, 12, 27, 6, 2, 17)
    _ellipse(g, 12, 30, 6, 2, 13)
    _ellipse(g, 40, 28, 6, 4, 16)
    _ellipse(g, 40, 27, 6, 2, 17)
    _ellipse(g, 40, 30, 6, 2, 13)
    for x in range(7, 18, 2):
        g[32][x] = 13
    for x in range(35, 46, 2):
        g[32][x] = 13
    # placa central vermelha (abertura em V do sobretudo)
    _poly(g, [(22, 30), (30, 30), (31, 47), (26, 58), (21, 47)], 4)
    _poly(g, [(24, 31), (28, 31), (28, 46), (26, 54), (24, 46)], 5)
    # correntes douradas entre as ombreiras (dois arcos)
    for (px, py) in [(15, 31), (19, 35), (23, 37), (26, 38), (29, 37), (33, 35), (37, 31)]:
        g[py][px] = 10
    for (px, py) in [(18, 30), (22, 33), (26, 34), (30, 33), (34, 30)]:
        g[py][px] = 10
    # punhos fechados
    _fist(g, 12, 51)
    _fist(g, 40, 51)
    # cabeça (emerge da gola), luz à esquerda
    _ellipse(g, cx, 15, 7, 9, 6)
    _ellipse(g, cx, 15, 7, 9, 7, half="r")
    _ellipse(g, cx - 1, 14, 6, 8, 6, half="l")
    for (px, py) in [(cx - 3, 12), (cx - 2, 12), (cx + 2, 12), (cx + 3, 12), (cx, 8), (cx, 10)]:
        g[py][px] = 7
    # bocarra com presas
    _rect(g, cx - 6, 17, cx + 6, 21, 9)
    for x in range(cx - 6, cx + 7, 2):
        g[17][x] = 8
        g[18][x] = 8
    for x in range(cx - 5, cx + 6, 2):
        g[21][x] = 8
        g[20][x] = 8
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
