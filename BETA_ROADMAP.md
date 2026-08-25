# European Electricity Atlas – Fahrplan zur öffentlichen Beta

Stand: 25. August 2026  
Akzeptierte Release-Candidate-Basis: `fd9ed6e` (`feat(beta): add public project and privacy information`)
Aktueller Arbeitsstand: Railway-Testadresse und persistente Datenbanken sind online, öffentliche Projekt-, Kontakt- und Datenschutzhinweise sind veröffentlicht und `ee-atlas.eu` ist per DNS mit dem Dienst verbunden. Die Zertifizierungsstelle validiert derzeit die HTTPS-Challenge; danach folgen Origin-Umschaltung, Domain-Smoke-Test und Veröffentlichung von `v0.4.0` mit dem Titel `Beta`.

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
- [x] Die lokale Testsuite verwendet ausschließlich lokale Fixtures und führt keine Live-Imports aus; Kennzahlenbeschriftung und Refresh-Lebenszyklus besitzen eigene Verträge.
- [x] Eine GitHub-Actions-Pipeline für Python 3.11, Node 22, JavaScript-Syntax und die vollständige Testsuite ist eingerichtet; ein grüner Lauf des finalen Release Candidate bleibt Pflicht.
- [x] Portable Laufzeitparameter, strikter Datenbankstart, komponentenbezogener Healthcheck und ein konsistenter Community-Backupbefehl sind lokal umgesetzt und dokumentiert.
- [x] Alle sichtbaren Kennzahlen verwenden einen gemeinsamen Dreiklang aus Thema, Messgröße und Einheit beziehungsweise Bezugsgröße.
- [x] Der vollständige Refresh arbeitet mit einem isolierten Kandidaten, schützt die Community-Datenbank und räumt temporäre Datenbanken nach Abschluss wieder auf.

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

- [x] Finales `atlas.sqlite3` aus dem kontrollierten Importablauf erzeugen.
- [x] Datenbankintegrität, 31-Länder-Katalog, Zeitabdeckung und fehlende Werte automatisiert prüfen.
- [x] Ember-Werte für DE, FR, UK, ES und NO gegen die gespeicherten offiziellen Quellantworten prüfen. Die Türkei ist bewusst kein Atlasland.
- [x] Je Stichprobenland Erzeugung, Verbrauch, erneuerbare Erzeugung, erneuerbaren Anteil und eine landestypische Technologie prüfen.
- [x] Monats- und Jahreswerte sowie aktuelle YTD-/Vorläufigkeitskennzeichnung abdecken.
- [x] Die fünf verknüpften Jahreskennzahlen anhand ihrer Eingangsgrößen stichprobenartig nachrechnen.
- [x] Echte Nullwerte klar von fehlenden Werten unterscheiden.
- [x] `COVERAGE.generated.md` und `SUMMARY.generated.json` für den finalen Datenstand neu erzeugen.
- [x] Den historischen Energy-Charts-Bericht ausdrücklich von der aktuellen Ember-Validierung trennen.
- [x] Der Projekteigentümer akzeptiert die vorläufige nichtkommerzielle Beta-Nutzung aggregierter Werte aus dem JRC European Energy Storage Inventory bei klarer Attribution sowie Schätzungs- und Unvollständigkeitshinweisen. Eine weitergehende Rechteklärung oder spätere Ablösung durch Ember ist Post-Beta-Arbeit; eine rechtliche Freigabe wird damit nicht behauptet.
- [x] Der technische JRC-Refresh nutzt die offizielle Dashboard-Oberfläche mit sichtbaren Filtern für Operational, Electrochemical und Pumped Hydro Storage (PHS); die vier XLSX-Exporte werden nur nach vollständiger Validierung atomar übernommen.

**Gate Daten:** **READY FOR BETA – OWNER RISK ACCEPTED.** Der vollständige Refresh ist veröffentlicht; 140/140 Ember-Einzelprüfungen und 15/15 Kreuznachrechnungen bestanden. Datenbank, Coverage, Summary und Validierungsbericht beziehen sich auf SHA-256 `433CD46792264F366EC8DF51B52521B44034F7CAAE7C68DF289A704254A93B50`.

