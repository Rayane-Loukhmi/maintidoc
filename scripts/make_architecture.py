"""Génère les deux schémas d'architecture MaintiDoc en PNG."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

NAVY = "#17324d"
BLUE = "#dceaf7"
GREEN = "#dff3e4"
ORANGE = "#fde8cf"
PURPLE = "#e9e1f8"
GREY = "#eef1f4"


def box(ax, x, y, w, h, title, lines, color, title_size=10.5, body_size=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.015",
                                linewidth=1.1, edgecolor=NAVY, facecolor=color))
    ax.text(x + w / 2, y + h - 0.03, title, ha="center", va="top",
            fontsize=title_size, fontweight="bold", color=NAVY)
    ax.text(x + 0.012, y + h - 0.09, "\n".join(lines), ha="left", va="top",
            fontsize=body_size, color="#1f2933", linespacing=1.25)


def arrow(ax, start, end, text="", color=NAVY):
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="->", lw=1.5, color=color))
    if text:
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.012,
                text, ha="center", va="bottom", fontsize=7.5, color=color)


def global_architecture():
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("MaintiDoc — architecture globale du prototype", fontsize=18,
                 fontweight="bold", color=NAVY, pad=16)

    # Ligne 1 : interface et recherche
    box(ax, 0.02, 0.67, 0.14, 0.20, "Interface",
        ["Streamlit", "question + image", "preuves + citations"], BLUE)
    box(ax, 0.18, 0.67, 0.18, 0.20, "Recherche texte",
        ["BGE-M3 · 1024 dim", "Qdrant · 26 passages", "reranker optional"], GREEN)
    box(ax, 0.38, 0.67, 0.18, 0.20, "Recherche image",
        ["CLIP · 512 dim", "5 schémas", "requête anglaise"], GREEN)
    box(ax, 0.58, 0.67, 0.16, 0.20, "Fusion",
        ["RRF par page", "texte + visuel", "top 4 pages"], PURPLE)
    box(ax, 0.76, 0.67, 0.22, 0.20, "Génération",
        ["Ollama local", "llama3.2 / Qwen VL", "JSON + citations"], BLUE)

    # Ligne 2 : données et preuves
    box(ax, 0.02, 0.38, 0.14, 0.20, "Données",
        ["manuel PDF", "9 pages", "OCR optional"], GREY)
    box(ax, 0.18, 0.38, 0.16, 0.20, "Index",
        ["Qdrant text collection", "Qdrant image collection", "chunks.json"], GREY)
    box(ax, 0.36, 0.38, 0.18, 0.20, "Preuves",
        ["passages + tableaux", "1 image max", "IDs + pages"], ORANGE)
    box(ax, 0.56, 0.38, 0.16, 0.20, "Validation",
        ["LangGraph route", "IDs autorisés", "statut d'incertitude"], ORANGE)
    box(ax, 0.74, 0.38, 0.24, 0.20, "Serveur MCP",
        ["get_equipment_history", "get_open_tickets", "create_ticket(token)"], GREEN)

    # Ligne 3 : gouvernance
    box(ax, 0.56, 0.10, 0.42, 0.15, "Gouvernance et traçabilité",
        ["approbation humaine · jeton lié au contenu", "idempotence · audit.jsonl"], PURPLE,
        title_size=10.5, body_size=8)

    # Flux principaux
    arrow(ax, (0.16, 0.80), (0.18, 0.80))
    arrow(ax, (0.16, 0.72), (0.18, 0.72))
    arrow(ax, (0.36, 0.80), (0.38, 0.80), "rangs")
    arrow(ax, (0.36, 0.73), (0.38, 0.73), "rangs")
    arrow(ax, (0.56, 0.77), (0.58, 0.77), "rangs")
    arrow(ax, (0.66, 0.67), (0.66, 0.58), "pages")
    arrow(ax, (0.54, 0.48), (0.56, 0.48))
    arrow(ax, (0.54, 0.43), (0.76, 0.72), "preuves")
    arrow(ax, (0.87, 0.67), (0.64, 0.48), "JSON", color="#5b6b7a")
    arrow(ax, (0.66, 0.38), (0.66, 0.25), "ticket")
    arrow(ax, (0.16, 0.38), (0.18, 0.38))
    arrow(ax, (0.34, 0.38), (0.36, 0.38))
    arrow(ax, (0.18, 0.48), (0.18, 0.67), "index", color="#5b6b7a")
    arrow(ax, (0.38, 0.48), (0.38, 0.67), "index", color="#5b6b7a")

    fig.tight_layout()
    fig.savefig(DOCS / "architecture_globale.png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


def mcp_architecture():
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("MaintiDoc — architecture spécifique MCP et validation humaine",
                 fontsize=18, fontweight="bold", color=NAVY, pad=16)

    box(ax, 0.02, 0.58, 0.17, 0.24, "Technicien",
        ["question", "photo", "contexte"], BLUE)
    box(ax, 0.21, 0.58, 0.19, 0.24, "Application",
        ["prépare le brouillon", "affiche le contenu", "demande l'accord"], BLUE)
    box(ax, 0.42, 0.58, 0.18, 0.24, "Approbation",
        ["humain explicite", "jeton lié au hash", "contenu exact"], ORANGE)
    box(ax, 0.62, 0.58, 0.17, 0.24, "Client MCP",
        ["appel typé", "stdio", "sans accès direct"], PURPLE)
    box(ax, 0.81, 0.58, 0.17, 0.24, "Serveur MCP",
        ["vérifie le jeton", "vérifie le contenu", "crée le ticket"], GREEN)

    box(ax, 0.62, 0.18, 0.17, 0.24, "Outils",
        ["get_equipment_history", "get_open_tickets", "create_ticket"], GREEN)
    box(ax, 0.81, 0.18, 0.17, 0.24, "Données",
        ["historique fictif", "tickets.json", "approvals.json"], GREY)
    box(ax, 0.42, 0.18, 0.18, 0.24, "Audit",
        ["audit.jsonl", "qui / quoi / quand", "traçabilité"], ORANGE)
    box(ax, 0.21, 0.18, 0.19, 0.24, "Idempotence",
        ["clé unique", "pas de doublon", "même ticket"], PURPLE)

    arrow(ax, (0.19, 0.70), (0.21, 0.70))
    arrow(ax, (0.40, 0.70), (0.42, 0.70))
    arrow(ax, (0.60, 0.70), (0.62, 0.70))
    arrow(ax, (0.79, 0.70), (0.81, 0.70))
    arrow(ax, (0.895, 0.58), (0.895, 0.42))
    arrow(ax, (0.81, 0.30), (0.79, 0.30))
    arrow(ax, (0.62, 0.30), (0.60, 0.30))
    arrow(ax, (0.42, 0.30), (0.40, 0.30))

    ax.text(0.5, 0.06,
            "Règle : aucune création sans jeton d'approbation lié au contenu ; "
            "toute modification du brouillon invalide l'accord.",
            ha="center", fontsize=10, color=NAVY, style="italic")
    fig.tight_layout()
    fig.savefig(DOCS / "architecture_mcp.png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    global_architecture()
    mcp_architecture()
    print("schémas écrits dans", DOCS)
