# European Electricity Atlas – Roadmap

Stand: 23. September 2026

Betriebsstand laut dokumentierter Abnahme vom 23. September 2026: Der
Monats-Refresh ist in Railway aktiviert (Tag 2, 03:00 UTC). Der betreute
September-Lauf wurde veröffentlicht; historische Ember-Quellenlücken blieben
mit expliziter Qualitätskennzeichnung erhalten. Abdeckungsschutz,
Betriebssystem-Sperren, Retryplanung und begrenzte Cache-Bereinigung sind aktiv.
Die Abnahme ist ein datierter Befund, kein laufender Live-Status.

Diese Roadmap trennt den aktuell umgesetzten Projektstand von offenen Produktentscheidungen. Historische K2-Arbeitsaufträge sind als solche gekennzeichnet und gelten nicht als aktuelle Spezifikation.

Betriebsnachtrag 23. September 2026: JRC-Speicherinventar und Battery-Charts
sind als optionale Headless-Browser-Exporte in den Monatslauf integriert.
Battery-Charts nutzt die öffentlichen CSV-Downloads; lokale JSONs bleiben
explizite Overrides. Für Railway ist die offizielle Build-Variable
`RAILPACK_PYTHON_PLAYWRIGHT_INSTALL=1` und die Installation der Python-Abhängigkeiten
über `requirements.txt` nötig. Der Linux-Live-Test beider Quellen war auf einer
flüchtigen Datenbankkopie erfolgreich; dabei wurden weder Atlas noch Community
in Produktion verändert. Eine Veröffentlichung dieser Browserdaten durch den
nächsten Monatslauf bleibt vom Akquisitionstest zu unterscheiden.

Lokaler Folgeschritt: Quellenwarnungen im öffentlichen Health-Endpunkt,
reproduzierbare Offline-Berichte und zusätzliche Monatswechsel-/Fehlertests.
Diese Änderungen benötigen noch Commit, Push und Deployment; sie werden hier
nicht als bereits produktiv ausgegeben.

Der operative Weg bis zur Veröffentlichung mit Abnahme-Gates steht in [BETA_ROADMAP.md](BETA_ROADMAP.md).

## Aktuelle Arbeitsprioritäten

### 1. Datenstände nachvollziehbar halten – August-Datengate historisch abgeschlossen

- Der vollständige Refresh vom 25. August 2026 hat alle acht Datenpfade sequenziell aktualisiert und den validierten Kandidaten als `data/atlas.sqlite3` veröffentlicht.
- Datenbankintegrität, 31-Länder-Katalog, Zeitabdeckung, Null-/Fehlwerttrennung, 140 Ember-Einzelstichproben und 15 Kreuznachrechnungen sind in der historischen August-Abnahme dokumentiert.
- `BETA_DATA_VALIDATION.md` beschreibt den damaligen Datei-SHA-256 `433CD46792264F366EC8DF51B52521B44034F7CAAE7C68DF289A704254A93B50`. Neue Coverage-/Summary-/Validierungsberichte sind durch `REPORT_MANIFEST.generated.json` ihrem eigenen logischen Snapshot zugeordnet. Lokale Berichte bestätigen nicht automatisch den inzwischen erneuerten Produktionsstand.
- Der neue `refresh-all`-Ablauf erstellt Kandidat und Rückfallkopie nur noch unter `data/.refresh-work/<run-id>/`, schützt `community.sqlite3` und räumt temporäre Datenbanken sowie Sidecars nach Erfolg oder kontrolliertem Fehler wieder auf.
- Die Türkei bleibt bewusst außerhalb des Atlas und ist kein Prüf- oder Erweiterungsziel.

**Abnahme:** Bei jedem neuen Berichtssatz stimmen alle Datei-Prüfsummen mit dem Manifest überein; geprüfter Snapshot, Auswertungsjahr und Aggregationskalender sind eindeutig. Historische Abnahmen bleiben datiert.

### 2. Öffentliche Beta betreiben und als Patch fortschreiben

