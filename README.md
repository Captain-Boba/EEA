# European Electricity Atlas – Data Core v0.1

Lokale Datenpipeline für 31 europäische Atlasländer. Ember liefert vergleichbare Monats- und Jahreswerte für Erzeugung, Nachfrage, Energiemix, Nettoimporte, CO₂-Intensität und Großhandelspreise. Eurostat ergänzt jährliche Bevölkerung und BIP-Kennzahlen. Speicher-Snapshots aus dem JRC European Energy Storage Inventory werden ausschließlich aus einer manuell heruntergeladenen und geprüften CSV übernommen.

## Voraussetzungen und Installation

- Python 3.11 oder neuer
- Internetzugang nur für Ember- und Eurostat-Importe

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Es gibt keine Laufzeitabhängigkeiten außerhalb der Python-Standardbibliothek.

## Ember-Zugang und Stromdaten

Der API-Schlüssel wird zuerst aus `EMBER_API_KEY` und andernfalls aus der lokalen, ignorierten Datei `EMBER_API_KEY.txt` gelesen. Er wird nie ausgegeben oder in SQLite gespeichert; gespeicherte Request-URLs enthalten ausschließlich `api_key=REDACTED`.

```powershell
$env:EMBER_API_KEY="<API-Key>"
eea import --year 2025
eea import --from-year 2015
eea import --year 2025 --countries DE FR ES UK
eea import --year 2025 --months 1 7
```

Der historische Cache wird wiederverwendet. `--refresh` erzwingt den erneuten Abruf und atomaren Ersatz des ausdrücklich angeforderten Zeitraums. Die Weboberfläche führt keine Importe aus.

Nationale monatliche Großhandelspreise benötigen keinen API-Key:

```powershell
eea import-prices
```

Der Preisimport prüft Header, den 31-Länder-Katalog, ISO3-Codes, Monatsschlüssel und endliche numerische Werte vor dem atomaren Ersatz. Albanien kann in der unveränderten Ember-Rohdatei vorkommen, wird aber nicht in die Atlas-Faktentabelle übernommen. Leere Preiszellen bleiben fehlende Coverage. Der laufende Monat ist vorläufig; Jahrespreise werden nach tatsächlicher Monatsdauer gewichtet und nur mit zwölf abgeschlossenen Monaten vollständig ausgewiesen.

## Eurostat-Jahresdaten

```powershell
eea import-eurostat --from-year 2015
```

Der Import ruft nacheinander genau drei Datensätze ab:

- `demo_gind`: Bevölkerung am Jahresanfang
- `nama_10_gdp`: BIP zu laufenden Preisen
- `nama_10_pc`: BIP pro Kopf in Kaufkraftstandards

Es läuft höchstens eine Eurostat-Anfrage gleichzeitig. Temporäre Fehler und HTTP 429 werden mit begrenztem Backoff und `Retry-After` behandelt. Erst nachdem alle drei Antworten strukturell und numerisch validiert wurden, werden Faktentabelle und Rohcache atomar ersetzt.

