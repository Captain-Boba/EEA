# European Electricity Atlas – Roadmap

Stand: 12. August 2026

Diese Datei bündelt die offenen Entwicklungspunkte des Projekts. Abgeschlossene Grundlagen werden getrennt aufgeführt, damit die Prioritätenliste ausschließlich noch ausstehende Arbeiten enthält.

## Prioritäten

### 1. Monatliche JRC-Speicheraktualisierung automatisieren

- Einen konservativen, höchstens einmal monatlich laufenden Download für die beiden JRC-Dashboard-Exporte `Power (GW)` und `Capacity (GWh)` entwickeln.
- Zuerst prüfen, ob JRC einen stabilen und für automatisierte Abrufe vorgesehenen Download-Endpunkt bereitstellt. Nur falls das nicht möglich ist, eine klar gekennzeichnete Browser-Automatisierung für das Qlik-Dashboard verwenden.
- In beiden Exporten exakt dieselben Filter anwenden: `Project status = Operational` und `Technology = Mechanical + Electrochemical`.
- Beide Dateien vollständig herunterladen und erst gemeinsam importieren, nachdem Snapshot-Datum, Header, Länder, Filterstatus und numerische Werte validiert wurden.
- Unveränderte Rohdateien, Abrufzeitpunkt, SHA-256 und Herkunft speichern. Bei Download-, Struktur- oder Validierungsfehlern muss der vorhandene Snapshot unverändert bleiben.
- Abrufe mit klarer Kennung, Timeouts, begrenzten Wiederholungen und ohne parallele Requests ausführen.
- In Dokumentation und Oberfläche weiterhin deutlich machen, dass diese JRC-Werte elektrisch aufladbare Speicherprojekte abbilden und nicht die gesamte nationale Wasserkraft-Magazinkapazität.

**Abnahme:** Ein einzelner Befehl lädt beide Exporte, validiert sie und ersetzt den JRC-Snapshot atomar. Ein geplanter monatlicher Lauf darf bei unveränderten oder fehlerhaften Quelldaten weder Duplikate noch Datenverlust erzeugen.

## Kurzfristige Produktziele

### 2. Kartendarstellung vergrößern und besser ausrichten

- Der Karte deutlich mehr sichtbare Fläche geben und ungenutzten horizontalen Raum vermeiden.
- Einen passenderen Europa-Ausschnitt mit einer eher quadratischen beziehungsweise ausgewogen kompakten Darstellung erarbeiten.
- Desktop-, Tablet- und Mobilansicht getrennt prüfen; kleine Länder müssen weiterhin per Maus und Tastatur erreichbar bleiben.
- `Werte anzeigen` standardmäßig aktivieren, ohne die Karte bei kleinen Ländern oder engen Viewports unlesbar zu machen.

**Abnahme:** Europa ist ohne unnötige Leerräume vollständig sichtbar, die Karte nutzt den verfügbaren Platz und Wertelabels sind beim ersten Laden eingeschaltet.

### 3. Karteninteraktion auf einen festen Länderfokus umstellen

- Die Vergleichsauswahl über Klicks auf Kartenländer vollständig entfernen.
- Ein angeklicktes Land in der Infokachel rechts neben der Karte festhalten, bis ein anderes Land gewählt oder der Fokus ausdrücklich gelöst wird.
- Hover und Tastaturfokus dürfen weiterhin temporäre Informationen zeigen, sollen den festgehaltenen Länderfokus aber nicht unbeabsichtigt überschreiben.
- Die Infokachel muss Land, Kennzahl, Wert, Einheit, Zeitraum beziehungsweise Snapshot, Datenstatus und Quelle enthalten.

**Abnahme:** Kartenklicks verändern keine Vergleichsauswahl mehr. Maus- und Tastaturbedienung können genau ein Land sichtbar und nachvollziehbar in der Infokachel festhalten.

### 4. Vergleichstool um Diagramme und freie Länderzahl erweitern

- Kennzahlen im Vergleichstool als aussagekräftige Graphen beziehungsweise Zeitreihen plotten.
- Das feste Limit von vier Vergleichsländern entfernen.
- Legende, Farben, Achsen, Einheiten und fehlende Werte auch bei vielen Ländern lesbar halten.
- Auswahl und Entfernung von Ländern so gestalten, dass ein großer Vergleichssatz kontrollierbar bleibt; bei visueller Überladung warnen, aber kein willkürliches hartes Limit setzen.

**Abnahme:** Mehr als vier Länder lassen sich auswählen und gemeinsam tabellarisch sowie grafisch vergleichen, ohne dass fehlende Werte als Null dargestellt werden.

### 5. Ländersteckbrief entwickeln

- Aus der Länderliste eine zusammenhängende Detailansicht für ein einzelnes Land öffnen.
- Vor der Umsetzung entscheiden, ob eine eigene Seite, ein großes Modal oder ein responsives Seitenpanel die beste Navigation bietet.
- Alle verfügbaren Kennzahlen nach Stromsystem, Energiemix, Handel, Preisen, Klima, Sozioökonomie und Speicher gruppiert darstellen.
- Zeitraum, Datenstatus, fehlende Coverage und Quellen direkt an den jeweiligen Werten sichtbar machen.

**Abnahme:** Ein Land kann aus der Tabelle geöffnet werden und besitzt eine vollständige, auch auf kleinen Bildschirmen nutzbare Steckbriefansicht ohne stilles Auffüllen fehlender Daten.

### 6. Quartettvergleich auf Basis der Ländersteckbriefe ergänzen

