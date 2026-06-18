#!/usr/bin/env python3
"""Gera as pílulas estáticas (contato, stack e tecnologias dos projetos)."""

import os
import re
import time
import urllib.request

import svgchip

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# Stack: tile escura + ícone colorido + texto claro
STACK_FILL = "#22303f"
STACK_FG = "#eef2f7"
STACK_STROKE = "#3a4f6a"

# slugs Simple Icons (monocromático) -> usado em contato/projetos (ícone branco)
SLUGS = {
    "Python": ["python"], "TypeScript": ["typescript"], "JavaScript": ["javascript"],
    "PHP": ["php"], "React": ["react"], "Vite": ["vite"], "FastAPI": ["fastapi"],
    "OpenAI": ["openai"], "Pinecone": ["pinecone"], "MySQL": ["mysql"],
    "LinkedIn": ["linkedin"], "Gmail": ["gmail"],
}
MONO_LOGOS = {"Pinecone": "logos/pinecone-icon"}

# ícones COLORIDOS (Iconify) para o Stack
COLORED = {
    "Python": ["logos/python"], "TypeScript": ["logos/typescript-icon"],
    "JavaScript": ["logos/javascript"], "PHP": ["logos/php"], "PowerShell": ["logos/powershell"],
    "HTML": ["logos/html-5"], "CSS": ["logos/css-3"], "React": ["logos/react"],
    "Vite": ["logos/vitejs"], "FastAPI": ["logos/fastapi-icon"], "PyTorch": ["logos/pytorch-icon"],
    "OpenAI": ["logos/openai-icon"], "Pinecone": ["logos/pinecone-icon"],
    "Hugging Face": ["logos/hugging-face-icon"], "Railway": ["logos/railway"],
    "Twig": ["vscode-icons/file-type-twig"], "Playwright": ["logos/playwright"],
    "Git": ["logos/git-icon"], "VS Code": ["logos/visual-studio-code"],
    "MySQL": ["logos/mysql-icon"], "uv": ["logos/astral"], "Claude": ["logos/claude-ai-icon", "logos/anthropic-icon"],
}
# cor de marca para fallback (quando não há ícone colorido pronto)
BRAND = {"PowerShell": "#5391FE", "uv": "#DE5FE9", "Claude": "#D97757", "Railway": "#FFFFFF"}
# slug Simple Icons para tingir quando não há colorido (logos) disponível
FALLBACK_SLUG = {"PowerShell": "powershell", "uv": "uv", "Railway": "railway"}

_ctr = [0]


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=15).read().decode()


def _viewbox(svg):
    m = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', svg)
    return (float(m.group(1)), float(m.group(2))) if m else (24.0, 24.0)


def _paths(svg):
    return re.findall(r'<path[^>]*\sd="([^"]+)"', svg)


def mono_icon(label, fg="#ffffff"):
    urls = [f"https://cdn.simpleicons.org/{s}" for s in SLUGS.get(label, [])]
    urls += [f"https://api.iconify.design/simple-icons/{s}.svg" for s in SLUGS.get(label, [])]
    if label in MONO_LOGOS:
        urls.append(f"https://api.iconify.design/{MONO_LOGOS[label]}.svg")
    for url in urls:
        try:
            svg = _fetch(url)
        except Exception:
            continue
        ps = _paths(svg)
        if ps:
            inner = "".join(f'<path d="{d}" fill="{fg}"/>' for d in ps)
            w, h = _viewbox(svg)
            time.sleep(0.1)
            return (inner, w, h)
    return None


def _namespace(inner):
    _ctr[0] += 1
    pfx = f"ic{_ctr[0]}_"
    inner = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{pfx}{m.group(1)}"', inner)
    inner = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{pfx}{m.group(1)})', inner)
    inner = re.sub(r'((?:xlink:)?href)="#([^"]+)"', lambda m: f'{m.group(1)}="#{pfx}{m.group(2)}"', inner)
    return inner


def color_icon(label):
    for ic in COLORED.get(label, []):
        try:
            svg = _fetch(f"https://api.iconify.design/{ic}.svg")
        except Exception:
            continue
        if "<path" not in svg and "<g" not in svg:
            continue
        inner = re.sub(r"(?is)^.*?<svg[^>]*>", "", svg)
        inner = re.sub(r"(?is)</svg>\s*$", "", inner).strip()
        if not inner:
            continue
        w, h = _viewbox(svg)
        time.sleep(0.1)
        return (_namespace(inner), w, h)
    # fallback: ícone monocromático tingido com a cor de marca
    slug = FALLBACK_SLUG.get(label)
    if slug:
        hexc = BRAND.get(label, "#cfd8e3")
        for url in (f"https://cdn.simpleicons.org/{slug}",
                    f"https://api.iconify.design/simple-icons/{slug}.svg"):
            try:
                svg = _fetch(url)
            except Exception:
                continue
            ps = _paths(svg)
            if ps:
                inner = "".join(f'<path d="{d}" fill="{hexc}"/>' for d in ps)
                w, h = _viewbox(svg)
                time.sleep(0.1)
                return (inner, w, h)
    return None


def citems(labels):
    return [(l, color_icon(l)) for l in labels]


def mitems(labels):
    return [(l, mono_icon(l)) for l in labels]


def write(name, content):
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
        f.write(content)


def main():
    os.makedirs(ASSETS, exist_ok=True)

    # Contato (aço + ícone branco)
    write("contact-linkedin.svg", svgchip.pill("LinkedIn", mono_icon("LinkedIn"), height=40, size=15))
    write("contact-gmail.svg", svgchip.pill("Gmail", mono_icon("Gmail"), height=40, size=15))

    # Stack (categorias, tile escura, ícone colorido)
    def stack(labels):
        return svgchip.row(citems(labels), max_width=560, fill=STACK_FILL, fg=STACK_FG,
                           stroke=STACK_STROKE, height=34, size=14)
    write("tech-langs.svg", stack(["Python", "TypeScript", "JavaScript", "PHP", "PowerShell", "HTML", "CSS"]))
    write("tech-frameworks.svg", stack(["React", "Vite", "FastAPI", "PyTorch", "OpenAI", "Pinecone", "Hugging Face", "Twig"]))
    write("tech-tools.svg", stack(["Railway", "uv", "Playwright", "Git", "VS Code", "Claude"]))

    # Tecnologias por projeto (aço + ícone branco)
    write("proj-comac.svg", svgchip.row(mitems(["Python", "FastAPI", "OpenAI", "Pinecone"]), max_width=340))
    write("proj-muller.svg", svgchip.row(mitems(["React", "TypeScript", "Vite"]), max_width=340))
    write("proj-clarivid.svg", svgchip.row(mitems(["PHP", "MySQL", "JavaScript"]), max_width=340))

    # Utilitárias
    write("privado.svg", svgchip.pill("privado", fill="#5A6B7B", height=24, size=12))
    write("ver-repos.svg", svgchip.pill("Ver todos os repositórios", height=30, size=14))

    print("Pílulas geradas.")


if __name__ == "__main__":
    main()
