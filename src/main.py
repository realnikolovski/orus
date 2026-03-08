import streamlit as st

from db import init_db
from pages import PAGE_RENDERERS


st.set_page_config(page_title="Orus", layout="wide")
init_db()

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


def set_page(page_name: str):
    st.session_state.page = page_name


def nav_button(label: str, page_name: str):
    is_active = st.session_state.page == page_name
    st.button(
        label,
        key=f"nav_{page_name}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
        on_click=set_page,
        args=(page_name,),
    )


with st.sidebar:
    st.markdown("## Orus")
    st.caption("Portfolio-Check (MVP)")
    st.divider()

    nav_button("📊 Dashboard", "Dashboard")
    nav_button("📁 Portfolio", "Portfolio")
    nav_button("⬇️ Daten", "Daten")
    nav_button("📈 Analyse", "Analyse")
    nav_button("🎯 Gewichte (Ziel)", "Gewichte")
    nav_button("💰 Investiert (Ist)", "Investiert")
    nav_button("🔁 Check & Rebalancing", "Rebalancing")

    st.divider()
    st.caption("Empfohlener Ablauf:")
    st.caption("Portfolio → Daten → Gewichte → Investiert → Rebalancing")


page = st.session_state.page
PAGE_RENDERERS.get(page, PAGE_RENDERERS["Dashboard"])()
