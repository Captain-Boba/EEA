# API-Untersuchung – Energy-Charts v2

Stand: 10. August 2026. Primärquelle ist der aktuelle [OpenAPI-Vertrag](https://api.energy-charts.info/openapi.json), ergänzt durch den maschinenlesbaren Katalog `GET /v2` und reale 2025-Stichproben/Jahresimporte.

## Relevante Endpoints

| Endpoint | Verwendung | API-Einheit / Semantik | Atlas-Entscheidung |
|---|---|---|---|
| `/v2/public_power` | öffentliche Nettoerzeugung je Typ und Last | MW; Timestamp = Intervallbeginn | gemeinsame Erzeugungsbasis für alle Länder |
| `/v2/total_power` | gesamte Nettoerzeugung inkl. industrieller Eigenerzeugung | MW; laut Vertrag derzeit nur DE | nicht verwendet, da länderübergreifend nicht vergleichbar |
| `/v2/price` | Day-Ahead-Preis je Gebotszone | EUR/MWh | nur eindeutige Einzelzonen; zeitgewichtet |
| `/v2/cbpf` | physische bilaterale Grenzflüsse | GW; positiv Import, negativ Export | Quelle für Import, Export, Saldo und bilaterale Flüsse |
| `/v2/cbet` | geplante kommerzielle Austausche | GW; positiv Import, negativ Export | gespeichert werden könnte es später; nicht mit physischen Flüssen vermischt |
| `/v2/installed_power` | installierte Leistung je Typ | meist GW; Bestandswert am Periodenende | jährlich, nach MW normalisiert |

Kein öffentlicher v2-Endpoint liefert eine historische CO₂-Intensitätszeitreihe. `carbon_intensity` bleibt daher `null`.

## Länder und Gebotszonen

Der Country-Enum enthält alle zehn Pilotländer (`de`, `fr`, `es`, `it`, `pl`, `uk`, `no`, `se`, `dk`, `nl`) sowie weitere europäische Länder und Aggregate. Für Preise gilt ein separater Gebotszonen-Enum:

- DE: `DE-LU` (nicht exakt staatsgleich)
- FR: `FR`
- ES: `ES`
- PL: `PL`
- NL: `NL`
- IT: mehrere Festlands-/Inselzonen
- NO: `NO1`–`NO5` (zusätzlich `NO2NSL`, nicht als normale Landeszone aggregiert)
- SE: `SE1`–`SE4`
- DK: `DK1`, `DK2`
- UK: keine Preiszone im v2-Katalog

Für Mehrzonenländer wird kein ungewichteter Mittelwert als scheinbar nationaler Preis ausgegeben. Eine belastbare Aggregation benötigt zonale Last-/Verbrauchsgewichte und eine Produktentscheidung.

## Auflösung und Zeitraum

Reale Jahresimporte 2025 ergaben:

| Land | Erzeugung/Last | physische Flüsse | Preis |
|---|---|---|---|
| DE, FR, ES, PL, NL | 15 min | 15 min | gemischt 60/15 min |
| IT, NO, SE, DK | 60 min | 15 min | nicht national aggregiert |
| UK | 30 min | 15 min | nicht verfügbar |

Der Preisendpoint liefert für das Gesamtjahr 2025 wegen der Umstellung keine einheitliche `resolution`/`interval_minutes`. Die Pipeline bestimmt deshalb die Dauer jedes Wertes aus der Differenz aufeinanderfolgender UTC-Timestamps. DST-Dopplungen bleiben durch Offset und UTC-Schlüssel eindeutig.

Die Dokumentation nennt keine feste länder- und serienbezogene historische Startgrenze für `public_power`. `available_from`/`available_until` beschreiben die tatsächlich zurückgegebene Antwortspanne. Historische Tages-Probes wurden von der öffentlichen Rate-Begrenzung dauerhaft mit HTTP 429 gebremst; daher wird keine unbestätigte Startjahreszahl behauptet. Für den Auftrag ist das komplette Kalenderjahr 2025 für alle Pilotländer lokal nachgewiesen. Bei `installed_power` variieren die Spannen; die Antwortmetadaten werden vollständig gespeichert (DE-Stichprobe: ab 2002, einschließlich Projektionsspalten bis 2030).

## Kategorien und Definitionen

Direkt zugeordnet werden Solar, Wind Onshore/Offshore, Laufwasser, Speicherwasser, Pumpspeichererzeugung, Biomasse, Kernkraft, Gas, Kohle, Braunkohle und Öl. Folgende reale Serien bleiben dokumentiert in `generation_other`:

- `geothermal`
- `other_renewables`
- `waste`
- `others`
- `battery` / `battery_consumption`

Damit wird keine nicht freigegebene EE-Klassifikation erfunden. Pumpspeicherverbrauch wird nicht als negative Erzeugung eingerechnet; Pumpspeichererzeugung ist derzeit Wasser und dadurch erneuerbar. Beides ist eine K1-Entscheidung.

## Datenqualität und Vergleichbarkeit

- `public_power` ist öffentlich/netto; nationale Betreiberberichte können Eigenerzeugung, Eigenverbrauch, Inseln oder Schätzungen zusätzlich enthalten.
- Last ist die von der Quelle gemeldete `load`-Reihe und nicht automatisch identisch mit nationalem Bruttoverbrauch.
- Physische Flüsse (`cbpf`) und Handel (`cbet`) haben verschiedene Bedeutungen.
- Import und Export werden aus allen bilateralen Flüssen getrennt integriert; der Saldo ist Import minus Export.
- Rohantworten, SHA-256, Request-URL, Lizenz, Auflösung und verfügbare Antwortspanne werden gespeichert.
- Fehlende/duplizierte Intervalle und unbekannte Kategorien erzeugen sichtbare `quality_issue`-Einträge.
- Installierte Leistung ist ein Snapshot zum Periodenende, keine Energie. Projektspalten, Batterie-Energie (GWh) und Solar-AC werden nicht doppelt in die Gesamtsumme addiert.

