"""Ligne de commande : télécharger, backtester, tracer, rapporter. Chaque commande est rejouable."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Moteur d'allocation sous politique de placement : Black-Litterman, HRP, Brinson, bandes.")

# La politique de placement du dépôt : un profil équilibré canadien, 65 % croissance, 35 % revenu.
TARGETS = {"XIU.TO": 0.25, "XSP.TO": 0.20, "XIN.TO": 0.15, "XRE.TO": 0.05, "XBB.TO": 0.25, "XSB.TO": 0.10}
EQUITIES = ["XIU.TO", "XSP.TO", "XIN.TO"]


def _policy():
    from pops.policy import Policy

    return Policy(targets=TARGETS)


@app.callback()
def main() -> None:
    """Sous-commandes nommées."""


@app.command()
def oracles() -> None:
    """Vérifie le module Black-Litterman contre les tables de He-Litterman (1999) et d'Idzorek (2005)."""
    import subprocess
    import sys

    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "-q", "tests/test_oracles.py"]))


@app.command()
def fetch() -> None:
    """Télécharge les prix ajustés des six FNB de Toronto (Yahoo, non commités)."""
    from pops import data

    prices = data.fetch()
    typer.echo(f"{prices.shape[0]} jours, {prices.shape[1]} FNB, de {prices.index[0].date()} "
               f"à {prices.index[-1].date()} -> {data.RAW}")


@app.command()
def backtest(out: Path = Path("results")) -> None:
    """Le walk-forward complet, écrit les tables dans results/tables et les figures dans results/figures."""
    from pops import data, engine, figures

    returns = data.load_returns()
    result = engine.run_backtest(returns, _policy(), EQUITIES)
    tables = out / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    engine.summary(result).to_csv(tables / "backtest_resume.csv")
    result.weights_bl.to_csv(tables / "poids_black_litterman.csv")
    result.views_log.to_csv(tables / "journal_des_vues.csv", index=False)
    result.attribution().to_csv(tables / "attribution_brinson.csv")
    result.returns.to_csv(tables / "rendements_nets.csv")
    paths = figures.make_all(result, out / "figures")
    typer.echo(f"{len(result.returns)} mois hors échantillon ({result.returns.index[0].strftime('%Y-%m')} "
               f"à {result.returns.index[-1].strftime('%Y-%m')}), tables -> {tables}, "
               f"{len(paths)} figures -> {out / 'figures'}")


@app.command()
def report() -> None:
    """Le rapport de placement du dernier mois observé, régénérable à l'identique."""
    from pops import data
    from pops.report import monthly_report

    path = monthly_report(data.load_returns(), _policy(), EQUITIES)
    typer.echo(f"rapport écrit : {path}")


if __name__ == "__main__":
    app()
