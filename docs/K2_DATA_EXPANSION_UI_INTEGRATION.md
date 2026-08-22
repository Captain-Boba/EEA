# K2-Auftrag: Daten-Erweiterung in die Atlas-Oberfläche einbinden

> **Archivierter Arbeitsauftrag vom 14. August 2026.** Dieser Text dokumentiert
> die damalige Übergabe an K2 und ist keine aktuelle Implementierungsanleitung.
> HEAD, Testzahl und Arbeitsstand in Abschnitt 2 sind historische Angaben. Für
> den gegenwärtigen Stand gelten `README.md`, `ROADMAP.md`,
> `TIMESERIES_COMPARISON.md`, `MAP_ASSET.md` und die ausführbaren Tests.

## 1. Ziel

Die bereits implementierten fünf Ableitungen sowie die neuen Eurostat-, EEA- und JRC-Daten so in die bestehende Atlas-Oberfläche einbinden, dass Nutzer sie nach Land und Zeitraum auffinden, vergleichen und fachlich korrekt einordnen können. K2 bearbeitet ausschließlich die UI-/API-Einbindung und die zugehörigen Tests; Importlogik, Formeln und reale Quelldaten bleiben geschützt.

## 2. Verbindlicher Ausgangsstand

- Repository: `E:\EEA`
- Branch: `main`
- HEAD beim Erstellen dieses Auftrags: `79de95c85fad1e60ea51b3449902891ef67f8a35`
- Der Auftrag basiert **nicht allein auf HEAD**, sondern auf dem derzeitigen uncommitteten Arbeitsstand. Vor Beginn ist zu prüfen, dass die unten genannten neuen und geänderten Dateien vorhanden sind.
- Die lokale Datenbank `data/atlas.sqlite3` gehört zum Abnahmestand, ist jedoch kein von K2 zu bearbeitendes Artefakt.
- Referenzdatenbank beim Erstellen dieses Auftrags:
  - SHA-256: `edde470db65e9ec39c888a858955e731d5fa4f3ec741f6bec78e52bbb340dde9`
  - SQLite-Integritätsprüfung: `ok`
  - 121.908 Beobachtungen aus Ember (114.027), Eurostat (5.624), Battery-Charts (1.680), JRC (307) und EEA (270)
  - 50 physisch gespeicherte und 72 katalogisierte Kennzahlen
- Offline-Baseline: `PYTHONPATH=src python -m unittest discover -s tests -v` lief vor Übergabe mit 88 erfolgreichen Tests.
- Es wurde nichts gestaged, committed, gepusht, getaggt oder veröffentlicht.

### Bereits implementiert und von K2 nur zu konsumieren

- Fünf Ableitungen:
  - `renewable_per_capita_mwh`
  - `low_carbon_share_pct`
  - `self_sufficiency_pct`
  - `estimated_generation_emissions_mtco2eq`
  - `decarbonization_rate_pct`
- Elektromobilität:
  - `bev_stock`
  - `bev_new_registrations`
  - `ev_battery_nominal_capacity_est_gwh`
- Eurostat-Erweiterungen: installierte Leistungen, jährliche Haushalts- und Nicht-Haushaltsstrompreise samt Komponenten, Bruttoimporte und Bruttoexporte.
- EEA-Treibhausgasinventar: `eea_ghg_1a1a_mtco2eq` für IPCC-Kategorie 1.A.1.a.
- JRC-Wasserkraftinventar als Snapshot:
  - `hydro_plant_capacity_gw`
  - `hydro_pumping_power_gw`
  - `hydro_reservoir_energy_gwh`
- `/api/metrics`, `/api/summary`, `/api/compare` und `/api/storage` liefern die erforderlichen Daten und Metadaten bereits aus.
- Karte und Zeitreihenvergleich sind kataloggetrieben. Neue Jahreskennzahlen werden dadurch grundsätzlich bereits angeboten; Snapshot-Kennzahlen sind bewusst nicht im Zeitreihenvergleich.

## 3. Arbeitskopie und Dateieigentum

Vor jeder Änderung ausführen und im Feedback festhalten:

```powershell
git status --short
git diff -- web/app.js tests/test_frontend_timeseries.py
```

Folgende Änderungen sind bereits vorhanden und dürfen nicht verloren gehen:

