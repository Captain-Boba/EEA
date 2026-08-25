# Beta-Datenvalidierung

Prüfauftrag: `K4-BETA-DATA-001` / finaler vollständiger Datenrefresh

Prüfdatum: 25. August 2026

Datengate: **READY FOR BETA – OWNER RISK ACCEPTED**

## Kurzentscheidung

Der vollständige Refresh wurde auf einer konsistenten Kandidatenkopie ausgeführt, technisch und fachlich validiert und anschließend kontrolliert als `data/atlas.sqlite3` veröffentlicht. Alle Pflichtquellen waren erfolgreich. Der neue K2-Importer bezog das European Energy Storage Inventory über die sichtbaren Exportfunktionen des offiziellen JRC-Dashboards: eine Dashboard-Sitzung und vier getrennte XLSX-Downloads für Batterie/Pumpspeicher und Leistung/Kapazität. Es gab keinen Retry.

Die Türkei ist bewusst kein Atlasland. Ihre frühere Nennung war eine irrtümliche Prüfvorgabe und ist kein Datenmangel. Die vorläufige Nutzung der JRC-Storage-Werte bleibt eine bewusste Produkt- und Risikoentscheidung des Eigentümers; eine rechtliche Freigabe wird nicht behauptet. Schätzungen und unvollständige Projektabdeckung bleiben gekennzeichnet.

## 1. Identität, Sicherung und Veröffentlichung

| Merkmal | Wert |
|---|---|
| Git-Branch / geprüfter HEAD | `main` / `2fa48869d981307cbca5861b21558783ebabe0cd` |
| Produktive Datenbank | `data/atlas.sqlite3` |
| Alter SHA-256 | `EDDE470DB65E9EC39C888A858955E731D5FA4F3EC741F6BEC78E52BBB340DDE9` |
| Neuer SHA-256 | `433CD46792264F366EC8DF51B52521B44034F7CAAE7C68DF289A704254A93B50` |
| Neue Größe / Datenstand UTC | 75.403.264 Byte / 2026-08-25 04:24:42 |
| Temporäre konsistente Rückfallkopie | `data/atlas.sqlite3-pre-refresh-20260825-attempt2` (nach Abnahme entfernt) |
| Rückfallkopie SHA-256 | `FB827BE8EC09B4FB29882652590D57E015313F652F61BEAFF4AC7DCDEC5EF7E8` |
| Temporärer validierter Kandidat | `data/atlas.sqlite3-refresh-candidate-20260825-attempt2` (nach Abnahme entfernt) |
| Kandidaten-SHA-256 | `433CD46792264F366EC8DF51B52521B44034F7CAAE7C68DF289A704254A93B50` |
| Veröffentlichung | Atomarer Dateitausch; veröffentlichter Hash entspricht exakt dem Kandidatenhash |

Die Rückfallkopie wurde mit der SQLite-Backup-API konsistent erzeugt. Ihr Dateihash unterscheidet sich wegen der von SQLite neu geschriebenen Seitenstruktur vom ursprünglichen Dateihash; fachlicher Ausgangsbestand, 121.908 Beobachtungen und Integrität wurden vor dem Refresh bestätigt. Nach Veröffentlichung, Hashvergleich und Abnahme wurden die temporären Kandidaten, Rückfallkopien und Testdatenbanken entfernt. Künftige Läufe verwenden dafür ausschließlich den automatisch bereinigten Arbeitsbereich `data/.refresh-work/<run-id>/`.

## 2. Importergebnisse

Alle Abrufe wurden sequenziell ausgeführt.

| Quelle | Ergebnis | Finaler Stand / Änderung |
|---|---|---|
| Ember-Stromdaten | **PASS** – 31/31 Länder, 2015–2026, keine Länder- oder Endpointfehler | 114.101 Ember-Zeilen insgesamt; gegenüber alt +74 Schlüssel, 0 entfernt, 467 Werte/Qualitäten geändert |
| Ember-Großhandelspreise | **PASS** | 3.970 Monatszeilen, 31 Länder, Cache-SHA `fd667713c2a614de59f9ea945412a83b7aeaca39275ef4fb3e3835e9a5d24085` |
| Eurostat-Kern | **PASS** | 1.021 Zeilen aus `demo_gind`, `nama_10_gdp`, `nama_10_pc` |
| Eurostat-Zusatz | **PASS** | 4.603 Zeilen; zusammen 5.624 Eurostat-Zeilen; 0 Schlüssel hinzugefügt/entfernt, 9 revidierte Werte |
| JRC Hydro-power database | **PASS** | 67 Zeilen, 27 Länder, Release 2023-10-25, fachlich unverändert |
| EEA-Inventaremissionen | **PASS** | 270 Zeilen, 27 Länder, 2015–2024, fachlich unverändert; quellenbedingt ohne ME/MK/RS/UK |
| Battery-Charts Deutschland | **PASS** | exakt 1 Energie- und 1 Leistungsrequest mit 2,1 s Abstand; beide HTTP 200; 1.680 Zeilen bis 2026-08-25 |
| JRC European Energy Storage Inventory | **PASS** | eine offizielle Dashboard-Sitzung, 4 XLSX-Exporte, 0 Retries; 150 Storage-Zeilen zum Stichtag 2026-08-25 ersetzt |

