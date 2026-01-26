import pandas as pd
import requests
from io import StringIO


def fetch_prices(symbol):
    """
    Holt Tagesdaten von Stooq (kein API-Key nötig).
    Beispiel: AAPL.US, MSFT.US
    """
    url = f"https://stooq.com/q/d/l/?s={symbol.lower()}&i=d"
    r = requests.get(url, timeout=20)
    r.raise_for_status()

    df = pd.read_csv(StringIO(r.text))

    # Stooq liefert: Date, Open, High, Low, Close, Volume
    df = df.rename(columns={"Date": "date", "Close": "close"})
    df["symbol"] = symbol.upper()
    df = df[["symbol", "date", "close"]].dropna()

    # close sicher als Zahl
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna()

    return df
