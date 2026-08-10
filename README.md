# European Electricity Atlas – Data Core v0.1

Lokale, nachvollziehbare Datenpipeline für 32 europäische Atlasländer. Die Anwendung verbindet den bisherigen Energy-Charts-Zehnerkatalog mit Ember-Erzeugung, -Nachfrage, -CO₂-Intensität und nationalen Großhandelspreisen, hält die Quellantworten in SQLite vor und stellt Jahres-/Monatsaggregationen über ein schlichtes Analyse-UI bereit.

## Voraussetzungen und Installation (Windows)

- Python 3.11 oder neuer
- Internetzugang nur für den Datenimport

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Es gibt keine Laufzeit-Abhängigkeiten außerhalb der Python-Standardbibliothek.

## Datenimport

Energy-Charts bleibt die Standardquelle. Ember kann ausdrücklich über `--source ember` ausgewählt werden. Der Ember-Schlüssel wird zuerst aus `EMBER_API_KEY` und andernfalls aus der lokalen, ignorierten Datei `EMBER_API_KEY.txt` gelesen.

Der verbindliche Atlas- und Ember-Katalog umfasst 32 Länder. Der Energy-Charts-Importer bleibt ausdrücklich auf die bisherigen zehn Länder begrenzt und fragt bei einem Standardimport keine neu hinzugekommenen Länder ab.

Komplettes Energy-Charts-Jahr 2025 für die zehn dort unterstützten Atlasländer:

```powershell
eea import --year 2025
```

Energy-Charts-Historie ab 2015 bis zum laufenden Jahr für genau diese zehn Länder:

```powershell
eea import --source energy-charts --from-year 2015
```

Nur die Testmonate Januar und Juli:

```powershell
eea import --year 2025 --months 1 7
```

Nur einzelne Länder:

```powershell
eea import --year 2025 --countries DE FR ES
```

Ember-Monats- und Jahreswerte für alle Pilotländer:

```powershell
$env:EMBER_API_KEY="<API-Key>"
eea import --source ember --year 2025
```

Gesamte Atlas-Historie ab 2015 bis einschließlich laufendem Jahr; laufende Jahre werden nur über verfügbare Monatswerte ergänzt, Jahresendpunkte nur für abgeschlossene Jahre abgefragt:

```powershell
eea import --source ember --from-year 2015
```

Der Server und die Weboberfläche führen keine Importe aus, sondern lesen ausschließlich die lokale SQLite-Datenbank. Der Bereichsimport trennt abgeschlossene Historie vom laufenden Jahr und verwendet passende Antworten aus `api_cache` erneut. Dadurch wird die historische Reihe bei späteren Aktualisierungen nicht erneut heruntergeladen; nur der aktuelle Zeitraum wird fortgeschrieben. `--refresh` erzwingt weiterhin bewusst einen Neuabruf.

Ember für ausgewählte Länder:

```powershell
eea import --source ember --year 2025 --countries DE FR ES UK
```

Nationale monatliche Ember-Großhandelspreise ohne API-Key importieren:

```powershell
eea import-prices
```

Der Preisimport lädt die vollständige Ember-CSV, validiert Header, 32-Länder-Katalog, ISO3-Codes, Monatsschlüssel und alle vorhandenen Preise als endliche numerische Werte und ersetzt erst danach Rohdaten-Cache und normalisierte Monatswerte atomar. Leere Preiszellen kennzeichnen eine nicht veröffentlichte Land-Monat-Kombination, werden als fehlende Coverage ausgelassen und niemals als Null gespeichert. Die unveränderte CSV sowie HTTP-Metadaten und SHA-256 werden in `source_cache` gespeichert. Laufende Monate erhalten `provisional_current_month`. Jahrespreise sind nach Kalendertagen gewichtet, bei zwölf abgeschlossenen Monaten vollständig und im laufenden Jahr YTD; unvollständige historische Jahre liefern keinen scheinbar vollständigen Jahrespreis.

