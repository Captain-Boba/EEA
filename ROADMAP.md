# European Electricity Atlas – Roadmap

Stand: 25. August 2026

Diese Roadmap trennt den aktuell umgesetzten Projektstand von offenen Produktentscheidungen. Historische K2-Arbeitsaufträge sind als solche gekennzeichnet und gelten nicht als aktuelle Spezifikation.

Der operative Weg bis zur Veröffentlichung mit Abnahme-Gates steht in [BETA_ROADMAP.md](BETA_ROADMAP.md).

## Aktuelle Arbeitsprioritäten

### 1. Europa Overload responsiv abschließen

- Die Postkartenbreite nicht länger auf beiden Referenzmonitoren nahezu identisch deckeln, sondern an die tatsächlich verfügbare Seitenfläche koppeln.
- 1920×1080 und 2560×1440 jeweils bei 100 % Browserzoom abnehmen: keine problematische Überdeckung des Atlas, keine horizontale Scrollleiste, vollständige Captions und sichtbar bessere Nutzung der WQHD-Fläche.
- Das globale `body { zoom: 1.1; }` prüfen und nicht durch weitere Zoom- oder Transform-Tricks kompensieren.
- Die bereits vorhandene Vollbildgalerie mit Stern-Schließen, zyklischer Tastaturbedienung und öffentlichen Daumenstimmen bewahren.

**Abnahme:** Die Postkarten sind auf Full HD kompakt und auf WQHD sichtbar größer; beide Ansichten funktionieren zusammen mit der Vollbildgalerie ohne Überdeckung oder Scrollsprünge.

### 2. Öffentliche Beta vorbereiten

- Den aktuellen SQLite- und Standardbibliothek-Ansatz beibehalten; keine neue Datenbanktechnik und keine unnötige Infrastruktur einführen.
- Host und Port konfigurierbar machen, einen hostinggeeigneten Start und den vorhandenen Healthcheck absichern sowie feste Windows-Pfade ausschließen.
- Den Datenbankpfad für einen persistenten, read-only Hostingbetrieb konfigurierbar machen. Die getrennte Community-Datenbank für öffentliche Stimmen benötigt einen konfigurierbaren persistenten Schreibpfad und ein dokumentiertes Backupverfahren. Datenupdates bleiben zunächst der kontrollierte Ablauf `lokaler Import → Validierung → geprüfte atlas.sqlite3 → neuer Deploy`.
- Keine Importfunktion über die Weboberfläche und keinen automatischen Scheduler als Startvoraussetzung einführen.
- Zuerst eine Hoster-Testadresse vollständig prüfen. DNS für `ee-atlas.eu` erst nach erfolgreicher Abnahme verbinden.
- Deployment, Umgebungsvariablen, Datenbankaustausch und spätere Domainverbindung in einer verständlichen Schrittfolge dokumentieren.

**Abnahme:** Lokaler Windowsbetrieb und hostingähnlicher Betrieb starten reproduzierbar; Atlas, API, Direktlinks, Vollbildansichten und Exporte sind an der Testadresse geprüft. Erst danach wird die Domain verbunden und die Beta veröffentlicht.

### 3. Haupttabelle fachlich erweitern

- Die verfügbare Desktopbreite mit weiteren, bewusst ausgewählten Kennzahlen nutzen.
- Vor der Umsetzung eine feste Spaltenauswahl beschließen. Die Haupttabelle bleibt ein kuratierter Überblick; Karte und Zeitreihenvergleich bieten weiterhin den vollständigen jeweils geeigneten Kennzahlenkatalog.
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

### 5. Datenprüfung und Berichte modernisieren

- Die als historisch gekennzeichnete `data/reports/VALIDATION.generated.md` durch einen reproduzierbaren Validierungsbericht des aktuellen Ember-Datenkerns ablösen.
- Den Vertrag des CLI-Befehls `report` bereinigen: Hilfe, tatsächlich erzeugte Dateien und Dokumentation müssen übereinstimmen.
- Für eine repräsentative Auswahl großer und kleiner Länder monatliche und jährliche Ember-Werte manuell gegen die Quelldaten prüfen. Mindestens Erzeugung, Nachfrage, eine absolute Erzeugungsart und deren Anteil dokumentieren.
- Coverage, YTD-/Vorläufigkeitsstatus, Quellen und fehlende Werte in Bericht, API und Oberfläche konsistent halten.
- Datenlücken weiterhin als `null` behandeln; echte Nullwerte bleiben davon unterscheidbar.

