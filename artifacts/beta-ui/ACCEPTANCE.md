# K3-BETA-UI-001 – Desktop-Abnahme

## Ausgangslage

- HEAD bei Beginn: `ec731697edfbdce4c10f58e1a8cbec563a1a38fb`
- Referenz `3b74a44`: Vorfahr des HEAD
- Browser: nur **Codex In-app Browser** verfügbar (`type: iab`)
- Gemessene Umgebung: 1280 × 720 CSS-Pixel, DPR 1, `visualViewport.scale = 1`
- Firefox war nicht steuerbar/verfügbar. Ein separat steuerbarer Chromium-Browser war ebenfalls nicht verfügbar.
- 1920 × 1080 und 2560 × 1440 konnten nicht exakt hergestellt werden. Die Pflichtabnahme in beiden Referenzgrößen ist daher **nicht** als durchgeführt ausgewiesen.

## Geprüfte Szenarien (eingeschränkt auf die verfügbare Umgebung)

- Header, Steuerleiste, Jahr/Zeitraum, Auswahlzähler und normale Scrollbewegung
- Europakarte mit Wertbeschriftungen und Legende
- Karten-Vollbild
- Plottool mit fünf Ländern, Zeitraum-Voreinstellung, Live-Ranking und Plot-Vollbild
- Stromsysteme in Gesamtansicht; Tabellenkopf und Ausklappzustand
- Ländersteckbrief per Direktlink (`DE`) einschließlich oberer Scrollposition und Quellenzeile
- Europa Overload: vor Aktivierung keine Postkarten-/Bild-Elemente; nach Opt-in aktiver Schalter. Die Postkarten selbst sind unter 1500 px absichtlich ausgeblendet; Galerie, Tastaturnavigation und WQHD-Gutter konnten deshalb nicht visuell abgenommen werden.

## Befunde

### Behoben

- **P1 – horizontale Seitenscrollleiste:** Die technisch ausgeblendeten Vergleichs-`select`-Elemente wurden durch `.comparison-controls select { width: 100% }` wieder auf volle Breite gesetzt. Das erzeugte eine Dokumentbreite von 2201 px bei 1265 px Viewportbreite. Die selektive Regel für `select.sr-only` stellt nun die 1-px-Größe wieder her.
- Nachprüfung: Karte, Plottool, erweitere Stromsystem-Tabelle sowie Karten- und Plottool-Vollbild messen jeweils `scrollWidth === clientWidth`.

### Offen / nicht abnehmbar

- **Abnahmeumgebung:** Firefox, Full HD und WQHD sind nicht verfügbar. Die verpflichtenden zwölf Referenz-Screenshots werden daher nicht unter irreführenden Namen abgelegt.
- Europa-Overload-Gallery (einschließlich Bild 1 ↔ 250, Keyboard-Loop, Voting-Fallback und Gutter-Anordnung) ist bei 1280 px aufgrund des vorgesehenen `max-width: 1499px`-Verhaltens nicht visuell prüfbar.
- `prefers-reduced-motion` ließ sich in diesem Browser nicht simulieren.

## Abgelegte, maßstabsgetreu benannte Evidenz

- `available-1280x720-overview-fixed.png`
- `available-1280x720-table-expanded-fixed.png`
- `available-1280x720-map-fullscreen-fixed.png`
- `available-1280x720-comparison-fullscreen.png`
- `available-1280x720-country-profile-direct.png`
- `available-1280x720-overload-enabled.png`

## Automatisierte Prüfungen

- `PYTHONPATH=src <bundled-python> -m unittest discover -s tests` → **155 Tests OK**
- `<bundled-node> --check web/app.js` → **OK**
- `<bundled-node> --check web/wallpapers.js` → **OK**
- `git diff --check` → **OK**

## Nachträgliche Eigentümerabnahme

Der Projekteigentümer hat die Anwendung anschließend selbst bei Full HD und WQHD geprüft und am 25. August 2026 vorläufig abgenommen; dabei fiel ihm kein problematischer Darstellungsfehler auf. Diese praktische Abnahme ersetzt nicht die oben transparent dokumentierten Einschränkungen der Agentenumgebung. Galerie-Tastaturpfade, `prefers-reduced-motion` und die browserübergreifende Prüfung werden auf der Hoster-Testadresse erneut kontrolliert.

## Ergebnis

**ACCEPTED BY OWNER** – Der in der Agentenprüfung gefundene P1-Überlauf ist behoben, und Full HD/WQHD sind durch den Projekteigentümer vorläufig freigegeben. Die verbleibenden Browser- und Bedienvarianten sind Nachprüfungen für die Hoster-Testadresse, kein lokaler Desktop-Beta-Blocker.
