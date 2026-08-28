"""Vues systématiques : deux règles mécaniques produisent chaque mois les vues du modèle Black-Litterman.

Une vue est une opinion chiffrée sur un écart de rendement entre deux classes, avec une confiance en
pourcent que la méthode d'Idzorek (2005) convertit en incertitude Omega. Ici, aucune opinion humaine :
les deux vues sortent d'un calcul sur les prix passés, toujours arrêté au dernier mois observé, jamais
sur le mois qu'on s'apprête à vivre.

1. Momentum 12-1 (Jegadeesh et Titman, 1993) : parmi les trois poches d'actions, celle qui a le mieux
   performé sur les douze mois passés, dernier mois exclu, bat la pire. Q = +2 % par an, confiance 50 %.
2. Renversement de long terme (De Bondt et Thaler, 1985), le proxy de valorisation fondé sur les prix :
   la poche d'actions la plus faible sur cinq ans bat la plus forte. Q = +1 % par an, confiance 25 %.

Les Q et confiances sont des choix déclarés, pas des estimations : ils fixent l'ampleur de l'inclinaison,
et les bandes de la politique la bornent de toute façon.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MOMENTUM_Q, MOMENTUM_CONF = 0.02, 0.50
REVERSAL_Q, REVERSAL_CONF = 0.01, 0.25


@dataclass(frozen=True)
class View:
    name: str            # « momentum » ou « renversement »
    long: str            # la classe que la vue favorise
    short: str           # la classe que la vue défavorise
    q: float             # écart de rendement annualisé attendu
    confidence: float    # confiance Idzorek, dans (0, 1)

    def p_row(self, assets: list[str]) -> np.ndarray:
        row = np.zeros(len(assets))
        row[assets.index(self.long)] = 1.0
        row[assets.index(self.short)] = -1.0
        return row


def momentum_view(history: pd.DataFrame, equities: list[str]) -> View | None:
    """Vue momentum 12-1 : cumul des mois t-13 à t-2, le dernier mois observé est exclu."""
    if len(history) < 13:
        return None
    window = history[equities].iloc[-13:-1]
    cumul = (1.0 + window).prod() - 1.0
    best, worst = cumul.idxmax(), cumul.idxmin()
    if best == worst:
        return None
    return View("momentum", best, worst, MOMENTUM_Q, MOMENTUM_CONF)


def reversal_view(history: pd.DataFrame, equities: list[str]) -> View | None:
    """Vue de renversement : cumul des soixante derniers mois, la plus faible est favorisée."""
    if len(history) < 60:
        return None
    cumul = (1.0 + history[equities].iloc[-60:]).prod() - 1.0
    weakest, strongest = cumul.idxmin(), cumul.idxmax()
    if weakest == strongest:
        return None
    return View("renversement", weakest, strongest, REVERSAL_Q, REVERSAL_CONF)


def build_views(history: pd.DataFrame, equities: list[str]) -> list[View]:
    """Les vues du mois, calculées sur l'historique arrêté au dernier mois observé."""
    return [v for v in (momentum_view(history, equities), reversal_view(history, equities)) if v is not None]
