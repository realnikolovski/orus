import pandas as pd
import streamlit as st

from db import (
    init_db,
    add_asset, remove_asset, load_assets,
    save_prices, load_prices,
    save_target_weight, load_target_weights,
    save_holding_value, load_holdings
)
from data_client import fetch_prices
from analytics import add_user_friendly_columns


# -----------------------------
# Basic UI setup
# -----------------------------
st.set_page_config(page_title="Orus", layout="wide")
init_db()

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


def header(title: str, subtitle: str = ""):
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.divider()


def pct(x: float) -> float:
    return float(x)


def safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def page_portfolio():
    header("Orus", "Portfolio verwalten (MVP)")

    st.subheader("Assets hinzufügen/entfernen")
    st.caption("Assets sind die Symbole, die du analysieren willst (z. B. AAPL.US).")

    left, right = st.columns([2, 1])

    with left:
        with st.container(border=True):
            st.markdown("**Asset hinzufügen**")
            preset = st.selectbox(
                "Vordefinierte Auswahl (optional)",
                ["—", "AAPL.US", "MSFT.US", "NVDA.US", "AMZN.US", "GOOGL.US", "TSLA.US", "SPY.US", "QQQ.US"],
            )
            custom = st.text_input("Oder eigenes Symbol eingeben", placeholder="z.B. AAPL.US")

            symbol_to_add = custom.strip() if custom.strip() else (preset if preset != "—" else "")

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


def page_data():
    header("Orus", "Marktdaten aktualisieren (MVP)")

    assets = load_assets()
    if len(assets) == 0:
        st.info("Keine Assets vorhanden. Gehe zu „Portfolio“ und füge Symbole hinzu.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.container(border=True):
            st.markdown("**Daten holen & speichern**")
            st.caption("Orus lädt Preisdaten und speichert die letzten N Tage in der Datenbank (SQLite).")

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
                        status.info(f"{sym}: gespeichert ({len(df)} Tage)")
                    except Exception as e:
                        fail += 1
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
            "Dieses MVP nutzt Stooq als Datenquelle (ohne API-Key). "
            "Viele US-Symbole funktionieren gut mit `.US` am Ende, z. B. `AAPL.US`, `MSFT.US`, `SPY.US`."
        )


def page_analysis():
    header("Orus", "Analyse – Entwicklung & Vergleich")

    assets = load_assets()
    if len(assets) == 0:
        st.info("Keine Assets vorhanden. Gehe zu „Portfolio“ und füge Symbole hinzu.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        selected = st.multiselect(
            "Welche Assets analysieren?",
            options=assets,
            default=[assets[0]] if assets else []
        )
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

    # --- Wir sammeln pro Asset: result_df (mit price + daily_change_pct) ---
    results = {}
    kpis = []

    for sym in selected:
        rows = load_prices(sym)
        if len(rows) == 0:
            st.warning(f"Keine Daten für {sym}. Bitte unter „Daten“ aktualisieren.")
            return

        df = pd.DataFrame(rows, columns=["symbol", "date", "close"]).sort_values("date")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # Zeitraum + Intervall
        df = df.tail(int(days_to_show)).copy()
        if int(step) > 1:
            df = df.iloc[:: int(step)].copy()

        # Falls durch Intervall zu wenig übrig bleibt:
        if len(df) < 2:
            st.warning(
                f"Für {sym} sind nach Zeitraum/Intervall nur {len(df)} Datenpunkt(e) übrig. "
                "Wähle mehr Tage oder ein kleineres Intervall."
            )
            return

        result = add_user_friendly_columns(df)
        result["date"] = pd.to_datetime(result["date"], errors="coerce")
        result = result.dropna(subset=["date"]).sort_values("date")

        results[sym] = result

        last_price = float(result["price"].iloc[-1])
        last_change = result["daily_change_pct"].iloc[-1]
        kpis.append({
            "Asset": sym,
            "Aktueller Preis": round(last_price, 2),
            "Veränderung zum Vortag (%)": None if pd.isna(last_change) else round(float(last_change), 2),
        })

    # --- KPI Tabelle ---
    st.subheader("Kurzübersicht")
    st.dataframe(pd.DataFrame(kpis), use_container_width=True)

    st.divider()

    # =========================
    # FALL 1: genau 1 Asset
    # =========================
    if len(selected) == 1:
        sym = selected[0]
        result = results[sym].set_index("date")

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
                show = results[sym][["date", "price", "daily_change_pct"]].copy()
                show = show.rename(columns={
                    "date": "Datum",
                    "price": "Preis",
                    "daily_change_pct": "Tägliche Veränderung (%)",
                })
                st.dataframe(show.tail(50), use_container_width=True)

        return

    # =========================
    # FALL 2: mehrere Assets
    # =========================
    # Hier NICHT concat(dict), sondern DataFrame(dict) => Spalten sind sauber die Symbole
    price_series = {sym: results[sym].set_index("date")["price"] for sym in selected}
    change_series = {sym: results[sym].set_index("date")["daily_change_pct"] for sym in selected}

    prices_df = pd.DataFrame(price_series).sort_index()
    change_df = pd.DataFrame(change_series).sort_index()

    # optional: Lücken füllen, damit Linien nicht abbrechen
    prices_df = prices_df.ffill()
    change_df = change_df.ffill()

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