- Railway Hobby betreibt den Atlas mit einem persistenten Volume unter `/data`, einer ausschließlich lesend geöffneten `atlas.sqlite3` und einer getrennten beschreibbaren `community.sqlite3`.
- Host, Port und Datenbankpfade sind laufzeitkonfigurierbar. `/api/health` überwacht beide Datenbanken, und `--require-existing-db` verhindert den Start mit einem fehlenden oder ungültigen Analysedatensatz.
- Die Hoster-Testadresse, Prozessneustart, Stimmenpersistenz, Datenbanktausch und ein extern gesichertes Community-Backup sind praktisch geprüft und in `docs/DEPLOYMENT.md` dokumentiert.
- Projekt-, Kontakt-, Datenschutz- und Cookieinformationen sind öffentlich erreichbar.
- `ee-atlas.eu` ist per DNS und gültigem Railway-Zertifikat erreichbar. Die endgültige HTTPS-Origin ist aktiv; Startseite und `/api/health` antworten öffentlich erfolgreich.
- `v0.4.0` mit dem Titel `Beta`, aktueller README, Vorschaubildern und geprüftem Datenbanksnapshot ist veröffentlicht.
- Die vollständige 1920-Pixel-Desktoparbeitsfläche auf Mobilgeräten mit Pinch-Zoom und horizontaler Navigation ist umgesetzt. Der maschinenlesbare Datenzugriff bietet `/llms.txt`, ein Endpunktverzeichnis unter `/api/`, anklickbare Beispiele unter `/api.html` und `/openapi.json`.
- Datenupdates bleiben der kontrollierte Ablauf `Kandidat → Validierung → atomarer Datenbanktausch`. Der standardmäßig deaktivierte, in dieser Railway-Installation ausdrücklich aktivierte Monats-Scheduler nutzt dasselbe `/data`-Volume und berührt `community.sqlite3` nie. Optionale Quellfehler dürfen ältere Werte erhalten und müssen als solche sichtbar bleiben.

**Abnahme:** `https://ee-atlas.eu`, Healthcheck, Kernnavigation, Exporte und öffentliche Abstimmung funktionieren über die endgültige Domain; CI ist auf dem finalen Release-Commit grün und der Release enthält ausschließlich die vorgesehenen Artefakte.

### 3. Haupttabelle fachlich erweitern

- Die verfügbare Desktopbreite mit weiteren, bewusst ausgewählten Kennzahlen nutzen.
- Vor der Umsetzung eine feste Spaltenauswahl beschließen. Die Haupttabelle bleibt ein kuratierter Überblick; Karte und Zeitvergleich bieten weiterhin den vollständigen jeweils geeigneten Kennzahlenkatalog.
- Kandidaten nach Informationsgewinn auswählen, nicht nach bloßer Datenverfügbarkeit. Insbesondere Doppelungen zwischen absoluten Werten, Anteilen und stark korrelierten Größen vermeiden.
- Bestehende Funktionen bewahren: sticky Tabellenkopf unter der globalen Steuerleiste, zentrierte Spalten, Top-10-/Gesamtansicht, sortierabhängige Ränge, Vergleichsauswahl, Kartenaufruf und einheitliche Nachkommastellen einschließlich nachgestellter Nullen.
- In der Speichertabelle bleibt die Reihenfolge Speicherenergie, Entladeleistung, äquivalente Entladedauer – jeweils zuerst Batterie, danach Pumpspeicher.

**Abnahme:** Die zusätzliche Spaltenauswahl ist fachlich dokumentiert und nutzt große Bildschirme besser, ohne die Tabelle zu einer unlesbaren Vollansicht aller Kennzahlen zu machen.

### 4. Quartettvergleich auf Basis der Ländersteckbriefe ergänzen

- Mehrere Länder als kompakte Steckbriefkarten nebeneinander vergleichen.
- Für jede Kennzahl dokumentieren, ob ein höherer, ein niedrigerer oder kein Wert als vorteilhaft markiert werden darf.
- Fehlende oder zeitlich nicht vergleichbare Werte neutral behandeln.
- Nettoimporte und andere Kennzahlen ohne allgemeine Gewinnerichtung niemals künstlich als Sieg oder Niederlage darstellen.

**Abnahme:** Ausgewählte Länder lassen sich übersichtlich als Quartett vergleichen; jede Hervorhebung folgt einer dokumentierten Kennzahlenregel.

### 5. Berichtskette – lokal konsolidiert, bei neuen Datenständen erneut ausführen

