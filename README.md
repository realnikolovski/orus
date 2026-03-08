# Orus – Portfolio Check & Rebalancing (MVP)

Orus ist eine kleine Streamlit-App zur Analyse eines Portfolios und zur Erkennung von Rebalancing-Bedarf.
Das Tool vergleicht **Soll-Gewichte (Ziel)** mit **Ist-Investitionen** und zeigt verständlich, wann und wie ein Portfolio angepasst werden sollte.

Das Projekt ist als **MVP (Minimum Viable Product)** aufgebaut und fokussiert auf eine einfache, nachvollziehbare Analyse.

---

# Features

* Portfolio mit mehreren Assets verwalten
* Marktdaten automatisch laden
* Analyse einzelner oder mehrerer Assets
* Vergleich der Asset-Performance
* Zielgewichte (Soll) definieren
* Investierte Beträge (Ist) erfassen
* Drift-Analyse zwischen Soll und Ist
* Rebalancing-Vorschläge (Kaufen / Verkaufen)
* Dashboard mit Portfolio-Übersicht

---

# Projektstruktur

```
orus/
│
├─ src/
│  ├─ app.py              # Hauptanwendung (Streamlit)
│  ├─ db.py               # Datenbankfunktionen
│  ├─ data_loader.py      # Laden von Marktdaten
│  ├─ analytics.py        # Analysefunktionen
│  └─ utils.py            # Hilfsfunktionen
│
├─ data/
│  └─ prices.db           # SQLite Datenbank
│
├─ requirements.txt       # Python Abhängigkeiten
└─ README.md
```

---

# Voraussetzungen

Installiert sein müssen:

* Python **3.10 oder neuer**
* Git

---

# Installation

Repository klonen:

```bash
git clone https://github.com/USERNAME/orus.git
cd orus
```

Virtuelle Umgebung erstellen (empfohlen):

Mac / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Abhängigkeiten installieren:

```bash
pip install -r requirements.txt
```

---

# Anwendung starten

Im Projektordner:

```bash
streamlit run src/app.py
```

Die App startet dann automatisch im Browser unter:

```
http://localhost:8501
```

---

# Nutzung der App

Empfohlener Ablauf:

1. **Portfolio**

   * Assets hinzufügen (z. B. Aktien oder ETFs)

2. **Daten**

   * Marktdaten laden / aktualisieren

3. **Gewichte (Ziel)**

   * Zielverteilung des Portfolios festlegen

4. **Investiert (Ist)**

   * Aktuell investierte Beträge eintragen

5. **Check & Rebalancing**

   * Drift zwischen Soll und Ist analysieren
   * Rebalancing-Vorschläge anzeigen

6. **Analyse**

   * Performance einzelner Assets oder Vergleiche

---

# Datenquelle

Die historischen Preisdaten werden über öffentliche Marktdaten geladen.
Die Daten werden lokal in einer **SQLite-Datenbank** gespeichert.

---

# Hinweis (MVP)

Dieses Projekt ist ein **Proof-of-Concept / MVP** und dient zur Demonstration von:

* Portfolioanalyse
* Rebalancing-Logik
* einfacher Datenanalyse mit Python
* Entwicklung einer Streamlit-App

Es handelt sich **nicht um eine Finanzberatung**.

---

# Lizenz

Dieses Projekt ist für Lern- und Demonstrationszwecke gedacht.
