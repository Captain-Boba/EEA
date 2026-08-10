# European Electricity Atlas – Data Core v0.1

Lokale Ember-Datenpipeline für 32 europäische Atlasländer. Die Anwendung importiert vergleichbare Monats- und Jahreswerte für Erzeugung, Nachfrage, Energiemix, CO₂-Intensität und nationale Großhandelspreise, speichert Quellantworten nachvollziehbar in SQLite und stellt sie über eine lokale Weboberfläche bereit.

## Voraussetzungen und Installation

- Python 3.11 oder neuer
- Internetzugang nur für Datenimporte

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Es gibt keine Laufzeitabhängigkeiten außerhalb der Python-Standardbibliothek.

## Ember-Zugang

Der API-Schlüssel wird zuerst aus `EMBER_API_KEY` und andernfalls aus der lokalen, ignorierten Datei `EMBER_API_KEY.txt` gelesen. Er wird nie ausgegeben oder in SQLite gespeichert; gespeicherte Request-URLs enthalten ausschließlich `api_key=REDACTED`.

```powershell
$env:EMBER_API_KEY="<API-Key>"
```

## Datenimport

Einzeljahr für alle 32 Länder:

```powershell
eea import --year 2025
```

Vollständige Atlas-Historie ab 2015 bis zum laufenden Jahr:

```powershell
eea import --from-year 2015
```

Ausgewählte Länder oder Monate:

```powershell
eea import --year 2025 --countries DE FR ES UK
eea import --year 2025 --months 1 7
```

Nationale monatliche Großhandelspreise werden ohne API-Key aus Embers Preis-CSV importiert:

```powershell
eea import-prices
```

Der Preisimport validiert Header, 32-Länder-Katalog, ISO3-Codes, Monatsschlüssel und endliche numerische Preise, bevor Cache und Monatswerte atomar ersetzt werden. Leere Preiszellen bleiben fehlende Coverage. Der laufende Monat wird als vorläufig markiert; Jahrespreise werden nach Kalendertagen gewichtet und nur mit zwölf abgeschlossenen Monaten als vollständig ausgewiesen.

Abgeschlossene historische Antworten werden aus dem lokalen Cache wiederverwendet. `--refresh` erzwingt einen erneuten Abruf des angeforderten Zeitraums. Die Weboberfläche führt selbst keine Importe aus.

## Migration älterer Datenbanken

Nach dem Wechsel auf Ember-only entfernt dieser einmalige Befehl alle nicht von Ember stammenden Beobachtungen und Caches sowie obsolete Intervalltabellen und optimiert anschließend SQLite:

```powershell
eea migrate-ember-only
```

## Start

```powershell
eea serve --port 8765
```

Danach [http://127.0.0.1:8765](http://127.0.0.1:8765) öffnen.

## API

- `/api/countries`
- `/api/summary?year=2025`
- `/api/summary?year=2025&month=7`
- `/api/compare?year=2025&countries=DE,FR`
- `/api/coverage?year=2025`

Ohne `source` wird Ember verwendet. `source=ember` bleibt als explizite Schreibweise zulässig; andere Quellen werden abgelehnt.

## Berichte

```powershell
eea report --year 2025
```

Erzeugt `COVERAGE.generated.md` und `SUMMARY.generated.json` unter `data/reports/`.

## Datenmodell

`period_observation` ist die kanonische Faktentabelle. Der Monat ist die kleinste Analyseeinheit; geprüfte Jahreswerte werden separat mit `granularity=yearly` gespeichert. `api_cache` enthält redigierte Ember-JSON-Antworten, `source_cache` die unveränderte Ember-Preis-CSV samt HTTP-Metadaten und SHA-256.

- Erzeugung und Nachfrage: TWh
- Preis: EUR/MWh
- CO₂-Intensität: gCO₂eq/kWh

Jahreswerte werden aus geprüften Ember-Jahreswerten oder – wo ausdrücklich vorgesehen – aus vollständigen Monatsreihen gebildet. Laufende Jahre werden als YTD ausgewiesen. Fehlende Werte bleiben `null` und werden nicht als Null erfunden oder aus anderen Quellen ergänzt.

## Tests

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
```

## Bekannte Einschränkungen

- Albanien und einzelne historische Land-Monat-Kombinationen können reguläre Coverage-Lücken besitzen.
- Bruttoimport, Bruttoexport, negative Preisstunden und operative Intervallstatistiken sind nicht Teil des Monatsatlas.
- Der Ember-Endpunkt für Jahresnachfrage kann zeitweise fehlen; ein Jahreswert wird nur aus genau zwölf vorhandenen Monatswerten abgeleitet.
- Aktuelle Monate und Jahre können vorläufig sein und später durch Ember revidiert werden.

Weitere Details: [Ember-Abdeckung](docs/EMBER_COVERAGE.md).
