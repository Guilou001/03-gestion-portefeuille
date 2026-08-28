"""Le rapport mensuel régénérable : une commande, un fichier markdown, une figure, aucun chiffre retapé.

`pops report` rejoue la décision du dernier mois observé (les mêmes 60 mois d'estimation, les mêmes
vues, les mêmes bornes) et écrit ce qu'un comité de placement attend : les positions contre leurs
bandes, les vues du mois avec leur confiance, l'inclinaison des rendements attendus, et la décision.
Relancer la commande un mois plus tard produit le rapport suivant, sans intervention.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pops.engine import DELTA, TAU, WINDOW, bl_month_weights
from pops.figures import fig_tilts
from pops.policy import Policy


def monthly_report(returns: pd.DataFrame, policy: Policy, equities: list[str],
                   out_dir: Path = Path("reports/monthly")) -> Path:
    """Écrit le rapport du dernier mois complet de `returns` et rend le chemin du fichier."""
    assets = list(policy.targets)
    month = returns.index[-1].strftime("%Y-%m")
    history = returns[assets].iloc[-WINDOW:]
    w, views, pi, mu = bl_month_weights(history, policy, equities, DELTA, TAU)

    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(exist_ok=True)
    fig_path = fig_dir / f"tilts_{month}.png"
    fig_tilts(pi, mu, assets, month, fig_path)

    targets = np.array([policy.targets[a] for a in assets])
    lines = [
        f"# Rapport de placement, {month}",
        "",
        f"Généré par `pops report` sur les prix arrêtés à fin {month} ; fenêtre d'estimation de "
        f"{WINDOW} mois ({history.index[0].strftime('%Y-%m')} à {history.index[-1].strftime('%Y-%m')}), "
        f"delta = {DELTA}, tau = {TAU}. Chaque chiffre de ce rapport est recalculé à la génération.",
        "",
        "## Les positions recommandées, contre la politique",
        "",
        "| Classe | Cible | Bande | Poids recommandé | Écart à la cible |",
        "|---|---:|---:|---:|---:|",
    ]
    for i, a in enumerate(assets):
        lines.append(f"| {a} | {100 * targets[i]:.0f} % | ± {100 * policy.band:.0f} pts "
                     f"| {100 * w[i]:.1f} % | {100 * (w[i] - targets[i]):+.1f} pts |")
    lines += [
        "",
        "Comment lire ce tableau : le poids recommandé vient de l'optimisation sous bandes, il ne peut "
        "pas sortir de « cible ± bande », donc l'écart à la cible mesure la force de la vue, plafonnée "
        f"à {100 * policy.band:.0f} points par construction.",
        "",
        "## Les vues du mois",
        "",
    ]
    if views:
        lines += ["| Vue | Favorise | Défavorise | Écart attendu (an) | Confiance |", "|---|---|---|---:|---:|"]
        for v in views:
            lines.append(f"| {v.name} | {v.long} | {v.short} | {100 * v.q:+.0f} % | {100 * v.confidence:.0f} % |")
    else:
        lines.append("Aucune vue ce mois-ci : les poids recommandés retombent sur les cibles de la politique.")
    lines += [
        "",
        f"![Inclinaison des rendements attendus](figures/tilts_{month}.png)",
        "",
        "Comment lire cette figure : chaque ligne est une classe d'actifs ; le point bleu est le rendement "
        "excédentaire annualisé qui justifierait les cibles de la politique (l'équilibre Pi), le point "
        "vermillon le rendement une fois les vues du mois mélangées à cet équilibre. L'écart entre les "
        "deux points est l'effet combiné des vues, dosé par leurs confiances via l'Omega d'Idzorek.",
        "",
    ]
    path = out_dir / f"{month}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
