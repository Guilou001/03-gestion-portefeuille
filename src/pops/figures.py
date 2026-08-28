"""Les cinq figures du dépôt, chacune construite pour être lue seule : titres qui affirment,
axes étiquetés en unités réelles, palette lisible par tous (style.py), une idée par figure."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pops.engine import BacktestResult
from pops.policy import run_policy
from pops.style import OKABE_ITO, use_style

LABELS = {
    "black_litterman": "Black-Litterman sous bandes",
    "politique_bandes": "Politique à bandes (sans vue)",
    "hrp": "Parité de risque hiérarchique",
    "equipondere": "Équipondéré",
}
CRISES = [("2008-06", "2009-06", "2008-2009"), ("2020-02", "2020-04", "2020")]


def _shade_crises(ax: plt.Axes) -> None:
    for start, end, label in CRISES:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), color="0.85", zorder=0)
        ax.text(pd.Timestamp(start), ax.get_ylim()[1], f" {label}", va="top", fontsize=8, color="0.4")


def fig_richesse(result: BacktestResult, dest: Path) -> None:
    """100 $ investis au départ, valeur nette de coûts, échelle logarithmique."""
    use_style()
    fig, ax = plt.subplots(figsize=(9, 5))
    wealth = 100.0 * (1.0 + result.returns).cumprod()
    for col in wealth:
        ax.plot(wealth.index, wealth[col], label=f"{LABELS[col]} ({wealth[col].iloc[-1]:,.0f} $)".replace(",", " "))
    ax.set_yscale("log")
    ticks = [75, 100, 150, 200, 300]
    ax.set_yticks(ticks, [f"{t} $" for t in ticks])
    ax.set_ylabel("Valeur de 100 $ investis, en CAD (échelle logarithmique)".replace("$", r"\$"))
    ax.set_xlabel("")
    ax.set_title("Quatre façons d'appliquer la même politique, nettes de 10 pb par transaction")
    _shade_crises(ax)
    ax.legend(loc="upper left")
    fig.savefig(dest)
    plt.close(fig)


def fig_poids(result: BacktestResult, dest: Path) -> None:
    """Un panneau par classe : le poids Black-Litterman circule dans sa bande, jamais au-delà."""
    use_style()
    import matplotlib.dates as mdates

    assets = list(result.policy.targets)
    fig, axes = plt.subplots(2, 3, figsize=(11, 5.5), sharex=True)
    for ax, asset, color in zip(axes.flat, assets, OKABE_ITO, strict=False):
        target = result.policy.targets[asset]
        band = result.policy.band
        ax.axhspan(100 * (target - band), 100 * (target + band), color="0.9", zorder=0)
        ax.axhline(100 * target, color="0.5", linewidth=0.8, linestyle="--")
        ax.plot(result.weights_bl.index, 100 * result.weights_bl[asset], color=color)
        ax.set_title(asset, fontsize=10)
        ax.set_ylim(100 * max(0.0, target - band - 0.03), 100 * (target + band + 0.03))
        ax.xaxis.set_major_locator(mdates.YearLocator(4))
        ax.tick_params(axis="x", labelsize=9)
    for ax in axes[:, 0]:
        ax.set_ylabel("Poids (%)")
    fig.suptitle("Les vues inclinent les poids, les bandes de la politique les bornent "
                 "(zone grise : bande, pointillé : cible)")
    fig.savefig(dest)
    plt.close(fig)


def fig_bandes(result: BacktestResult, asset: str, dest: Path) -> None:
    """Le mécanisme des bandes sur une seule classe : dérive, sortie de bande, retour au bord."""
    use_style()
    policy_out = run_policy(result.returns_assets, result.policy)
    target = result.policy.targets[asset]
    band = result.policy.band
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.axhspan(100 * (target - band), 100 * (target + band), color="0.9", zorder=0,
               label="Bande de tolérance (cible ± 5 pts)")
    ax.axhline(100 * target, color="0.5", linewidth=0.8, linestyle="--", label="Cible de la politique")
    ax.plot(policy_out.weights.index, 100 * policy_out.weights[asset], color=OKABE_ITO[0],
            label=f"Poids de {asset}, dérive puis retour au bord")
    events = [d for d in policy_out.events]
    ax.plot(events, [100 * policy_out.weights.loc[d, asset] for d in events], "v",
            color=OKABE_ITO[3], markersize=5, linestyle="none",
            label=f"Rééquilibrages ({len(events)} en {len(policy_out.weights)} mois)")
    ax.set_ylabel("Poids (%)")
    ax.set_ylim(100 * (target - band) - 3.0, 100 * (target + band) + 3.0)
    ax.set_title(f"On ne touche à rien tant que {asset} reste dans sa bande")
    ax.legend(loc="upper left", fontsize=9)
    fig.savefig(dest)
    plt.close(fig)


def fig_attribution(result: BacktestResult, dest: Path) -> None:
    """L'effet d'allocation cumulé par classe : quelles inclinaisons ont payé, lesquelles ont coûté."""
    use_style()
    attr = result.attribution().drop(index="TOTAL")
    alloc = (100 * attr["allocation"]).sort_values()
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = [OKABE_ITO[2] if v >= 0 else OKABE_ITO[3] for v in alloc]
    ax.barh(alloc.index, alloc.values, color=colors)
    ax.axvline(0, color="0.3", linewidth=0.8)
    ax.set_xlabel("Effet d'allocation cumulé (points de pourcentage, chaînage de Cariño)")
    ax.set_title("D'où vient l'écart entre Black-Litterman et la politique, classe par classe")
    for y, v in enumerate(alloc.values):
        ax.text(v + (0.08 if v >= 0 else -0.08), y, f"{v:+.1f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=9)
    fig.savefig(dest)
    plt.close(fig)


def fig_tilts(pi: np.ndarray, mu: np.ndarray, assets: list[str], month: str, dest: Path) -> None:
    """L'équilibre contre l'a posteriori du dernier mois : ce que les vues ont déplacé, et de combien."""
    use_style()
    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(len(assets))
    ax.hlines(y, 100 * pi, 100 * mu, color="0.6", linewidth=1.2)
    ax.plot(100 * pi, y, "o", color=OKABE_ITO[0], label="Équilibre de la politique (Pi)")
    ax.plot(100 * mu, y, "o", color=OKABE_ITO[3], label="Après les vues (a posteriori)")
    ax.set_yticks(y, assets)
    ax.set_xlabel("Rendement excédentaire attendu, annualisé (%)")
    ax.set_title(f"Ce que les vues de {month} déplacent, classe par classe")
    ax.legend(loc="lower right", fontsize=9)
    ax.invert_yaxis()
    fig.savefig(dest)
    plt.close(fig)


def make_all(result: BacktestResult, out_dir: Path) -> list[Path]:
    """Les quatre figures du backtest (la cinquième, les tilts, appartient au rapport mensuel)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, fn in (
        ("richesse_nette.png", lambda p: fig_richesse(result, p)),
        ("poids_black_litterman.png", lambda p: fig_poids(result, p)),
        ("bandes_politique.png", lambda p: fig_bandes(result, "XIU.TO", p)),
        ("attribution_brinson.png", lambda p: fig_attribution(result, p)),
    ):
        path = out_dir / name
        fn(path)
        paths.append(path)
    return paths