Alle normalisierten Zeitreihen verwenden den Monat als kleinste Einheit. Energy-Charts-Leistungs-, Preis- und Flussantworten werden unmittelbar beim Import monatsweise integriert; einzelne Intervalle und bilaterale Gegenparteien werden nicht als Analysezeilen gespeichert. Ember-Daten werden als bereits aggregierte Periodenwerte separat gespeichert und niemals mit Energy-Charts-Werten summiert. Die Weboberfläche zeigt eine gemeinsame, möglichst vollständige Ansicht: Erzeugung und Energiemix kommen geschlossen bevorzugt aus Energy-Charts und bei fehlender Abdeckung aus Ember; fehlender Verbrauch und CO₂-Intensität werden aus Ember ergänzt. Der nationale Ember-Preis hat Vorrang vor dem bisherigen Energy-Charts-Preis. Import, Export und installierte Leistung kommen ausschließlich aus Energy-Charts. Ein ausklappbarer Quellenblock unter den Tabellen dokumentiert Anbieter, Endpunkte, Verarbeitung, Lizenz und Zusammenführungsregeln; die kombinierte API-Antwort enthält zusätzlich die Herkunft je Kennzahl in `value_sources`. Ember-Daten stehen unter CC BY 4.0.

Ohne `source` liefern `/api/summary` und `/api/compare` diese kombinierte Ansicht. Die getrennten Rohsichten bleiben für Analyse und Nachvollziehbarkeit über `source=energy-charts` beziehungsweise `source=ember` verfügbar. `source=combined` kann auch ausdrücklich angegeben werden.

Beim gezielten Einzeljahresimport wird der Ember-Endpunkt für Jahresverbrauch weiterhin direkt abgefragt und ein API-Fehler bleibt in der Importzusammenfassung sichtbar. Der historische Bereichsimport verwendet für den Verbrauch dagegen die vollständigeren Monatsdaten und leitet einen Jahresverbrauch transparent nur aus genau zwölf vorhandenen Ember-Monatswerten ab; Energy-Charts-Daten werden dafür nicht verwendet.

Die Jahresauswahl der lokalen Weboberfläche ist auf 2015 bis zum laufenden Kalenderjahr begrenzt. Eventuell in Quellen oder Cache vorhandene ältere Werte werden dort bewusst nicht angeboten.

Bereits vorhandene oder überdeckende Zeiträume kommen aus `api_cache` und werden nicht erneut geladen. Der Rohcache bewahrt die unveränderte Quellenantwort zur Nachvollziehbarkeit; fachliche Abfragen verwenden ausschließlich Monats-/Jahreswerte. Der erste Jahresimport erfolgt rate-limit-schonend als Jahresabruf und wird direkt in Monate zerlegt. Existiert nur ein Teilbestand, prüft der Import Monatssegmente und lädt ausschließlich fehlende Segmente nach. `--months` ersetzt ausschließlich die genannten Monate; Kapazitätssnapshots werden bei einem Monatsimport nicht verändert. Jeder Teilbereich wird erst nach erfolgreichem Download beziehungsweise erfolgreicher Cache-Auswertung innerhalb einer atomaren Transaktion ersetzt. Bei Download-, Validierungs- oder Normalisierungsfehlern bleibt der bisherige normalisierte Teilbereich erhalten. `--refresh` lädt nur die angeforderten Zeiträume neu. Die CLI meldet erfolgreiche Teilbereiche, Fehler und die Anzahl erhaltener Altzeilen; bei mindestens einem Teilfehler endet sie mit einem Exitcode ungleich null. Die öffentliche API ist rate-limitiert; HTTP 429 wird mit begrenztem Backoff wiederholt.

## Start

```powershell
eea serve
```

