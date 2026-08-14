# European Electricity Atlas – Roadmap

Stand: 14. August 2026

Diese Roadmap enthält nur noch offene oder bewusst fortlaufende Arbeiten. Bereits umgesetzte Funktionen sind weiter unten als verifizierter Projektstand dokumentiert.

## Aktuelle Arbeitsprioritäten

### 1. Haupttabelle erweitern und Scrollverhalten abschließen

- Die Tabellenköpfe beim vertikalen Scrollen dauerhaft sichtbar halten. Sie müssen direkt unterhalb der globalen Sticky-Steuerleiste liegen, auch wenn diese durch Umbruch ihre Höhe verändert, und dürfen nicht von ihr verdeckt werden.
- Kopf- und Datenspalten müssen beim horizontalen Scrollen exakt ausgerichtet bleiben.
- Die Haupttabelle um weitere fachlich sinnvolle Kennzahlen aus dem vorhandenen Katalog erweitern, damit die verfügbare Desktopbreite für zusätzliche Informationen genutzt wird.
- Die konkrete zusätzliche Spaltenauswahl vor der Umsetzung festlegen. Keine beliebige Vollbelegung und keine doppelte Darstellung derselben Aussage; die Haupttabelle bleibt ein kuratierter Überblick, während Karte und Zeitreihenvergleich weiterhin den vollständigen Kennzahlenkatalog anbieten.
- Sämtliche Spaltenüberschriften und Inhalte konsistent zentrieren. Die Länderzelle wird dabei als gemeinsame Einheit aus Flagge, Name, Kürzel und Status behandelt.
- Bestehende Funktionen bewahren: Top-10-/Gesamtansicht, sortierabhängige Rangnummern, Auswahl für den Zeitreihenvergleich, Kartenaufruf je Kennzahl, lokale Flaggen und einheitliche Nachkommastellen einschließlich nachgestellter Nullen.
- In der Speichertabelle gilt weiterhin die Reihenfolge Speicherenergie beziehungsweise Kapazität, Entladeleistung, äquivalente Entladedauer – jeweils zuerst Batterie, danach Pumpspeicher.

**Abnahme:** Der Tabellenkopf bleibt beim Seiten- und Tabellen-Scrollen direkt unter der globalen Steuerleiste sichtbar und spaltenbündig. Auf großen Bildschirmen nutzt die Haupttabelle die verfügbare Breite mit den zuvor festgelegten zusätzlichen Kennzahlen, ohne unlesbare Verdichtung. Sortierung, Ränge, Auswahl und Kartenaktionen funktionieren unverändert.

### 2. Festen Kartenfokus vollständig bedienbar machen

- Der bereits vorhandene dauerhafte Fokus eines angeklickten Landes bleibt von Hover, Tastaturfokus und Vergleichsauswahl getrennt.
- Eine eindeutige Aktion zum Lösen des festgehaltenen Länderfokus ergänzen; alternativ darf ein erneuter Klick auf dasselbe Land den Fokus nachvollziehbar lösen.
- Fokus setzen, Fokus lösen und die unveränderte Vergleichsauswahl automatisiert absichern.

**Abnahme:** Ein Land lässt sich per Maus und Tastatur festhalten und wieder lösen. Temporäre Tooltips überschreiben die Infokachel nicht und Kartenaktionen verändern niemals die Länderauswahl des Zeitreihenvergleichs.

### 3. Ländersteckbrief entwickeln

- Aus Tabelle und Karte eine zusammenhängende Detailansicht für genau ein Land öffnen.
- Vor der Umsetzung festlegen, ob eine eigene Ansicht, ein großes Modal oder ein Seitenpanel die verständlichste Navigation bietet.
- Alle verfügbaren Kennzahlen nach Stromsystem, Energiemix, Handel, Preisen, Klima, Sozioökonomie und Speicher gruppieren.
- Zeitraum, Einheit, Datenstatus, fehlende Coverage und Quelle direkt am jeweiligen Wert zeigen.
- Fehlende Daten niemals durch Nullwerte oder Schätzungen ersetzen.

**Abnahme:** Ein Land besitzt eine vollständige, klar gegliederte Detailansicht, die aus der bestehenden Atlasoberfläche geöffnet und eindeutig wieder verlassen werden kann.

### 4. Quartettvergleich auf Basis der Ländersteckbriefe ergänzen

- Mehrere Länder als kompakte Steckbriefkarten nebeneinander vergleichen.
- Für jede Kennzahl fachlich dokumentieren, ob ein höherer, ein niedrigerer oder kein Wert als vorteilhaft markiert werden darf.
- Fehlende oder zeitlich nicht vergleichbare Werte neutral behandeln.
- Nettoimporte und andere Kennzahlen ohne allgemeine Gewinnerichtung niemals künstlich als Sieg oder Niederlage darstellen.

