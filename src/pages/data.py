import logging
import streamlit as st

from data_client import fetch_prices
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
                fail = 0

                progress = st.progress(0)
                status = st.empty()

                for i, sym in enumerate(assets, start=1):
                    try:
                        df = fetch_prices(sym).tail(int(days_to_store))
                        save_prices(df)
                        ok += 1
                        logger.info("Data update successful", extra={"symbol": sym, "rows": len(df)})
                        status.info(f"{sym}: gespeichert ({len(df)} Tage)")
                    except Exception as e:
                        fail += 1
                        logger.exception("Data update failed", extra={"symbol": sym})
                        status.error(f"{sym}: Fehler: {e}")

                    progress.progress(i / len(assets))

                if fail == 0:
                    st.success(f"Fertig: {ok}/{len(assets)} aktualisiert.")
                else:
                    st.warning(f"Fertig: OK={ok}, Fehler={fail}. (Einige Symbole liefern evtl. keine Daten.)")

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
