import pandas as pd


def add_user_friendly_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Kleine Helfer: close umbenennen, tägliche Prozent-Change rechnen."""
    df = df.sort_values("date").copy()

    # "close" bleibt intern ok, aber für UI erzeugen wir "price"
    df["price"] = df["close"]

    # pct_change gibt 0.01 für 1% -> wir machen Prozent draus
    df["daily_change_pct"] = df["price"].pct_change() * 100

    return df