Das entspricht Eurostats [Fair-Use-Empfehlung](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/asynchronous-api): eine Extraktionsanfrage zur Zeit und keine Parallelisierung. Eurostat erlaubt die Wiederverwendung statistischer Daten grundsätzlich mit Quellenangabe. Die [Eurostat-Ausnahmen](https://ec.europa.eu/eurostat/help/copyright-notice) schließen die kommerzielle Wiederverwendung bestimmter Daten für Länder außerhalb EU, EFTA sowie Beitritts- und Kandidatenländern aus. Das betrifft insbesondere die UK-Werte und muss vor einer kommerziellen Veröffentlichung separat geklärt oder ausgeschlossen werden.

Erzeugung und Verbrauch pro Kopf werden nur in der Jahresansicht und ausschließlich aus Ember-Stromwert und Eurostat-Bevölkerung desselben Kalenderjahres berechnet. Bei fehlender Eurostat-Coverage bleibt der Wert leer; ein anderes Jahr wird nicht als Ersatz benutzt.

## JRC-Speicher-Snapshot

Das interaktive JRC-Dashboard wird nicht automatisiert abgefragt. Für den regulären Import werden zwei gefilterte Diagrammexporte verwendet: `Power (GW)` und `Capacity (GWh)` nach Land, jeweils mit `Project status = Operational` und `Technology = Mechanical + Electrochemical`. Der auf dem Dashboard sichtbare Aktualisierungstag wird ausdrücklich mitgegeben:

```powershell
eea import-storage `
  --power-file .\data\imports\jrc-power.xlsx `
  --capacity-file .\data\imports\jrc-capacity.xlsx `
  --snapshot-date 2026-08-11
```

Die XLSX-Dateien müssen exakt die drei Exportspalten `Country`, `Project status` und `Power (GW)` beziehungsweise `Capacity (GWh)` besitzen. Nicht zum Atlas gehörende, bekannte Exportländer werden ignoriert; neue unbekannte Ländernamen lösen einen vollständigen Importabbruch aus. Länder ohne Exportzeile bleiben leer.

Alternativ bleibt das geprüfte CSV-Austauschformat verfügbar:

```powershell
eea import-storage --file .\data\imports\jrc-storage-reviewed.csv
```

Die CSV muss exakt diese Spalten besitzen:

```text
Country Code,Snapshot Date,Project Status,Technology,Subtechnology,Power (MW),Capacity (MWh)
```

Eine leere Vorlage liegt unter `docs/JRC_STORAGE_IMPORT_TEMPLATE.csv`. Leistung und Energie werden getrennt gespeichert; die Speicherdauer wird als `GWh/GW` abgeleitet. Die unveränderten XLSX-Dateien werden Base64-kodiert samt Dateiname, SHA-256 und Importzeitpunkt im Rohcache erhalten. JRC-Daten können Schätzungen und Inhalte externer Anbieter enthalten und müssen vor einer öffentlichen oder kommerziellen Weitergabe gesondert lizenzrechtlich geprüft werden.

Quelle und Disclaimer: [JRC European Energy Storage Inventory](https://ses.jrc.ec.europa.eu/storage-inventory). Das Dashboard nennt neben öffentlichen Daten ausdrücklich Wood Mackenzie und weist geschätzte Kapazitäten aus. Deshalb gibt es absichtlich keinen automatischen Dashboard-Scraper.

## Migration älterer Datenbanken

```powershell
eea migrate-atlas
```

Der Befehl entfernt Albanien, unbekannte Quellen, albanische Ember-API-Caches und obsolete Intervalltabellen. Ember-, Eurostat- und JRC-Daten der 31 Atlasländer bleiben erhalten. Der alte Name `migrate-ember-only` funktioniert vorübergehend als versteckter Alias.

## Serverstart

```powershell
eea serve --port 8765
```

Danach [http://127.0.0.1:8765](http://127.0.0.1:8765) öffnen. `Strg+C` beendet den Server; erscheint wieder `PS E:\EEA>`, ist er beendet.

## API

- `/api/countries`
- `/api/metrics`
- `/api/summary?year=2025`
- `/api/summary?year=2025&month=7`
- `/api/compare?year=2025&countries=DE,FR`
- `/api/coverage?year=2025`
- `/api/storage`

Die Summary bleibt eine Ember-Stromsicht mit transparent ergänzten, jahresgleichen Eurostat-Denominatoren. `source=ember` ist zulässig; unbekannte oder automatisch vermischte Quellsichten werden abgelehnt. Speicher-Snapshots besitzen einen separaten Endpunkt.

## Datenmodell

`period_observation` ist die kanonische Faktentabelle. Der Monat ist die kleinste Strom- und Preiseinheit; geprüfte Jahreswerte und JRC-Snapshots werden separat gespeichert. `api_cache` enthält redigierte Ember-JSON-Antworten. `source_cache` enthält Ember-Preis-CSV, Eurostat-JSON und die manuell geprüfte JRC-Austauschdatei samt Provenienz und SHA-256.

- Erzeugung, Nachfrage und Nettoimporte: TWh
- Preis: EUR/MWh
- CO₂-Intensität: gCO₂eq/kWh
- Speicherleistung: GW
- Speicherenergie: GWh

Positive Nettoimporte bedeuten Importüberschuss, negative Werte Exportüberschuss. Die Nettoimportquote ist `Nettoimporte / Verbrauch × 100`. Fehlende Werte bleiben `null` und werden weder als Null erfunden noch aus einem anderen Zeitraum ergänzt.

## Tests

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
git diff --check
```

## Bekannte Einschränkungen

- Einzelne historische Land-Monat-Kombinationen können reguläre Coverage-Lücken besitzen.
- Bruttoimport, Bruttoexport, negative Preisstunden und operative Intervallstatistiken sind nicht Teil des Monatsatlas.
- Der Ember-Endpunkt für Jahresnachfrage kann fehlen; ein Jahreswert wird nur aus genau zwölf Monatswerten abgeleitet.
- Aktuelle Monate und Jahre können vorläufig sein und später revidiert werden.
- JRC-Speicherwerte sind ein fachlich geprüfter Snapshot, keine automatisch aktualisierte Zeitreihe.

Weitere Details: [Ember-Abdeckung](docs/EMBER_COVERAGE.md).
