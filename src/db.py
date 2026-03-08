import sqlite3

DB_PATH = "orus.db"


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with connect() as conn:
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS prices (
            symbol TEXT NOT NULL,
            date   TEXT NOT NULL,
            close  REAL NOT NULL,
            PRIMARY KEY (symbol, date)
        )
        """
        )

        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS assets (
            symbol TEXT PRIMARY KEY
        )
        """
        )

        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS target_weights (
            symbol TEXT PRIMARY KEY,
            weight_pct REAL NOT NULL
        )
        """
        )

        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS holdings (
            symbol TEXT PRIMARY KEY,
            value_eur REAL NOT NULL
        )
        """
        )


def save_prices(df):
    """
    df muss Spalten haben: symbol, date, close
    """
    rows = df[["symbol", "date", "close"]].values.tolist()

    with connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO prices(symbol, date, close) VALUES (?, ?, ?)",
            rows,
        )


def load_prices(symbol):
    with connect() as conn:
        cur = conn.execute(
            "SELECT symbol, date, close FROM prices WHERE symbol=? ORDER BY date",
            (symbol.upper(),),
        )
        return cur.fetchall()


def add_asset(symbol):
    symbol = symbol.upper().strip()
    if symbol == "":
        return
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO assets(symbol) VALUES (?)",
            (symbol,),
        )


def remove_asset(symbol):
    symbol = symbol.upper().strip()
    with connect() as conn:
        conn.execute(
            "DELETE FROM assets WHERE symbol=?",
            (symbol,),
        )


def load_assets():
    with connect() as conn:
        cur = conn.execute("SELECT symbol FROM assets ORDER BY symbol")
        rows = cur.fetchall()
    return [row[0] for row in rows]


def save_target_weight(symbol, weight_pct):
    symbol = symbol.upper().strip()
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO target_weights(symbol, weight_pct) VALUES (?, ?)",
            (symbol, float(weight_pct)),
        )


def load_target_weights():
    with connect() as conn:
        cur = conn.execute(
            "SELECT symbol, weight_pct FROM target_weights ORDER BY symbol"
        )
        rows = cur.fetchall()
    return dict(rows)


def save_holding_value(symbol, value_eur):
    symbol = symbol.upper().strip()
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO holdings(symbol, value_eur) VALUES (?, ?)",
            (symbol, float(value_eur)),
        )


def load_holdings():
    with connect() as conn:
        cur = conn.execute("SELECT symbol, value_eur FROM holdings ORDER BY symbol")
        rows = cur.fetchall()
    return dict(rows)
