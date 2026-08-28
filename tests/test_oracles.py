"""Le module Black-Litterman contre les chiffres imprimés des deux papiers fondateurs.

Oracles extraits des PDF dans ``refs/oracles/`` (deux extractions recoupées, artefacts documentés dans
``idzorek_parametres.md``) : He et Litterman (1999) pour l'équilibre et la convention Omega/tau, Idzorek
(2005) pour la chaîne complète (équilibre, a posteriori, poids, confiances implicites) sur 8 classes
d'actifs. Tolérances : les tables sont imprimées à 2 décimales de pourcent, on teste à 0,01 point près
(0,05 pour les recompositions qui cumulent plusieurs arrondis d'impression).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pops import black_litterman as bl

ORACLES = Path(__file__).parents[1] / "refs" / "oracles"
TAU = 0.025          # Idzorek, page 15


@pytest.fixture(scope="module")
def idzorek():
    t1 = pd.read_csv(ORACLES / "idzorek_table1.csv")
    t2 = pd.read_csv(ORACLES / "idzorek_table2.csv")
    t5 = pd.read_csv(ORACLES / "idzorek_table5.csv", index_col=0)
    t6 = pd.read_csv(ORACLES / "idzorek_table6.csv")
    t7 = pd.read_csv(ORACLES / "idzorek_table7.csv")
    assets = list(t5.index)                 # les 8 classes, dans l'ordre de la covariance
    t1 = t1.set_index("asset_class").reindex(assets)
    t2 = t2.set_index("asset_class").reindex(assets)
    t6 = t6.set_index("asset_class").reindex(assets)
    t7 = t7.set_index("asset_class").reindex(assets)
    sigma = t5.values.astype(float)
    if sigma.max() > 1:                     # imprimée en pourcent² le cas échéant
        sigma = sigma / 1e4
    w_mkt = t2["market_capitalization_weight_pct"].values / 100
    pi_printed = t1["implied_equilibrium_pi_pct"].values / 100
    lam = 0.03 / float(w_mkt @ sigma @ w_mkt)          # prime de 3 % (note de la Table 1)
    p = np.array([
        [0, 0, 0, 0, 0, 0, 1, 0],
        [-1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0.9, -0.9, 0.1, -0.1, 0, 0],           # vue 3 pondérée par capitalisation (éq. 7)
    ], dtype=float)
    q = np.array([0.0525, 0.0025, 0.02])
    return sigma, w_mkt, pi_printed, lam, p, q, t6, t7


def test_hl_equilibrium_returns_match_table1():
    t1 = pd.read_csv(ORACLES / "hl_table1.csv")
    corr = pd.read_csv(ORACLES / "hl_table2_correlations.csv", index_col=0).values.astype(float)
    sig = t1["sigma_volatility_pct"].values / 100
    sigma = corr * np.outer(sig, sig)
    w_eq = t1["w_eq_market_cap_weight_pct"].values / 100
    pi = bl.equilibrium_returns(2.5, sigma, w_eq)
    printed = t1["pi_equilibrium_expected_return_pct"].values / 100
    assert np.abs(pi - printed).max() < 5e-4          # ±0,05 point : arrondis d'impression cumulés


def test_idzorek_lambda_matches_printed_value(idzorek):
    _, _, _, lam, *_ = idzorek
    assert lam == pytest.approx(3.07, abs=0.01)       # le papier imprime lambda ~ 3,07


def test_idzorek_equilibrium_matches_table1(idzorek):
    sigma, w_mkt, pi_printed, lam, *_ = idzorek
    pi = bl.equilibrium_returns(lam, sigma, w_mkt)
    assert np.abs(pi - pi_printed).max() < 1e-4       # ±0,01 point


def test_idzorek_omega_diagonal_matches_equation8(idzorek):
    sigma, _, _, _, p, _, _, _ = idzorek
    omega = bl.omega_proportional(sigma, TAU, p)
    assert np.allclose(np.diag(omega), [0.000709, 0.000141, 0.000866], atol=5e-7)


def test_idzorek_posterior_returns_match_table6(idzorek):
    sigma, _, pi_printed, lam, p, q, t6, _ = idzorek
    pi = bl.equilibrium_returns(lam, sigma, idzorek[1])
    mu = bl.posterior_returns(pi, sigma, TAU, p, q, bl.omega_proportional(sigma, TAU, p))
    printed = t6["new_combined_return_er_pct"].values / 100
    assert np.abs(mu - printed).max() < 1e-4          # exact aux 2 décimales imprimées


def test_idzorek_new_weights_match_table6(idzorek):
    sigma, _, _, lam, p, q, t6, _ = idzorek
    pi = bl.equilibrium_returns(lam, sigma, idzorek[1])
    mu = bl.posterior_returns(pi, sigma, TAU, p, q, bl.omega_proportional(sigma, TAU, p))
    w = np.linalg.solve(lam * sigma, mu)              # convention d'Idzorek : Sigma, sans le terme M^-1
    printed = t6["new_weight_pct"].values / 100
    assert np.abs(w - printed).max() < 2e-4           # ±0,02 point (le mémo documente 29,89 vs 29,88)


def test_idzorek_full_confidence_weights_match_table7(idzorek):
    sigma, w_mkt, _, lam, p, q, _, t7 = idzorek
    pi = bl.equilibrium_returns(lam, sigma, w_mkt)
    mu_100 = bl.posterior_returns(pi, sigma, TAU, p, q, np.eye(3) * 1e-12)
    w_100 = np.linalg.solve(lam * sigma, mu_100)
    printed = t7["new_weight_100pct_confidence_pct"].values / 100
    assert np.abs(w_100 - printed).max() < 2e-4


def test_idzorek_implied_confidences_match_table7(idzorek):
    sigma, w_mkt, _, lam, p, q, t6, t7 = idzorek
    pi = bl.equilibrium_returns(lam, sigma, w_mkt)
    mu = bl.posterior_returns(pi, sigma, TAU, p, q, bl.omega_proportional(sigma, TAU, p))
    w = np.linalg.solve(lam * sigma, mu)
    mu_100 = bl.posterior_returns(pi, sigma, TAU, p, q, np.eye(3) * 1e-12)
    w_100 = np.linalg.solve(lam * sigma, mu_100)
    implied = (w - w_mkt) / (w_100 - w_mkt)
    printed = t7["implied_confidence_level_pct"].values / 100
    ok = ~np.isnan(printed)
    assert np.abs(implied[ok] - printed[ok]).max() < 2e-3   # ±0,2 point (32,93 vs 32,94 documenté)
