"""Draw the README figure from published results, without rerunning the study.

Run from the repository with ``uv run python scripts/figure_presentation.py``.
The input tables remain the numerical source of truth.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
BLUE, ORANGE, GREEN, GREY = "#176B96", "#C56628", "#14816D", "#718096"
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 15,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#CBD5E0",
        "text.color": "#172B3A",
        "axes.labelcolor": "#172B3A",
        "xtick.color": "#425466",
        "ytick.color": "#425466",
        "axes.axisbelow": True,
    }
)


def number(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def finish(fig, axes, title, note, path="results/figures/presentation.png"):
    for ax in np.asarray(axes, dtype=object).ravel():
        ax.grid(axis="x", color="#EDF0F3", linewidth=0.8)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))
    fig.suptitle(title, x=0.02, ha="left", fontweight="bold", fontsize=16)
    fig.text(0.02, 0.015, note, ha="left", va="bottom", fontsize=9, color="#526575")
    fig.tight_layout(rect=(0, 0.075, 1, 0.91))
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    d = pd.read_csv(ROOT / "results/tables/backtest_resume.csv", index_col=0)
    keys = ["politique_bandes", "black_litterman", "equipondere"]
    labels = ["Plan avec seuils de rééquilibrage", "Plan modifié par les prévisions", "Répartition égale"]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    values = d.loc[keys, "rendement_annualise"].to_numpy() * 100
    ax.barh([2, 1, 0], values, color=[BLUE, ORANGE, GREY], height=0.5)
    for y, v in zip([2, 1, 0], values, strict=True):
        ax.text(v + 0.1, y, number(v) + " %", va="center")
    ax.set_yticks([2, 1, 0], labels)
    ax.set_xlim(0, values.max() * 1.2)
    ax.set_xlabel("Croissance annuelle composée après coûts (%)")
    finish(
        fig,
        [ax],
        "Les prévisions n'améliorent pas le plan sur cette période",
        "Novembre 2007 à août 2026 · six fonds cotés au Canada · rendements en dollars canadiens\n"
        "Coût de 0,10 % par montant négocié, hors achat initial. Les risques et compositions diffèrent entre règles.",
    )


if __name__ == "__main__":
    main()
