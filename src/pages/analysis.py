import pandas as pd
import streamlit as st

from analytics import add_user_friendly_columns
from db import load_assets, load_prices
from pages.common import header


def _load_result_for_symbol(sym: str, days_to_show: int, step: int):
    rows = load_prices(sym)
    if len(rows) == 0:
        return None, f"Keine Daten für {sym}. Bitte unter „Daten“ aktualisieren."

    df = pd.DataFrame(rows, columns=["symbol", "date", "close"]).sort_values("date")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df = df.tail(int(days_to_show)).copy()
    if int(step) > 1:
        df = df.iloc[:: int(step)].copy()

    if len(df) < 2:
        return (
            None,
            f"Für {sym} sind nach Zeitraum/Intervall nur {len(df)} Datenpunkt(e) übrig. "
            "Wähle mehr Tage oder ein kleineres Intervall.",
        )

    result = add_user_friendly_columns(df)
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result = result.dropna(subset=["date"]).sort_values("date")
    return result, None


def _build_kpi_row(sym: str, result: pd.DataFrame):
    last_price = float(result["price"].iloc[-1])
    last_change = result["daily_change_pct"].iloc[-1]
    return {
        "Asset": sym,
        "Aktueller Preis": round(last_price, 2),
        "Veränderung zum Vortag (%)": None if pd.isna(last_change) else round(float(last_change), 2),
    }


def _render_single_asset(sym: str, result: pd.DataFrame):
    result = result.set_index("date")
    left, right = st.columns([2, 1])

    with left:
        with st.container(border=True):
            st.markdown(f"**Preisentwicklung – {sym}**")
            st.line_chart(result["price"])
        with st.container(border=True):
            st.markdown("**Tägliche Veränderung (%)**")
            st.line_chart(result["daily_change_pct"])

    with right:
        with st.container(border=True):
            st.markdown("**Daten (letzte 50 Zeilen)**")
            show = result[["price", "daily_change_pct"]].reset_index().copy()
            show = show.rename(
                columns={
                    "date": "Datum",
                    "price": "Preis",
                    "daily_change_pct": "Tägliche Veränderung (%)",
                }
            )
            st.dataframe(show.tail(50), use_container_width=True)


def _render_multi_asset(results: dict[str, pd.DataFrame], selected: list[str]):
    price_series = {sym: results[sym].set_index("date")["price"] for sym in selected}
    change_series = {sym: results[sym].set_index("date")["daily_change_pct"] for sym in selected}

    prices_df = pd.DataFrame(price_series).sort_index().ffill()
    change_df = pd.DataFrame(change_series).sort_index().ffill()

    st.subheader("Preisvergleich (Index 100)")
    st.caption(
        "Alle ausgewählten Assets starten am Anfang des Zeitraums bei **100**. "
        "So vergleichst du die **prozentuale Entwicklung** direkt – auch bei unterschiedlichen Preisen."
    )

    norm_df = prices_df.copy()
    for col in norm_df.columns:
        first_valid = norm_df[col].dropna()
        if len(first_valid) > 0:
            start = first_valid.iloc[0]
            norm_df[col] = (norm_df[col] / start) * 100

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("**Entwicklung (Index 100)**")
            st.line_chart(norm_df)
    with right:
        with st.container(border=True):
            st.markdown("**Tägliche Veränderung (%)**")
            st.line_chart(change_df)

    with st.expander("Wie lese ich den Index-100-Chart?"):
        st.write(
            "- **100** = Startpunkt des Zeitraums\n"
            "- **120** = +20 % seit Start\n"
            "- **90** = −10 % seit Start\n\n"
            "Je höher die Linie, desto besser hat sich das Asset im Zeitraum entwickelt."
        )


def render():
    header("Orus", "Analyse – Entwicklung & Vergleich")

    assets = load_assets()
    if len(assets) == 0:
        st.info("Keine Assets vorhanden. Gehe zu „Portfolio“ und füge Symbole hinzu.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        selected = st.multiselect("Welche Assets analysieren?", options=assets, default=[assets[0]] if assets else [])
    with c2:
        days_to_show = st.slider("Zeitraum (Tage)", 20, 500, 90, 10)
    with c3:
        step = st.selectbox("Intervall (jeden n-ten Tag)", [1, 2, 5, 10, 20], index=0)

    if len(selected) == 0:
        st.warning("Bitte wähle mindestens ein Asset aus.")
        return
    if len(selected) > 6:
        st.warning("Bitte maximal 6 Assets auswählen, sonst wird es unübersichtlich.")
        return

    results = {}
    kpis = []

    for sym in selected:
        result, error = _load_result_for_symbol(sym, int(days_to_show), int(step))
        if error:
            st.warning(error)
            return
        results[sym] = result
        kpis.append(_build_kpi_row(sym, result))

    st.subheader("Kurzübersicht")
    st.dataframe(pd.DataFrame(kpis), use_container_width=True)
    st.divider()

    if len(selected) == 1:
        sym = selected[0]
        _render_single_asset(sym, results[sym])
        return

    _render_multi_asset(results, selected)
