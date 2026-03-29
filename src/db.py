import logging
import sqlite3
from typing import Tuple

import pandas as pd
from config import load_config

logger = logging.getLogger(__name__)
_config = load_config()
DB_PATH = _config.db_path


def connect():
    """Open a sqlite connection (reads path from config)."""
    try:
        return sqlite3.connect(DB_PATH, timeout=5)
    except sqlite3.DatabaseError as e:
        logger.exception("DB connection corrupted", extra={"db_path": DB_PATH})
        raise RuntimeError("Datenbank beschädigt oder nicht lesbar") from e
    except sqlite3.Error as e:
        logger.exception("DB connection failed", extra={"db_path": DB_PATH})
        raise RuntimeError("Datenbank-Verbindung fehlgeschlagen") from e


def init_db():
    """Create tables if missing so the app can start clean."""
    try:
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
        logger.info("Database initialized", extra={"db_path": DB_PATH})
    except sqlite3.DatabaseError as e:
        logger.exception("DB init failed (corrupt)", extra={"db_path": DB_PATH})
        raise RuntimeError("Datenbank beschädigt – Initialisierung nicht möglich") from e
    except sqlite3.Error as e:
        logger.exception("DB init failed", extra={"db_path": DB_PATH})
        raise RuntimeError("Datenbank-Initialisierung fehlgeschlagen") from e


def save_prices(df):
    """Speichert Preisdaten; df muss Spalten haben: symbol, date, close."""
    if df is None or df.empty:
        logger.warning("save_prices called with empty dataframe")
        return

    required = {"symbol", "date", "close"}
    if not required.issubset(df.columns):
        logger.error("save_prices missing required columns", extra={"columns": list(df.columns)})
        raise ValueError("DataFrame fehlt erforderliche Spalten")

    safe_df = df.copy()
    safe_df["date"] = safe_df["date"].astype(str)
    safe_df["close"] = pd.to_numeric(safe_df["close"], errors="coerce")
    safe_df = safe_df.dropna(subset=["date", "close"])

    rows = safe_df[["symbol", "date", "close"]].values.tolist()

    try:
        with connect() as conn:
            conn.execute("BEGIN")
            conn.executemany(
                "INSERT OR REPLACE INTO prices(symbol, date, close) VALUES (?, ?, ?)",
                rows,
            )
            conn.commit()
        logger.info("Prices stored", extra={"rows": len(rows)})
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to save prices (corrupt)", extra={"rows": len(rows)})
        raise RuntimeError("Datenbank beschädigt – Preise konnten nicht gespeichert werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to save prices", extra={"rows": len(rows)})
        raise RuntimeError("Datenbank-Fehler beim Speichern der Preise") from e


def load_prices(symbol) -> list[Tuple[str, str, float]]:
    """Hol alle Preise für ein Symbol sortiert nach Datum."""
    sym = symbol.upper()
    try:
        with connect() as conn:
            cur = conn.execute(
                "SELECT symbol, date, close FROM prices WHERE symbol=? ORDER BY date",
                (sym,),
            )
            rows = cur.fetchall()
        return rows
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to load prices (corrupt)", extra={"symbol": sym})
        raise RuntimeError("Datenbank beschädigt – Preise können nicht gelesen werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to load prices", extra={"symbol": sym})
        raise RuntimeError("Datenbank-Fehler beim Lesen von Preisen") from e


def add_asset(symbol):
    """Lege ein Asset an, falls nicht vorhanden."""
    sym = symbol.upper().strip()
    if sym == "":
        return
    try:
        with connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO assets(symbol) VALUES (?)",
                (sym,),
            )
        logger.info("Asset added", extra={"symbol": sym})
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to add asset (corrupt)", extra={"symbol": sym})
        raise RuntimeError("Datenbank beschädigt – Asset konnte nicht gespeichert werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to add asset", extra={"symbol": sym})
        raise RuntimeError("Datenbank-Fehler beim Hinzufügen eines Assets") from e


def remove_asset(symbol):
    """Entferne ein Asset komplett."""
    sym = symbol.upper().strip()
    try:
        with connect() as conn:
            conn.execute(
                "DELETE FROM assets WHERE symbol=?",
                (sym,),
            )
        logger.info("Asset removed", extra={"symbol": sym})
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to remove asset (corrupt)", extra={"symbol": sym})
        raise RuntimeError("Datenbank beschädigt – Asset konnte nicht entfernt werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to remove asset", extra={"symbol": sym})
        raise RuntimeError("Datenbank-Fehler beim Entfernen eines Assets") from e


def load_assets() -> list[str]:
    """Lade alle bekannten Assets als Liste."""
    try:
        with connect() as conn:
            cur = conn.execute("SELECT symbol FROM assets ORDER BY symbol")
            rows = cur.fetchall()
        return [row[0] for row in rows]
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to load assets (corrupt)")
        raise RuntimeError("Datenbank beschädigt – Assets können nicht gelesen werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to load assets")
        raise RuntimeError("Datenbank-Fehler beim Laden der Assets") from e


def save_target_weight(symbol, weight_pct):
    """Speichere Zielgewicht in Prozent für ein Asset."""
    sym = symbol.upper().strip()
    try:
        with connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO target_weights(symbol, weight_pct) VALUES (?, ?)",
                (sym, float(weight_pct)),
            )
        logger.info("Target weight saved", extra={"symbol": sym, "weight_pct": float(weight_pct)})
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to save target weight (corrupt)", extra={"symbol": sym})
        raise RuntimeError("Datenbank beschädigt – Zielgewicht konnte nicht gespeichert werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to save target weight", extra={"symbol": sym})
        raise RuntimeError("Datenbank-Fehler beim Speichern der Zielgewichte") from e


def load_target_weights():
    """Hole alle Zielgewichte als Dict."""
    try:
        with connect() as conn:
            cur = conn.execute(
                "SELECT symbol, weight_pct FROM target_weights ORDER BY symbol"
            )
            rows = cur.fetchall()
        return dict(rows)
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to load target weights (corrupt)")
        raise RuntimeError("Datenbank beschädigt – Zielgewichte können nicht gelesen werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to load target weights")
        raise RuntimeError("Datenbank-Fehler beim Laden der Zielgewichte") from e


def save_holding_value(symbol, value_eur):
    """Speichere investierten Euro-Betrag pro Asset."""
    sym = symbol.upper().strip()
    try:
        with connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO holdings(symbol, value_eur) VALUES (?, ?)",
                (sym, float(value_eur)),
            )
        logger.info("Holding saved", extra={"symbol": sym, "value_eur": float(value_eur)})
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to save holding (corrupt)", extra={"symbol": sym})
        raise RuntimeError("Datenbank beschädigt – Holdings konnten nicht gespeichert werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to save holding", extra={"symbol": sym})
        raise RuntimeError("Datenbank-Fehler beim Speichern der Holdings") from e


def load_holdings():
    """Hole investierte Beträge als Dict."""
    try:
        with connect() as conn:
            cur = conn.execute("SELECT symbol, value_eur FROM holdings ORDER BY symbol")
            rows = cur.fetchall()
        return dict(rows)
    except sqlite3.DatabaseError as e:
        logger.exception("Failed to load holdings (corrupt)")
        raise RuntimeError("Datenbank beschädigt – Holdings können nicht gelesen werden") from e
    except sqlite3.Error as e:
        logger.exception("Failed to load holdings")
        raise RuntimeError("Datenbank-Fehler beim Laden der Holdings") from e
