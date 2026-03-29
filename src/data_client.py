import logging
from typing import Final, Iterable

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# yfinance akzeptiert Symbole wie "AAPL" oder "AAPL.US".
YF_PERIOD: Final[str] = "max"
YF_INTERVAL: Final[str] = "1d"


def _candidate_symbols(symbol: str) -> Iterable[str]:
    """Try the symbol as given and, if suffixed with .US, also the plain ticker."""
    sym = symbol.strip().upper()
    if not sym:
        return []
    yield sym
    if sym.endswith(".US"):
        yield sym[:-3]


def _download_symbol(sym: str) -> pd.DataFrame | None:
    """Pull raw history for one ticker via yfinance."""
    ticker = yf.Ticker(sym)
    try:
        return ticker.history(period=YF_PERIOD, interval=YF_INTERVAL, actions=False, auto_adjust=False)
    except Exception as e:
        logger.exception("yfinance download failed", extra={"symbol": sym})
        raise ConnectionError("Verbindungsfehler zu yfinance") from e


def fetch_prices(symbol: str) -> pd.DataFrame:
    """Holt Tagesdaten von yfinance mit robuster Fehlerbehandlung.

    Versucht zunächst das eingegebene Symbol, probiert bei .US-Suffix auch die Variante ohne Suffix.
    """

    requested_sym = symbol.strip().upper()
    tried = []
    last_empty = False

    for sym in _candidate_symbols(symbol):
        logger.info("Fetching prices", extra={"symbol": sym})
        tried.append(sym)
        raw = _download_symbol(sym)

        if raw is None or raw.empty:
            last_empty = True
            logger.warning("No data returned", extra={"symbol": sym})
            continue

        df = raw.reset_index()
        if "Date" in df.columns:
            df = df.rename(columns={"Date": "date"})
        elif "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "date"})
        else:
            # fallback: first column is the index we just reset
            df = df.rename(columns={df.columns[0]: "date"})

        df = df.rename(columns={"Close": "close"})
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        expected_cols = {"date", "close"}
        if not expected_cols.issubset(df.columns):
            logger.error("Unexpected columns from yfinance", extra={"symbol": sym, "columns": list(df.columns)})
            raise ValueError("Unerwartetes Datenformat von yfinance")

        # Immer mit dem ursprünglich angefragten Symbol speichern, damit Portfolio-Namen konsistent bleiben
        df["symbol"] = requested_sym if requested_sym else sym
        df = df[["symbol", "date", "close"]].dropna()

        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["date"] = df["date"].astype(str)
        df = df.dropna()

        if df.empty:
            last_empty = True
            logger.warning("Dataframe empty after cleaning", extra={"symbol": sym})
            continue

        logger.info("Fetched prices", extra={"symbol": sym, "rows": len(df)})
        return df

    if last_empty:
        raise ValueError(f"Keine Daten von yfinance erhalten (versucht: {', '.join(tried)})")
    raise ValueError("Symbol ist leer")