- `eea report` erzeugt Coverage, Summary, Offline-Validierung (Markdown/JSON) und ein Prüfmanifest aus derselben lesenden SQLite-Transaktion. `--as-of` fixiert den Aggregationskalender.
- Der frühere Energy-Charts-Bericht liegt unter `docs/history/ENERGY_CHARTS_VALIDATION_2025.md`; die August-Abnahme wird nicht umgeschrieben.
- Gespeicherte monatliche und jährliche Ember-Beobachtungen für DE, FR, UK, ES und NO werden gegen den jeweils neuesten passenden Rohdaten-Cache geprüft. Erhaltene Altwerte und fehlende Caches sind nicht frisch bestätigt. Der Vergleich verwendet dieselbe Normalisierung wie der Import und ist keine unabhängige Quellenprüfung.
- Coverage, YTD-/Vorläufigkeitsstatus, Quellen und fehlende Werte in Bericht, API und Oberfläche konsistent halten.
- Datenlücken weiterhin als `null` behandeln; echte Nullwerte bleiben davon unterscheidbar.

**Abnahme:** Nach jedem gewünschten Datenstand den Bericht ausdrücklich gegen diesen Snapshot ausführen. Manifest prüfen, Fehler und Warnungen unterscheiden; ein erfolgreicher lokaler Bericht ist keine Produktionsabnahme und kein Nachweis aktueller Quelldaten.

### 6. Speicherpflege und internationale Coverage stabilisieren

- JRC Storage im Monatslauf als isolierte Headless-Sitzung mit vier gefilterten XLSX-Downloads betreiben (Operational Electrochemical sowie Pumped Hydro Storage, jeweils Leistung und Energie). Ein erfolgreich abgeschlossener Monat wird nicht automatisch wiederholt; gescheiterte Gesamtläufe können erneut abrufen.
- Battery-Charts über die beiden öffentlichen CSV-Exportknöpfe aktualisieren. Explizit konfigurierte lokale JSON-Dateien bleiben Overrides; unvollständige Overrides führen nicht stillschweigend zu Netzwerkzugriffen.
- Reale Monatsläufe beobachten: Kritische Kernquellfehler verhindern die Veröffentlichung; optionale Browser-/Exportfehler erhalten Daten und Cache dieser Quelle. Ein insgesamt erfolgreicher Monat wiederholt optionale Fehler erst im nächsten Monat.
- Der lokale Health-Ausbau weist genau diese Quellenwarnungen aus, ohne eine funktionierende Website wegen älterer Quelldaten auf HTTP 503 zu setzen.
- Änderungen des nicht formal versionierten JRC-Dashboard-Exports und der Battery-Charts-Antworten sichtbar dokumentieren, statt die Validierung stillschweigend zu lockern.
- Für Länder außerhalb Deutschlands transparent prüfen, welche stationären Batterieklassen im JRC-Projektbestand fehlen. Fehlende Heim- oder Gewerbespeicher nicht schätzen.
- Mittelfristig bei Ember nach einem CC-BY-4.0-Datensatz für Batterie- und Pumpspeicherenergie sowie Entladeleistung fragen und bei Verfügbarkeit die Übergangsquellen ablösen.
- Die weitergehende Rechteklärung des JRC-Projektbestands bleibt Post-Beta-Arbeit. Für die vorläufige nichtkommerzielle Beta hat der Projekteigentümer die Nutzung aggregierter Werte mit Attribution sowie Schätzungs- und Unvollständigkeitshinweisen akzeptiert; eine rechtliche Freigabe wird nicht behauptet.

**Abnahme:** Mehrere reale Monatsaktualisierungen mit beiden Browserquellen, erhaltenen historischen Abdeckungen und eindeutigem Quellenstatus. Der erfolgreiche Linux-Akquisitionstest ersetzt diesen Langzeitnachweis nicht.

### 7. Zusätzliche Leistungs- und Wasserkraftkennzahlen evaluieren

