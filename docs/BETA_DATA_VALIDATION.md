# Beta-Datenvalidierung

Prüfauftrag: `K4-BETA-DATA-001` / finaler vollständiger Datenrefresh

Prüfdatum: 25. August 2026

Datengate: **PARTIAL / NOT PROMOTED**

## Kurzentscheidung

Der kontrollierte Refresh wurde vollständig bis zur letzten Pflichtquelle auf einer gesicherten Kandidatenkopie ausgeführt. Ember, Ember-Großhandelspreise, Eurostat-Kern- und Zusatzdaten, JRC Hydro, EEA-Inventaremissionen und Battery-Charts waren erfolgreich. Der einzige erlaubte Request an das JRC European Energy Storage Inventory antwortete jedoch mit **HTTP 404**. Es gab keinen Retry.

Weil damit ein Pflichtimport fehlschlug, wurde der Kandidat nicht als vollständig aktualisiert bezeichnet, nicht nach `data/atlas.sqlite3` übernommen und nicht für die Berichterzeugung verwendet. Die produktive Datenbank und die bestehenden generierten Reports blieben unverändert. Der Kandidat wird zur Diagnose aufbewahrt.

Die Türkei ist bewusst kein Atlasland. Ihre frühere Nennung war eine irrtümliche Prüfvorgabe und ist kein Datenmangel. Die vorläufige Nutzung der vorhandenen JRC-Storage-Werte bleibt eine bewusste Produkt- und Risikoentscheidung des Eigentümers; eine rechtliche Freigabe wird nicht behauptet.

## 1. Identität, Sicherung und Veröffentlichung

| Merkmal | Wert |
|---|---|
| Git-Branch / HEAD | `main` / `018645195552f0c77770e2298fdba8a2a56e733a` |
| Produktive Datenbank vor und nach dem Auftrag | `data/atlas.sqlite3` |
| Produktiver SHA-256 vor und nach dem Auftrag | `EDDE470DB65E9EC39C888A858955E731D5FA4F3EC741F6BEC78E52BBB340DDE9` |
| Produktive Größe / Änderungszeit UTC | 55.631.872 Byte / 2026-08-14 08:22:30 |
| Konsistente Rückfallkopie | `data/atlas.sqlite3-pre-refresh-20260825` |
| Rückfallkopie SHA-256 | `FB827BE8EC09B4FB29882652590D57E015313F652F61BEAFF4AC7DCDEC5EF7E8` |
| Erhaltener Kandidat | `data/atlas.sqlite3-refresh-candidate-20260825` |
| Kandidat SHA-256 | `CC2DA2375EFA1B39FD8824D539F7618E9EA1A087D86018FE0A7FC7EA7C5B47C0` |
| Kandidat Größe / Integrität | 75.403.264 Byte / `PRAGMA integrity_check = ok` |
| Veröffentlichung | **nicht erfolgt** |

Die Rückfallkopie wurde mit der SQLite-Backup-API konsistent erzeugt. Ihr Dateihash unterscheidet sich wegen der von SQLite neu geschriebenen Seitenstruktur vom Originalhash; fachlicher Ausgangsbestand, 121.908 Beobachtungen und Integrität wurden vor dem Refresh bestätigt.

## 2. Importergebnisse

Alle Abrufe wurden sequenziell ausgeführt.

| Quelle | Ergebnis | Kandidatenstand / Änderung |
|---|---|---|
| Ember-Stromdaten | **PASS** – 31/31 Länder, 2015–2026, kein Länder- oder Endpointfehler | 114.101 Ember-Zeilen insgesamt; gegenüber alt +74 Schlüssel, 0 entfernt, 467 Werte/Qualitäten geändert |
| Ember-Großhandelspreise | **PASS** | 3.970 Monatszeilen, 31 Länder, Cache-SHA `fd667713…` |
| Eurostat-Kern | **PASS** | 1.021 Zeilen aus `demo_gind`, `nama_10_gdp`, `nama_10_pc` |
| Eurostat-Zusatz | **PASS** | 4.603 Zeilen; zusammen 5.624 Eurostat-Zeilen; 0 Schlüssel hinzugefügt/entfernt, 9 revidierte Werte |
| JRC Hydro-power database | **PASS** | 67 Zeilen, 27 Länder, Release 2023-10-25, 0 fachliche Änderungen |
| EEA-Inventaremissionen | **PASS** | 270 Zeilen, 27 Länder, 2015–2024, 0 fachliche Änderungen; quellenbedingt ohne ME/MK/RS/UK |
| Battery-Charts Deutschland | **PASS** | exakt 1 Energie- und 1 Leistungsrequest mit 2,1 s Abstand; beide HTTP 200; 1.680 Zeilen bis 2026-08-24 |
| JRC European Energy Storage Inventory | **FAIL** | exakt 1 Request, HTTP 404, 0 Retries; vorhandene 150 API-Storage-Zeilen bis 2026-08-12 unverändert bewahrt |

