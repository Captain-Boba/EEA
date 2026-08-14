# European Electricity Atlas – Roadmap

Stand: 13. August 2026

Diese Datei bündelt die offenen Entwicklungspunkte des Projekts. Abgeschlossene Grundlagen werden getrennt aufgeführt, damit die Prioritätenliste ausschließlich noch ausstehende Arbeiten enthält.

## Prioritäten

### 1. Regelmäßige Speicherpflege etablieren

- Den neuen bewussten JRC-CLI-Abruf zunächst höchstens einmal pro Kalendermonat betreiben und seine Abdeckung beobachten.
- Battery-Charts vorerst ausschließlich über den manuellen, atomaren JSON-Dateiimport aktualisieren. Der vorbereitete Online-Zugriff bleibt technisch deaktiviert, bis seine Nutzung ausdrücklich geklärt ist.
- Nach Betriebserfahrung entscheiden, ob ein externer monatlicher Scheduler sinnvoll ist; der Atlas-Server selbst darf weiterhin keine Hintergrundabfragen auslösen.
- Strukturänderungen der nicht formal versionierten JRC-Projekt-API und der manuell exportierten Battery-Charts-Antworten sichtbar dokumentieren, statt die Validierung stillschweigend zu lockern.
- Die Lizenz- und Weitergabesituation des JRC-Projektbestands vor einer öffentlichen oder kommerziellen Datenveröffentlichung abschließend klären.
- In Dokumentation und Oberfläche weiterhin deutlich machen, dass der JRC-Projektbestand nicht die nationale Wasserkraft-Magazinkapazität abbildet.

**Abnahme:** Mehrere reale Monatsaktualisierungen laufen mit maximal einem JRC-Request und ohne Battery-Charts-Netzwerkzugriff; der getrennte Dateiimport erzeugt weder Duplikate noch Datenverlust.

## Kurzfristige Produktziele

### 2. Kartendarstellung vergrößern, maximieren und exportieren

- Der Karte deutlich mehr sichtbare Fläche geben und ungenutzten horizontalen Raum vermeiden.
- Den bestehenden geografischen Europa-Ausschnitt beibehalten; die Karte soll größer dargestellt, aber nicht neu zugeschnitten werden.
- Eine Vollbildfunktion ergänzen, mit der die Karte maximiert und anschließend eindeutig wieder verlassen werden kann.
- Den jeweils aktuellen Kartenstand exportierbar machen. Der Export muss die aktive Kennzahl, Darstellung, Farbskala, sichtbaren Werte und eine automatisch dazu erzeugte Legende enthalten.
- Desktop-, Tablet- und Mobilansicht getrennt prüfen; kleine Länder müssen weiterhin per Maus und Tastatur erreichbar bleiben.
- `Werte anzeigen` standardmäßig aktivieren, ohne die Karte bei kleinen Ländern oder engen Viewports unlesbar zu machen.

**Abnahme:** Die Karte nutzt bei unverändertem geografischem Ausschnitt deutlich mehr Fläche, lässt sich vollständig maximieren und wiederherstellen und kann in ihrem aktuellen Zustand mit passender automatisch erzeugter Legende exportiert werden. Wertelabels sind beim ersten Laden eingeschaltet.

### 3. Festen Länderfokus der Karte vervollständigen

- Kartenklicks sind bereits von der Vergleichsauswahl entkoppelt. Diese Trennung beibehalten und automatisiert absichern.
- Ein angeklicktes Land in der Infokachel rechts neben der Karte festhalten, bis ein anderes Land gewählt oder der Fokus ausdrücklich gelöst wird.
- Hover und Tastaturfokus dürfen weiterhin temporäre Informationen im Tooltip zeigen, sollen den festgehaltenen Länderfokus in der Infokachel aber nicht überschreiben.
- Eine eindeutige Aktion zum Lösen des festgehaltenen Länderfokus ergänzen.
- Die bereits vorhandenen Angaben zu Land, Kennzahl, Wert, Einheit, Zeitraum beziehungsweise Snapshot, Datenstatus und Quelle beibehalten.

**Abnahme:** Kartenklicks verändern keine Vergleichsauswahl mehr. Maus- und Tastaturbedienung können genau ein Land sichtbar und nachvollziehbar in der Infokachel festhalten.

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
- Das optisch gebrochene Feld beziehungsweise die Überschrift `Auswahl` oben links entfernen; die Länderauswahl stattdessen ohne diesen sichtbaren Spaltentitel zugänglich beschriften.
- Sämtliche Spaltenüberschriften und Tabellenwerte horizontal zentrieren. Eine ausdrücklich linksbündig gewünschte Bezeichnungsspalte müsste vor der Umsetzung gesondert festgelegt werden.
- Dezimalstellen je Spalte einheitlich lang darstellen. Nachgestellte Nullen dürfen nicht unterdrückt werden, wenn dadurch innerhalb derselben Spalte unterschiedlich viele Nachkommastellen sichtbar wären.

