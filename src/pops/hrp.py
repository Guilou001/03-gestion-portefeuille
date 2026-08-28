"""Parité de risque hiérarchique (López de Prado, 2016), la construction en trois étapes du papier.

L'idée : au lieu d'inverser une covariance bruitée, on regroupe les actifs par ressemblance (arbre de
corrélations), on les réordonne le long de l'arbre, puis on répartit le budget de risque de haut en bas par
bissection, chaque moitié recevant l'inverse de sa variance. Aucune inversion de matrice : la méthode reste
définie même quand la covariance est singulière.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import squareform


def correlation_distance(corr: pd.DataFrame) -> np.ndarray:
    """Distance de corrélation du papier : d = racine((1 - rho) / 2), dans [0, 1]."""
    return np.sqrt(np.clip((1.0 - corr.values) / 2.0, 0.0, None))


def quasi_diagonal_order(link: np.ndarray, n: int) -> list[int]:
    """Ordre des feuilles de l'arbre (single linkage) : les actifs semblables deviennent voisins."""
    tree = to_tree(link, rd=False)
    return tree.pre_order()


def _cluster_variance(cov: np.ndarray, idx: list[int]) -> float:
    sub = cov[np.ix_(idx, idx)]
    ivp = 1.0 / np.diag(sub)
    w = ivp / ivp.sum()
    return float(w @ sub @ w)


def hrp_weights(cov: pd.DataFrame) -> pd.Series:
    """Poids HRP : arbre single-linkage sur la distance de corrélation, puis bissection récursive."""
    corr = cov.div(np.sqrt(np.outer(np.diag(cov), np.diag(cov))), axis=None)
    corr = pd.DataFrame(corr.values, index=cov.index, columns=cov.columns)
    dist = correlation_distance(corr)
    link = linkage(squareform(dist, checks=False), method="single")
    order = quasi_diagonal_order(link, len(cov))

    weights = pd.Series(1.0, index=[cov.index[i] for i in order])
    clusters = [[cov.index.get_loc(t) for t in weights.index]]
    cov_v = cov.values
    while clusters:
        clusters = [half for c in clusters if len(c) > 1
                    for half in (c[: len(c) // 2], c[len(c) // 2:])]
        for left, right in zip(clusters[::2], clusters[1::2], strict=False):
            var_left = _cluster_variance(cov_v, left)
            var_right = _cluster_variance(cov_v, right)
            alpha = 1.0 - var_left / (var_left + var_right)
            weights.iloc[[weights.index.get_loc(cov.index[i]) for i in left]] *= alpha
            weights.iloc[[weights.index.get_loc(cov.index[i]) for i in right]] *= 1.0 - alpha
    return weights.reindex(cov.index)