def page_weights():
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
            # einfache Toleranz, damit Nutzer nicht an Rundung scheitert
            if total < 99.0 or total > 101.0:
                st.error("Die Summe sollte ungefähr 100% sein (z. B. 99% bis 101%).")
                return
            for sym, w in edited.items():
                save_target_weight(sym, w)
            st.success("Zielgewichte gespeichert.")


def page_holdings():
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


def page_check_rebalancing():
    header("Orus", "Portfolio-Check & Rebalancing (MVP)")

    assets = load_assets()
    if len(assets) == 0:
        st.info("Keine Assets vorhanden. Gehe zu „Portfolio“ und füge Symbole hinzu.")
        return

    target = load_target_weights()
    holdings = load_holdings()

    if len(target) == 0:
        st.info("Keine Zielgewichte gespeichert. Gehe zu „Gewichte (Ziel)“.")
        return

    if len(holdings) == 0:
        st.info("Keine investierten Beträge gespeichert. Gehe zu „Investiert (Ist)“.")
        return

    total_portfolio = sum(float(holdings.get(sym, 0.0)) for sym in assets)
    if total_portfolio <= 0:
        st.warning("Gesamt investiert ist 0€. Bitte unter „Investiert (Ist)“ Beträge eintragen.")
        return

    # -----------------------------
    # Einstellungen + Erklärung
    # -----------------------------
    with st.container(border=True):
        st.markdown("### Einstellungen (wann soll Orus handeln?)")
        st.write(
            "Orus vergleicht deine **Ziel-Verteilung** mit deiner **aktuellen Verteilung**. "
            "Wenn ein Asset zu stark abweicht, schlägt Orus vor, Geld umzuverteilen."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            drift_threshold_pp = st.slider(
                "Abweichung ab der gehandelt wird (Prozentpunkte)",
                0.5, 10.0, 2.0, 0.5
            )
        with c2:
            min_trade_eur = st.slider(
                "Min. Trade-Betrag (€)",
                0, 500, 50, 10
            )
        with c3:
            mode = st.selectbox(
                "Rebalancing-Stil",
                ["Zur Zielverteilung zurück (Standard)", "Sanft (nur 50% korrigieren)"]
            )

        with st.expander("Hilfe: Was sind „Prozentpunkte (pp)“?"):
            st.write(
                "**Prozentpunkte** sind die Differenz zwischen zwei Prozentwerten.\n\n"
                "Beispiel: Ziel 50%, aktuell 53% → Abweichung = **+3 pp**.\n"
                f"Mit einer Schwelle von **{drift_threshold_pp:.1f} pp** handelt Orus erst, "
                "wenn du klar über/unter deinem Ziel bist."
            )

    factor = 1.0 if mode.startswith("Zur") else 0.5

    # -----------------------------
    # Berechnung
    # -----------------------------
    overview_rows = []
    suggestions = []

    for sym in assets:
        target_pct = float(target.get(sym, 0.0))
        current_value = float(holdings.get(sym, 0.0))

        current_pct = 100.0 * current_value / total_portfolio
        drift_pp = current_pct - target_pct  # + = zu viel, - = zu wenig

        # Ampel-Logik (visuell)
        abs_drift = abs(drift_pp)
        if abs_drift <= drift_threshold_pp:
            traffic = "🟢 OK"
        elif abs_drift <= 2 * drift_threshold_pp:
            traffic = "🟡 Beobachten"
        else:
            traffic = "🔴 Handeln"

        # Zielwert in €
        target_value = (target_pct / 100.0) * total_portfolio
        needed_change_full = target_value - current_value  # + kaufen, - verkaufen
        trade_eur = needed_change_full * factor

        action = "OK"
        reason = "Im Toleranzbereich"

        if abs_drift > drift_threshold_pp:
            if trade_eur > 0:
                action = "Kaufen"
                reason = f"Zu niedrig gewichtet ({drift_pp:.1f} pp)"
            elif trade_eur < 0:
                action = "Verkaufen"
                reason = f"Zu hoch gewichtet (+{drift_pp:.1f} pp)"

        # Mindestbetrag
        if action != "OK" and abs(trade_eur) < min_trade_eur:
            action = "OK"
            reason = f"Trade wäre < {min_trade_eur}€"

        overview_rows.append({
            "Ampel": traffic,
            "Asset": sym,
            "Ziel (%)": round(target_pct, 1),
            "Aktuell (%)": round(current_pct, 1),
            "Abweichung (pp)": round(drift_pp, 1),
            "Investiert (€)": round(current_value, 2),
        })

        if action != "OK":
            suggestions.append({
                "Asset": sym,
                "Empfehlung": action,
                "Betrag (€)": round(abs(trade_eur), 2),
                "Begründung": reason,
            })

    overview_df = pd.DataFrame(overview_rows).sort_values("Abweichung (pp)", ascending=False)
    sug_df = pd.DataFrame(suggestions)

    # -----------------------------
    # Anzeige: Übersicht + Ampel
    # -----------------------------
    st.subheader("Übersicht (Ziel vs. Aktuell)")
    st.caption("Die Ampel zeigt dir auf einen Blick, wo Handlungsbedarf besteht.")
    st.dataframe(overview_df, use_container_width=True)

    # -----------------------------
    # Tutorial-Box: So setzt du es um
    # -----------------------------
    st.subheader("So setzt du die Vorschläge praktisch um (Schritt-für-Schritt)")
    with st.container(border=True):
        st.markdown(
            "1. **Verkaufen (wenn nötig)**: Verkaufe zuerst die Assets mit **„Verkaufen“**, damit Geld frei wird.\n"
            "2. **Kaufen**: Kaufe danach die Assets mit **„Kaufen“**.\n"
            "3. **Nicht übertreiben**: Wenn Trades sehr klein sind, ignoriere sie (dafür ist der Mindestbetrag da).\n"
            "4. **Danach prüfen**: Passe die „Investiert (Ist)“-Werte an und schau nochmal in den Check."
        )

        st.caption(
            "Hinweis: Dieses MVP rechnet ohne Gebühren/Steuern. In echt können kleine Trades unattraktiv sein."
        )

    # -----------------------------
    # Vorschläge
    # -----------------------------
    st.subheader("Rebalancing-Vorschläge")
    if sug_df.empty:
        st.success("Keine Trades nötig (alles im Toleranzbereich oder unter Mindestbetrag).")
    else:
        # Sinnvolle Sortierung: erst Verkäufe, dann Käufe
        order_map = {"Verkaufen": 0, "Kaufen": 1}
        sug_df["_order"] = sug_df["Empfehlung"].map(order_map).fillna(9)
        sug_df = sug_df.sort_values(["_order", "Betrag (€)"], ascending=[True, False]).drop(columns=["_order"])

        st.dataframe(sug_df, use_container_width=True)

        sells = sug_df[sug_df["Empfehlung"] == "Verkaufen"]["Betrag (€)"].sum()
        buys = sug_df[sug_df["Empfehlung"] == "Kaufen"]["Betrag (€)"].sum()

        st.info(
            f"Zusammenfassung: Verkaufen ≈ {sells:.2f}€, Kaufen ≈ {buys:.2f}€. "
            "Idealerweise finanzieren Verkäufe die Käufe (ohne Gebühren)."
        )

    # -----------------------------
    # Export
    # -----------------------------
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

def page_dashboard():
    header("Orus", "Dashboard – Überblick")

    assets = load_assets()
    target = load_target_weights()
    holdings = load_holdings()

    # --- Quick checks / guided UX ---
    if len(assets) == 0:
        st.info("Start: Gehe zu „Portfolio“ und füge mindestens ein Asset hinzu.")
        return

    if len(target) == 0:
        st.info("Nächster Schritt: Gehe zu „Gewichte (Ziel)“ und setze deine Ziel-Verteilung.")
        return

    if len(holdings) == 0:
        st.info("Nächster Schritt: Gehe zu „Investiert (Ist)“ und trage deine investierten Beträge ein.")
        return

    total_value = sum(float(holdings.get(sym, 0.0)) for sym in assets)
    if total_value <= 0:
        st.warning("Dein Gesamtwert ist 0€. Trage unter „Investiert (Ist)“ Werte ein.")
        return

    # --- Drift & Suggestions (gleiche Logik wie Rebalancing-Seite, aber kompakt) ---
    # Default-Einstellungen fürs Dashboard (ohne Regler)
    drift_threshold_pp = 2.0
    min_trade_eur = 50.0
    factor = 1.0  # Standard: zurück zum Ziel

    drift_rows = []
    suggestions = []

    for sym in assets:
        target_pct = float(target.get(sym, 0.0))
        current_value = float(holdings.get(sym, 0.0))
        current_pct = 100.0 * current_value / total_value
        drift_pp = current_pct - target_pct

        # Zielwert und Tradebedarf (voller Rebalance)
        target_value = (target_pct / 100.0) * total_value
        trade_eur = (target_value - current_value) * factor  # + kaufen, - verkaufen

        # Ampel für Dashboard (kurz)
        abs_drift = abs(drift_pp)
        if abs_drift <= drift_threshold_pp:
            traffic = "🟢"
        elif abs_drift <= 2 * drift_threshold_pp:
            traffic = "🟡"
        else:
            traffic = "🔴"

        drift_rows.append({
            "Ampel": traffic,
            "Asset": sym,
            "Ziel (%)": round(target_pct, 1),
            "Aktuell (%)": round(current_pct, 1),
            "Abweichung (pp)": round(drift_pp, 1),
        })

        # Vorschläge zählen (nur wenn über Threshold + min trade)
        if abs_drift > drift_threshold_pp and abs(trade_eur) >= min_trade_eur:
            action = "Kaufen" if trade_eur > 0 else "Verkaufen"
            suggestions.append({
                "Asset": sym,
                "Empfehlung": action,
                "Betrag (€)": round(abs(trade_eur), 2),
            })

    drift_df = pd.DataFrame(drift_rows)
    if not drift_df.empty:
        max_abs_drift = float(drift_df["Abweichung (pp)"].abs().max())
    else:
        max_abs_drift = 0.0

    sug_df = pd.DataFrame(suggestions)

    # --- Daten-Status: grob prüfen, ob Preise vorhanden sind ---
    # (Einfach: checke, ob zumindest für ein Asset Preiszeilen existieren)
    assets_with_prices = 0
    for sym in assets:
        if len(load_prices(sym)) > 0:
            assets_with_prices += 1

    # --- KPI Cards ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Gesamtwert", f"{total_value:,.2f} €".replace(",", " "))
    k2.metric("Assets", str(len(assets)))
    k3.metric("Max. Abweichung", f"{max_abs_drift:.1f} pp")
    k4.metric("Vorschläge", str(len(sug_df)))

    st.divider()

    # --- Callouts / next action ---
    if assets_with_prices < len(assets):
        st.warning(
            f"Marktdaten fehlen für {len(assets) - assets_with_prices} Asset(s). "
            "Gehe zu „Daten“ und aktualisiere."
        )
    elif len(sug_df) == 0:
        st.success("Alles im grünen Bereich: Keine sinnvollen Rebalancing-Trades nötig (bei Standard-Schwellen).")
    else:
        st.info("Es gibt Rebalancing-Vorschläge. Gehe zu „Check & Rebalancing“ für Details und Anleitung.")

    # --- Compact tables ---
    left, right = st.columns([2, 1])

    with left:
        with st.container(border=True):
            st.markdown("**Übersicht: Ziel vs. Aktuell (Ampel)**")
            # sortiere nach stärkster Abweichung
            drift_show = drift_df.sort_values("Abweichung (pp)", key=lambda s: s.abs(), ascending=False)
            st.dataframe(drift_show, use_container_width=True)

    with right:
        with st.container(border=True):
            st.markdown("**Top-Vorschläge**")
            if sug_df.empty:
                st.write("Keine Trades nötig.")
            else:
                # sortiere nach Betrag
                top = sug_df.sort_values("Betrag (€)", ascending=False).head(6)
                st.dataframe(top, use_container_width=True)

    st.divider()

    with st.expander("Was bedeutet die Ampel?"):
        st.write(
            "🟢 **OK**: Abweichung ist klein (Standard: ≤ 2 pp)\n\n"
            "🟡 **Beobachten**: merkbare Abweichung (ca. 2–4 pp)\n\n"
            "🔴 **Handeln**: deutliche Abweichung (> 4 pp)\n\n"
            "Du kannst die genauen Einstellungen unter „Check & Rebalancing“ anpassen."
        )



# -----------------------------
# Sidebar navigation
# -----------------------------
with st.sidebar:
    st.markdown("## Orus")
    st.caption("Portfolio-Check (MVP)")
    st.divider()

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

if page == "Dashboard":
    page_dashboard()
elif page == "Portfolio":
    page_portfolio()
elif page == "Daten":
    page_data()
elif page == "Analyse":
    page_analysis()
elif page == "Gewichte":
    page_weights()
elif page == "Investiert":
    page_holdings()
elif page == "Rebalancing":
    page_check_rebalancing()