**Abnahme:** Ausgewählte Länder lassen sich übersichtlich als Quartett vergleichen; jede Hervorhebung folgt einer dokumentierten Kennzahlenregel.

### 5. Datenprüfung und Coverage-Berichte auf den aktuellen Datenkern umstellen

- Die eingecheckten Dateien unter `data/reports/` ersetzen oder entfernen: Sie dokumentieren noch den früheren Energy-Charts-Datenstand und sind nicht mehr mit der aktuellen Ember-only-Anwendungsarchitektur vereinbar.
- Neue Berichte aus dem aktuellen Schema mit Ember, Ember-Preisen, Eurostat, Battery-Charts und JRC erzeugen.
- Den Vertrag des CLI-Befehls `report` bereinigen: Hilfe, tatsächlich erzeugte Dateien und Dokumentation müssen übereinstimmen; die veraltete `VALIDATION.generated.md` darf nicht als scheinbar aktuelles Ergebnis liegen bleiben.
- Für eine repräsentative Auswahl großer und kleiner Länder monatliche und jährliche Ember-Werte manuell gegen die Quelldaten prüfen. Mindestens Erzeugung, Nachfrage, eine absolute Erzeugungsart und deren Anteil dokumentieren.
- Coverage, YTD-/Vorläufigkeitsstatus, Quellen und fehlende Werte in Bericht, API und Oberfläche konsistent halten.
- Datenlücken weiterhin als `null` behandeln; echte Nullwerte bleiben davon unterscheidbar.

**Abnahme:** Es existiert kein aktueller Bericht mehr, der Energy Charts als Anwendungsquelle ausweist. Dokumentierte Ember-Stichproben sind nachvollziehbar, und Bericht, API sowie Oberfläche beschreiben denselben Datenbestand.

### 6. Speicherpflege und internationale Coverage stabilisieren

- Den bewussten JRC-CLI-Abruf höchstens einmal pro Kalendermonat betreiben und die reale Abdeckung beobachten.
- Battery-Charts ausschließlich über den manuellen, atomaren Import der beiden JSON-Dateien aktualisieren. Der Atlas darf keinen automatischen Battery-Charts-Netzwerkzugriff ausführen.
- Nach mehreren realen Aktualisierungen entscheiden, ob ein externer monatlicher Scheduler sinnvoll ist. Der Atlas-Server selbst startet weiterhin keine Hintergrundimporte.
- Änderungen der nicht formal versionierten JRC-Projekt-API und der Battery-Charts-Antworten sichtbar dokumentieren, statt die Validierung stillschweigend zu lockern.
- Für Länder außerhalb Deutschlands transparent prüfen, welche stationären Batterieklassen im JRC-Projektbestand fehlen. Fehlende Heim- oder Gewerbespeicher nicht schätzen.
- Die Lizenz- und Weitergabesituation des JRC-Projektbestands vor einer öffentlichen oder kommerziellen Datenveröffentlichung abschließend klären.

**Abnahme:** Mehrere reale Monatsaktualisierungen laufen mit maximal einem JRC-Request, ohne Battery-Charts-Netzwerkzugriff, ohne Duplikate und ohne Verlust des vorherigen Datenstands bei Fehlern.

### 7. Wasserkraft-Magazinkapazität als eigene Kennzahl evaluieren

- Eine belastbare, möglichst europaweit vergleichbare Quelle für den Energieinhalt regulierter Wasserkraftreservoirs suchen.
- Diese Kennzahl strikt von Pumpspeicher-Speicherenergie und vom JRC-Projektportfolio trennen.
- Nationale Sonderquellen nur verwenden, wenn Definition, Stichtag und Vergleichbarkeit transparent ausgewiesen werden können.

**Abnahme:** Vor einer Implementierung liegt eine dokumentierte Quellen- und Definitionsentscheidung vor; Pumpspeicherwerte werden nicht als allgemeine Wasserkraft-Magazinkapazität ausgegeben.

## Verifizierter Projektstand

### Release- und Qualitätsstand

- Aktueller Checkout: `main` und `origin/main` auf `79de95c`; der Funktionsstand ist mit `v0.3.0` auf `10aa837` markiert. Die nachfolgenden Commits aktualisieren ausschließlich Dokumentation und Vorschaubilder.
- 82 automatisierte Tests wurden am 14. August 2026 mit `PYTHONPATH=src` erfolgreich ausgeführt.
- Das Web-Frontend lädt Karte, Flaggen, Logo und Diagramme vollständig lokal und verwendet keine Laufzeit-CDNs oder externen Kartendienste.

### Datenkern