Danach [http://127.0.0.1:8000](http://127.0.0.1:8000) öffnen. Das UI greift ausschließlich auf SQLite zu, nie direkt auf Energy-Charts.

## Berichte

```powershell
eea report --year 2025
```

Erzeugt in `data/reports/`:

- `COVERAGE.generated.md`
- `VALIDATION.generated.md`
- `SUMMARY.generated.json`

## Datenbank zurücksetzen

```powershell
eea reset-db
```

Dies löscht nur die konfigurierte lokale SQLite-Datei (Standard: `data/atlas.sqlite3`).

## Tests

Nach Installation:

```powershell
python -m unittest discover -s tests -v
```

Ohne Installation aus dem Checkout:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
```

## Kanonisches Modell und Einheiten

`period_observation` ist die kanonische Faktentabelle für Energy-Charts, Ember und Ember-Preise. Die kleinste Granularität ist `monthly`; Jahreswerte werden aus vollständigen Monaten gebildet oder als geprüfte `yearly`-Quellenwerte gespeichert. `observation` und `bilateral_flow` sind ausschließlich leere Legacy-Strukturen für die einmalige Migration älterer Datenbanken. `metric` enthält die kanonischen Größen (`generation_*`, `consumption`, `import_total`, `export_total`, `net_import`, `day_ahead_price`, `carbon_intensity`).

- normalisierte Erzeugung, Verbrauch und Flüsse: TWh je Monat
- Preis: EUR/MWh
- CO₂-Intensität: gCO2eq/kWh
- installierte Leistung: MW; Bestandswert am Ende des gemeldeten Zeitraums

Die Summary-Ausgabe enthält für installierte Leistung zusätzlich `installed_capacity_snapshot`, `installed_capacity_snapshot_year`, `installed_capacity_age_years` und `installed_capacity_status`. Ein Snapshot, der mehr als zwei Kalenderjahre vor dem Berichtsjahr liegt, wird als `stale` markiert und setzt den Datenstatus mindestens auf `partial`. Bei Photovoltaik wird `solar_dc` bevorzugt; `solar_ac` dient als Fallback, wenn kein DC-Wert vorhanden ist.

Erneuerbar sind zentral in `config.RENEWABLE_METRICS` ausschließlich Solar, Wind Onshore, Wind Offshore, Wasser und Biomasse. Geothermie, Abfall und „other renewables“ bleiben in v0.1 bewusst `generation_other`, bis K1 die Klassifikation entscheidet.

## Bekannte Einschränkungen

- Erzeugung ist **öffentliche Nettoerzeugung**, nicht zwingend die gesamte nationale Erzeugung; industrielle Eigenerzeugung und Eigenverbrauch können fehlen.
- Energy-Charts v2 stellt keine CO₂-Intensitätszeitreihe bereit. Es wird nichts geschätzt.
- Die UK-Erzeugungs- und Lastreihen sind 2025 unvollständig (fehlende Technologien und viele Nullwerte) und werden als teilweise statt als vergleichbar markiert.
- FR, ES und DK enthalten 2025 einzelne oder monatsweise Lastlücken. Unvollständige Periodenwerte werden nicht als scheinbar vollständige Verbrauchssumme ausgegeben; Details stehen im Coverage Report.
- In der Energy-Charts-Rohsicht besitzen IT, NO, SE und DK mehrere Preiszonen; UK fehlt im Preiszonen-Katalog und DE verwendet DE-LU. Die kombinierte Ansicht nutzt stattdessen bevorzugt Embers nationale Monats-/Jahrespreise.
- Physische Flüsse (`cbpf`) sind keine Handelsfahrpläne (`cbet`).
- Pumpspeichererzeugung liegt unter Wasser und zählt nach der derzeitigen Mindestdefinition als erneuerbar; das weicht von offiziellen Anteilsdefinitionen ab.
- Der v2-Preisdatensatz 2025 wechselt in der Quelle von Stunden- zu Viertelstundenwerten. Der Import gewichtet diese einmalig nach realer Dauer und speichert ausschließlich den resultierenden Monatswert und seine Monatsstatistiken.
- Die länderweise historische Startgrenze von `public_power` ist in der API-Dokumentation nicht fest angegeben. Der automatisierte Report weist deshalb nur das früheste **lokal importierte** Jahr aus.
- Preis-Lizenzen unterscheiden sich je Gebotszone. Die API-Antwort samt Lizenz wird im Importmetadatensatz gespeichert.

Weitere Details: [API-Untersuchung](docs/API_RESEARCH.md), [Ergebnisbericht](docs/RESULT_REPORT.md), [K1-Entscheidungen](docs/K1_DECISIONS.md).
