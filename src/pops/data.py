"""Données : six FNB de Toronto téléchargés de Yahoo Finance, rendements mensuels totaux.

Les prix sont ajustés des dividendes et fractionnements (série « adjusted close » de Yahoo), donc le
rendement mensuel calculé dessus est un rendement TOTAL, dividendes réinvestis. Les données restent en
CAD, ne sont jamais commitées (licence Yahoo : usage personnel), et se retéléchargent par ``pops fetch``.
Biais connu et déclaré : Yahoo ne garde que les FNB encore cotés, mais les six choisis existent sans
interruption depuis leur création, le biais de survie ne joue donc pas ici.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Les six classes d'actifs de la politique, chacune par le FNB de Toronto le plus ancien de sa classe.
ETFS: dict[str, str] = {
    "XIU.TO": "Actions canadiennes (S&P/TSX 60, depuis 1999)",
    "XSP.TO": "Actions américaines (S&P 500 couvert en CAD, depuis 2001)",
    "XIN.TO": "Actions internationales (MSCI EAFE couvert en CAD, depuis 2001)",
    "XRE.TO": "Immobilier coté (FPI canadiennes plafonnées, depuis 2002)",
    "XBB.TO": "Obligations canadiennes (univers, depuis 2000)",
    "XSB.TO": "Obligations court terme (depuis 2000)",
}

RAW = Path("data/raw/prix_fnb.parquet")


def fetch(dest: Path = RAW) -> pd.DataFrame:
    """Télécharge les prix ajustés quotidiens des six FNB et les écrit en parquet."""
    import yfinance as yf

    prices = yf.download(list(ETFS), period="max", auto_adjust=True, progress=False)["Close"]
    prices = prices[list(ETFS)].dropna(how="all")
    dest.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(dest)
    return prices


def monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Rendements mensuels totaux, restreints à la période où les six FNB existent tous."""
    monthly = prices.resample("ME").last()
    rets = monthly.pct_change()
    return rets.dropna()


def load_returns(path: Path = RAW) -> pd.DataFrame:
    """Charge le parquet local et rend les rendements mensuels ; erreur claire si le fetch manque."""
    if not path.exists():
        raise FileNotFoundError(f"{path} absent : lancer d'abord `pops fetch` (les prix ne sont pas commités)")
    return monthly_returns(pd.read_parquet(path))
