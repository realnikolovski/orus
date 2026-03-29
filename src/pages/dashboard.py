import pandas as pd
import streamlit as st

from db import load_assets, load_holdings, load_prices, load_target_weights
from pages.common import header

DRIFT_COL = "Abweichung (pp)"
AMOUNT_COL = "Betrag (€)"


def _validate_prereqs(assets, target, holdings):
    """Check, ob alle nötigen Eingaben vorhanden sind."""
    if len(assets) == 0:
        st.info("Start: Gehe zu „Portfolio“ und füge mindestens ein Asset hinzu.")
        return False
    if len(target) == 0:
        st.info("Nächster Schritt: Gehe zu „Gewichte (Ziel)“ und setze deine Ziel-Verteilung.")
        return False
    if len(holdings) == 0:
        st.info("Nächster Schritt: Gehe zu „Investiert (Ist)“ und trage deine investierten Beträge ein.")
        return False
    return True


def _build_drift_data(assets, target, holdings, total_value, drift_threshold_pp, min_trade_eur):
    """Berechne Abweichungen und Trade-Vorschläge für die Kacheln."""
    drift_rows = []
    suggestions = []

    for sym in assets:
        target_pct = float(target.get(sym, 0.0))
        current_value = float(holdings.get(sym, 0.0))
        current_pct = 100.0 * current_value / total_value
        drift_pp = current_pct - target_pct

        target_value = (target_pct / 100.0) * total_value
        trade_eur = target_value - current_value

        abs_drift = abs(drift_pp)
        if abs_drift <= drift_threshold_pp:
            traffic = "🟢"
        elif abs_drift <= 2 * drift_threshold_pp:
            traffic = "🟡"
        else:
            traffic = "🔴"

        drift_rows.append(
            {
                "Ampel": traffic,
                "Asset": sym,
                "Ziel (%)": round(target_pct, 1),
                "Aktuell (%)": round(current_pct, 1),
                DRIFT_COL: round(drift_pp, 1),
            }
        )

        if abs_drift > drift_threshold_pp and abs(trade_eur) >= min_trade_eur:
            suggestions.append(
                {
                    "Asset": sym,
                    "Empfehlung": "Kaufen" if trade_eur > 0 else "Verkaufen",
                    AMOUNT_COL: round(abs(trade_eur), 2),
                }
            )

    return pd.DataFrame(drift_rows), pd.DataFrame(suggestions)


def render():
    """Dashboard-Übersicht mit Ampel und Top-Vorschlägen."""
    header("Orus", "Dashboard – Überblick")

    assets = load_assets()
    target = load_target_weights()
    holdings = load_holdings()
    if not _validate_prereqs(assets, target, holdings):
        return

    total_value = sum(float(holdings.get(sym, 0.0)) for sym in assets)
    if total_value <= 0:
        st.warning("Dein Gesamtwert ist 0€. Trage unter „Investiert (Ist)“ Werte ein.")
        return

    drift_df, sug_df = _build_drift_data(
        assets=assets,
        target=target,
        holdings=holdings,
        total_value=total_value,
        drift_threshold_pp=2.0,
        min_trade_eur=50.0,
    )

    max_abs_drift = float(drift_df[DRIFT_COL].abs().max()) if not drift_df.empty else 0.0
    assets_with_prices = sum(1 for sym in assets if len(load_prices(sym)) > 0)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Gesamtwert", f"{total_value:,.2f} €".replace(",", " "))
    k2.metric("Assets", str(len(assets)))
    k3.metric("Max. Abweichung", f"{max_abs_drift:.1f} pp")
    k4.metric("Vorschläge", str(len(sug_df)))

    st.divider()

    if assets_with_prices < len(assets):
        st.warning(
            f"Marktdaten fehlen für {len(assets) - assets_with_prices} Asset(s). "
            "Gehe zu „Daten“ und aktualisiere."
        )
    elif len(sug_df) == 0:
        st.success("Alles im grünen Bereich: Keine sinnvollen Rebalancing-Trades nötig (bei Standard-Schwellen).")
    else:
        st.info("Es gibt Rebalancing-Vorschläge. Gehe zu „Check & Rebalancing“ für Details und Anleitung.")

    left, right = st.columns([2, 1])
    with left:
        with st.container(border=True):
            st.markdown("**Übersicht: Ziel vs. Aktuell (Ampel)**")
            drift_show = drift_df.sort_values(DRIFT_COL, key=lambda s: s.abs(), ascending=False)
            st.dataframe(drift_show, use_container_width=True)

    with right:
        with st.container(border=True):
            st.markdown("**Top-Vorschläge**")
            if sug_df.empty:
                st.write("Keine Trades nötig.")
            else:
                top = sug_df.sort_values(AMOUNT_COL, ascending=False).head(6)
                st.dataframe(top, use_container_width=True)

    st.divider()
    with st.expander("Was bedeutet die Ampel?"):
        st.write(
            "🟢 **OK**: Abweichung ist klein (Standard: ≤ 2 pp)\n\n"
            "🟡 **Beobachten**: merkbare Abweichung (ca. 2–4 pp)\n\n"
            "🔴 **Handeln**: deutliche Abweichung (> 4 pp)\n\n"
            "Du kannst die genauen Einstellungen unter „Check & Rebalancing“ anpassen."
        )
