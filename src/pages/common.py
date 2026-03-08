import streamlit as st


def header(title: str, subtitle: str = ""):
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.divider()


def safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default