- Prüfen, ob für Photovoltaik eine europaweit vergleichbare DC-Nennleistung in GWp als eigene Kennzahl verfügbar ist. Die vorhandene Eurostat-Kennzahl bleibt korrekt als elektrische Nettoleistung in GW bezeichnet.
- Eine belastbare Quelle für den Energieinhalt regulierter Wasserkraftreservoirs suchen und strikt von Pumpspeicher-Speicherenergie sowie dem unvollständigen JRC-Anlagenportfolio trennen.
- Nationale Sonderquellen nur verwenden, wenn Definition, Stichtag und Vergleichbarkeit transparent ausgewiesen werden können.

**Abnahme:** Vor jeder Implementierung liegt eine dokumentierte Quellen- und Definitionsentscheidung vor. GW und GWp sowie Pumpspeicher- und allgemeine Reservoirenergie werden nicht vermischt.

## Umgesetzter Projektstand

### Zweisprachige Oberfläche

- Englische Basissprache mit vollständiger deutscher Übersetzung und DE/EN-Schalter.
- Kennzahlen, Ländersteckbriefe, Exporte, Hinweise und 250 Galerietitel sind lokalisiert.
- Sprache und aktuelle Ansicht bleiben beim Wechsel erhalten; der Erstaufruf ohne
  Sprachwahl bleibt Deutsch und verändert die Startseiten-URL nicht.
- Optionale API-Anzeigesprache `lang=en|de` bei unveränderten Zahlen und IDs.
- Technische Details und lokaler Browsercheck: [LOCALIZATION.md](docs/LOCALIZATION.md).

### Datenkern

- 31 europäische Atlasländer; Albanien und Russland gehören nicht zum Katalog.
- Monats- und Jahreswerte sind ab 2015 vorgesehen. Ember ist die alleinige Anwendungsquelle für Erzeugung, Nachfrage, Energiemix, Nettoimporte, CO₂-Intensität und nationale Großhandelspreise.
- Der zentrale Kennzahlenkatalog enthält 87 Definitionen. Für Gesamtstromerzeugung, Erneuerbare, einzelne erneuerbare und fossile Technologien sowie Kernenergie stehen jährliche Pro-Kopf-Werte auf Basis der Bevölkerung desselben Kalenderjahrs bereit. Fünf zusätzliche Jahreskennzahlen verknüpfen Erzeugung, Verbrauch und Inventaremissionen mit dem nominalen BIP sowie Haushalts- mit Großhandelspreisen und Bruttostromhandel mit dem Verbrauch.
- Eurostat ergänzt Bevölkerung, BIP, installierte elektrische Nettoleistung, Endkundenpreise, Bruttostromhandel und Elektromobilität.
- Haushaltsstrompreise und ihre Bestandteile werden in der analytischen Ausgabe in ct/kWh dargestellt; Nicht-Haushaltswerte bleiben in EUR/MWh. Die importierten Eurostat-Rohwerte werden dadurch nicht umgeschrieben.
- EEA-Inventaremissionen sowie das JRC-Wasserkraftinventar sind als eigenständige, klar beschriftete Datensätze integriert.
- Batterien und Pumpspeicher sind in Speicherenergie, Entladeleistung und äquivalente Entladedauer getrennt. Deutschland-Batterien stammen aus Battery-Charts; andere Batterien und sämtliche Pumpspeicher aus JRC.
- Netzwerkimporte sind validiert, zurückhaltend und atomar. Fehlerhafte Aktualisierungen verändern vorhandene Daten nicht.
- Der vollständige `refresh-all`-Ablauf arbeitet in einem isolierten Verzeichnis auf demselben Datenträger, prüft Dateisperren vor dem ersten Abruf, veröffentlicht nur einen validierten Kandidaten und hinterlässt standardmäßig keine persistenten Kandidaten- oder Rückfallkopien.

### Europakarte und Midnight-Grid-Oberfläche

