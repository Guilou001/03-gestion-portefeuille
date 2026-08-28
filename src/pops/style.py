"""Style matplotlib commun : une figure se lit sans sa légende externe et sans zoomer.

Palette d'Okabe et Ito (2008), huit couleurs distinguables par les lecteurs daltoniens ; polices de
11 points minimum ; grille discrète ; pas de cadre au-dessus ni à droite ; 200 points par pouce.
"""

from __future__ import annotations

import matplotlib as mpl
from cycler import cycler

OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]


def use_style() -> None:
    """Applique le style du dépôt à toutes les figures qui suivent."""
    mpl.rcParams.update({
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "figure.constrained_layout.use": True,
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "axes.prop_cycle": cycler(color=OKABE_ITO),
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
        "lines.linewidth": 1.6,
    })