- `ROADMAP.md`: bestehende Nutzeränderung; für K2 vollständig geschützt.
- `web/app.js` und `tests/test_frontend_timeseries.py`: bereits vorhandene Arbeiten an kontrastreichen Zeitreihenfarben.
- In `web/app.js` ist außerdem der Snapshot-Hinweis bereits auf kennzahlspezifische Datenstände verallgemeinert.

K2 darf `web/app.js` und `tests/test_frontend_timeseries.py` nur mit kleinen, lokal begrenzten Patches bearbeiten. Die Farbpalette, `MIN_CHART_COLOR_DISTANCE`, `assignCountryColors`, `colorDistance` und die zugehörigen Erwartungen werden nicht umgebaut. Wenn diese Dateien parallel anderweitig bearbeitet werden, Arbeit stoppen und die Eigentümerschaft mit K1 klären; keine automatisierte Komplettformatierung oder großflächige Ersetzung.

### Geschützte Implementierung

Ohne nachgewiesenen Integrationsfehler nicht ändern:

- `src/electricity_atlas/eea_ghg_importer.py`
- `src/electricity_atlas/eurostat_supplement.py`
- `src/electricity_atlas/hydro_importer.py`
- Import- und Ableitungslogik in `src/electricity_atlas/ember_aggregation.py`
- Quellkonfiguration in `src/electricity_atlas/config.py`
- Datenbankschema und reale Datenbank `data/atlas.sqlite3`
- `tests/test_data_expansion.py`

Ein vermuteter Fehler in diesem geschützten Bereich wird reproduzierbar dokumentiert und an K1 zurückgegeben, nicht im Vorbeigehen behoben.

## 4. Exakter Arbeitsumfang

### A. Kataloggetriebene Einbindung verifizieren und vervollständigen

1. Sicherstellen, dass alle neuen Jahreskennzahlen in der Karte in ihrer vorgesehenen Gruppe und Familie auswählbar sind.
2. Sicherstellen, dass alle vergleichbaren neuen Jahreskennzahlen im Zeitreihenvergleich auswählbar sind.
3. Bei Auswahl einer nur jährlich verfügbaren Kennzahl aus der Monatsansicht muss die bestehende automatische Umschaltung auf `Jahr` erhalten bleiben.
4. Die drei JRC-Wasserkraftinventar-Kennzahlen bleiben Snapshot-Kennzahlen: Karte ja, Zeitreihe nein, Anzeige mit ihrem je Kennzahl ausgewiesenen Datenstand.
5. Fehlende Werte werden immer als `—` dargestellt. K2 darf keine Vorjahreswerte fortschreiben und keinen „letzten verfügbaren Wert“ in den gewählten Zeitraum hineinziehen.

### B. Elektromobilität sichtbar einbinden

Eine eigene, kompakte Ranking-Tabelle **„Elektromobilität“** unterhalb des Stromsystem-Rankings und vor dem Zeitreihenvergleich ergänzen. Sie verwendet den aktuell gewählten Jahreszeitraum und zeigt:

- batterieelektrische Pkw im Bestand,
- neue batterieelektrische Pkw,
- theoretische nominale EV-Batteriekapazität in GWh.

Die Tabelle folgt den vorhandenen Tabellenmustern:

- Top 10 nach aktiver Sortierung, optional „Alle Länder anzeigen“;
- Rang wird nach jeder Sortierung neu berechnet;
- Zahlen und Tabellenzellen bleiben zentriert und nutzen die Präzision aus dem Metrikkatalog;
- in der Monatsansicht wird die Tabelle nicht mit Jahreswerten vermischt, sondern mit einem eindeutigen Hinweis deaktiviert oder verborgen;
- Werte für ein gewähltes Jahr bleiben leer, wenn Eurostat sie für Land/Jahr nicht liefert.

Direkt an der Tabelle muss fachlich eindeutig stehen:

> Theoretische nominale Batteriekapazität = BEV-Bestand × 60 kWh. Das ist weder nutzbare Energie noch eine V2G- oder netzverfügbare Speicherkapazität.

Die 60-kWh-Annahme darf nicht als Eingabe, konfigurierbarer Faktor oder beobachteter Quellenwert erscheinen.

### C. Quellen- und Definitionshinweise aktualisieren

Die vorhandenen Bereiche „Datenquellen und Herkunft“ sowie „Definitions- und Coverage-Hinweise“ in `web/index.html` um die tatsächlich eingebundenen Daten erweitern:

