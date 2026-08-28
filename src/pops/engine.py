"""Le moteur de bout en bout : chaque mois, estimer, incliner, borner, facturer les coûts.

La boucle walk-forward, la règle qui interdit de voir le futur : la décision du mois t n'utilise que les
mois 1 à t-1. Concrètement, pour chaque mois t après une fenêtre de chauffe de 60 mois :

1. la covariance annualisée s'estime sur les 60 mois qui précèdent t ;
2. l'équilibre est celui de la politique de placement : Pi = delta Sigma w_cible, les rendements qui
   justifieraient de détenir exactement les poids cibles (l'optimisation inverse de Black-Litterman) ;
3. les deux vues systématiques (momentum, renversement) se calculent sur le même historique, et la
   méthode d'Idzorek convertit leurs confiances en Omega ;
4. les rendements a posteriori donnent des poids optimaux sous DEUX contraintes : investi à 100 %, et
   chaque poids reste dans la bande de sa politique (cible plus ou moins 5 points), donc jamais de vente
   à découvert et jamais de pari qui violerait le document de politique ;
5. le portefeuille paie 10 points de base sur chaque dollar échangé, écart entre les nouveaux poids et
   les poids de la veille après dérive des prix.

Trois références subissent le même traitement sur la même période : la politique rééquilibrée par bandes
(le portefeuille « sans vue »), la parité de risque hiérarchique réestimée chaque mois, et l'équipondéré.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from pops import black_litterman as bl
from pops.brinson import multi_period
from pops.hrp import hrp_weights
from pops.policy import Policy, run_policy
from pops.views import View, build_views

WINDOW = 60
DELTA = 2.5
TAU = 0.025


@dataclass
class BacktestResult:
    returns: pd.DataFrame          # rendements mensuels nets des quatre portefeuilles
    weights_bl: pd.DataFrame       # poids Black-Litterman décidés en début de mois
    weights_hrp: pd.DataFrame
    views_log: pd.DataFrame        # une ligne par vue et par mois : nom, long, short
    turnover: pd.Series            # rotation mensuelle du portefeuille Black-Litterman
    policy: Policy
    returns_assets: pd.DataFrame | None = None   # rendements des classes sur la période hors échantillon

    def attribution(self) -> pd.DataFrame:
        """Attribution de Brinson du portefeuille Black-Litterman contre les cibles de la politique.

        Les deux portefeuilles détiennent les mêmes FNB, donc l'effet de sélection est nul par
        construction : tout l'écart actif est de l'allocation, et le tableau le montre classe par classe.
        """
        idx = self.weights_bl.index
        cols = list(self.policy.targets)
        bench_w = pd.DataFrame([self.policy.targets] * len(idx), index=idx)[cols]
        rets = self.returns_assets.loc[idx, cols]
        return multi_period(self.weights_bl[cols], bench_w, rets, rets)


def bounded_bl_weights(mu: np.ndarray, sigma_p: np.ndarray, delta: float,
                       targets: np.ndarray, band: float) -> np.ndarray:
    """Poids moyenne-variance sous bandes : max w'mu - delta/2 w'Sigma_p w, somme 1, cible ± bande."""
    def objective(w: np.ndarray) -> float:
        return float(-w @ mu + 0.5 * delta * w @ sigma_p @ w)

    def gradient(w: np.ndarray) -> np.ndarray:
        return -mu + delta * sigma_p @ w

    bounds = [(max(0.0, t - band), min(1.0, t + band)) for t in targets]
    res = minimize(objective, targets, jac=gradient, bounds=bounds, method="SLSQP",
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}])
    if not res.success:
        raise RuntimeError(f"optimisation sous bandes échouée : {res.message}")
    return res.x


def bl_month_weights(history: pd.DataFrame, policy: Policy, equities: list[str],
                     delta: float = DELTA, tau: float = TAU) -> tuple[np.ndarray, list[View], np.ndarray, np.ndarray]:
    """La décision d'un mois : poids bornés, vues retenues, et le couple (Pi, mu) pour le rapport."""
    assets = list(policy.targets)
    targets = np.array([policy.targets[a] for a in assets])
    sigma = history[assets].cov().values * 12.0
    pi = bl.equilibrium_returns(delta, sigma, targets)
    views = build_views(history, equities)
    if views:
        p = np.vstack([v.p_row(assets) for v in views])
        q = np.array([v.q for v in views])
        conf = np.array([v.confidence for v in views])
        omega = bl.idzorek_omega(sigma, tau, p, q, conf, pi, delta)
        mu = bl.posterior_returns(pi, sigma, tau, p, q, omega)
        sigma_p = sigma + bl.posterior_covariance(sigma, tau, p, omega)
    else:
        mu = pi
        sigma_p = sigma * (1.0 + tau)
    w = bounded_bl_weights(mu, sigma_p, delta, targets, policy.band)
    return w, views, pi, mu


