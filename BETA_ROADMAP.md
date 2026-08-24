# European Electricity Atlas – Fahrplan zur öffentlichen Beta

Stand: 25. August 2026  
Technische Ausgangsbasis: `3b74a44` (`feat: add persistent Europa Overload voting and gallery navigation`)

## Zielzustand

Die öffentliche Beta ist erreicht, wenn der Atlas unter einer Hoster-Testadresse und anschließend unter `ee-atlas.eu` reproduzierbar läuft, der veröffentlichte Datenstand nachvollziehbar geprüft ist und alle zentralen Nutzerwege ohne lokale Entwicklungsumgebung funktionieren.

Die Beta ist ausdrücklich desktop-first. Eine vollständige Mobile-Parität, der Quartettvergleich und zusätzliche Forschungsdatensätze sind keine Veröffentlichungsvoraussetzung.

## Bereits erreicht

- [x] `main` und `origin/main` stehen auf demselben akzeptierten Commit.
- [x] 31 Atlasländer und 87 Kennzahlendefinitionen sind integriert.
- [x] Karte, sortierbare Tabellen, Zeitreihenvergleich und direkt verlinkbare Ländersteckbriefe sind umgesetzt.
- [x] Karten- und Plotexporte sowie Vergleichs-CSV funktionieren lokal.
- [x] Europa Overload besitzt einen kanonischen Katalog mit 250 stabil identifizierten Bildern.
- [x] Die Vollbildgalerie unterstützt zyklische Vor-/Zurück-Navigation, Tastaturbedienung und begrenztes Vorladen.
- [x] Öffentliche Daumenstimmen werden mit Score und geteilten Rangplätzen serverseitig ausgewertet.
- [x] Stimmen liegen getrennt vom austauschbaren Analysedatensatz in `community.sqlite3`.
- [x] Browserkennungen werden nur gehasht gespeichert; Same-Origin-Prüfung, kleine Requestkörper und ein einfacher Rate-Limiter sind vorhanden.
- [x] Die lokale Testsuite umfasst 143 erfolgreiche Tests; sie verwendet keine Live-Imports.

## Kritischer Pfad

### 1. Aktuellen UI-Stand visuell abnehmen

- [ ] Gesamte Anwendung bei 1920×1080 und 2560×1440 mit 100 % Browserzoom prüfen.
- [ ] Europa-Overload-Postkarten dürfen weder Atlas noch Bedienelemente problematisch überdecken.
- [ ] Full HD muss kompakt bleiben; WQHD muss die zusätzliche Seitenfläche sichtbar nutzen.
- [ ] Keine horizontale Scrollleiste, abgeschnittenen Captions oder Scrollsprünge.
- [ ] Sticky Steuerleiste und Tabellenköpfe über lange Tabellen hinweg prüfen.
- [ ] Karte, Plottool und Ländersteckbriefe jeweils in Normal- und Vollbildzuständen prüfen.
- [ ] Galerie mit Maus, Tab-Taste, Pfeiltasten, Escape, Hintergrundklick und Europa-Stern bedienen.
- [ ] Reduzierte Bewegung mit `prefers-reduced-motion` kontrollieren.

**Gate UI:** Für beide Referenzauflösungen liegen Abnahmebilder und eine kurze Ergebnisnotiz vor. Bekannte kosmetische Restpunkte sind dokumentiert und blockieren keine Kernfunktion.

### 2. Datenstand für die Beta freigeben

- [ ] Finales `atlas.sqlite3` aus dem kontrollierten Importablauf erzeugen.
- [ ] Datenbankintegrität, 31-Länder-Katalog, Zeitabdeckung und fehlende Werte automatisiert prüfen.
- [ ] Ember-Werte für eine repräsentative Auswahl manuell gegen die Quelle prüfen, mindestens DE, FR, UK, ES, NO und TR.
- [ ] Je Stichprobenland mindestens Erzeugung, Verbrauch, erneuerbare Erzeugung, erneuerbaren Anteil und eine Technologie prüfen.
- [ ] Monats- und Jahreswerte sowie aktuelle YTD-/Vorläufigkeitskennzeichnung abdecken.
- [ ] Die fünf verknüpften Jahreskennzahlen anhand ihrer Eingangsgrößen stichprobenartig nachrechnen.
- [ ] Echte Nullwerte klar von fehlenden Werten unterscheiden.
- [ ] `COVERAGE.generated.md` und `SUMMARY.generated.json` für den finalen Datenstand neu erzeugen.
- [ ] Den historischen Energy-Charts-Validierungsbericht nicht als aktuelle Validierung ausliefern; aktuellen Bericht erzeugen oder den historischen Bericht eindeutig außerhalb des Beta-Artefakts halten.
- [ ] Weitergabe und öffentliche Anzeige der JRC-Speicherdaten abschließend freigeben. Falls diese Freigabe offen bleibt, JRC-basierte Speicherwerte aus der öffentlichen Beta entfernen, statt Unsicherheit zu verschweigen.

