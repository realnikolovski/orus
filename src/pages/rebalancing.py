import pandas as pd
import streamlit as st

from db import load_assets, load_holdings, load_target_weights
from pages.common import header

AMOUNT_COL = "Betrag (€)"


def _validate_inputs(assets, target, holdings):
    if len(assets) == 0:
        st.info("Keine Assets vorhanden. Gehe zu „Portfolio“ und füge Symbole hinzu.")
        return False
    if len(target) == 0:
        st.info("Keine Zielgewichte gespeichert. Gehe zu „Gewichte (Ziel)“.")
        return False
    if len(holdings) == 0:
        st.info("Keine investierten Beträge gespeichert. Gehe zu „Investiert (Ist)“.")
        return False
    return True


def _controls():
    with st.container(border=True):
        st.markdown("### Einstellungen (wann soll Orus handeln?)")
        st.write(
            "Orus vergleicht deine **Ziel-Verteilung** mit deiner **aktuellen Verteilung**. "
            "Wenn ein Asset zu stark abweicht, schlägt Orus vor, Geld umzuverteilen."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            drift_threshold_pp = st.slider("Abweichung ab der gehandelt wird (Prozentpunkte)", 0.5, 10.0, 2.0, 0.5)
        with c2:
            min_trade_eur = st.slider("Min. Trade-Betrag (€)", 0, 500, 50, 10)
        with c3:
            mode = st.selectbox(
                "Rebalancing-Stil",
                ["Zur Zielverteilung zurück (Standard)", "Sanft (nur 50% korrigieren)"],
            )

        with st.expander("Hilfe: Was sind „Prozentpunkte (pp)“?"):
            st.write(
                "**Prozentpunkte** sind die Differenz zwischen zwei Prozentwerten.\n\n"
                "Beispiel: Ziel 50%, aktuell 53% → Abweichung = **+3 pp**.\n"
                f"Mit einer Schwelle von **{drift_threshold_pp:.1f} pp** handelt Orus erst, "
                "wenn du klar über/unter deinem Ziel bist."
            )

    factor = 1.0 if mode.startswith("Zur") else 0.5
    return drift_threshold_pp, min_trade_eur, factor


def _traffic_status(abs_drift: float, drift_threshold_pp: float) -> str:
    if abs_drift <= drift_threshold_pp:
        return "🟢 OK"
    if abs_drift <= 2 * drift_threshold_pp:
        return "🟡 Beobachten"
    return "🔴 Handeln"


def _action_for_drift(drift_pp: float, trade_eur: float, drift_threshold_pp: float, min_trade_eur: float):
    abs_drift = abs(drift_pp)
    if abs_drift <= drift_threshold_pp:
        return "OK", "Im Toleranzbereich"

    if trade_eur > 0:
        action, reason = "Kaufen", f"Zu niedrig gewichtet ({drift_pp:.1f} pp)"
    elif trade_eur < 0:
        action, reason = "Verkaufen", f"Zu hoch gewichtet (+{drift_pp:.1f} pp)"
    else:
        action, reason = "OK", "Im Toleranzbereich"

    if action != "OK" and abs(trade_eur) < min_trade_eur:
        return "OK", f"Trade wäre < {min_trade_eur}€"
    return action, reason


def _build_tables(assets, target, holdings, total_portfolio, drift_threshold_pp, min_trade_eur, factor):
    overview_rows = []
    suggestions = []

    for sym in assets:
        target_pct = float(target.get(sym, 0.0))
        current_value = float(holdings.get(sym, 0.0))
        current_pct = 100.0 * current_value / total_portfolio
        drift_pp = current_pct - target_pct

        abs_drift = abs(drift_pp)
        traffic = _traffic_status(abs_drift, drift_threshold_pp)

        target_value = (target_pct / 100.0) * total_portfolio
        trade_eur = (target_value - current_value) * factor
        action, reason = _action_for_drift(drift_pp, trade_eur, drift_threshold_pp, min_trade_eur)

        overview_rows.append(
            {
                "Ampel": traffic,
                "Asset": sym,
                "Ziel (%)": round(target_pct, 1),
                "Aktuell (%)": round(current_pct, 1),
                "Abweichung (pp)": round(drift_pp, 1),
                "Investiert (€)": round(current_value, 2),
            }
        )

        if action != "OK":
            suggestions.append(
                {
                    "Asset": sym,
                    "Empfehlung": action,
                    AMOUNT_COL: round(abs(trade_eur), 2),
                    "Begründung": reason,
                }
            )

    overview_df = pd.DataFrame(overview_rows).sort_values("Abweichung (pp)", ascending=False)
    sug_df = pd.DataFrame(suggestions)
    return overview_df, sug_df


def _render_howto():
    st.subheader("So setzt du die Vorschläge praktisch um (Schritt-für-Schritt)")
    with st.container(border=True):
        st.markdown(
            "1. **Verkaufen (wenn nötig)**: Verkaufe zuerst die Assets mit **„Verkaufen“**, damit Geld frei wird.\n"
            "2. **Kaufen**: Kaufe danach die Assets mit **„Kaufen“**.\n"
            "3. **Nicht übertreiben**: Wenn Trades sehr klein sind, ignoriere sie (dafür ist der Mindestbetrag da).\n"
            "4. **Danach prüfen**: Passe die „Investiert (Ist)“-Werte an und schau nochmal in den Check."
        )
        st.caption("Hinweis: Dieses MVP rechnet ohne Gebühren/Steuern. In echt können kleine Trades unattraktiv sein.")


def _render_suggestions(sug_df: pd.DataFrame):
    st.subheader("Rebalancing-Vorschläge")
    if sug_df.empty:
        st.success("Keine Trades nötig (alles im Toleranzbereich oder unter Mindestbetrag).")
        return sug_df

    order_map = {"Verkaufen": 0, "Kaufen": 1}
    sug_df["_order"] = sug_df["Empfehlung"].map(order_map).fillna(9)
    sug_df = sug_df.sort_values(["_order", AMOUNT_COL], ascending=[True, False]).drop(columns=["_order"])
    st.dataframe(sug_df, use_container_width=True)

    sells = sug_df[sug_df["Empfehlung"] == "Verkaufen"][AMOUNT_COL].sum()
    buys = sug_df[sug_df["Empfehlung"] == "Kaufen"][AMOUNT_COL].sum()
    st.info(
        f"Zusammenfassung: Verkaufen ≈ {sells:.2f}€, Kaufen ≈ {buys:.2f}€. "
        "Idealerweise finanzieren Verkäufe die Käufe (ohne Gebühren)."
    )
    return sug_df


def render():
    header("Orus", "Portfolio-Check & Rebalancing (MVP)")

    assets = load_assets()
    target = load_target_weights()
    holdings = load_holdings()
    if not _validate_inputs(assets, target, holdings):
        return

    total_portfolio = sum(float(holdings.get(sym, 0.0)) for sym in assets)
    if total_portfolio <= 0:
        st.warning("Gesamt investiert ist 0€. Bitte unter „Investiert (Ist)“ Beträge eintragen.")
        return

    drift_threshold_pp, min_trade_eur, factor = _controls()
    overview_df, sug_df = _build_tables(
        assets=assets,
        target=target,
        holdings=holdings,
        total_portfolio=total_portfolio,
        drift_threshold_pp=drift_threshold_pp,
        min_trade_eur=min_trade_eur,
        factor=factor,
    )

    st.subheader("Übersicht (Ziel vs. Aktuell)")
    st.caption("Die Ampel zeigt dir auf einen Blick, wo Handlungsbedarf besteht.")
    st.dataframe(overview_df, use_container_width=True)

    _render_howto()
    sug_df = _render_suggestions(sug_df)

    st.divider()
    st.subheader("Export")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Übersicht als CSV",
            data=overview_df.to_csv(index=False).encode("utf-8"),
            file_name="orus_portfolio_overview.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Vorschläge als CSV",
            data=sug_df.to_csv(index=False).encode("utf-8"),
            file_name="orus_rebalancing_suggestions.csv",
            mime="text/csv",
            use_container_width=True,
        )
