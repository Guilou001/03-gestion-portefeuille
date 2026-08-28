"""Politique de placement (IPS) : cibles, bandes de tolérance, rééquilibrage au bord, coûts.

Une politique de placement, le document qui fixe les poids cibles par classe d'actifs et les bandes de
tolérance autour, se met en œuvre ici en trois règles mécaniques :

1. les poids dérivent avec les rendements entre deux dates de contrôle ;
2. tant que chaque poids reste dans sa bande [cible - bande, cible + bande], on ne touche à rien
   (chaque transaction coûte, et l'hystérésis évite d'osciller autour de la cible) ;
3. quand une classe sort de sa bande, on ramène TOUTES les classes au bord de leur bande du côté de la
   cible (« trade to the edge »), pas à la cible elle-même : c'est la variante la moins coûteuse mesurée
   par la littérature des bandes de non-échange ; le résidu de budget est ensuite réparti au prorata de
   la marge restante des bandes, de sorte que le portefeuille rééquilibré respecte toutes les bandes.

Les coûts sont facturés en points de base sur la valeur échangée.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class Policy:
    targets: dict[str, float]                  # cibles par classe, somme 1
    band: float = 0.05                         # demi-largeur commune des bandes (5 points de poids)
    fee: float = 0.001                         # 10 pb par unité échangée

    def __post_init__(self) -> None:
        total = sum(self.targets.values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"les cibles doivent sommer à 1 (reçu {total})")


@dataclass
class RebalanceOutcome:
    returns_net: pd.Series
    weights: pd.DataFrame
    trades: pd.DataFrame
    n_rebalances: int = 0
    total_costs: float = 0.0
    turnover_total: float = 0.0
    events: list[pd.Timestamp] = field(default_factory=list)


def _project_into_bands(w: pd.Series, policy: Policy) -> pd.Series:
    """Ramène les poids dérivés au point le plus proche de l'ensemble « chaque poids dans sa bande,
    somme à 1 » : d'abord chaque poids au bord de sa bande, puis le résidu de budget réparti au
    prorata de la marge restante des autres bandes (une simple renormalisation ressortirait des
    bandes, l'ensemble est non vide puisque les cibles somment à 1)."""
    lo = pd.Series({c: max(0.0, t - policy.band) for c, t in policy.targets.items()})
    hi = pd.Series({c: min(1.0, t + policy.band) for c, t in policy.targets.items()})
    new_w = w.clip(lower=lo, upper=hi)
    for _ in range(len(w) + 1):
        residual = 1.0 - float(new_w.sum())
        if abs(residual) < 1e-12:
            break
        room = (hi - new_w) if residual > 0 else (new_w - lo)
        total_room = float(room.sum())
        if total_room <= 0:
            raise RuntimeError("bandes infaisables : aucune marge pour absorber le résidu de budget")
        new_w = (new_w + residual * room / total_room).clip(lower=lo, upper=hi)
    return new_w


def run_policy(asset_returns: pd.DataFrame, policy: Policy) -> RebalanceOutcome:
    """Applique la politique sur des rendements périodiques (colonnes = classes de la politique)."""
    cols = list(policy.targets)
    r = asset_returns[cols]
    w = pd.Series(policy.targets, dtype=float)
    rows_w, rows_trades, rets = [], [], []
    n_rebal, costs_total, turnover_total, events = 0, 0.0, 0.0, []
    for date, ret in r.iterrows():
        gross = float((w * ret).sum())
        w = w * (1 + ret) / (1 + gross)                      # dérive
        trade = pd.Series(0.0, index=w.index)
        # tolérance numérique : un poids ramené AU bord (écart exactement égal à la bande) reste en place
        out_of_band = (w - pd.Series(policy.targets)).abs() > policy.band + 1e-9
        if out_of_band.any():
            new_w = _project_into_bands(w, policy)
            trade = new_w - w
            w = new_w
            n_rebal += 1
            events.append(date)
        cost = policy.fee * float(trade.abs().sum())
        costs_total += cost
        turnover_total += float(trade.abs().sum())
        rets.append(gross - cost)
        rows_w.append(w.copy())
        rows_trades.append(trade)
    return RebalanceOutcome(
        returns_net=pd.Series(rets, index=r.index, name="net"),
        weights=pd.DataFrame(rows_w, index=r.index),
        trades=pd.DataFrame(rows_trades, index=r.index),
        n_rebalances=n_rebal, total_costs=costs_total, turnover_total=turnover_total, events=events,
    )
