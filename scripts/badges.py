#!/usr/bin/env python3
"""Gera as pílulas estáticas (contato, stack e tecnologias dos projetos) com ícones."""

import os
import re
import time
import urllib.request

import svgchip

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# nome exibido -> slugs candidatos no Simple Icons
SLUGS = {
    "Python": ["python"], "TypeScript": ["typescript"], "JavaScript": ["javascript"],
    "PHP": ["php"], "PowerShell": ["powershell"], "HTML": ["html5"], "CSS": ["css3", "css"],
    "React": ["react"], "Vite": ["vite"], "FastAPI": ["fastapi"], "PyTorch": ["pytorch"],
    "OpenAI": ["openai"], "Pinecone": ["pinecone"], "Hugging Face": ["huggingface"],
    "Railway": ["railway"], "Twig": ["twig"], "uv": ["uv", "astral"], "Playwright": ["playwright"],
    "Git": ["git"], "VS Code": [], "Claude": ["claude", "anthropic"], "MySQL": ["mysql"],
    "LinkedIn": ["linkedin"], "Gmail": ["gmail"],
}

# fallback no set 'logos' do Iconify (para marcas removidas do Simple Icons)
LOGOS = {
    "Pinecone": "logos/pinecone-icon", "Twig": "vscode-icons/file-type-twig",
    "VS Code": "logos/visual-studio-code",
}

_cache = {}


def _urls(label):
    for slug in SLUGS.get(label, []):
        yield f"https://cdn.simpleicons.org/{slug}"
    for slug in SLUGS.get(label, []):
        yield f"https://api.iconify.design/simple-icons/{slug}.svg"
    if label in LOGOS:
        yield f"https://api.iconify.design/{LOGOS[label]}.svg"


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=15).read().decode()


def icon(label):
    if label in _cache:
        return _cache[label]
    result = None
    for url in _urls(label):
        try:
            svg = _fetch(url)
        except Exception:
            continue
        paths = re.findall(r'<path[^>]*\sd="([^"]+)"', svg)
        if not paths:
            continue
        vb = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', svg)
        size = max(float(vb.group(1)), float(vb.group(2))) if vb else 24.0
        result = (paths, size)
        break
    _cache[label] = result
    time.sleep(0.15)
    return result


def items(labels):
    return [(l, icon(l)) for l in labels]


def write(name, content):
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
        f.write(content)


def main():
    os.makedirs(ASSETS, exist_ok=True)

    write("contact-linkedin.svg", svgchip.pill("LinkedIn", icon("LinkedIn"), height=40, size=15))
    write("contact-gmail.svg", svgchip.pill("Gmail", icon("Gmail"), height=40, size=15))

    langs = ["Python", "TypeScript", "JavaScript", "PHP", "PowerShell", "HTML", "CSS"]
    tools = ["React", "Vite", "FastAPI", "PyTorch", "OpenAI", "Pinecone", "Hugging Face",
             "Railway", "Twig", "uv", "Playwright", "Git", "VS Code", "Claude"]
    write("stack-langs.svg", svgchip.row(items(langs), max_width=520))
    write("stack-tools.svg", svgchip.row(items(tools), max_width=520))

    write("proj-comac.svg", svgchip.row(items(["Python", "FastAPI", "OpenAI", "Pinecone"]), max_width=340))
    write("proj-muller.svg", svgchip.row(items(["React", "TypeScript", "Vite"]), max_width=340))
    write("proj-clarivid.svg", svgchip.row(items(["PHP", "MySQL", "JavaScript"]), max_width=340))

    write("privado.svg", svgchip.pill("privado", fill="#5A6B7B", height=24, size=12))
    write("ver-repos.svg", svgchip.pill("Ver todos os repositórios", height=30, size=14))

    missing = [k for k in SLUGS if icon(k) is None]
    print("Pílulas geradas. Sem ícone:", missing or "nenhum")


if __name__ == "__main__":
    main()