- Eurostat: installierte Leistung, Preisbestandteile, Bruttohandel sowie BEV-Bestand und Neuzulassungen zusätzlich zu Bevölkerung/BIP;
- EEA: Treibhausgasinventar, Kategorie 1.A.1.a; sichtbar erläutern, dass diese Kategorie öffentliche Strom- **und Wärmeerzeugung** umfasst und kein reiner Stromwert ist;
- JRC-Wasserkraftinventar: statischer Anlagen-Snapshot, getrennt vom bereits vorhandenen Storage-Inventory-Abruf; nur direkt berichtete Speicherenergie, fehlende Energie bleibt fehlend;
- Ableitungen: neutral und knapp erklären, insbesondere Vorzeichen der Dekarbonisierungsrate und Charakter der geschätzten Erzeugungsemissionen.

Quellenlinks und bereits vorhandene Lizenztexte nicht entfernen. Keine weitergehende Lizenzfreigabe behaupten.

### D. Kontext in Karte und Vergleich

- Für Elektromobilität, EEA-Emissionen und JRC-Wasserkraft muss Quelle, Einheit, Zeitraum/Datenstand und Fehlstatus in der vorhandenen Karten-Detailansicht korrekt erscheinen.
- Kartenlegende und Kartenexport müssen weiterhin Kennzahl, Einheit und aktuell gewählte Darstellung widerspiegeln.
- Im Zeitreihenvergleich müssen Jahreskennzahlen Jahresfelder und Jahres-Presets verwenden. Snapshot-Kennzahlen dürfen dort nicht erscheinen.
- Die bestehende Europakarten-Geometrie und der Ausschnitt bleiben unverändert.

### E. Tests

Tests auf Vertrags- und DOM-Ebene ergänzen. Mindestens abdecken:

1. Die EV-Tabelle enthält genau die drei vorgesehenen Kennzahlen und berechnet Ränge nach jeder Sortierung neu.
2. Monatsansicht mischt keine Jahres-EV-Werte ein.
3. `null` bleibt `—`; insbesondere wird ein fehlender 2025-Wert nicht mit 2024 befüllt.
4. `ev_battery_nominal_capacity_est_gwh` ist als Schätzung mit 60-kWh-Hinweis gekennzeichnet.
5. JRC-Wasserkraftinventar bleibt Snapshot-only und ist im Zeitreihenvergleich ausgeschlossen.
6. EEA 1.A.1.a wird als Strom- und Wärmeerzeugung beschrieben.
7. Die vorhandenen Farbkontrast-Tests für zehn Länder bleiben unverändert grün.
8. Neue Steuerelemente sind per Tastatur bedienbar und haben sinnvolle Beschriftungen/Statusrollen.

## 5. Fachliche Referenzwerte für die Abnahme

Diese Werte dienen der Integrationsprüfung gegen die übergebene lokale Datenbank; sie sind keine Anweisung, Werte im Frontend fest zu codieren:

- Deutschland 2025:
  - BEV-Bestand: `2.034.260`
  - BEV-Neuzulassungen: `545.142`
  - theoretische nominale Kapazität: `122,0556 GWh`
- Vereinigtes Königreich:
  - 2025 bleibt bei den EV-Kennzahlen fehlend;
  - 2024 ist der jüngste vorhandene Wert.
- Gemeinsamer Länderschnitt 2024:
  - 31 Länder
  - 8.026.091 BEV
  - 481,56546 GWh theoretische nominale Kapazität
- JRC-Wasserkraftinventar: Datenstand `2023-10-25`; kein Umschreiben auf das aktuell gewählte Kalenderjahr.
- EEA-Reihe: 2015 bis 2024; 2025 bleibt fehlend.

## 6. Nicht-Ziele

- Keine neuen Datenquellen, Datensätze, Metriken oder Formeln.
- Keine erneuten Live-Imports und keine Netzwerkzugriffe für Tests.
- Keine Änderung der 60-kWh-Annahme.
- Keine Addition von EV-Batterien zu stationären Batterie- oder Pumpspeicherwerten.
- Keine pauschale Erweiterung der bestehenden Stromsystem-Haupttabelle um alle 72 Metriken.
- Kein automatisches Springen auf den letzten vollständigen Zeitraum.
- Keine Ersetzung fehlender oder negativer Residualwerte durch null.
- Kein Redesign der Karte, keine Änderung des Europa-Ausschnitts und kein Umbau der Zeitreihenfarben.
- Keine Migration, kein Schemawechsel und keine Änderung der Importtransaktionen.
- Kein Staging, Commit, Merge, Push, Tag oder Release ohne neuen ausdrücklichen Auftrag.

