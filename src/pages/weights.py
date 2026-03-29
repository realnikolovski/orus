import streamlit as st

from db import load_assets, load_target_weights, save_target_weight
from pages.common import header, safe_float


def render():
    """Zielgewichte in % je Asset erfassen und speichern."""
    header("Orus", "Ziel-Verteilung festlegen (Soll)")

    assets = load_assets()
    if len(assets) == 0:
        st.info("Keine Assets vorhanden. Gehe zu „Portfolio“ und füge Symbole hinzu.")
        return

    st.caption("Gib an, wie du dein Portfolio aufteilen willst. Beispiel: 50% ETF, 50% Aktien.")
    weights = load_target_weights()

    total = 0.0
    edited = {}

    with st.container(border=True):
        st.markdown("**Zielgewichte in %**")
        for sym in assets:
            current = safe_float(weights.get(sym, 0.0))
            val = st.number_input(f"{sym}", min_value=0.0, max_value=100.0, value=float(current), step=1.0)
            edited[sym] = val
            total += val

        st.divider()
        st.metric("Summe", f"{total:.1f}%")

        if st.button("Zielgewichte speichern", type="primary", use_container_width=True):
            if total < 99.0 or total > 101.0:
                st.error("Die Summe sollte ungefähr 100% sein (z. B. 99% bis 101%).")
                return
            for sym, w in edited.items():
                save_target_weight(sym, w)
            st.success("Zielgewichte gespeichert.")