Für Battery-Charts wurden beide Antworten zuerst als temporäre Dateien gespeichert und gemeinsam vollständig validiert: gültiges UTF-8/JSON, erwartetes Schema, streng steigende und identische 140 Monatsstichtage, nichtnegative numerische Werte sowie erfolgreicher Probeimport. Erst danach wurden `battery-energy.json` und `battery-power.json` ersetzt und in den Kandidaten importiert.

| Battery-Datei | SHA-256 | Letzter Stichtag |
|---|---|---|
| `battery-energy.json` | `84393C689D024F03C4A55BE018C6A2AC367A7F9819F2EF649BB64FBDB972FCB9` | 2026-08-24 |
| `battery-power.json` | `B439533D26885B899A38036159D436DE8010C108A80545E473E9E7E0AA411B5F` | 2026-08-24 |

## 3. Kandidateninventur

| Kennzahl | Vorher | Kandidat |
|---|---:|---:|
| Beobachtungen gesamt | 121.908 | 121.982 |
| monatlich | 106.526 | 106.600 |
| jährlich | 15.075 | 15.075 |
| Snapshot | 307 | 307 |
| Länder | 31 | 31 |
| Primärschlüsselduplikate | 0 | 0 |
| Zeilen mit SQL-NULL in Pflichtfeldern | 0 | 0 |

Vorhanden sind exakt `AT, BE, BG, CH, CZ, DE, DK, EE, ES, FI, FR, GR, HR, HU, IE, IT, LT, LU, LV, ME, MK, NL, NO, PL, PT, RO, RS, SE, SI, SK, UK`. Es fehlen keine Katalogländer; unerwartete Länder sowie `TR`, `AL` und `RU` sind nicht vorhanden. API-Schlüssel wurden weder in Cache-URLs noch in Payloads gespeichert.

### Zeitabdeckung je Quelle im Kandidaten

| Quelle | Zeilen | Frühester Beginn | Spätestes Ende |
|---|---:|---|---|
| Ember | 114.101 | 2015-01-01 | 2026-08-31 |
| Eurostat | 5.624 | 2015-01-01 | 2026-12-31 |
| Battery-Charts | 1.680 | 2015-01-01 | 2026-08-24 |
| JRC | 307 | 2023-10-25 | 2026-08-12 |
| EEA | 270 | 2015-01-01 | 2024-12-31 |

Ember-Jahresreihen reichen bis 2025; 2026 wird aus vorhandenen Monatswerten als YTD gebildet. Im Kandidaten sind 39 Reihen als `provisional_current_month` und vier Batteriedauern als `derived_provisional` gekennzeichnet. Fehlende Werte bleiben fehlende Beobachtungen; es wurden keine 2025-/2026-Werte aus Vorjahren kopiert. Echte, quellenberichtete Nullwerte bleiben unverändert erhalten.

## 4. Fachliche Nachprüfung

### Ember-Stichprobe

Für DE, FR, UK, ES und NO wurden jeweils das Jahr 2025 sowie die Monate 2025-01, 2025-07 und 2026-07 geprüft. Je Zeitraum wurden Gesamterzeugung, Demand, erneuerbare Erzeugung, eine landestypische Erzeugungsart, CO2-Intensität, Großhandelspreis und EE-Anteil aus der neuesten passenden gespeicherten Quellantwort gegen den Laufzeitwert verglichen.

