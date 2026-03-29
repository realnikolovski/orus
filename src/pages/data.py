import logging
import streamlit as st

from data_client import DataEmptyError, DataFormatError, DataSourceUnavailable, fetch_prices
from db import load_assets, save_prices
from pages.common import header

logger = logging.getLogger(__name__)


def render():
    """Daten-Tab: zieht Kurse, speichert sie und zeigt Status an."""
    header("Orus", "Marktdaten aktualisieren (MVP)")

    assets = load_assets()
    if len(assets) == 0:
        st.info("Keine Assets vorhanden. Gehe zu „Portfolio“ und füge Symbole hinzu.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.container(border=True):
            st.markdown("**Daten holen & speichern**")
            st.caption("Orus lädt Preisdaten (yfinance) und speichert die letzten N Tage in der Datenbank (SQLite).")

            days_to_store = st.slider("Wie viele Tage speichern?", 50, 2000, 300, 50)

            if st.button("Jetzt aktualisieren", type="primary", use_container_width=True):
                ok = 0
                empty = 0
                format_fail = 0
                source_fail = 0
                db_fail = 0
                other_fail = 0

                progress = st.progress(0)
                status = st.empty()

                for i, sym in enumerate(assets, start=1):
                    try:
                        df = fetch_prices(sym).tail(int(days_to_store))
                        save_prices(df)
                        ok += 1
                        logger.info("Data update successful", extra={"symbol": sym, "rows": len(df)})
                        status.info(f"{sym}: gespeichert ({len(df)} Tage)")
                    except DataEmptyError as e:
                        empty += 1
                        logger.warning("No data returned", extra={"symbol": sym})
                        status.warning(f"{sym}: keine Daten ({e})")
                    except DataFormatError as e:
                        format_fail += 1
                        logger.exception("Data format invalid", extra={"symbol": sym})
                        status.error(f"{sym}: Daten korrupt/unerwartet: {e}")
                    except DataSourceUnavailable as e:
                        source_fail += 1
                        logger.exception("Data source unavailable", extra={"symbol": sym})
                        status.error(f"{sym}: Quelle nicht erreichbar – später erneut versuchen. {e}")
                    except RuntimeError as e:
                        db_fail += 1
                        logger.exception("DB error during update", extra={"symbol": sym})
                        status.error(f"{sym}: Datenbank-Fehler: {e}")
                    except Exception as e:
                        other_fail += 1
                        logger.exception("Data update failed", extra={"symbol": sym})
                        status.error(f"{sym}: Unbekannter Fehler: {e}")

                    progress.progress(i / len(assets))

                summary = (
                    f"OK={ok} | leer={empty} | Formatfehler={format_fail} | Quelle down={source_fail} | "
                    f"DB-Fehler={db_fail} | sonstige Fehler={other_fail}"
                )

                if source_fail == 0 and db_fail == 0 and other_fail == 0 and format_fail == 0:
                    st.success(f"Fertig: {ok}/{len(assets)} aktualisiert. {summary}")
                else:
                    st.warning(f"Fertig mit Problemen: {summary}")

    with col2:
        with st.container(border=True):
            st.markdown("**Assets in deinem Portfolio**")
            st.write(assets)

    st.divider()
    with st.expander("Hinweis zu Symbolen"):
        st.write(
            "Dieses MVP nutzt **yfinance** als Datenquelle. Typische Symbole: "
            "`AAPL`, `NVDA`, `SPY`, `QQQ` (ohne `.US`)."
        )
