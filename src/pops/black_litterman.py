"""Black-Litterman, dans les conventions de He et Litterman (1999) et d'Idzorek (2005).

Le modèle répond à un problème concret : l'optimisation moyenne-variance classique explose dès qu'on lui
donne des prévisions brutes. Black-Litterman part des rendements d'équilibre (ceux qui justifieraient les
poids de capitalisation observés), puis les incline vers les vues de l'investisseur proportionnellement à la
confiance qu'il leur accorde. Trois pièges de conventions, tous documentés dans les tests contre les tables
des deux papiers : tau multiplie la covariance de l'a priori ; Omega est la covariance du bruit des vues
(les deux papiers la construisent différemment) ; les poids non contraints somment à w_eq + une combinaison
des vues, PAS à 1 (He-Litterman, note 5 : le portefeuille non contraint contient 1/(1+tau) de risqué).
"""

from __future__ import annotations

import numpy as np


def equilibrium_returns(delta: float, sigma: np.ndarray, w_eq: np.ndarray) -> np.ndarray:
    """Optimisation inverse : les rendements excédentaires qui rendent w_eq optimal, Pi = delta Sigma w."""
    return delta * sigma @ w_eq


def posterior_returns(pi: np.ndarray, sigma: np.ndarray, tau: float, p: np.ndarray, q: np.ndarray,
                      omega: np.ndarray) -> np.ndarray:
    """Rendements a posteriori : moyenne bayésienne de l'équilibre et des vues (He-Litterman, éq. 8).

    ``p`` (k, n) sélectionne les actifs de chaque vue, ``q`` (k,) est le rendement vu, ``omega`` (k, k)
    la covariance du bruit des vues. Formule stable : Pi + tau Sigma P' (P tau Sigma P' + Omega)^-1 (Q - P Pi).
    """
    p = np.atleast_2d(p)
    q = np.atleast_1d(q)
    ts_pt = tau * sigma @ p.T
    middle = np.linalg.solve(p @ ts_pt + omega, q - p @ pi)
    return pi + ts_pt @ middle


def posterior_covariance(sigma: np.ndarray, tau: float, p: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """Covariance de l'estimation a posteriori M^-1 (He-Litterman, éq. 9) ; la covariance des rendements
    pour l'optimisation est Sigma + M^-1 (leur convention Sigma_p barre)."""
    p = np.atleast_2d(p)
    ts = tau * sigma
    m_inv = ts - ts @ p.T @ np.linalg.solve(p @ ts @ p.T + omega, p @ ts)
    return m_inv


def unconstrained_weights(mu: np.ndarray, sigma: np.ndarray, tau: float, p: np.ndarray | None = None,
                          omega: np.ndarray | None = None, delta: float = 2.5) -> np.ndarray:
    """Poids optimaux non contraints w* = (delta Sigma_p)^-1 mu, avec Sigma_p = Sigma + M^-1.

    Sans vue, w* = w_eq/(1+tau) : la fraction 1/(1+tau) est la conséquence documentée de l'incertitude
    d'estimation (He-Litterman, note de bas de page 5), pas un bug de normalisation.
    """
    if p is None:
        sigma_p = sigma * (1 + tau)
    else:
        sigma_p = sigma + posterior_covariance(sigma, tau, p, omega)
    return np.linalg.solve(delta * sigma_p, mu)


def omega_proportional(sigma: np.ndarray, tau: float, p: np.ndarray) -> np.ndarray:
    """Omega « proportionnel » de He-Litterman : diagonale de P tau Sigma P' (vues calibrées sur l'a priori)."""
    p = np.atleast_2d(p)
    return np.diag(np.diag(p @ (tau * sigma) @ p.T))


def idzorek_omega(sigma: np.ndarray, tau: float, p: np.ndarray, q: np.ndarray,
                  confidences: np.ndarray, pi: np.ndarray, delta: float) -> np.ndarray:
    """Omega calibré sur des confiances en pourcent (Idzorek, 2005, la méthode du « tilt »).

    Pour chaque vue k prise seule : à confiance 100 %, les poids bougent de w_100 - w_eq ; à confiance C_k,
    Idzorek cherche l'omega_k diagonal tel que l'inclinaison observée vaille C_k fois cette inclinaison
    maximale. Résolution numérique par balayage fin, comme dans le papier (minimisation de l'écart de poids).
    """
    p = np.atleast_2d(p)
    q = np.atleast_1d(q)
    confidences = np.atleast_1d(confidences)
    w_eq = np.linalg.solve(delta * sigma, pi)
    omegas = np.zeros(len(q))
    for k in range(len(q)):
        pk = p[[k]]
        qk = q[[k]]
        # inclinaison à confiance totale : Omega -> 0 (vue certaine)
        mu_100 = posterior_returns(pi, sigma, tau, pk, qk, np.array([[1e-12]]))
        w_100 = np.linalg.solve(delta * sigma, mu_100)   # convention d'Idzorek : Sigma, pas Sigma + M^-1
        tilt_target = w_eq + confidences[k] * (w_100 - w_eq)

        def weight_gap(log_omega: float, pk=pk, qk=qk, target=tilt_target) -> float:
            om = np.array([[np.exp(log_omega)]])
            mu_k = posterior_returns(pi, sigma, tau, pk, qk, om)
            w_k = np.linalg.solve(delta * sigma, mu_k)
            return float(np.sum((w_k - target) ** 2))

        from scipy.optimize import minimize_scalar

        base = (pk @ (tau * sigma) @ pk.T).item()
        res = minimize_scalar(weight_gap, bounds=(np.log(base) - 12, np.log(base) + 12), method="bounded")
        omegas[k] = float(np.exp(res.x))
    return np.diag(omegas)