**Abnahme:** Kein als aktuell bezeichneter Bericht weist Energy Charts als Anwendungsquelle aus. Dokumentierte Ember-Stichproben sind nachvollziehbar, und Bericht, API sowie Oberfläche beschreiben denselben Datenbestand. Der historische Bericht kann anschließend entfallen.

### 6. Speicherpflege und internationale Coverage stabilisieren

- Den bewussten JRC-CLI-Abruf höchstens einmal pro Kalendermonat betreiben und die reale Abdeckung beobachten.
- Battery-Charts ausschließlich über den manuellen, atomaren Import der beiden JSON-Dateien aktualisieren. Der Atlas führt keinen automatischen Battery-Charts-Netzwerkzugriff aus.
- Nach mehreren realen Aktualisierungen entscheiden, ob ein externer monatlicher Scheduler sinnvoll ist. Der Atlas-Server selbst startet weiterhin keine Hintergrundimporte.
- Änderungen der nicht formal versionierten JRC-Projekt-API und der Battery-Charts-Antworten sichtbar dokumentieren, statt die Validierung stillschweigend zu lockern.
- Für Länder außerhalb Deutschlands transparent prüfen, welche stationären Batterieklassen im JRC-Projektbestand fehlen. Fehlende Heim- oder Gewerbespeicher nicht schätzen.
- Die Lizenz- und Weitergabesituation des JRC-Projektbestands vor einer öffentlichen oder kommerziellen Datenveröffentlichung abschließend klären.

**Abnahme:** Mehrere reale Monatsaktualisierungen laufen mit maximal einem JRC-Request, ohne Battery-Charts-Netzwerkzugriff, ohne Duplikate und ohne Verlust des vorherigen Datenstands bei Fehlern.

### 7. Zusätzliche Leistungs- und Wasserkraftkennzahlen evaluieren

- Prüfen, ob für Photovoltaik eine europaweit vergleichbare DC-Nennleistung in GWp als eigene Kennzahl verfügbar ist. Die vorhandene Eurostat-Kennzahl bleibt korrekt als elektrische Nettoleistung in GW bezeichnet.
- Eine belastbare Quelle für den Energieinhalt regulierter Wasserkraftreservoirs suchen und strikt von Pumpspeicher-Speicherenergie sowie dem unvollständigen JRC-Anlagenportfolio trennen.
- Nationale Sonderquellen nur verwenden, wenn Definition, Stichtag und Vergleichbarkeit transparent ausgewiesen werden können.

**Abnahme:** Vor jeder Implementierung liegt eine dokumentierte Quellen- und Definitionsentscheidung vor. GW und GWp sowie Pumpspeicher- und allgemeine Reservoirenergie werden nicht vermischt.

## Umgesetzter Projektstand

### Datenkern

- 31 europäische Atlasländer; Albanien und Russland gehören nicht zum Katalog.
- Monats- und Jahreswerte sind ab 2015 vorgesehen. Ember ist die alleinige Anwendungsquelle für Erzeugung, Nachfrage, Energiemix, Nettoimporte, CO₂-Intensität und nationale Großhandelspreise.
- Der zentrale Kennzahlenkatalog enthält 87 Definitionen. Für Gesamtstromerzeugung, Erneuerbare, einzelne erneuerbare und fossile Technologien sowie Kernenergie stehen jährliche Pro-Kopf-Werte auf Basis der Bevölkerung desselben Kalenderjahrs bereit. Fünf zusätzliche Jahreskennzahlen verknüpfen Erzeugung, Verbrauch und Inventaremissionen mit dem nominalen BIP sowie Haushalts- mit Großhandelspreisen und Bruttostromhandel mit dem Verbrauch.
- Eurostat ergänzt Bevölkerung, BIP, installierte elektrische Nettoleistung, Endkundenpreise, Bruttostromhandel und Elektromobilität.
- Haushaltsstrompreise und ihre Bestandteile werden in der analytischen Ausgabe in ct/kWh dargestellt; Nicht-Haushaltswerte bleiben in EUR/MWh. Die importierten Eurostat-Rohwerte werden dadurch nicht umgeschrieben.
- EEA-Inventaremissionen sowie das JRC-Wasserkraftinventar sind als eigenständige, klar beschriftete Datensätze integriert.
- Batterien und Pumpspeicher sind in Speicherenergie, Entladeleistung und äquivalente Entladedauer getrennt. Deutschland-Batterien stammen aus Battery-Charts; andere Batterien und sämtliche Pumpspeicher aus JRC.
- Netzwerkimporte sind validiert, zurückhaltend und atomar. Fehlerhafte Aktualisierungen verändern vorhandene Daten nicht.