### 3. Hostingpaket herstellen

- [x] Railway Hobby als Beta-Hoster und ein persistentes Volume unter `/data` festlegen.
- [x] Das geprüfte `atlas.sqlite3` als `/data/atlas.sqlite3` bereitstellen und im Webprozess ausschließlich lesend öffnen.
- [x] Die Community-Datenbank getrennt als `/data/community.sqlite3` auf demselben persistenten Volume betreiben.
- [x] Anwendung lokal mit explizitem beziehungsweise umgebungsbasiertem Host, Port und getrennten Datenbankpfaden starten; keine festen Windows-Pfade verwenden.
- [x] Python-Prozess hinter Railways verwaltetem HTTPS-Endpunkt betreiben.
- [x] Die Abstimmungs-API gegen die explizit konfigurierte öffentliche HTTPS-Origin absichern und nicht aus weitergereichten Host-Headern ableiten.
- [x] Grundlegende HTTP-Sicherheitsheader für statische Dateien und API-Antworten ergänzen.
- [x] Dienststart und manuellen Prozessneustart auf Railway praktisch prüfen; Stimmen bleiben dabei erhalten.
- [x] `/api/health` meldet Atlas- und Community-Datenbankzustand ohne lokale Pfade und ist als Railway-Healthcheck eingerichtet.
- [x] Railway-Laufzeitlogs verwenden; Anwendung protokolliert weder API-Schlüssel noch Community-Cookie oder Browserhash.
- [x] SQLite-konsistentes Community-Backup im laufenden Railway-Container erzeugen und als lokale Sicherung herunterladen.
- [x] Isolierten Austausch von `atlas.sqlite3` einschließlich Rollback und automatischer Bereinigung testen, ohne `community.sqlite3` oder Stimmen zu verändern.
- [x] Deployment, Umgebungsvariablen, Datenbanktausch, Backup und Rollback in `docs/DEPLOYMENT.md` dokumentieren.

**Gate Hosting:** **BETA READY.** Railway-Dienst, persistentes Volume, HTTPS, Healthcheck, Neustartpersistenz und eine extern gespeicherte konsistente Community-Sicherung sind nachgewiesen. Railway-eigene Backups/PITR und ein vollständiger Restore-Drill benötigen den Pro-Tarif und sind für das nichtkritische Overload-Easter-Egg ausdrücklich Post-Beta.

### 4. Hoster-Testadresse vollständig abnehmen

- [x] Startseite und alle lokalen Kernassets laden auf der Railway-Adresse ohne festgestellten Konsolenfehler.
- [x] Tabellen ein- und ausklappen sowie Länder aus der Oberfläche auswählen.
- [ ] Kartensortierung sowie Tabellen-, SVG- und PNG-Exporte auf der Railway-Adresse manuell abnehmen.
- [x] Karte fokussieren, Kennzahlzustand erhalten und Vollbild öffnen und schließen.
- [x] Zeitreihe mit mehreren Ländern, Atlas-Durchschnitt, Zeitpreset und Direktlink prüfen.
- [ ] Vergleichs-CSV/SVG/PNG auf der Railway-Adresse manuell herunterladen und öffnen.
- [x] Ländersteckbrief aus der Karte öffnen; Browser-Zurück/Vorwärts erhält den verlinkten Zustand.
- [ ] Europa Overload aktivieren und bestätigen, dass Wikimedia-Bilder erst nach Aktivierung angefordert werden.
- [ ] Galerie und öffentliche Abstimmung mit zwei getrennten Browserprofilen testen.
- [x] Öffentliche Scores nach einem manuellen Railway-Prozessneustart erneut abrufen.
- [ ] Stimme mit zwei Browserprofilen ändern und entfernen.
- [ ] Ausfall der Voting-API simulieren: Galerie bleibt bedienbar, erfundene Ergebnisse erscheinen nicht.
- [ ] Kernpfade mindestens in Firefox und einem Chromium-basierten Browser prüfen.
- [x] Projekt-, Kontakt-, Datenschutz- und Cookieinformationen mit öffentlicher Kontaktmöglichkeit veröffentlichen.

