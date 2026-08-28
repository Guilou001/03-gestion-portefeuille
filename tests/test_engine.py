"""Le moteur sur données synthétiques, sans réseau : vues, absence de fuite, bandes, rapport."""

import numpy as np
import pandas as pd
import pytest

from pops.engine import run_backtest
from pops.policy import Policy
from pops.report import monthly_report
from pops.views import build_views, momentum_view, reversal_view

TARGETS = {"XIU.TO": 0.25, "XSP.TO": 0.20, "XIN.TO": 0.15, "XRE.TO": 0.05, "XBB.TO": 0.25, "XSB.TO": 0.10}
EQUITIES = ["XIU.TO", "XSP.TO", "XIN.TO"]


def synthetic_returns(n: int = 90, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2015-01-31", periods=n, freq="ME")
    return pd.DataFrame(rng.normal(0.005, 0.03, (n, len(TARGETS))), index=idx, columns=list(TARGETS))


def test_momentum_view_favours_the_best_trailing_equity():
    r = synthetic_returns(70)
    r.loc[r.index[-13:-1], "XSP.TO"] = 0.05     # douze mois forts, dernier mois exclu du calcul
    r.loc[r.index[-13:-1], "XIN.TO"] = -0.05
    view = momentum_view(r, EQUITIES)
    assert view.long == "XSP.TO" and view.short == "XIN.TO"


def test_momentum_ignores_the_most_recent_month():
    r = synthetic_returns(70)
    r.loc[r.index[-13:-1], "XSP.TO"] = 0.05
    r.loc[r.index[-13:-1], "XIN.TO"] = -0.05
    before = momentum_view(r, EQUITIES)
    r.loc[r.index[-1], "XSP.TO"] = -0.60        # un krach du dernier mois ne change pas la vue 12-1
    after = momentum_view(r, EQUITIES)
    assert (before.long, before.short) == (after.long, after.short)


def test_reversal_view_favours_the_five_year_loser():
    r = synthetic_returns(70)
    r.loc[r.index[-60:], "XIU.TO"] = -0.01
    r.loc[r.index[-60:], "XSP.TO"] = 0.02
    view = reversal_view(r, EQUITIES)
    assert view.long == "XIU.TO" and view.short == "XSP.TO"


def test_short_history_yields_no_views():
    r = synthetic_returns(10)
    assert build_views(r, EQUITIES) == []


@pytest.fixture(scope="module")
def backtest():
    return run_backtest(synthetic_returns(90), Policy(targets=TARGETS), EQUITIES)


def test_weights_stay_inside_policy_bands(backtest):
    policy = backtest.policy
    for asset in TARGETS:
        w = backtest.weights_bl[asset]
        assert (w >= policy.targets[asset] - policy.band - 1e-6).all()
        assert (w <= policy.targets[asset] + policy.band + 1e-6).all()
    assert np.allclose(backtest.weights_bl.sum(axis=1), 1.0, atol=1e-6)


def test_last_month_return_does_not_change_any_decision(backtest):
    shocked = synthetic_returns(90)
    shocked.iloc[-1] = -0.30                     # le futur bouge, les décisions passées ne doivent pas
    again = run_backtest(shocked, Policy(targets=TARGETS), EQUITIES)
    pd.testing.assert_frame_equal(backtest.weights_bl, again.weights_bl)


def test_attribution_is_pure_allocation(backtest):
    attr = backtest.attribution()
    assert abs(attr.loc["TOTAL", "selection"]) < 1e-12
    assert abs(attr.loc["TOTAL", "interaction"]) < 1e-12
    active = (1 + (backtest.weights_bl * backtest.returns_assets).sum(axis=1)).prod() \
        - (1 + (backtest.returns_assets @ pd.Series(TARGETS))).prod()
    assert attr.loc["TOTAL", "total"] == pytest.approx(active, abs=1e-10)


def test_monthly_report_is_written(tmp_path):
    path = monthly_report(synthetic_returns(70), Policy(targets=TARGETS), EQUITIES, out_dir=tmp_path)
    text = path.read_text(encoding="utf-8")
    assert path.name.endswith(".md") and "Rapport de placement" in text and "Comment lire" in text