def _drift(w: pd.Series, ret: pd.Series) -> pd.Series:
    gross = float((w * ret).sum())
    return w * (1.0 + ret) / (1.0 + gross)


def run_backtest(returns: pd.DataFrame, policy: Policy, equities: list[str],
                 window: int = WINDOW, delta: float = DELTA, tau: float = TAU) -> BacktestResult:
    """Le walk-forward complet ; l'achat initial n'est facturé à aucun portefeuille, déclaré."""
    assets = list(policy.targets)
    r = returns[assets]
    oos = r.index[window:]
    rows_w, rows_hrp, views_rows, rets_bl, rets_hrp, rets_ew, turn = [], [], [], [], [], [], []
    prev_bl = prev_hrp = prev_ew = None
    ew = pd.Series(1.0 / len(assets), index=assets)
    for t in range(window, len(r)):
        date = r.index[t]
        history = r.iloc[t - window:t]
        ret_t = r.iloc[t]

        w_arr, views, _, _ = bl_month_weights(history, policy, equities, delta, tau)
        w_bl = pd.Series(w_arr, index=assets)
        w_hrp = hrp_weights(history.cov())

        # premier mois sans coût, comme la politique à bandes qui démarre aux cibles : les quatre
        # portefeuilles partent investis, la comparaison ne facture que les rotations ultérieures
        for w_new, prev, out in ((w_bl, prev_bl, rets_bl), (w_hrp, prev_hrp, rets_hrp), (ew, prev_ew, rets_ew)):
            trade = float((w_new - prev).abs().sum()) if prev is not None else 0.0
            cost = policy.fee * trade
            out.append(float((w_new * ret_t).sum()) - cost)
            if w_new is w_bl:
                turn.append(trade)
        prev_bl, prev_hrp, prev_ew = _drift(w_bl, ret_t), _drift(w_hrp, ret_t), _drift(ew, ret_t)

        rows_w.append(w_bl)
        rows_hrp.append(w_hrp)
        for v in views:
            views_rows.append({"date": date, "vue": v.name, "favorise": v.long, "defavorise": v.short})

    policy_out = run_policy(r.loc[oos], policy)
    out = BacktestResult(
        returns=pd.DataFrame({
            "black_litterman": pd.Series(rets_bl, index=oos),
            "politique_bandes": policy_out.returns_net,
            "hrp": pd.Series(rets_hrp, index=oos),
            "equipondere": pd.Series(rets_ew, index=oos),
        }),
        weights_bl=pd.DataFrame(rows_w, index=oos),
        weights_hrp=pd.DataFrame(rows_hrp, index=oos),
        views_log=pd.DataFrame(views_rows),
        turnover=pd.Series(turn, index=oos, name="rotation"),
        policy=policy,
    )
    out.returns_assets = r.loc[oos]
    return out


def summary(result: BacktestResult) -> pd.DataFrame:
    """Le tableau de synthèse : rendement annualisé calendaire, volatilité, rendement par unité de
    volatilité (pas un ratio de Sharpe : le taux sans risque n'est pas soustrait), pire creux, rotation."""
    rows = {}
    years = len(result.returns) / 12.0    # 226 rendements mensuels composés = 226/12 années d'accumulation
    for name, series in result.returns.items():
        wealth = (1.0 + series).cumprod()
        cagr = float(wealth.iloc[-1] ** (1.0 / years) - 1.0)
        vol = float(series.std() * np.sqrt(12.0))
        drawdown = float((wealth / wealth.cummax() - 1.0).min())
        rows[name] = {
            "rendement_annualise": cagr,
            "volatilite_annualisee": vol,
            "rendement_sur_volatilite": cagr / vol if vol > 0 else np.nan,
            "pire_creux": drawdown,
        }
    table = pd.DataFrame(rows).T
    table.loc["black_litterman", "rotation_annuelle"] = float(result.turnover.iloc[1:].mean() * 12.0)
    table.loc["politique_bandes", "rotation_annuelle"] = float(
        run_policy(result.returns_assets, result.policy).turnover_total / years)
    return table