### Europakarte und Midnight-Grid-Oberfläche

- Die lokale SVG-Karte unterstützt den vollständigen Karten-Kennzahlenkatalog mit getrennten Familien und Darstellungen.
- Für ausdrücklich als verzögert berichtete Jahreskennzahlen, insbesondere installierte Leistung und die Inventaremissions-BIP-Relation, verwendet die Karte bei Bedarf das jüngste verfügbare frühere Datenjahr und weist angefordertes sowie tatsächliches Jahr getrennt aus. Es findet kein Datenbank-Backfill statt.
- Der geografische Europa-Ausschnitt ist beibehalten, die Karte ist groß und nativ vollbildfähig.
- Werte sind standardmäßig sichtbar. Die Legende nennt Minimum und Maximum samt Land sowie den Atlas-Durchschnitt. SVG- und PNG-Export enthalten den aktuellen Kartenstand mit Titel, Zeitraum, Einheit, Farbskala und automatisch erzeugter Legende.
- Kartenklicks setzen einen dauerhaften Länderfokus und verändern die Vergleichsauswahl nicht. Ein Klick auf den Kartenhintergrund löst den Fokus wieder.
- Ländersteckbriefe sind eine vollbreite, direkt verlinkbare Detailansicht. Sie öffnen aus Tabellen und aus dem Kartenfokus, bewahren die Vergleichsauswahl und zeigen jeden Katalogwert mit Zeitbasis, tatsächlichem Datenstand, Quelle, Status und Qualität. Monatswerte, Jahreswerte und Snapshots werden nicht vermischt; fehlende Werte bleiben leer. Kapazitätswerte können das jüngste verfügbare frühere Berichtsjahr anzeigen, ohne einen Datenbank-Backfill vorzunehmen.
- Die globale Leiste für Jahr, Zeitraum, Auswertung und Vergleich wandert beim Scrollen mit.
- Das Browser-Tab zeigt `EEA` und die aktuelle Hauptansicht.
- `Europa Overload` ist ein optionaler, speicherbarer Schalter für 250 kuratierte und attribuierte Wikimedia-Commons-Postkarten aus den Atlasländern. Ohne Aktivierung werden keine Postkartenbilder geladen.
- Die Postkarten lassen sich per Maus und Tastatur in einer Vollbildgalerie öffnen. Titel, Land, Urheber, Lizenz und Commons-Link bleiben sichtbar; öffentliche Daumenstimmen, Score und geteilte Rangplätze werden getrennt in der Community-Datenbank gespeichert.
- Lokales Atlas-Logo, kontextbezogene Info-Popovers, konsistente Interaktionszustände, reduzierte Bewegung bei `prefers-reduced-motion` sowie dezente Auswahl-, Sortier-, Fokus- und Exportanimationen sind umgesetzt.
- Karten- und Plottool-Auswahl verwenden gruppierte Atlas-Menüs. Kennzahlenvarianten folgen, soweit vorhanden, der Reihenfolge absolut, Anteil und pro Kopf.

### Tabellen

