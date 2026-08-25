# European Electricity Atlas – Fahrplan zur öffentlichen Beta

Stand: 25. August 2026  
Akzeptierte Git-Basis: `ec73169` (`fix: polish atlas interactions and document the beta path`)
Aktueller Arbeitsstand: uncommitteter, gemeinsam geprüfter Beta-Kandidat mit CI-, Hosting-, UI-Abnahme- und Datenvalidierungsarbeiten

## Zielzustand

Die öffentliche Beta ist erreicht, wenn der Atlas unter einer Hoster-Testadresse und anschließend unter `ee-atlas.eu` reproduzierbar läuft, der veröffentlichte Datenstand nachvollziehbar geprüft ist und alle zentralen Nutzerwege ohne lokale Entwicklungsumgebung funktionieren.

Die Beta ist ausdrücklich desktop-first. Eine vollständige Mobile-Parität, der Quartettvergleich und zusätzliche Forschungsdatensätze sind keine Veröffentlichungsvoraussetzung.

## Bereits erreicht

- [x] `main` und `origin/main` stehen auf demselben akzeptierten Commit.
- [x] 31 Atlasländer und 87 Kennzahlendefinitionen sind integriert.
- [x] Karte, sortierbare Tabellen, Zeitvergleich und direkt verlinkbare Ländersteckbriefe sind umgesetzt.
- [x] Karten- und Plotexporte sowie Vergleichs-CSV funktionieren lokal.
- [x] Europa Overload besitzt einen kanonischen Katalog mit 250 stabil identifizierten Bildern.
- [x] Die Vollbildgalerie unterstützt zyklische Vor-/Zurück-Navigation, Tastaturbedienung und begrenztes Vorladen.
- [x] Öffentliche Daumenstimmen werden mit Score und geteilten Rangplätzen serverseitig ausgewertet.
- [x] Stimmen liegen getrennt vom austauschbaren Analysedatensatz in `community.sqlite3`.
- [x] Browserkennungen werden nur gehasht gespeichert; Same-Origin-Prüfung, kleine Requestkörper und ein einfacher Rate-Limiter sind vorhanden.
- [x] Die lokale Testsuite umfasst 155 erfolgreiche Tests; sie verwendet keine Live-Imports.
- [x] Eine GitHub-Actions-Pipeline für Python 3.11, Node 22, JavaScript-Syntax und die vollständige Testsuite ist vorbereitet; der erste Lauf auf GitHub steht bis zum Push noch aus.
- [x] Portable Laufzeitparameter, strikter Datenbankstart, komponentenbezogener Healthcheck und ein konsistenter Community-Backupbefehl sind lokal umgesetzt und dokumentiert.

## Kritischer Pfad

### 1. Aktuellen UI-Stand visuell abnehmen

- [x] Gesamte Anwendung bei 1920×1080 und 2560×1440 mit 100 % Browserzoom durch den Projekteigentümer prüfen.
- [x] Europa-Overload-Postkarten überdecken Atlas und Bedienelemente in der Eigentümerabnahme nicht problematisch.
- [x] Full HD bleibt kompakt; WQHD nutzt die zusätzliche Seitenfläche sichtbar.
- [x] Der in der Agentenprüfung gefundene horizontale Überlauf durch unsichtbare Vergleichsauswahlen ist behoben; in der Eigentümerabnahme fiel kein weiterer problematischer Überlauf auf.
- [x] Sticky Steuerleiste und Tabellenköpfe sowie Karte, Zeitvergleich und Ländersteckbriefe wurden im verfügbaren Browser geprüft.
- [ ] Galerie mit Maus, Tab-Taste, Pfeiltasten, Escape, Hintergrundklick und Europa-Stern bedienen.
- [ ] Reduzierte Bewegung mit `prefers-reduced-motion` kontrollieren.

**Gate UI:** Die Full-HD-/WQHD-Darstellung ist am 25. August 2026 durch den Projekteigentümer vorläufig abgenommen. Die eingeschränkte Agentenprüfung und ihr behobener Überlauffehler sind in `artifacts/beta-ui/ACCEPTANCE.md` dokumentiert. Galerie-Tastaturpfade und reduzierte Bewegung werden spätestens auf der Hoster-Testadresse erneut geprüft.

### 2. Datenstand für die Beta freigeben

- [ ] Finales `atlas.sqlite3` aus dem kontrollierten Importablauf erzeugen.
- [ ] Datenbankintegrität, 31-Länder-Katalog, Zeitabdeckung und fehlende Werte automatisiert prüfen.
- [ ] Ember-Werte für eine repräsentative Auswahl manuell gegen die Quelle prüfen, mindestens DE, FR, UK, ES und NO. Die Türkei ist bewusst kein Atlasland.
- [ ] Je Stichprobenland mindestens Erzeugung, Verbrauch, erneuerbare Erzeugung, erneuerbaren Anteil und eine Technologie prüfen.
- [ ] Monats- und Jahreswerte sowie aktuelle YTD-/Vorläufigkeitskennzeichnung abdecken.
- [ ] Die fünf verknüpften Jahreskennzahlen anhand ihrer Eingangsgrößen stichprobenartig nachrechnen.
- [ ] Echte Nullwerte klar von fehlenden Werten unterscheiden.
- [ ] `COVERAGE.generated.md` und `SUMMARY.generated.json` für den finalen Datenstand neu erzeugen.
- [ ] Den historischen Energy-Charts-Validierungsbericht nicht als aktuelle Validierung ausliefern; aktuellen Bericht erzeugen oder den historischen Bericht eindeutig außerhalb des Beta-Artefakts halten.
- [x] Der Projekteigentümer akzeptiert die vorläufige nichtkommerzielle Beta-Nutzung aggregierter Werte aus dem JRC European Energy Storage Inventory bei klarer Attribution sowie Schätzungs- und Unvollständigkeitshinweisen. Eine weitergehende Rechteklärung oder spätere Ablösung durch Ember ist Post-Beta-Arbeit; eine rechtliche Freigabe wird damit nicht behauptet.

