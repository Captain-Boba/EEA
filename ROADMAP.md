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

### 2. Wasserkraft-Magazinkapazität separat erfassen

- Eine belastbare, möglichst europaweit vergleichbare Quelle für den Energieinhalt regulierter Wasserkraftreservoirs evaluieren.
- Die Kennzahl strikt vom JRC-Portfolio aus Pumpspeichern und Batterien trennen.
- Nationale Sonderquellen wie NVE nur verwenden, wenn Definition, Stichtag und Vergleichbarkeit transparent ausgewiesen werden können.

### 3. Speichertechnologien getrennt ausweisen

- Prüfen, ob Leistung und Energie konsistent nach mechanischen und elektrochemischen Speichern exportiert werden können.
- Eine äquivalente Volllast-Entladedauer nur für fachlich zusammengehörige Leistung und Energie berechnen.
- Keine gerätebezogene Entladedauer aus bloßen nationalen Summen vortäuschen.

### 4. Coverage und Datenqualität weiter sichtbar machen

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