- Haupt-, Speicher- und Elektromobilitätstabellen besitzen lokale Flaggen, sortierabhängige Ränge, explizite Auf-/Ab-Sortierung und einheitliche Formatierung.
- Tabellenköpfe bleiben beim vertikalen Scrollen unter der globalen Steuerleiste sichtbar; Kopf- und Datenspalten bleiben ausgerichtet.
- Beim Ausklappen bleibt die aktuelle Kameraposition erhalten. Beim Einklappen wird zur jeweiligen Tabellenüberschrift zurückgescrollt.
- Spaltenüberschriften und Inhalte sind zentriert; die frühere gebrochene sichtbare Überschrift `Auswahl` ist entfernt.
- Numerische Werte verwenden je Kennzahl eine einheitliche Präzision mit nachgestellten Nullen.
- Kennzahlenspalten lassen sich sortieren, markieren die aktive Sortierspalte und können aus Haupt-, Speicher- und Elektromobilitätstabelle direkt auf die Karte übertragen werden.
- In der Haupttabelle dient der Rangkreis gleichzeitig als eindeutige Auswahlaktion für den Ländervergleich; eine separate sichtbare Auswahlspalte ist nicht erforderlich.
- Die Speichertabelle zeigt Speicherenergie vor Entladeleistung und Entladedauer.

### Zeitreihenvergleich

- Ein bis zehn eindeutige Länder und genau eine zeitfähige Kennzahl können monatlich oder jährlich verglichen werden; Snapshot-Kennzahlen bleiben ausgeschlossen.
- Der native SVG-Plot enthält echte Datenlücken, lokale Endpunktflaggen, kollisionsbehandelte Ländertags, kontrastreiche flaggenbasierte Linienfarben und einen Atlas-Durchschnitt über alle jeweils vorhandenen Länderwerte.
- Das Live-Ranking folgt dem berührten oder fixierten Zeitpunkt und ordnet die gewählten Länder neu. Hover-Aktualisierungen werden mit 120 Millisekunden führend und nachlaufend gedrosselt, ohne die freie Bewegung durch den Plot zu verhindern; Klick fixiert sofort.
- Relative Veränderungen verwenden das Startjahr des gewählten Zeitraums. Bei Monatswerten wird stets derselbe Kalendermonat dieses Basisjahrs verglichen. Fehlende und echte Null-Basiswerte bleiben unberechnet.
- YTD, ein Jahr, drei Jahre, fünf Jahre, zehn Jahre und Max stehen als Schnellbereiche bereit; ein eigener Zeitraum bleibt möglich.
- Die Y-Achse kann zwischen vollständigem Bezugsrahmen und sichtbarem Datenbereich wechseln. Normale Prozentwerte behalten 100 % als Obergrenze, divergierende Kennzahlen können symmetrisch um null dargestellt werden; der Modus ist Bestandteil des Direktlinks.
- Standard- und Vollbildansicht verwenden dieselbe Diagrammgeometrie. Auswahl, Zeitraum, Kennzahl und fixierter Zeitpunkt bleiben beim Wechsel erhalten.
- Direktlinks sowie lokale CSV-, SVG- und PNG-Exporte sind umgesetzt.

### Qualitätssicherung

- Der vollständige lokale Stand besteht am 25. August 2026 aus 143 erfolgreichen automatisierten Tests.
- Die automatisierte Testsuite verwendet ausschließlich lokale Fixtures und führt keine Live-Imports aus.
- Karte, Flaggen, Logo und Diagramme sind lokale Assets. Nur der ausdrücklich aktivierte Europa-Overload-Modus lädt Wikimedia-Commons-Bilder.
- Der ältere K2-Auftrag `docs/K2_DATA_EXPANSION_UI_INTEGRATION.md` bleibt als archivierte Übergabedokumentation erhalten.

## Leitplanken

- Der Atlas ist desktop-first. Mobile Ansichten müssen die Kerninhalte erreichbar halten, benötigen aber keine erzwungene Funktions- oder Layoutparität mit der großflächigen Desktopanalyse.
- Monat ist die kleinste Einheit für Strom- und Preisdaten.
- Fehlende Werte bleiben fehlend und werden niemals als erfundene Nullwerte dargestellt.
- Fachlich unterschiedliche Quellen und Definitionen dürfen nicht automatisch addiert oder vermischt werden.
- Bei Speicherkennzahlen wird Speicherenergie beziehungsweise Kapazität immer vor Entladeleistung dargestellt.
- Installierte elektrische Nettoleistung wird in GW dargestellt; GWp wird nur für eine künftig eigens definierte Photovoltaik-Nennleistung verwendet.
- API-Schlüssel und andere Zugangsdaten dürfen weder ausgegeben noch in SQLite gespeichert werden.
- Tests führen keine Live-Imports aus und verwenden ausschließlich lokale Fixtures.