Für Battery-Charts wurden beide Antworten zuerst temporär gespeichert und gemeinsam vollständig validiert: gültiges UTF-8/JSON, erwartetes Schema, streng steigende und identische 140 Monatsstichtage, nichtnegative numerische Werte sowie erfolgreicher Probeimport. Erst danach wurden die lokalen Dateien ersetzt und in den Kandidaten importiert.

| Battery-Datei | SHA-256 | Letzter Stichtag |
|---|---|---|
| `battery-energy.json` | `230DB64FB32A4D98FF6B33655CC573D5001D65011DECB100933AE7EC81A4451C` | 2026-08-25 |
| `battery-power.json` | `30ECBD2D6F6970913B8D726460510EA75326FA12737C2214820FB0CC744350CA` | 2026-08-25 |

Die vier JRC-Exporte besitzen gültige XLSX-Signaturen und stimmen jeweils mit dem gespeicherten SHA-256 überein. Das Dashboard lieferte vollständige Wertepaare für 27 Atlasländer bei Batterien und 23 Atlasländer bei Pumpspeichern. Deutschland verwendet im Laufzeitmodell weiterhin ausschließlich den vollständigeren Battery-Charts-MaStR-Gesamtbestand; JRC-Batteriewerte werden nicht hinzuaddiert. Für andere Länder wird das JRC-Projektinventar verwendet. Batterie, Pumpspeicher und allgemeine Reservoirenergie bleiben getrennt.

## 3. Finale Datenbankinventur

| Kennzahl | Vorher | Final |
|---|---:|---:|
| Beobachtungen gesamt | 121.908 | 121.982 |
| monatlich | 106.526 | 106.600 |
| jährlich | 15.075 | 15.075 |
| Snapshot | 307 | 307 |
| Länder | 31 | 31 |
| Primärschlüsselduplikate | 0 | 0 |
| Zeilen mit SQL-NULL in Pflichtfeldern | 0 | 0 |
| `PRAGMA integrity_check` | `ok` | `ok` |

Vorhanden sind exakt `AT, BE, BG, CH, CZ, DE, DK, EE, ES, FI, FR, GR, HR, HU, IE, IT, LT, LU, LV, ME, MK, NL, NO, PL, PT, RO, RS, SE, SI, SK, UK`. Es fehlen keine Katalogländer; unerwartete Länder sowie `TR`, `AL` und `RU` sind nicht vorhanden. API-Schlüssel wurden weder in Cache-URLs noch in Payloads gespeichert.

### Zeitabdeckung je Quelle

| Quelle | Zeilen | Frühester Beginn | Spätestes Ende |
|---|---:|---|---|
| Ember | 114.101 | 2015-01-01 | 2026-08-31 |
| Eurostat | 5.624 | 2015-01-01 | 2026-12-31 |
| Battery-Charts | 1.680 | 2015-01-01 | 2026-08-25 |
| JRC | 307 | 2023-10-25 | 2026-08-25 |
| EEA | 270 | 2015-01-01 | 2024-12-31 |

Ember-Jahresreihen reichen bis 2025; 2026 wird aus vorhandenen Monatswerten als YTD gebildet. Im finalen Stand sind 39 Reihen als `provisional_current_month` und vier Batteriedauern als `derived_provisional` gekennzeichnet. Fehlende Werte bleiben fehlende Beobachtungen; es wurden keine 2025-/2026-Werte aus Vorjahren kopiert. Echte, quellenberichtete Nullwerte bleiben erhalten.

## 4. Fachliche Nachprüfung

### Ember-Stichprobe

Für DE, FR, UK, ES und NO wurden jeweils das Jahr 2025 sowie die Monate 2025-01, 2025-07 und 2026-07 geprüft. Je Zeitraum wurden Gesamterzeugung, Demand, erneuerbare Erzeugung, eine landestypische Erzeugungsart, CO2-Intensität, Großhandelspreis und EE-Anteil aus der neuesten passenden gespeicherten offiziellen Ember-Quellantwort gegen den Laufzeitwert verglichen.

