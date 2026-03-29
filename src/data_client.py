import logging
import time
from math import isfinite
from typing import Final, Iterable

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# yfinance akzeptiert Symbole wie "AAPL" oder "AAPL.US".
YF_PERIOD: Final[str] = "max"
YF_INTERVAL: Final[str] = "1d"
MAX_RETRIES: Final[int] = 3
BACKOFF_SECONDS: Final[float] = 1.5


class DataSourceUnavailable(ConnectionError):
    """Die Datenquelle ist nicht erreichbar oder bricht mehrfach ab."""


class DataEmptyError(ValueError):
    """Die Datenquelle liefert keine Daten für das gewünschte Symbol."""


class DataFormatError(ValueError):
    """Die Daten sind vorhanden, aber das Format ist unerwartet/korrupt."""


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
    return ticker.history(
        period=YF_PERIOD,
        interval=YF_INTERVAL,
        actions=False,
        auto_adjust=False,
        raise_errors=False,
    )


def _download_with_retry(sym: str) -> pd.DataFrame | None:
    """Mehrfach versuchen, um kurzzeitige Netzprobleme abzufangen."""
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return _download_symbol(sym)
        except Exception as exc:  # yfinance gibt breite Exceptions
            last_exc = exc
            logger.warning(
                "yfinance download failed; retrying",
                extra={"symbol": sym, "attempt": attempt, "max": MAX_RETRIES},
            )
            time.sleep(BACKOFF_SECONDS * attempt)

    logger.exception("yfinance unavailable after retries", extra={"symbol": sym})
    if last_exc:
        raise DataSourceUnavailable("Verbindungsfehler zu yfinance") from last_exc
    raise DataSourceUnavailable("Verbindungsfehler zu yfinance")


def fetch_prices(symbol: str) -> pd.DataFrame:
    """Holt Tagesdaten von yfinance mit robuster Fehlerbehandlung.

    Versucht zunächst das eingegebene Symbol, probiert bei .US-Suffix auch die Variante ohne Suffix.
    """

    requested_sym = symbol.strip().upper()
    if not requested_sym:
        raise DataEmptyError("Symbol ist leer")

    tried = []
    last_empty = False

    for sym in _candidate_symbols(symbol):
        logger.info("Fetching prices", extra={"symbol": sym})
        tried.append(sym)
        raw = _download_with_retry(sym)

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
            raise DataFormatError("Unerwartetes Datenformat von yfinance")

        df["symbol"] = requested_sym if requested_sym else sym
        df = df[["symbol", "date", "close"]]

        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["date"] = df["date"].astype(str)
        df = df.dropna(subset=["date", "close"])

        # zusätzliche Plausibilisierung
        df = df.drop_duplicates(subset=["date"], keep="last")
        df = df[df["close"].notnull()]
        df = df[df["close"].apply(lambda x: pd.notna(x) and isfinite(x))]
        df = df.sort_values("date")

        if df.empty:
            last_empty = True
            logger.warning("Dataframe empty after cleaning", extra={"symbol": sym})
            continue

        logger.info("Fetched prices", extra={"symbol": sym, "rows": len(df)})
        return df

    if last_empty:
        raise DataEmptyError(f"Keine Daten von yfinance erhalten (versucht: {', '.join(tried)})")
    raise DataEmptyError("Symbol ist leer")