- 31 europäische Atlasländer; Albanien und Russland gehören nicht zum Katalog.
- Monats- und Jahreswerte sind ab 2015 vorgesehen. Ember ist die alleinige Anwendungsquelle für Erzeugung, Nachfrage, Energiemix, Nettoimporte und CO₂-Intensität; die separate Ember-Preisdatei liefert monatliche und gewichtete jährliche Großhandelspreise.
- Eurostat ergänzt jährliche Bevölkerung, BIP und daraus abgeleitete Pro-Kopf-Kennzahlen.
- Batterien und Pumpspeicher sind in Speicherenergie, Entladeleistung und äquivalente Entladedauer getrennt. Deutschland-Batterien stammen aus Battery-Charts; andere Batterien und sämtliche Pumpspeicher aus JRC.
- Netzwerkimporte sind validiert, zurückhaltend und atomar. Fehlerhafte Aktualisierungen dürfen vorhandene Daten nicht verändern.

### Europakarte und Midnight-Grid-Oberfläche

- Die interaktive lokale SVG-Karte unterstützt den vollständigen Karten-Kennzahlenkatalog mit getrennten Familien und Darstellungen.
- Der geografische Europa-Ausschnitt wurde beibehalten, die Karte vergrößert und als native Vollbildansicht umgesetzt.
- Werte sind standardmäßig sichtbar. SVG- und PNG-Export enthalten den aktuellen Kartenstand mit Titel, Zeitraum, Einheit, Farbskala und automatisch erzeugter Legende.
- Kartenklicks setzen bereits einen dauerhaften Länderfokus und verändern die Vergleichsauswahl nicht; offen ist nur noch die explizite Aktion zum Lösen dieses Fokus.
- Die globale Leiste für Jahr, Zeitraum, Auswertung und Vergleich ist sticky.
- Eigenständiges lokales Atlas-Logo, kontextbezogene Info-Popovers, konsistente Interaktionszustände, reduzierte Bewegung bei `prefers-reduced-motion` und dezente Auswahl-, Sortier-, Fokus- und Exportanimationen sind umgesetzt.

### Tabellen

- Haupt- und Speichertabelle besitzen lokale Flaggen, Top-10-/Gesamtansicht, sortierabhängige Ränge und animierte Umsortierung.
- Das früher sichtbare gebrochene Feld `Auswahl` wurde entfernt; die Auswahlspalte besitzt nur noch eine zugängliche, visuell versteckte Bezeichnung.
- Numerische Werte verwenden je Kennzahl eine einheitliche Präzision mit nachgestellten Nullen.
- Jede Haupttabellen-Kennzahl lässt sich sortieren und direkt auf die Karte übertragen.
- Die Speichertabelle zeigt bereits Speicherenergie vor Entladeleistung und Entladedauer.
- Noch offen sind der korrekte Sticky-Abstand des Tabellenkopfs unter der globalen Steuerleiste, die vollständig zentrierte Länderzelle und die Auswahl zusätzlicher Haupttabellenspalten.

### Zeitreihenvergleich V1 und V2

- Ein bis zehn eindeutige Länder und genau eine zeitfähige Kennzahl können monatlich oder jährlich verglichen werden; Snapshot-Kennzahlen bleiben ausgeschlossen.
- Der native SVG-Plot enthält Datenlücken, lokale Endpunktflaggen, kollisionsbehandelte Ländertags, kontrastreiche flaggenbasierte Linienfarben und einen Atlas-Durchschnitt über alle jeweils vorhandenen Länderwerte.
- Das Live-Ranking folgt dem berührten oder fixierten Zeitpunkt und ordnet alle gewählten Länder neu.
- Relative Veränderungen verwenden unabhängig vom sichtbaren Zeitraum die feste Basis 2015: jährlich das Jahr 2015, monatlich denselben Kalendermonat 2015. Fehlende und echte Null-Basiswerte bleiben unberechnet.
- YTD, ein Jahr, drei Jahre, fünf Jahre, zehn Jahre und Max stehen als Schnellbereiche bereit; ein eigener Zeitraum bleibt möglich.
- Standard- und Vollbildansicht verwenden dieselbe Diagrammgeometrie. Auswahl, Zeitraum, Kennzahl und fixierter Zeitpunkt bleiben beim Wechsel erhalten.
- Direktlinks sowie lokale CSV-, SVG- und PNG-Exporte sind umgesetzt.

## Leitplanken

- Der Atlas ist desktop-first. Mobile Ansichten müssen die Kerninhalte erreichbar halten, benötigen aber keine erzwungene Funktions- oder Layoutparität mit der großflächigen Desktopanalyse.
- Monat ist die kleinste Einheit für Strom- und Preisdaten.
- Fehlende Werte bleiben fehlend und werden niemals als erfundene Nullwerte dargestellt.
- Fachlich unterschiedliche Quellen und Definitionen dürfen nicht automatisch addiert oder vermischt werden.
- Bei Speicherkennzahlen wird Speicherenergie beziehungsweise Kapazität immer vor Entladeleistung dargestellt.
- API-Schlüssel und andere Zugangsdaten dürfen weder ausgegeben noch in SQLite gespeichert werden.
- Tests führen keine Live-Imports aus und verwenden ausschließlich lokale Fixtures.
