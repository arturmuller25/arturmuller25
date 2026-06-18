#!/usr/bin/env python3
"""Gera as pílulas estáticas (contato, stack e tecnologias dos projetos)."""

import os
import svgchip

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def write(name, content):
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
        f.write(content)


def main():
    os.makedirs(ASSETS, exist_ok=True)

    # Contato (pílulas isoladas, clicáveis, um pouco maiores para destaque)
    write("contact-linkedin.svg", svgchip.pill("LinkedIn", height=38, size=15))
    write("contact-gmail.svg", svgchip.pill("Gmail", height=38, size=15))

    # Stack
    langs = ["Python", "TypeScript", "JavaScript", "PHP", "PowerShell", "HTML", "CSS"]
    tools = ["React", "Vite", "FastAPI", "PyTorch", "OpenAI", "Pinecone", "Hugging Face",
             "Railway", "Twig", "uv", "Playwright", "Git", "VS Code", "Claude"]
    write("stack-langs.svg", svgchip.row(langs, max_width=480))
    write("stack-tools.svg", svgchip.row(tools, max_width=480))

    # Tecnologias por projeto
    write("proj-comac.svg", svgchip.row(["Python", "FastAPI", "OpenAI", "Pinecone"], max_width=300))
    write("proj-muller.svg", svgchip.row(["React", "TypeScript", "Vite"], max_width=300))
    write("proj-clarivid.svg", svgchip.row(["PHP", "MySQL", "JavaScript"], max_width=300))

    # Pílulas utilitárias
    write("privado.svg", svgchip.pill("privado", fill="#5A6B7B", height=24, size=12))
    write("ver-repos.svg", svgchip.pill("Ver todos os repositórios", height=30, size=14))

    print("Pílulas geradas em assets/")


if __name__ == "__main__":
    main()