- Die lokale SVG-Karte unterstützt den vollständigen Karten-Kennzahlenkatalog mit getrennten Familien und Darstellungen.
- Für ausdrücklich als verzögert berichtete Jahreskennzahlen, insbesondere installierte Leistung und die Inventaremissions-BIP-Relation, verwendet die Karte bei Bedarf das jüngste verfügbare frühere Datenjahr und weist angefordertes sowie tatsächliches Jahr getrennt aus. Es findet kein Datenbank-Backfill statt.
- Der geografische Europa-Ausschnitt ist beibehalten, die Karte ist groß und nativ vollbildfähig.
- Werte sind standardmäßig sichtbar. Die Legende nennt Minimum und Maximum samt Land sowie den Atlas-Durchschnitt. SVG- und PNG-Export enthalten den aktuellen Kartenstand mit Titel, Zeitraum, Einheit, Farbskala und automatisch erzeugter Legende.
- Kartenklicks setzen einen dauerhaften Länderfokus und verändern die Vergleichsauswahl nicht. Ein Klick auf den Kartenhintergrund löst den Fokus wieder.
- Ländersteckbriefe sind eine vollbreite, direkt verlinkbare Detailansicht. Sie öffnen aus Tabellen und aus dem Kartenfokus, bewahren die Vergleichsauswahl und zeigen jeden Katalogwert mit Zeitbasis, tatsächlichem Datenstand, Quelle, Status und Qualität. Monatswerte, Jahreswerte und Snapshots werden nicht vermischt; fehlende Werte bleiben leer. Kapazitätswerte können das jüngste verfügbare frühere Berichtsjahr anzeigen, ohne einen Datenbank-Backfill vorzunehmen.
- Die globale Leiste für Jahr, Zeitraum, Auswertung und Vergleich wandert beim Scrollen mit.
- Am Seitenanfang zeigt das Browser-Tab `European Electricity Atlas`; beim Scrollen folgt es der aktuellen Hauptansicht mit einem kurzen `EEA`-Abschnittstitel.
- `Europa Overload` ist ein optionaler, speicherbarer Schalter für 250 kuratierte und attribuierte Wikimedia-Commons-Postkarten aus den Atlasländern. Ohne Aktivierung werden keine Postkartenbilder geladen.
- Die Postkarten lassen sich per Maus und Tastatur in einer Vollbildgalerie öffnen. In der geöffneten Galerie stimmen Pfeil nach oben und Pfeil nach unten über dieselben geschützten Voting-Aktionen wie die Daumen-Schaltflächen ab; außerhalb der Galerie bleibt das normale Tastenverhalten erhalten. Titel, Land, Urheber, Lizenz und Commons-Link bleiben sichtbar; öffentliche Daumenstimmen, Score und geteilte Rangplätze werden getrennt in der Community-Datenbank gespeichert.
- Lokales Atlas-Logo, kontextbezogene Info-Popovers, konsistente Interaktionszustände, reduzierte Bewegung bei `prefers-reduced-motion` sowie dezente Auswahl-, Sortier-, Fokus- und Exportanimationen sind umgesetzt.
- Karten- und Zeitvergleich-Auswahl verwenden gruppierte Atlas-Menüs. Kennzahlenvarianten folgen, soweit vorhanden, der Reihenfolge absolut, Anteil und pro Kopf.
- Karte, Zeitvergleich, Ländersteckbriefe und Exporte verwenden denselben dreiteiligen Beschriftungsvertrag aus Thema, Messgröße und Einheit beziehungsweise Bezugsgröße; technische Kennzahlen-IDs bleiben stabil.
- Auf Mobilgeräten bleibt bewusst die vollständige 1920-Pixel-Desktoparbeitsfläche erhalten. Sie wird initial auf die Gerätebreite skaliert; Zoom und horizontale Navigation bleiben verfügbar.

### Tabellen

- Haupt-, Speicher- und Elektromobilitätstabellen besitzen lokale Flaggen, sortierabhängige Ränge, explizite Auf-/Ab-Sortierung und einheitliche Formatierung.
- Tabellenköpfe bleiben beim vertikalen Scrollen unter der globalen Steuerleiste sichtbar; Kopf- und Datenspalten bleiben ausgerichtet.
- Beim Ausklappen bleibt die aktuelle Kameraposition erhalten. Beim Einklappen wird zur jeweiligen Tabellenüberschrift zurückgescrollt.
- Spaltenüberschriften und Inhalte sind zentriert; die frühere gebrochene sichtbare Überschrift `Auswahl` ist entfernt.
- Numerische Werte verwenden je Kennzahl eine einheitliche Präzision mit nachgestellten Nullen.
- Kennzahlenspalten lassen sich sortieren, markieren die aktive Sortierspalte und können aus Haupt-, Speicher- und Elektromobilitätstabelle direkt auf die Karte übertragen werden.
- In der Haupttabelle dient der Rangkreis gleichzeitig als eindeutige Auswahlaktion für den Ländervergleich; eine separate sichtbare Auswahlspalte ist nicht erforderlich.
- Die Speichertabelle zeigt Speicherenergie vor Entladeleistung und Entladedauer.