- **140/140 Einzelprüfungen PASS**
- maximale absolute Abweichung: 0,018689 Prozentpunkte beim aus gerundeten TWh-Werten neu berechneten EE-Anteil
- direkte TWh-, CO2- und Monats-Preiswerte liegen innerhalb der quellenbedingten Rundungstoleranz
- **372/372** Jahres-/YTD-Preisprüfungen über alle 31 Länder und 2015–2026 entsprechen der kalendertagegewichteten Produktregel; unvollständige historische Jahre bleiben fehlend, 2026 nutzt nur vorhandene abgeschlossene Monate

### Fünf Kreuzkennzahlen

Für DE, FR und ES wurden alle fünf Kennzahlen für 2024 unabhängig aus den Raw-Eingängen desselben Kalenderjahres nachgerechnet:

1. Erzeugung je nominalem BIP
2. Verbrauch je nominalem BIP
3. EEA-Strom-/Wärmeemissionen je nominalem BIP
4. Haushaltspreis minus kalendertagegewichteter Großhandelspreis
5. Bruttoimporte plus Bruttoexporte im Verhältnis zum Verbrauch

Ergebnis: **15/15 PASS**, maximale numerische Abweichung `0,0`. Division durch null und fehlende Eingänge bleiben gemäß Produktlogik fehlend. Die EEA-Reihe umfasst öffentliche Strom- und Wärmeerzeugung; das BIP ist nominal.

### Speicher

- Battery-Charts: 560 Länder-/Monats-/Segmentgruppen, 0 Fehler bei `Energie / Leistung = Dauer`
- JRC Batterie: 27 Ländergruppen, 0 Formelfehler
- JRC Pumpspeicher: 23 Ländergruppen, 0 Formelfehler
- JRC Hydro: 67 Anlageninventarzeilen weiterhin getrennt vom Storage Inventory
- der zuvor verwendete undokumentierte JRC-JSON-Endpunkt hat im finalen Bestand 0 Zeilen
- Schätzungs- und Unvollständigkeitskennzeichnungen bleiben erhalten

## 5. Tests und Berichte

| Prüfung | Ergebnis |
|---|---|
| Vollständige Python-Testsuite | **176 Tests, 0 Fehler, 0 übersprungen** |
| `node --check web/app.js` | PASS mit gebündelter Node-Laufzeit |
| `node --check web/wallpapers.js` | PASS mit gebündelter Node-Laufzeit |
| `git diff --check` | PASS; nur Zeilenenden-Hinweise an parallelen fremden Änderungen |

Die zwei vom aktuellen CLI-Befehl unterstützten Reports wurden zuerst gegen den validierten Kandidaten und nach Veröffentlichung erneut gegen `data/atlas.sqlite3` erzeugt. Beide Dateihashes stimmen zwischen Kandidat und veröffentlichtem Datenbankstand exakt überein.

| Report | Finaler SHA-256 | Status |
|---|---|---|
| `data/reports/COVERAGE.generated.md` | `DE65159043A161EF3EE045A5CD83DFF93502F3A4CD2546B0E97306286A3BBE20` | finaler 2025-Coverage-Bericht |
| `data/reports/SUMMARY.generated.json` | `6E08FAAEAC0D6C85E23F7667FC9F51E0A5AD5E1688ED946E95519D85F194D213` | finaler 2025-Summary-Bericht |

`data/reports/VALIDATION.generated.md` ist ausdrücklich als historischer Bericht der früheren Energy-Charts-Architektur gekennzeichnet, wird vom aktuellen `eea report` nicht erzeugt und gilt nicht als aktuelle Ember-Validierung.

## 6. Eigentümerentscheidungen und Grenzen

- **Türkei:** gegenstandslos; kein Atlasland, keine Beschaffung und kein Gate.
- **JRC-Nutzung:** Die aggregierten Storage-Inventory-Werte dürfen für die vorläufige nichtkommerzielle Beta mit Attribution sowie Schätzungs- und Unvollständigkeitshinweis verwendet werden. Dies ist eine akzeptierte Produktentscheidung, keine juristische Freigabe.
- **JRC-Abdeckung:** Fehlende Länderwerte bleiben fehlend. Das Dashboard-Inventar ist kein vollständiges nationales Register.
- **Datengate:** **READY FOR BETA – OWNER RISK ACCEPTED**.

## 7. Arbeitsbaumgrenze

K4 änderte ausschließlich die ausdrücklich freigegebenen Daten-/Reportdateien und diesen Prüfbericht. Während der Arbeit erschienen parallele fremde Änderungen an Kennzahlen-, Profil-, UI- und Testdateien; K4 hat sie weder bearbeitet, bereinigt, gestaged noch zurückgesetzt.

Kein Commit, kein Staging und kein Push wurden ausgeführt.