- Mehrere Ländersteckbriefe als kompakte Karten nebeneinander vergleichen.
- Pro Kennzahl deutlich zeigen, welches Land den höheren oder niedrigeren Wert besitzt.
- Vor jeder Hervorhebung fachlich festlegen, ob ein höherer, ein niedrigerer oder überhaupt kein Wert als „stärker“ gelten darf; beispielsweise ist eine niedrigere CO₂-Intensität positiv, während Nettoimporte keine allgemeine Gewinnerichtung besitzen.
- Fehlende und zeitlich nicht vergleichbare Werte neutral behandeln und niemals als Niederlage werten.

**Abnahme:** Ausgewählte Länder lassen sich als übersichtliche Quartettkarten vergleichen; jede Gewinner-Markierung folgt einer dokumentierten Kennzahlenregel.

### 7. Tabellenorientierung mit Flaggen und sortierabhängiger Rangnummer verbessern

- Neben jedem Ländernamen das passende Flaggen-Emoji anzeigen, einschließlich der internen Zuordnung `UK` zur britischen Flagge.
- Eine sichtbare Rangnummer als erste Datenspalte einführen. Sie zeigt ausschließlich die Position innerhalb der aktuell gewählten Sortierung.
- Nach jedem Wechsel von Sortierspalte oder Sortierrichtung vollständig neu nummerieren: Der oberste Eintrag erhält immer `1`, der nächste `2` und so weiter.
- Die Nummer ist keine feste Länder-ID. Bei einer absteigenden Sortierung nach Erzeugung trägt beispielsweise das Land mit der höchsten Erzeugung die `1`; bei aufsteigender Sortierung entsprechend das Land mit der niedrigsten dargestellten Erzeugung.
- Flaggen und sortierabhängige Ränge im Vergleich und im Steckbrief nur dort wiederverwenden, wo die zugrunde liegende Sortierung eindeutig sichtbar bleibt.

**Abnahme:** Jede sichtbare Tabellenzeile besitzt eine Flagge und den korrekten Rang der aktiven Sortierung. Nach jeder Umsortierung beginnt die neue Reihenfolge wieder bei `1`.

### 8. Oberfläche weiter polieren

- Abstände, Typografie, visuelle Hierarchie, Karten- und Tabellenproportionen sowie die Ausnutzung großer Bildschirme vereinheitlichen.
- Interaktive Zustände für Hover, Fokus, Auswahl, Laden, leere Daten und Fehler konsistent gestalten.
- Mobile Bedienung, Tastaturnavigation, Fokusreihenfolge und ausreichende Kontraste erneut vollständig abnehmen.
- Neue Steckbrief-, Quartett- und Diagrammansichten in dasselbe visuelle System integrieren.

**Abnahme:** Die Kernabläufe Karte, Tabelle, Vergleich und Ländersteckbrief wirken visuell zusammengehörig und funktionieren ohne Seiten-Overflow auf Desktop und Mobilgeräten.

## Weitere Daten- und Qualitätsziele

### 9. Wasserkraft-Magazinkapazität separat erfassen

- Eine belastbare, möglichst europaweit vergleichbare Quelle für den Energieinhalt regulierter Wasserkraftreservoirs evaluieren.
- Die Kennzahl strikt vom JRC-Portfolio aus Pumpspeichern und Batterien trennen.
- Nationale Sonderquellen wie NVE nur verwenden, wenn Definition, Stichtag und Vergleichbarkeit transparent ausgewiesen werden können.

### 10. Speichertechnologien getrennt ausweisen

- Prüfen, ob Leistung und Energie konsistent nach mechanischen und elektrochemischen Speichern exportiert werden können.
- Eine äquivalente Volllast-Entladedauer nur für fachlich zusammengehörige Leistung und Energie berechnen.
- Keine gerätebezogene Entladedauer aus bloßen nationalen Summen vortäuschen.

### 11. Coverage und Datenqualität weiter sichtbar machen

- Quellenumfang, fehlende Länder und vorläufige Zeiträume direkt an den jeweiligen Kennzahlen erläutern.
- Automatisch erzeugte Coverage-Berichte für Ember, Eurostat und JRC konsistent halten.
- Fehlende Werte weiterhin als fehlende Coverage behandeln und niemals durch erfundene Nullwerte ersetzen.

## Aktueller Projektstand

- 31 europäische Atlasländer; Albanien ist nicht Teil des Katalogs.
- Webansicht und Datenhaltung sind auf Monats- und Jahreswerte ab 2015 ausgerichtet.
- Ember liefert Stromerzeugung, Nachfrage, Energiemix, Nettoimporte, CO₂-Intensität und Großhandelspreise.
- Eurostat ergänzt jährliche Bevölkerung und BIP-Kennzahlen.
- JRC-Speicherdaten werden derzeit als manuell heruntergeladener, validierter Snapshot importiert.
- Rohdaten und Provenienz werden lokal gespeichert; fehlerhafte Aktualisierungen dürfen bestehende Daten nicht verändern.

## Leitplanken

- Keine automatische Vermischung fachlich unterschiedlicher Quellen oder Definitionen.
- Monat ist die kleinste Einheit für Strom- und Preisdaten.
- Netzwerkimporte müssen validiert, zurückhaltend und atomar sein.
- API-Schlüssel und andere Zugangsdaten dürfen weder ausgegeben noch gespeichert werden.
- Kein Live-Import in automatisierten Tests; Tests verwenden ausschließlich lokale Fixtures.
