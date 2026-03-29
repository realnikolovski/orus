import pandas as pd
import streamlit as st

from db import add_asset, load_assets, remove_asset
from pages.common import header


def render():
    """Portfolio-Tab: Assets hinzufügen/entfernen und anzeigen."""
    header("Orus", "Portfolio verwalten (MVP)")

    st.subheader("Assets hinzufügen/entfernen")
    st.caption("Assets sind die Symbole, die du analysieren willst (z. B. AAPL.US).")

    left, right = st.columns([2, 1])

    with left:
        with st.container(border=True):
            st.markdown("**Asset hinzufügen**")
            preset = st.selectbox(
                "Vordefinierte Auswahl (optional)",
                ["—", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA", "SPY", "QQQ"],
            )
            custom = st.text_input("Oder eigenes Symbol eingeben", placeholder="z.B. AAPL")

            custom_value = custom.strip()
            symbol_to_add = custom_value if custom_value else ""
            if symbol_to_add == "" and preset != "—":
                symbol_to_add = preset

            if st.button("Hinzufügen", type="primary", use_container_width=True):
                if symbol_to_add == "":
                    st.warning("Bitte ein Symbol auswählen oder eingeben.")
                else:
                    add_asset(symbol_to_add)
                    st.success(f"Hinzugefügt: {symbol_to_add.upper().strip()}")

    with right:
        with st.container(border=True):
            st.markdown("**Asset entfernen**")
            assets = load_assets()
            if len(assets) == 0:
                st.info("Noch keine Assets gespeichert.")
            else:
                sym = st.selectbox("Asset", assets)
                if st.button("Entfernen", use_container_width=True):
                    remove_asset(sym)
                    st.warning(f"Entfernt: {sym}")

    st.divider()
    st.subheader("Aktuelle Asset-Liste")

    assets = load_assets()
    if len(assets) == 0:
        st.info("Füge oben mindestens ein Asset hinzu.")
    else:
        st.dataframe(pd.DataFrame({"Symbol": assets}), use_container_width=True)
