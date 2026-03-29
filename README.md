# Orus – Portfolio Check & Rebalancing (MVP)

Orus ist eine Streamlit-App für schnelle Portfolio-Checks: Zielgewichte vs. Ist-Beträge vergleichen, Abweichungen sehen und einfache Rebalancing-Vorschläge erhalten. Fokus: leicht nachvollziehbar, lokal lauffähig, ohne API-Keys.

---

## Features (Kurzfassung)

- Portfolio-Assets verwalten (Anlegen/Löschen)
- Kurse per **yfinance** laden und lokal (SQLite) speichern
- Analyse je Asset oder im Vergleich (interaktive Altair-Charts, 30d-Volatilität)
- Zielgewichte (Soll) und Ist-Beträge pflegen
- Drift-Berechnung und Rebalancing-Vorschläge (Kaufen/Verkaufen) mit CSV-Export
- Dashboard mit Ampelindikatoren und Top-Vorschlägen
- Logging in Datei und Konsole (konfigurierbar)

---

## Stack

- Python 3.10+
- Streamlit
- pandas
- yfinance
- Altair (Charts)
- SQLite (lokale DB)

---

## Projektstruktur

```
orus/
├─ README.md
├─ requirements.txt
├─ orus.db              # SQLite Datenbank (wird bei Bedarf angelegt)
└─ src/
   ├─ main.py           # App-Start (Streamlit Router + Logging)
   ├─ config.py         # Basis-Konfig (DB-Pfad, Log-Level/-File)
   ├─ logging_utils.py  # Logging-Setup
   ├─ db.py             # DB-Zugriffe
   ├─ data_client.py    # Kurs-Download via yfinance
   ├─ analytics.py      # Hilfsfunktionen (z. B. pct_change)
   └─ pages/            # Streamlit-Seiten
      ├─ dashboard.py
      ├─ portfolio.py
      ├─ data.py
      ├─ weights.py
      ├─ holdings.py
      ├─ rebalancing.py
      ├─ analysis.py
      └─ common.py
```

---

## Installation

Repository klonen:

```bash
git clone https://github.com/realnikolovski/orus.git
cd orus
```

Virtuelle Umgebung (empfohlen):

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Mac/Linux
source .venv/bin/activate
```

Abhängigkeiten installieren:

```bash
pip install -r requirements.txt
```

---

## Start der Anwendung

Im Projektordner:

```bash
streamlit run src/main.py
```

Standard: http://localhost:8501 (Streamlit zeigt den genauen Port an).

---

## Empfohlener Ablauf in der App

1) **Portfolio**: Assets anlegen (Ticker ohne `.US`, z. B. AAPL, NVDA, SPY).
2) **Daten**: Kurse via yfinance laden und speichern.
3) **Gewichte (Ziel)**: Soll-Gewichte in % hinterlegen.
4) **Investiert (Ist)**: Aktuell investierte Euro-Beträge eintragen.
5) **Check & Rebalancing**: Abweichungen prüfen, Vorschläge einsehen/exportieren.
6) **Analyse**: Preisverlauf, tägliche Changes, 30d-Volatilität und Multi-Asset-Vergleich.

---

## Konfiguration (optional über Umgebungsvariablen)

- `ORUS_DB_PATH` – Pfad zur SQLite-Datei (Default: `orus.db`).
- `ORUS_LOG_LEVEL` – Log-Level, z. B. `INFO` oder `DEBUG` (Default: `INFO`).
- `ORUS_LOG_FILE` – Log-Datei (Default: `orus.log`).

---

## Datenquelle

- Kursdaten: **yfinance** (keine API-Keys nötig). Bitte gängige Ticker ohne `.US` nutzen.
- Speicherung: lokale SQLite-DB (`prices`, `assets`, `target_weights`, `holdings`).

---

## Entwicklung & Qualität

- Code-Style: flake8

```bash
python -m flake8 src
```

- Tests: aktuell keine automatischen Tests vorhanden. Manuelle Smoke-Tests über die App (Daten laden → Analyse → Rebalancing) empfohlen.

---

## Hinweis (MVP)

Orus ist ein Lern-/Demo-Projekt. Keine Finanzberatung. Daten können unvollständig oder verspätet sein.

---

## Lizenz

Nur für Lern- und Demonstrationszwecke.