- **140/140 Einzelprüfungen PASS**
- maximale absolute Abweichung: 0,018689 Prozentpunkte beim aus gerundeten TWh-Werten neu berechneten EE-Anteil
- direkte TWh-, CO2- und Monats-Preiswerte liegen innerhalb der quellenbedingten Rundungstoleranz
- 372 Jahres-/YTD-Preisprüfungen über alle 31 Länder und 2015–2026 entsprechen der kalendertagegewichteten Produktregel; unvollständige historische Jahre bleiben fehlend, 2026 nutzt vorhandene abgeschlossene Monate

### Fünf Kreuzkennzahlen

Für DE, FR und ES wurden alle fünf Kennzahlen für 2024 unabhängig aus den Raw-Eingängen nachgerechnet:

1. Erzeugung je nominalem BIP
2. Verbrauch je nominalem BIP
3. EEA-Strom-/Wärmeemissionen je nominalem BIP
4. Haushaltspreis minus kalendertagegewichteter Großhandelspreis
5. Bruttoimporte plus Bruttoexporte im Verhältnis zum Verbrauch

Ergebnis: **15/15 PASS**, maximale numerische Abweichung `0,0`.

### Speicher

- Battery-Charts: 560 Länder-/Monats-/Segmentgruppen, 0 Fehler bei `Energie / Leistung = Dauer`
- JRC Pumpspeicher: 23 Gruppen, 0 Formelfehler
- JRC Hydro: 67 Anlageninventarzeilen weiterhin getrennt vom Storage Inventory
- JRC Storage bleibt wegen des fehlgeschlagenen Refreshs auf dem Stichtag 2026-08-12; Schätzungs- und Unvollständigkeitskennzeichnungen bleiben erhalten

## 5. Tests und Berichte

| Prüfung | Ergebnis |
|---|---|
| Vollständige Python-Testsuite | **157 Tests, 0 Fehler, 0 übersprungen** |
| `node --check web/app.js` | PASS |
| `node --check web/wallpapers.js` | PASS |
| `git diff --check` | PASS; nur Zeilenenden-Warnungen an fremden Änderungen |

Die Reports wurden absichtlich **nicht** neu erzeugt, weil der Kandidat wegen der fehlgeschlagenen Pflichtquelle nicht veröffentlicht werden darf.

| Bestehender Report | Unveränderter SHA-256 | Status |
|---|---|---|
| `data/reports/COVERAGE.generated.md` | `DE65159043A161EF3EE045A5CD83DFF93502F3A4CD2546B0E97306286A3BBE20` | gehört weiterhin zum alten Produktivhash |
| `data/reports/SUMMARY.generated.json` | `A2FC1ABF941D91A1C152F8DBFBD15469672204287EBC34F5A9CD176F0C745D74` | weiterhin veraltet; nicht als Kandidatenreport ausgegeben |

## 6. Eigentümerentscheidungen und verbleibender Blocker

- **Türkei:** gegenstandslos; kein Atlasland, keine Beschaffung und kein Gate.
- **JRC-Nutzung:** Die vorhandenen aggregierten Storage-Inventory-Werte dürfen für die vorläufige nichtkommerzielle Beta mit Attribution sowie Schätzungs- und Unvollständigkeitshinweis verwendet werden. Dies ist eine akzeptierte Produktentscheidung, keine juristische Freigabe.
- **Blocker:** Der konfigurierte offizielle JRC-Storage-API-Endpunkt lieferte beim einzigen erlaubten Request HTTP 404. Ohne erfolgreiche Pflichtquelle darf der Kandidat nicht veröffentlicht werden.

## 7. Arbeitsbaumgrenze

K4 änderte ausschließlich die ausdrücklich freigegebenen Battery-Charts-Dateien, den ignorierten Kandidaten und diesen Bericht. Produktivdatenbank und generierte Reports blieben unverändert. Während der Arbeit erschienen parallele fremde Änderungen an Roadmaps, UI-Dokumentation, Tests sowie `web/`; K4 hat sie weder bearbeitet, bereinigt, gestaged noch zurückgesetzt.

Kein Commit, kein Staging und kein Push wurden ausgeführt.