**Gate Daten:** Der konkrete Beta-Datenbankhash, der Coverage-Bericht und die dokumentierten Stichproben sind akzeptiert. Keine ungeklärte Datenquelle wird versehentlich veröffentlicht.

### 3. Hostingpaket herstellen

- [ ] Hoster und persistente Speicherorte festlegen.
- [ ] `atlas.sqlite3` auf einem persistenten, für den Webprozess nur lesbaren Pfad bereitstellen.
- [ ] `EEA_COMMUNITY_DB` auf einen getrennten persistenten Schreibpfad setzen.
- [ ] Anwendung mit explizitem Host, Port und Datenbankpfad starten; keine festen Windows-Pfade verwenden.
- [ ] Python-Prozess nicht unmittelbar dem Internet aussetzen, sondern hinter einem HTTPS-Reverse-Proxy betreiben.
- [ ] Reverse Proxy so konfigurieren, dass `Host` und `X-Forwarded-Proto` kontrolliert gesetzt und nicht ungeprüft vom Client übernommen werden.
- [ ] TLS, Requestgrößen, sinnvolle Zeitlimits und grundlegende Sicherheitsheader am Proxy konfigurieren.
- [ ] Dienststart, automatischen Neustart und Verhalten nach einem Serverreboot einrichten.
- [ ] `/api/health` in den Hoster-Healthcheck aufnehmen.
- [ ] Zugriffs- und Fehlerlogs mit begrenzter Aufbewahrung bereitstellen; keine API-Schlüssel oder Browserkennungen protokollieren.
- [ ] SQLite-konsistentes Backup für `community.sqlite3` einrichten und eine Wiederherstellung praktisch testen.
- [ ] Austausch von `atlas.sqlite3` testen, ohne `community.sqlite3` oder Stimmen zu verlieren.
- [ ] Deployment, Umgebungsvariablen, Datenbanktausch, Backup und Rollback in einer eigenen Anleitung dokumentieren.

**Gate Hosting:** Neustart, Healthcheck, Datenbanktausch, Voting-Persistenz, Backup und Restore wurden auf der Hoster-Testadresse nachgewiesen.

### 4. Hoster-Testadresse vollständig abnehmen

- [ ] Startseite und alle lokalen Assets laden ohne Konsolenfehler.
- [ ] Tabelle sortieren, ein- und ausklappen sowie Länder auswählen.
- [ ] Karte fokussieren, Kennzahl wechseln, Vollbild öffnen und SVG/PNG exportieren.
- [ ] Zeitreihe mit mehreren Ländern, Atlas-Durchschnitt, Zeitpreset, Direktlink und CSV/SVG/PNG prüfen.
- [ ] Ländersteckbriefe aus Tabelle und Karte öffnen; Browser-Zurück/Vorwärts testen.
- [ ] Europa Overload aktivieren und bestätigen, dass Wikimedia-Bilder erst nach Aktivierung angefordert werden.
- [ ] Galerie und öffentliche Abstimmung mit zwei getrennten Browserprofilen testen.
- [ ] Stimme ändern, entfernen und nach Prozessneustart erneut abrufen.
- [ ] Ausfall der Voting-API simulieren: Galerie bleibt bedienbar, erfundene Ergebnisse erscheinen nicht.
- [ ] Kernpfade mindestens in Firefox und einem Chromium-basierten Browser prüfen.
- [ ] Operator-, Kontakt-, Datenschutz- und Cookieinformationen vor Veröffentlichung bereitstellen und fachlich prüfen lassen; technische Tests ersetzen keine rechtliche Freigabe.