**Gate Daten:** K4 hat den bisherigen Kandidaten technisch erfolgreich geprüft; 140 von 140 durchführbaren Ember-Einzelvergleichen und die fünf Kreuznachrechnungen bestanden. Vor der Freigabe fehlen noch der einmalige kontrollierte Komplett-Refresh, ein neuer Datenbankhash sowie dazu passende Coverage-, Summary- und Validierungsberichte.

### 3. Hostingpaket herstellen

- [ ] Hoster und persistente Speicherorte festlegen.
- [ ] `atlas.sqlite3` auf einem persistenten, für den Webprozess nur lesbaren Pfad bereitstellen.
- [ ] `EEA_COMMUNITY_DB` auf einen getrennten persistenten Schreibpfad setzen.
- [x] Anwendung lokal mit explizitem beziehungsweise umgebungsbasiertem Host, Port und getrennten Datenbankpfaden starten; keine festen Windows-Pfade verwenden.
- [ ] Python-Prozess nicht unmittelbar dem Internet aussetzen, sondern hinter einem HTTPS-Reverse-Proxy betreiben.
- [ ] Reverse Proxy so konfigurieren, dass `Host` und `X-Forwarded-Proto` kontrolliert gesetzt und nicht ungeprüft vom Client übernommen werden.
- [ ] TLS, Requestgrößen, sinnvolle Zeitlimits und grundlegende Sicherheitsheader am Proxy konfigurieren.
- [ ] Dienststart, automatischen Neustart und Verhalten nach einem Serverreboot einrichten.
- [x] `/api/health` meldet Atlas- und Community-Datenbankzustand ohne lokale Pfade; Aufnahme in den realen Hoster-Healthcheck steht aus.
- [ ] Zugriffs- und Fehlerlogs mit begrenzter Aufbewahrung bereitstellen; keine API-Schlüssel oder Browserkennungen protokollieren.
- [x] SQLite-konsistenten Backupbefehl für `community.sqlite3` lokal umsetzen und mit temporären Daten testen; realen Hoster-Backupplan später einrichten.
- [ ] Austausch von `atlas.sqlite3` testen, ohne `community.sqlite3` oder Stimmen zu verlieren.
- [x] Deployment, Umgebungsvariablen, Datenbanktausch, Backup und Rollback in `docs/DEPLOYMENT.md` dokumentieren.

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

1. **K4 – Kontrollierter Komplett-Refresh und finales Datengate**
   Alle acht Datenpfade genau einmal schonend aktualisieren, einen validierten Kandidaten statt einer Teilaktualisierung veröffentlichen und Reports sowie Prüfsummen neu erzeugen.

2. **K2 – Reportvertrag bereinigen**
   CLI-Hilfe, tatsächlich erzeugte Coverage-/Summary-Artefakte und Dokumentation angleichen; keine Daten fachlich verändern.

3. **Hosting-Testadresse herstellen**
   Bereits vorbereitete Laufzeitkonfiguration, persistente Pfade, Reverse Proxy, HTTPS, Healthcheck und Community-Backup beim gewählten Hoster praktisch einrichten.

4. **K1 – Release-Candidate-Abnahme**  
   Nachweise zusammenführen, offene Punkte priorisieren, Releaseumfang festlegen und die Domainumschaltung erst nach bestandenem Gate freigeben.

Der aktuelle gemeinsame Arbeitsbaum wird erst nach Abschluss der laufenden Einheiten dokumentiert geprüft und committed. Der Datenrefresh arbeitet auf einer gesicherten Kandidatenkopie und verändert keine fremde Code-Diff.

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
- Ablösung von JRC und Battery-Charts durch einen künftigen Ember-Speicherdatensatz
- abschließende Rechteklärung des JRC European Energy Storage Inventory über die für die vorläufige nichtkommerzielle Beta akzeptierte Risikoposition hinaus

## Noch notwendige Produktentscheidungen

- Hoster und Betriebsmodell
- zuständige Person für Betrieb, Backups und Störungsreaktion
- Inhalt und verantwortliche Angaben der öffentlichen Betreiber-, Kontakt- und Datenschutzhinweise
- gewünschte Beta-Versionsnummer und Veröffentlichungsdatum

## Definition of Done

Die Beta ist nicht allein durch einen erfolgreichen Commit erreicht. Sie gilt als freigegeben, wenn alle fünf Gates – UI, Daten, Hosting, Testadresse und Release – dokumentiert bestanden sind und K1 die Veröffentlichung ausdrücklich freigibt.
