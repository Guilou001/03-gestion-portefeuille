"""Style matplotlib commun : une figure se lit sans sa légende externe et sans zoomer.

Palette d'Okabe et Ito (2008), huit couleurs distinguables par les lecteurs daltoniens ; polices de
11 points minimum ; grille discrète ; pas de cadre au-dessus ni à droite ; 200 points par pouce.
"""

from __future__ import annotations

from gvf.style import OKABE_ITO, appliquer, formateur  # noqa: F401

# La palette et les réglages viennent de la couche partagée du portefeuille : les mêmes
# couleurs et la même virgule décimale dans tous les dépôts, corrigées à un seul endroit.


def use_style():
    """Les réglages communs, puis le formateur d'axe en français."""
    appliquer()
    return formateur()
