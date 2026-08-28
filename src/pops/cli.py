"""Ligne de commande (les commandes s'étoffent avec les modules : oracles, backtest, rapport mensuel)."""

from __future__ import annotations

import typer

app = typer.Typer(help="Moteur d'allocation sous politique de placement : Black-Litterman, HRP, Brinson, bandes.")


@app.callback()
def main() -> None:
    """Sous-commandes nommées."""


@app.command()
def oracles() -> None:
    """Vérifie le module Black-Litterman contre les tables de He-Litterman (1999) et d'Idzorek (2005)."""
    import subprocess
    import sys

    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "-q", "tests/test_oracles.py"]))


if __name__ == "__main__":
    app()