**Abnahme:** Jede sichtbare Tabellenzeile besitzt eine Flagge und den korrekten Rang der aktiven Sortierung. Nach jeder Umsortierung beginnt die neue Reihenfolge wieder bei `1`. Überschriften und Inhalte sind zentriert, Dezimalstellen innerhalb einer Spalte einheitlich und die gebrochene sichtbare Überschrift `Auswahl` ist entfernt.

### 8. Oberfläche weiter polieren

- Die Steuerleiste mit Jahr, Zeitraum, `Auswerten` und `Vergleichen` beim Scrollen am oberen Rand des sichtbaren Fensters mitführen, ohne relevante Inhalte zu verdecken.
- Ein neues, zurückhaltendes Atlas-Logo entwickeln: klar wiedererkennbar und etwas eigenständiger als ein reiner Textschriftzug, aber bewusst nicht verspielt oder überladen.
- Bedienhinweise sprachlich und inhaltlich überarbeiten. Wiederkehrende Erklärtexte nicht dauerhaft an allen Ansichten offen anzeigen, sondern kontextbezogen über kleine, klar beschriftete Info-Schaltflächen zugänglich machen.
- Abstände, Typografie, visuelle Hierarchie, Karten- und Tabellenproportionen sowie die Ausnutzung großer Bildschirme vereinheitlichen.
- Interaktive Zustände für Hover, Fokus, Auswahl, Laden, leere Daten und Fehler konsistent gestalten.
- Mobile Bedienung, Tastaturnavigation, Fokusreihenfolge und ausreichende Kontraste erneut vollständig abnehmen.
- Neue Steckbrief-, Quartett- und Diagrammansichten in dasselbe visuelle System integrieren.

**Abnahme:** Die Steuerleiste bleibt beim Scrollen zuverlässig bedienbar, das neue Logo ist in Desktop- und Mobilansicht klar lesbar und Bedienhilfen lassen sich bei Bedarf aufrufen, ohne die Oberfläche dauerhaft mit Erklärungstexten zu füllen. Die Kernabläufe Karte, Tabelle, Vergleich und Ländersteckbrief wirken visuell zusammengehörig und funktionieren ohne Seiten-Overflow.

## Weitere Daten- und Qualitätsziele

### 9. Wasserkraft-Magazinkapazität separat erfassen

- Eine belastbare, möglichst europaweit vergleichbare Quelle für den Energieinhalt regulierter Wasserkraftreservoirs evaluieren.
- Die Kennzahl strikt vom JRC-Portfolio aus Pumpspeichern und Batterien trennen.
- Nationale Sonderquellen wie NVE nur verwenden, wenn Definition, Stichtag und Vergleichbarkeit transparent ausgewiesen werden können.

### 10. Speicher-Coverage weiter verbessern

- Für Länder außerhalb Deutschlands transparent prüfen, welche stationären Batterieklassen im JRC-Projektbestand fehlen.
- Keine fehlenden Heim- oder Gewerbespeicher schätzen; stattdessen Coverage-Typ und Datenlücken direkt am Wert ausweisen.
- Nur dann weitere nationale Gesamtbestände anbinden, wenn Leistung, Energie, Stichtag, Segmentgrenzen und Lizenz belastbar vergleichbar sind.

### 11. Coverage und Datenqualität weiter sichtbar machen

- Quellenumfang, fehlende Länder und vorläufige Zeiträume direkt an den jeweiligen Kennzahlen erläutern.
- Automatisch erzeugte Coverage-Berichte für Ember, Eurostat und JRC konsistent halten.
- Fehlende Werte weiterhin als fehlende Coverage behandeln und niemals durch erfundene Nullwerte ersetzen.

## Aktueller Projektstand

