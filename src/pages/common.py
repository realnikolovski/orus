import streamlit as st


def header(title: str, subtitle: str = ""):
    """Standard-Header mit Titel, optionaler Caption und Divider."""
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.divider()


def safe_float(x, default=0.0) -> float:
    """Best effort float-Konvertierung mit Fallback."""
    try:
        return float(x)
    except Exception:
        return default