### Zeitvergleich

- Ein bis zehn eindeutige Länder und genau eine zeitfähige Kennzahl können monatlich oder jährlich verglichen werden; Snapshot-Kennzahlen bleiben ausgeschlossen.
- Der native SVG-Plot enthält echte Datenlücken, lokale Endpunktflaggen, kollisionsbehandelte Ländertags, kontrastreiche flaggenbasierte Linienfarben und einen Atlas-Durchschnitt über alle jeweils vorhandenen Länderwerte.
- Das Live-Ranking folgt dem berührten oder fixierten Zeitpunkt und ordnet die gewählten Länder neu. Hover-Aktualisierungen werden mit 120 Millisekunden führend und nachlaufend gedrosselt, ohne die freie Bewegung durch den Plot zu verhindern; Klick fixiert sofort.
- Relative Veränderungen verwenden das Startjahr des gewählten Zeitraums. Bei Monatswerten wird stets derselbe Kalendermonat dieses Basisjahrs verglichen. Fehlende und echte Null-Basiswerte bleiben unberechnet.
- YTD, ein Jahr, drei Jahre, fünf Jahre, zehn Jahre und Max stehen als Schnellbereiche bereit; ein eigener Zeitraum bleibt möglich.
- Die Y-Achse kann zwischen vollständigem Bezugsrahmen und sichtbarem Datenbereich wechseln. Normale Prozentwerte behalten 100 % als Obergrenze, divergierende Kennzahlen können symmetrisch um null dargestellt werden; der Modus ist Bestandteil des Direktlinks.
- Standard- und Vollbildansicht verwenden dieselbe Diagrammgeometrie. Auswahl, Zeitraum, Kennzahl und fixierter Zeitpunkt bleiben beim Wechsel erhalten.
- Direktlinks sowie lokale CSV-, SVG- und PNG-Exporte sind umgesetzt.

### Qualitätssicherung

- Die automatisierte Testsuite verwendet ausschließlich lokale Fixtures, führt keine Live-Imports aus und deckt inzwischen auch den Refresh-Lebenszyklus sowie den dreiteiligen Beschriftungsvertrag ab.
- Eine GitHub-Actions-Pipeline führt dieselbe Suite mit Python 3.11 und Node 22 sowie JavaScript-Syntaxprüfungen auf Pushes, Pull Requests und manuellen Läufen aus.
- Die Full-HD-/WQHD-Darstellung wurde durch den Projekteigentümer vorläufig abgenommen. Ein bei der eingeschränkten Agentenprüfung gefundener horizontaler Überlauf ist behoben.
- Karte, Flaggen, Logo und Diagramme sind lokale Assets. Nur der ausdrücklich aktivierte Europa-Overload-Modus lädt Wikimedia-Commons-Bilder.
- Der ältere K2-Auftrag `docs/K2_DATA_EXPANSION_UI_INTEGRATION.md` bleibt als archivierte Übergabedokumentation erhalten.

## Leitplanken

- Der Atlas ist desktop-first. Mobile Browser erhalten die vollständige 1920-Pixel-Desktoparbeitsfläche initial skaliert; eine separate native Mobile-Oberfläche ist derzeit kein Produktziel.
- Monat ist die kleinste Einheit für Strom- und Preisdaten.
- Fehlende Werte bleiben fehlend und werden niemals als erfundene Nullwerte dargestellt.
- Fachlich unterschiedliche Quellen und Definitionen dürfen nicht automatisch addiert oder vermischt werden.
- Bei Speicherkennzahlen wird Speicherenergie beziehungsweise Kapazität immer vor Entladeleistung dargestellt.
- Installierte elektrische Nettoleistung wird in GW dargestellt; GWp wird nur für eine künftig eigens definierte Photovoltaik-Nennleistung verwendet.
- API-Schlüssel und andere Zugangsdaten dürfen weder ausgegeben noch in SQLite gespeichert werden.
- Tests führen keine Live-Imports aus und verwenden ausschließlich lokale Fixtures.