- 31 europäische Atlasländer; Albanien ist nicht Teil des Katalogs.
- Webansicht und Datenhaltung sind auf Monats- und Jahreswerte ab 2015 ausgerichtet.
- Ember liefert Stromerzeugung, Nachfrage, Energiemix, Nettoimporte, CO₂-Intensität und Großhandelspreise.
- Eurostat ergänzt jährliche Bevölkerung und BIP-Kennzahlen.
- Batterien und Pumpspeicher sind in Leistung, Energie und äquivalenter Entladedauer getrennt. Deutschland-Batterien stammen ausschließlich aus Battery-Charts; andere Batterien und alle Pumpspeicher aus JRC.
- `update-storage` respektiert einen monatlichen Cache und ruft ausschließlich JRC nach bewusster CLI-Ausführung ab. Battery-Charts besitzt nur den separaten manuellen JSON-Dateiimport; der frühere manuelle JRC-Import bleibt als veralteter Offline-Fallback erhalten.
- Das frühere tabellarische Vergleichsprovisorium ist durch einen nativen SVG-Zeitreihenplot für ein bis zehn Länder ersetzt. Monats- und Jahresauflösung stammen aus dem zentralen Kennzahlenkatalog; Snapshot-Kennzahlen bleiben ausgeschlossen.
- Der Zeitreihenvergleich enthält einen Atlas-Durchschnitt über alle jeweils vorhandenen Länderwerte, echte Datenlücken, ein rein zeitbezogenes Live-Ranking, Zeitpunktfixierung, lokale Flaggen sowie CSV-, SVG- und PNG-Export.
- Standard- und Vollbildansicht verwenden dieselben Plotproportionen und dieselbe großzügige Live-Ranking-Typografie. Im Vollbild bleibt außerdem die vollständige Steuerleiste sichtbar; der Zustand bleibt beim Wechsel erhalten. Linienfarben orientieren sich an kontrastreichen Flaggenfarben und weichen bei Konflikten auf unterscheidbare Ersatzfarben aus.
- Relative Veränderungen verwenden unabhängig vom sichtbaren Zeitraum den passenden Vergleichswert aus 2015: jährlich den Jahreswert, monatlich denselben Kalendermonat. Fehlende oder echte Null-Basiswerte bleiben unberechnet.
- Länderauswahl, Kennzahl und Zeitraum werden in einem defensiv validierten Direktlink gespeichert. Die alte `/api/compare`-Schnittstelle bleibt vorerst erhalten.
- Kartenklicks verändern die Vergleichsauswahl nicht mehr. Der dauerhafte Kartenfokus muss noch von temporärem Hover beziehungsweise Tastaturfokus getrennt und explizit lösbar gemacht werden.
- Rohdaten und Provenienz werden lokal gespeichert; fehlerhafte Aktualisierungen dürfen bestehende Daten nicht verändern.

## Abgeschlossene Grundlagen

### Zeitreihenvergleich V1

- Eigener `/api/timeseries`-Vertrag für ein bis zehn eindeutige Atlas-Länder und genau eine Kennzahl.
- Automatische Monatsauflösung, sofern verfügbar, andernfalls Jahresauflösung; Snapshot-Kennzahlen werden verständlich deaktiviert.
- Chronologische Länderreihen mit `null` für fehlende Perioden, ohne Interpolation oder erfundene Nullwerte.
- Atlas-Durchschnitt je Zeitpunkt über den vollständigen Länderkatalog; fehlende Werte werden ausgeschlossen und echte Nullwerte berücksichtigt.
- Lokaler nativer SVG-Plot mit bis zu zehn Länderlinien, gestricheltem Atlas-Durchschnitt, Endpunktflaggen, Kollisionsbehandlung, Nulllinie für vorzeichenbehaftete Kennzahlen und responsiver Darstellung.
- Live-Ranking am letzten beziehungsweise berührten Zeitpunkt, geteilte Ränge, Linienhervorhebung sowie fixierbarer Zeitpunkt.
- Wiederherstellbarer Direktlink und lokale CSV-, SVG- und PNG-Exporte; CSV-Lücken bleiben leer.
- 31 lokale SVG-Flaggen aus `flag-icons` einschließlich dokumentierter MIT-Lizenz; keine Diagramm-, Flaggen- oder CDN-Abrufe zur Laufzeit.

### Zeitreihenvergleich V2

- Identisches `15:8`-Plotverhältnis und dieselbe interne Diagrammgeometrie in Standard- und Vollbildansicht; das Ranking scrollt bei Bedarf innerhalb der gemeinsamen Arbeitsfläche.
- Native Vollbildansicht mit vollständiger Steuerleiste, identisch skaliertem Live-Ranking, sichtbarer Beenden-Aktion und `Escape`; Länder, Kennzahl, Zeitraum und fixierter Zeitpunkt bleiben beim Wechsel erhalten.
- Dünnere Länder- und Durchschnittslinien sowie rein zeitbezogener Hover ohne Einrasten, Hervorheben oder Abdunkeln einzelner Länderlinien.
- Dynamische Linienfarben aus kontrastreichen prägenden Flaggenfarben mit konfliktfreien Ersatzfarben für die aktuelle Auswahl.
- Feste 2015-Vergleichsbasis in API und Ranking: Jahreswert 2015 beziehungsweise derselbe Kalendermonat 2015, auch wenn der sichtbare Zeitraum später beginnt.
- Relative Veränderung in Prozent für alle Kennzahlen; fehlende und echte Null-Basiswerte ergeben `—`.

## Leitplanken

- Keine automatische Vermischung fachlich unterschiedlicher Quellen oder Definitionen.
- Monat ist die kleinste Einheit für Strom- und Preisdaten.
- Netzwerkimporte müssen validiert, zurückhaltend und atomar sein.
- API-Schlüssel und andere Zugangsdaten dürfen weder ausgegeben noch gespeichert werden.
- Kein Live-Import in automatisierten Tests; Tests verwenden ausschließlich lokale Fixtures.
