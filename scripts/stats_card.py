#!/usr/bin/env python3
"""
Gera cards de estatísticas e de linguagens servidos pelo próprio repositório
(não dependem de serviços externos instáveis e enxergam repositórios privados).

Usa a GraphQL API autenticada com um token em GH_TOKEN (ou GITHUB_TOKEN).
Só regenera se o token pertencer ao próprio usuário do perfil, para que um token
de bot (sem acesso aos números privados) não sobrescreva os cards com dados parciais.

Saída: assets/stats-light.svg, assets/stats-dark.svg,
       assets/langs-light.svg, assets/langs-dark.svg
"""

import os
import json
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
USER = os.environ.get("PROFILE_USER", "arturmuller25")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""

QUERY = """
query {
  viewer {
    login
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""

LIGHT = {
    "bg": "#F4F4F2", "border": "#DDE1E6", "title": "#36567D",
    "value": "#4A6FA5", "label": "#5A6B7B",
    "ramp": ["#36567D", "#4A6FA5", "#6E86A8", "#9aabc6", "#b9c4d6", "#d2dae6"],
}
DARK = {
    "bg": "#1c2530", "border": "#2d3f57", "title": "#8aa6c8",
    "value": "#7E97B8", "label": "#9fb0c4",
    "ramp": ["#aebccd", "#8aa6c8", "#6E86A8", "#5a78a0", "#46618a", "#36567D"],
}

def _hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _shift(c, f):
    r, g, b = _hx(c)
    if f >= 0:
        r, g, b = (round(v + (255 - v) * f) for v in (r, g, b))
    else:
        r, g, b = (round(v * (1 + f)) for v in (r, g, b))
    return "#%02x%02x%02x" % (r, g, b)


def _mix(c1, c2, t):
    a, b = _hx(c1), _hx(c2)
    return "#%02x%02x%02x" % tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3))


# Cor caracteristica de cada linguagem (baseada na logo/identidade oficial).
LANG_COLORS = {
    "Python": "#3776AB",      # azul da logo do Python
    "PHP": "#777BB4",         # roxo do elefante do PHP
    "HTML": "#E34F26",        # laranja do HTML5
    "TypeScript": "#3178C6",  # azul do TypeScript
    "CSS": "#563D7C",         # roxo/indigo (cor do CSS no GitHub)
    "Blade": "#F7523F",       # vermelho do Blade/Laravel
    "JavaScript": "#F7DF1E",  # amarelo do JavaScript
    "PowerShell": "#5391FE",  # azul do PowerShell
    "Shell": "#89E051",       # verde do Shell/Bash
    "C": "#A8B9CC", "SQLite": "#003B57",
    "Outros": "#94A3B8",      # cinza neutro
}
EXTRA = ["#F59E0B", "#8B5CF6", "#10B981", "#E11D48", "#0EA5E9", "#D946EF", "#84CC16"]


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "stats-card"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]["viewer"]


def render_stats(stats, pal):
    cols = [
        (stats["contribs"], "contribuições"),
        (stats["commits"], "commits"),
        (stats["issues"], "issues"),
        (stats["repos"], "repositórios"),
    ]
    w, h = 480, 150
    cx = [60 + i * 120 for i in range(4)]
    items = []
    for (val, lab), x in zip(cols, cx):
        items.append(
            f'<text x="{x}" y="92" text-anchor="middle" font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" '
            f'font-size="34" font-weight="800" fill="{pal["value"]}">{val}</text>'
            f'<text x="{x}" y="116" text-anchor="middle" font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" '
            f'font-size="13" fill="{pal["label"]}">{lab}</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Estatisticas do GitHub">
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{pal["bg"]}" stroke="{pal["border"]}"/>
  <text x="24" y="38" font-family="'Segoe UI',Helvetica,Arial,sans-serif" font-size="16" font-weight="700" fill="{pal["title"]}">Atividade no GitHub &#183; ultimo ano</text>
  <line x1="24" y1="50" x2="{w-24}" y2="50" stroke="{pal["border"]}"/>
  {''.join(items)}
</svg>
'''


def render_langs(langs, pal, palette=None):
    palette = palette or LANG_COLORS
    w = 480
    rows = (len(langs) + 1) // 2
    h = 104 + (rows - 1) * 22 + 18
    total = sum(v for _, v in langs) or 1
    bar_x, bar_w, bar_y, bar_h = 24, w - 48, 66, 14
    gap, n = 2.0, len(langs)
    colors = [palette.get(nm) or EXTRA[i % len(EXTRA)] for i, (nm, _) in enumerate(langs)]
    defs = [f'<clipPath id="r"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="7"/></clipPath>',
            '<linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0%" stop-color="#ffffff" stop-opacity="0.32"/>'
            '<stop offset="42%" stop-color="#ffffff" stop-opacity="0"/>'
            '<stop offset="58%" stop-color="#000000" stop-opacity="0"/>'
            '<stop offset="100%" stop-color="#000000" stop-opacity="0.22"/></linearGradient>']
    segs, legend, x = [], [], bar_x
    for i, (name, val) in enumerate(langs):
        frac = val / total
        seg_w = frac * bar_w
        c = colors[i]
        left = _mix(c, colors[i - 1] if i > 0 else c, 0.35)      # borda esquerda puxa pro vizinho anterior
        right = _mix(c, colors[i + 1] if i < n - 1 else c, 0.35)  # borda direita puxa pro proximo
        gid = f"g{i}"
        defs.append(
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0%" stop-color="{left}"/>'
            f'<stop offset="20%" stop-color="{c}"/>'
            f'<stop offset="80%" stop-color="{c}"/>'
            f'<stop offset="100%" stop-color="{right}"/></linearGradient>'
        )
        draw_w = seg_w - gap if i < n - 1 else seg_w
        if draw_w < 2:
            draw_w = max(2.0, seg_w)
        segs.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{draw_w:.1f}" height="{bar_h}" fill="url(#{gid})"/>'
                    f'<rect x="{x:.1f}" y="{bar_y}" width="{draw_w:.1f}" height="{bar_h}" fill="url(#gloss)"/>')
        x += seg_w
        col = i % 2
        row = i // 2
        lx = 28 + col * 230
        ly = 104 + row * 22
        legend.append(
            f'<circle cx="{lx}" cy="{ly-4}" r="5" fill="{c}" stroke="{_shift(c, -0.25)}" stroke-width="0.75"/>'
            f'<text x="{lx+12}" y="{ly}" font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" '
            f'font-size="13" fill="{pal["label"]}">{name} {frac*100:.1f}%</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Linguagens mais usadas">
  <defs>{''.join(defs)}</defs>
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{pal["bg"]}" stroke="{pal["border"]}"/>
  <text x="24" y="38" font-family="'Segoe UI',Helvetica,Arial,sans-serif" font-size="16" font-weight="700" fill="{pal["title"]}">Linguagens mais usadas &#183; todos os repos</text>
  <line x1="24" y1="50" x2="{w-24}" y2="50" stroke="{pal["border"]}"/>
  <g clip-path="url(#r)">{''.join(segs)}</g>
  {''.join(legend)}
</svg>
'''


def aggregate_langs(repos):
    totals = {}
    for node in repos:
        for e in node["languages"]["edges"]:
            totals[e["node"]["name"]] = totals.get(e["node"]["name"], 0) + e["size"]
    ordered = sorted(totals.items(), key=lambda kv: -kv[1])
    top = ordered[:8]
    rest = sum(v for _, v in ordered[8:])
    if rest:
        top.append(("Outros", rest))
    return top


def main():
    data = fetch()
    if (data.get("login") or "").lower() != USER.lower():
        print(f"Token nao pertence a {USER} (viewer={data.get('login')}); nao regenerando.")
        return
    cc = data["contributionsCollection"]
    repos = data["repositories"]["nodes"]
    stats = {
        "contribs": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "issues": cc["totalIssueContributions"],
        "repos": data["repositories"]["totalCount"],
    }
    langs = aggregate_langs(repos)
    os.makedirs(ASSETS, exist_ok=True)
    open(os.path.join(ASSETS, "stats-light.svg"), "w", encoding="utf-8").write(render_stats(stats, LIGHT))
    open(os.path.join(ASSETS, "stats-dark.svg"), "w", encoding="utf-8").write(render_stats(stats, DARK))
    open(os.path.join(ASSETS, "langs-light.svg"), "w", encoding="utf-8").write(render_langs(langs, LIGHT))
    open(os.path.join(ASSETS, "langs-dark.svg"), "w", encoding="utf-8").write(render_langs(langs, DARK))
    print("OK stats:", stats)
    print("OK langs:", langs)


if __name__ == "__main__":
    main()
