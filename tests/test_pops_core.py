"""Propriétés algébriques des quatre modules (sans données externes) ; les oracles papier sont testés à part."""

import numpy as np
import pandas as pd
import pytest

from pops import black_litterman as bl
from pops.brinson import multi_period, single_period
from pops.hrp import hrp_weights
from pops.policy import Policy, run_policy

rng = np.random.default_rng(11)


@pytest.fixture()
def market():
    n = 5
    a = rng.normal(size=(n, n))
    sigma = a @ a.T / 100 + np.eye(n) * 0.01
    w_eq = np.array([0.3, 0.25, 0.2, 0.15, 0.1])
    return sigma, w_eq


# ------------------------------------------------------------------ Black-Litterman
def test_reverse_optimization_roundtrip(market):
    sigma, w_eq = market
    pi = bl.equilibrium_returns(2.5, sigma, w_eq)
    w_back = np.linalg.solve(2.5 * sigma, pi)
    assert np.allclose(w_back, w_eq)


def test_no_view_weights_are_w_eq_over_one_plus_tau(market):
    sigma, w_eq = market
    pi = bl.equilibrium_returns(2.5, sigma, w_eq)
    w = bl.unconstrained_weights(pi, sigma, tau=0.05, delta=2.5)
    assert np.allclose(w, w_eq / 1.05)         # la note 5 de He-Litterman, testée telle quelle


def test_certain_view_is_honoured(market):
    sigma, w_eq = market
    pi = bl.equilibrium_returns(2.5, sigma, w_eq)
    p = np.zeros((1, 5))
    p[0, 0] = 1.0
    q = np.array([0.07])
    mu = bl.posterior_returns(pi, sigma, 0.05, p, q, np.array([[1e-14]]))
    assert mu[0] == pytest.approx(0.07, abs=1e-6)   # vue certaine sur l'actif 1 : imposée exactement


def test_zero_confidence_leaves_equilibrium(market):
    sigma, w_eq = market
    pi = bl.equilibrium_returns(2.5, sigma, w_eq)
    p = np.array([[1.0, -1.0, 0.0, 0.0, 0.0]])
    mu = bl.posterior_returns(pi, sigma, 0.05, p, np.array([0.10]), np.array([[1e9]]))
    assert np.allclose(mu, pi, atol=1e-6)           # confiance nulle (omega immense) : rien ne bouge


def test_idzorek_omega_interpolates_tilt(market):
    sigma, w_eq = market
    delta, tau = 2.5, 0.05
    pi = bl.equilibrium_returns(delta, sigma, w_eq)
    p = np.array([[0.0, 1.0, 0.0, -1.0, 0.0]])
    q = np.array([0.04])
    omega = bl.idzorek_omega(sigma, tau, p, q, np.array([0.5]), pi, delta)
    mu_half = bl.posterior_returns(pi, sigma, tau, p, q, omega)
    w_half = np.linalg.solve(delta * sigma, mu_half)
    mu_full = bl.posterior_returns(pi, sigma, tau, p, q, np.array([[1e-14]]))
    w_full = np.linalg.solve(delta * sigma, mu_full)
    tilt_ratio = (w_half - w_eq)[1] / (w_full - w_eq)[1]
    assert tilt_ratio == pytest.approx(0.5, abs=0.02)   # 50 % de confiance = la moitié de l'inclinaison


# ------------------------------------------------------------------ HRP
def test_hrp_weights_positive_and_sum_to_one(market):
    sigma, _ = market
    cov = pd.DataFrame(sigma, index=list("ABCDE"), columns=list("ABCDE"))
    w = hrp_weights(cov)
    assert w.sum() == pytest.approx(1.0)
    assert (w > 0).all()


def test_hrp_prefers_low_variance_assets():
    cov = pd.DataFrame(np.diag([0.01, 0.04, 0.09]), index=list("ABC"), columns=list("ABC"))
    w = hrp_weights(cov)
    assert w["A"] > w["B"] > w["C"]


# ------------------------------------------------------------------ Brinson
def test_brinson_effects_sum_to_active_return():
    idx = ["actions", "obligations", "encaisse"]
    w = pd.Series([0.65, 0.30, 0.05], index=idx)
    b = pd.Series([0.60, 0.35, 0.05], index=idx)
    r = pd.Series([0.04, 0.01, 0.002], index=idx)
    rb = pd.Series([0.035, 0.012, 0.002], index=idx)
    out = single_period(w, b, r, rb)
    active = float((w * r).sum() - (b * rb).sum())
    assert out.loc["TOTAL", "total"] == pytest.approx(active, abs=1e-12)


def test_brinson_multi_period_links_to_geometric_gap():
    idx = ["a", "b"]
    dates = pd.date_range("2024-01-31", periods=3, freq="ME")
    w = pd.DataFrame([[0.7, 0.3]] * 3, index=dates, columns=idx)
    b = pd.DataFrame([[0.6, 0.4]] * 3, index=dates, columns=idx)
    r = pd.DataFrame(rng.normal(0.01, 0.02, (3, 2)), index=dates, columns=idx)
    rb = r - 0.001
    out = multi_period(w, b, r, rb)
    rp = float((w * r).sum(axis=1).add(1).prod() - 1)
    rbench = float((b * rb).sum(axis=1).add(1).prod() - 1)
    assert out.loc["TOTAL", "total"] == pytest.approx(rp - rbench, rel=1e-6)


# ------------------------------------------------------------------ politique de placement
def test_policy_requires_unit_targets():
    with pytest.raises(ValueError):
        Policy(targets={"a": 0.5, "b": 0.4})


def test_policy_holds_inside_bands_and_rebalances_outside():
    dates = pd.date_range("2024-01-31", periods=4, freq="ME")
    r = pd.DataFrame({"actions": [0.02, 0.02, 0.25, 0.0], "obligations": [0.0, 0.0, 0.0, 0.0]}, index=dates)
    pol = Policy(targets={"actions": 0.6, "obligations": 0.4}, band=0.05, fee=0.001)
    out = run_policy(r, pol)
    assert out.n_rebalances == 1                      # seul le choc de 25 % fait sortir de la bande
    assert out.events == [dates[2]]
    w_after = out.weights.loc[dates[2]]
    assert abs(w_after["actions"] - 0.6) <= 0.05 + 1e-9   # ramené AU BORD de la bande, pas à la cible
    assert w_after.sum() == pytest.approx(1.0)
    assert out.total_costs == pytest.approx(0.001 * out.turnover_total)
