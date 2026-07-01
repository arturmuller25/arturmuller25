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

# Gradiente frio e elegante (combina com a paleta aço/quartzo do perfil)
GRAD = [(0.0, "#38BDF8"), (0.35, "#5488D8"), (0.66, "#7C6BE0"), (1.0, "#A855F7")]


def _hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _grad(t):
    t = max(0.0, min(1.0, t))
    for i in range(len(GRAD) - 1):
        p0, c0 = GRAD[i]
        p1, c1 = GRAD[i + 1]
        if p0 <= t <= p1:
            f = (t - p0) / (p1 - p0) if p1 > p0 else 0.0
            a, b = _hx(c0), _hx(c1)
            return "#%02x%02x%02x" % tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))
    return GRAD[-1][1]


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


def render_langs(langs, pal):
    w = 480
    rows = (len(langs) + 1) // 2
    h = 104 + (rows - 1) * 22 + 18
    total = sum(v for _, v in langs) or 1
    bar_x, bar_w, bar_y, bar_h = 24, w - 48, 66, 14
    stops = "".join(f'<stop offset="{p*100:.0f}%" stop-color="{c}"/>' for p, c in GRAD)
    dividers, legend, x = [], [], bar_x
    for i, (name, val) in enumerate(langs):
        frac = val / total
        mid = (x - bar_x + frac * bar_w / 2) / bar_w
        color = _grad(mid)
        x += frac * bar_w
        if i < len(langs) - 1:
            dividers.append(f'<rect x="{x-0.75:.1f}" y="{bar_y}" width="1.5" height="{bar_h}" '
                            f'fill="{pal["bg"]}" opacity="0.5"/>')
        col = i % 2
        row = i // 2
        lx = 28 + col * 230
        ly = 104 + row * 22
        legend.append(
            f'<circle cx="{lx}" cy="{ly-4}" r="5" fill="{color}"/>'
            f'<text x="{lx+12}" y="{ly}" font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" '
            f'font-size="13" fill="{pal["label"]}">{name} {frac*100:.1f}%</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Linguagens mais usadas">
  <defs>
    <linearGradient id="lg" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>
    <clipPath id="r"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="7"/></clipPath>
  </defs>
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{pal["bg"]}" stroke="{pal["border"]}"/>
  <text x="24" y="38" font-family="'Segoe UI',Helvetica,Arial,sans-serif" font-size="16" font-weight="700" fill="{pal["title"]}">Linguagens mais usadas &#183; todos os repos</text>
  <line x1="24" y1="50" x2="{w-24}" y2="50" stroke="{pal["border"]}"/>
  <g clip-path="url(#r)"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" fill="url(#lg)"/>{''.join(dividers)}</g>
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