**Gate Testadresse:** Es existiert eine unterschriebene beziehungsweise ausdrücklich bestätigte Abnahmeliste ohne offenen Fehler, der Daten verfälscht, Navigation blockiert, Stimmen verliert oder Exporte unbrauchbar macht.

### 5. Release Candidate und Veröffentlichung

- [ ] Vollständige Testsuite, JavaScript-Syntaxprüfungen und `git diff --check` auf dem Release Candidate ausführen.
- [ ] Sauberen Git-Status sowie Übereinstimmung von lokalem und Remote-Commit bestätigen.
- [x] Versionsnummer `v0.4.0` und Release-Titel `Beta` festlegen.
- [ ] Finale Release Notes und aktuelle Vorschaubilder vorbereiten.
- [ ] Geprüftes `atlas.sqlite3` mit SHA-256-Prüfsumme als Release-Artefakt bereitstellen.
- [ ] Sicherstellen, dass `community.sqlite3`, WAL-Dateien, Schlüssel und lokale Logs nicht im Release enthalten sind.
- [ ] Rollback auf die vorherige Anwendungsversion und den vorherigen Analysedatensatz dokumentieren.
- [ ] Zunächst den finalen Release Candidate auf der Testadresse deployen.
- [x] DNS für `ee-atlas.eu` nach Abnahme der Railway-Testadresse verbinden.
- [ ] Railways Zertifikatsvalidierung abschließen und `EEA_PUBLIC_ORIGIN` exakt auf `https://ee-atlas.eu` umstellen.
- [ ] Unmittelbar danach Healthcheck, Kernnavigation und eine Teststimme über `https://ee-atlas.eu` erneut prüfen.

**Gate Beta:** Domain, HTTPS, Atlasdaten, Community-Datenbank und Kernfunktionen sind erreichbar; ein getesteter Rollbackweg steht bereit.

## Empfohlene Arbeitspakete

1. **Railway-Testadresse fertig abnehmen**
   Exporte, Overload-Galerie, zwei Browserprofile und Firefox/Chromium kompakt prüfen; keine weitere Hostingarchitektur aufbauen.

2. **Produktionsdomain freigeben**
   Zertifikatsvalidierung abwarten, öffentliche Origin umstellen und Healthcheck, Kernnavigation sowie eine Teststimme über `ee-atlas.eu` prüfen.

3. **K1 – Release-Candidate-Abnahme**
   Dokumentation konsolidieren, CI prüfen, Release Notes und neue Vorschaubilder ergänzen und anschließend `v0.4.0` als `Beta` veröffentlichen.

Der veröffentlichte Datenstand bleibt von der Community-Datenbank getrennt. Künftige Komplett-Refreshes verwenden ausschließlich den dokumentierten `refresh-all`-Lebenszyklus; lose `pre-refresh`, `refresh-candidate`, `attempt2` oder Testdatenbanken gehören nicht zum unterstützten Zustand.

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
- Railway Pro, automatische Volume-Backups, PITR und ein vollständiger Restore-Drill für die nichtkritische Overload-Abstimmung

## Noch notwendige Produktentscheidungen

- zuständige Person für Betrieb, Backups und Störungsreaktion
- Veröffentlichungsdatum nach erfolgreichem Domain-Smoke-Test

## Definition of Done

Die Beta ist nicht allein durch einen erfolgreichen Commit erreicht. Sie gilt als freigegeben, wenn alle fünf Gates – UI, Daten, Hosting, Testadresse und Release – dokumentiert bestanden sind und K1 die Veröffentlichung ausdrücklich freigibt.
