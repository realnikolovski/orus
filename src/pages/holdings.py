import streamlit as st

from db import load_assets, load_holdings, save_holding_value
from pages.common import header, safe_float


def render():
    """Ist-Beträge pro Asset eingeben und sichern."""
    header("Orus", "Aktuell investiert (Ist)")

    assets = load_assets()
    if len(assets) == 0:
        st.info("Keine Assets vorhanden. Gehe zu „Portfolio“ und füge Symbole hinzu.")
        return

    st.caption("Gib an, wie viel Geld du aktuell pro Asset investiert hast (in €).")
    holdings = load_holdings()

    total_value = 0.0
    edited = {}

    with st.container(border=True):
        st.markdown("**Investierter Betrag in €**")
        for sym in assets:
            current = safe_float(holdings.get(sym, 0.0))
            val = st.number_input(f"{sym} (€)", min_value=0.0, value=float(current), step=50.0)
            edited[sym] = val
            total_value += val

        st.divider()
        st.metric("Gesamt investiert", f"{total_value:,.2f} €".replace(",", " "))

        if st.button("Beträge speichern", type="primary", use_container_width=True):
            for sym, v in edited.items():
                save_holding_value(sym, v)
            st.success("Investierte Beträge gespeichert.")