## 7. Abnahmekriterien

Der Auftrag ist erfüllt, wenn alle folgenden Punkte nachweisbar sind:

- Die fünf Ableitungen und die neuen Eurostat-/EEA-Jahreskennzahlen sind in Karte und – soweit `compare=true` – im Zeitreihenvergleich auffindbar.
- Die drei JRC-Wasserkraftmetriken sind mit dem korrekten Snapshot-Datum auf der Karte, aber nicht im Zeitreihenvergleich verfügbar.
- Die EV-Ranking-Tabelle funktioniert für Jahresansichten, sortiert/rankt korrekt und zeigt fehlende Werte ohne Fortschreibung.
- EV-Kapazität ist in jeder relevanten UI-Erklärung als theoretische nominale Schätzung und ausdrücklich nicht als V2G-/Netzspeicher gekennzeichnet.
- EEA 1.A.1.a wird nicht als reine Stromerzeugung missverstanden.
- Auswahl eines Jahres ohne Quellenwert bleibt leer; insbesondere UK-EV 2025 und EEA 2025.
- Bestehende Tabellen-, Karten-, Export-, Vergleichs- und Farbkontrastfunktionen regressieren nicht.
- Die Darstellung ist bei üblicher Desktopbreite und schmalem mobilen Viewport ohne abgeschnittene Bedienelemente nutzbar.
- Alle unten genannten Offline-Prüfungen sind grün.

## 8. Verifikation

Aus PowerShell im Repository:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -p "test_data_expansion.py" -v
python -m unittest discover -s tests -p "test_map.py" -v
python -m unittest discover -s tests -p "test_frontend_timeseries.py" -v
python -m unittest discover -s tests -v
python -m compileall -q src tests
node --check web/app.js
git diff --check
git status --short
```

Für die manuelle UI-Abnahme darf K2 den lokalen Server mit der bereits übergebenen Datenbank starten:

```powershell
$env:PYTHONPATH='src'
python -m electricity_atlas --db data/atlas.sqlite3 serve --port 8765
```

Manuell prüfen:

- Jahresansicht 2025: Deutschland-EV-Werte stimmen, UK bleibt leer.
- Jahresansicht 2024: UK-EV-Werte erscheinen.
- Monatsansicht: EV-Tabelle zeigt keine Jahreswerte.
- Karte: je eine neue Jahreskennzahl, EEA 1.A.1.a und JRC-Wasserkraftinventar auswählen; Einheit, Legende, Datenstand und Fehlwerte prüfen.
- Zeitreihe: eine neue Jahreskennzahl vergleichen und CSV/SVG/PNG prüfen; JRC-Snapshot ist nicht auswählbar.
- Desktop und schmaler Viewport; Tastaturbedienung und Fokusführung prüfen.

Diese manuelle Prüfung ist K2-Abnahmeevidenz, keine Produktions- oder Releasefreigabe.

## 9. Pflicht-Rückmeldung von K2

K2 liefert am Ende kompakt und vollständig:

1. geänderte Dateien;
2. kurze Beschreibung der UI-/Datenflusslösung;
3. Bestätigung, wie vorhandene Farbänderungen und geschützte Importlogik erhalten wurden;
4. exakte Testbefehle mit Ergebnis und Testanzahl;
5. Ergebnis der manuellen Prüfpunkte, getrennt nach Desktop und schmalem Viewport;
6. bekannte Risiken, Restpunkte oder Abweichungen;
7. `git status --short`;
8. `git diff --stat` und `git diff --check`;
9. ausdrückliche Angabe, dass nichts gestaged, committed, gepusht, getaggt oder veröffentlicht wurde.

Bei einem Widerspruch zwischen UI-Wunsch und bestehendem API-/Datenvertrag stoppt K2 an der kleinstmöglichen Stelle und meldet den konkreten Datensatz, Endpunkt, Zeitraum und reproduzierbaren Fehler an K1.
