"""Attribution de performance de Brinson-Fachler : d'où vient l'écart au portefeuille de politique ?

Pour chaque classe d'actifs i, avec les poids du portefeuille w_i et de la politique b_i, les rendements
r_i (portefeuille) et rb_i (référence), et R_b le rendement total de la référence :

- allocation_i = (w_i - b_i) (rb_i - R_b) : a-t-on surpondéré les classes qui ont battu la référence ?
- sélection_i  = b_i (r_i - rb_i) : a-t-on fait mieux que l'indice À L'INTÉRIEUR de la classe ?
- interaction_i = (w_i - b_i) (r_i - rb_i) : le croisement des deux effets.

La somme des trois sur toutes les classes égale exactement l'écart de rendement total, ce qu'un test
vérifie algébriquement. Le chaînage multi-périodes est géométrique par le facteur de Cariño, qui répartit
l'écart composé au prorata des écarts arithmétiques (documenté, testé sur la propriété de somme).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def single_period(weights: pd.Series, bench_weights: pd.Series, returns: pd.Series,
                  bench_returns: pd.Series) -> pd.DataFrame:
    """Attribution de Brinson-Fachler d'une période, une ligne par classe plus la ligne totale."""
    idx = weights.index
    r_b = float((bench_weights * bench_returns).sum())
    allocation = (weights - bench_weights) * (bench_returns - r_b)
    selection = bench_weights * (returns - bench_returns)
    interaction = (weights - bench_weights) * (returns - bench_returns)
    out = pd.DataFrame({"allocation": allocation, "selection": selection, "interaction": interaction}, index=idx)
    out["total"] = out.sum(axis=1)
    total = out.sum(axis=0).to_frame().T
    total.index = ["TOTAL"]
    return pd.concat([out, total])


def multi_period(weights: pd.DataFrame, bench_weights: pd.DataFrame, returns: pd.DataFrame,
                 bench_returns: pd.DataFrame) -> pd.DataFrame:
    """Chaînage de Cariño : les effets arithmétiques mensuels sont mis à l'échelle pour que leur somme
    égale l'écart GÉOMÉTRIQUE cumulé (portefeuille moins référence, composés)."""
    period_effects = []
    rp_total, rb_total = 1.0, 1.0
    for t in weights.index:
        eff = single_period(weights.loc[t], bench_weights.loc[t], returns.loc[t], bench_returns.loc[t])
        rp = float((weights.loc[t] * returns.loc[t]).sum())
        rb = float((bench_weights.loc[t] * bench_returns.loc[t]).sum())
        k_t = (np.log1p(rp) - np.log1p(rb)) / (rp - rb) if rp != rb else 1.0 / (1.0 + rp)
        period_effects.append(eff.drop(index="TOTAL") * k_t)
        rp_total *= 1.0 + rp
        rb_total *= 1.0 + rb
    summed = sum(period_effects)[["allocation", "selection", "interaction"]]   # sans la colonne total déjà sommée
    k_global = (rp_total - rb_total) / (np.log(rp_total) - np.log(rb_total)) \
        if rp_total != rb_total else rp_total
    out = summed * k_global
    out["total"] = out.sum(axis=1)
    total = out.sum(axis=0).to_frame().T
    total.index = ["TOTAL"]
    return pd.concat([out, total])