**Gate Testadresse:** Es existiert eine unterschriebene beziehungsweise ausdrücklich bestätigte Abnahmeliste ohne offenen Fehler, der Daten verfälscht, Navigation blockiert, Stimmen verliert oder Exporte unbrauchbar macht.

### 5. Release Candidate und Veröffentlichung

- [ ] Vollständige Testsuite, JavaScript-Syntaxprüfungen und `git diff --check` auf dem Release Candidate ausführen.
- [ ] Sauberen Git-Status sowie Übereinstimmung von lokalem und Remote-Commit bestätigen.
- [ ] Versionsnummer, Release Notes und aktuelle Vorschaubilder vorbereiten.
- [ ] Geprüftes `atlas.sqlite3` mit SHA-256-Prüfsumme als Release-Artefakt bereitstellen.
- [ ] Sicherstellen, dass `community.sqlite3`, WAL-Dateien, Schlüssel und lokale Logs nicht im Release enthalten sind.
- [ ] Rollback auf die vorherige Anwendungsversion und den vorherigen Analysedatensatz dokumentieren.
- [ ] Zunächst den finalen Release Candidate auf der Testadresse deployen.
- [ ] Erst nach letzter Abnahme DNS für `ee-atlas.eu` verbinden.
- [ ] Unmittelbar nach DNS-Umschaltung Healthcheck, Kernnavigation und eine Teststimme erneut prüfen.

**Gate Beta:** Domain, HTTPS, Atlasdaten, Community-Datenbank und Kernfunktionen sind erreichbar; ein getesteter Rollbackweg steht bereit.

## Empfohlene Arbeitspakete

1. **K2 – UI-Abnahme und verbleibende Desktop-Politur**  
   Nur responsive Darstellung und beobachtete UI-Fehler bearbeiten; keine Daten- oder Hostingarbeit beimischen.

2. **K4 – Beta-Datenfreigabe**  
   Datenbank read-only inventarisieren, Stichproben und Coverage dokumentieren, JRC-Freigabeentscheidung vorbereiten; keine UI-Implementierung.

3. **K2 – Hostingfähigkeit und Betriebsdokumentation**  
   Startkonfiguration, Reverse-Proxy-Vertrag, persistente Pfade, Healthcheck, Backup/Restore und Testdeployment umsetzen.

4. **K1 – Release-Candidate-Abnahme**  
   Nachweise zusammenführen, offene Punkte priorisieren, Releaseumfang festlegen und die Domainumschaltung erst nach bestandenem Gate freigeben.

Diese Pakete werden nacheinander auf akzeptierten Commits begonnen. Parallele Änderungen an `server.py`, den Datenbankpfaden oder der Europa-Overload-Oberfläche sind zu vermeiden.

## Kein Beta-Blocker

- zusätzliche Spalten in der Haupttabelle
- Quartettvergleich auf Basis der Ländersteckbriefe
- vollständige Mobile-Parität
- Benutzerkonten oder ein manipulationssicheres Wahlsystem
- automatische Datenimporte oder ein Scheduler im Atlas-Server
- weitere nationale Batteriequellen
- Photovoltaik-Nennleistung in GWp
- Energieinhalt konventioneller Wasserkraftreservoirs
- vollständiger Umbau aller historischen Berichte, sofern kein veralteter Bericht als aktuell veröffentlicht wird

## Noch notwendige Produktentscheidungen

- Hoster und Betriebsmodell
- zuständige Person für Betrieb, Backups und Störungsreaktion
- Umgang mit JRC-Speicherwerten, falls die öffentliche Weitergabe nicht rechtzeitig geklärt ist
- Inhalt und verantwortliche Angaben der öffentlichen Betreiber-, Kontakt- und Datenschutzhinweise
- gewünschte Beta-Versionsnummer und Veröffentlichungsdatum

## Definition of Done

Die Beta ist nicht allein durch einen erfolgreichen Commit erreicht. Sie gilt als freigegeben, wenn alle fünf Gates – UI, Daten, Hosting, Testadresse und Release – dokumentiert bestanden sind und K1 die Veröffentlichung ausdrücklich freigibt.
