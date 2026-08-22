# Lokale Europakarte

Die Weboberfläche verwendet ausschließlich das lokale Asset `web/assets/europe.svg`. Beim Öffnen der Karte werden weder Kartenkacheln noch CDN-Ressourcen oder externe Trackingdienste geladen.

## Quelle und Nutzungsbedingungen

- Datensatz: Natural Earth 1:50m Admin 0 Countries
- Version: 5.1.1
- Quelldatei: `ne_50m_admin_0_countries.geojson`
- Offizielles Repository: `https://github.com/nvkelso/natural-earth-vector`
- Verwendeter Versionspfad: `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.1/geojson/ne_50m_admin_0_countries.geojson`
- SHA-256 der Quelldatei: `3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb`

Natural Earth stellt sämtliche Raster- und Vektorkartendaten gemeinfrei bereit. Veränderung, elektronische Weitergabe und kommerzielle Nutzung sind erlaubt. Eine Quellenangabe ist nicht vorgeschrieben, wird im Atlas aber freiwillig geführt: [Natural Earth Terms of Use](https://www.naturalearthdata.com/about/terms-of-use/).

## Verarbeitung

Das Standardbibliothek-Skript `tools/build_europe_map.py` verarbeitet die einmalig während der Entwicklung heruntergeladene GeoJSON-Datei:

1. Auswahl der Länderflächen für den sichtbaren Ausschnitt `-25° bis 42° Länge` und `34° bis 72° Breite`.
2. Beschneidung mit einem außerhalb des sichtbaren Ausschnitts liegenden Rand von `-30° bis 55° Länge` und `30° bis 76° Breite`. Dadurch erscheinen künstliche Schnittkanten großer Nachbarländer nicht als politische Grenzen.
3. Vereinfachung der Polygonringe mit einer Toleranz von `0,035°`.
4. Equirektanguläre Projektion der geografischen Koordinaten in die lokale SVG-Ebene. Der erweiterte Beschneidungsrand bleibt dadurch sicher außerhalb des sichtbaren Ausschnitts.
5. Ausgabe eines lokalen responsiven SVG mit genau einem Pfad je Natural-Earth-Länderfeature.

Reproduzierbarer Entwicklungsbefehl:

```powershell
python tools\build_europe_map.py `
  .tmp\ne_50m_admin_0_countries.geojson `
  web\assets\europe.svg
```

Das vollständige weltweite GeoJSON wird nicht ausgeliefert. Das erzeugte SVG enthält 73 europäische beziehungsweise angrenzende Hintergrundflächen und alle 31 Atlasländer.

## Länderkennungen

Die Geometrie verwendet Natural-Earth- beziehungsweise ISO3-Codes. Die Laufzeitabbildung auf den Atlas-Katalog steht zentral in `web/app.js`. Besonders zu beachten:

- `GBR` → `UK`
- `GRC` → `GR`

Jeder der 31 von `/api/countries` gelieferten Atlas-Codes besitzt genau eine Kartenfläche. Nicht zum Atlas gehörende Länder bleiben als neutraler Hintergrund im SVG; dazu gehören insbesondere Albanien und Russland. Diese Flächen sind weder mit Atlaswerten verknüpft noch auswählbar.

## Laufzeitverhalten

- Kennzahlenfamilie und Darstellung werden getrennt gewählt; fehlende Werte bleiben grau und werden nicht als Null interpretiert.
- Bei jährlichen Kennzahlen der Familie `Installierte Leistung` darf die Karte auf das jüngste verfügbare frühere Jahr ab 2015 zurückfallen. Angefordertes Jahr und tatsächlich verwendetes Datenjahr werden getrennt ausgewiesen; die Datenbank wird dabei nicht fortgeschrieben oder aufgefüllt.
- Werte können auf der Karte ein- und ausgeblendet werden. SVG- und PNG-Export bilden den aktuellen Zustand einschließlich Titel, Zeitraum, Einheit, Farbskala und Legende ab.
- Ein Kartenklick setzt einen dauerhaften Länderfokus, ohne die Länderauswahl des Zeitreihenvergleichs zu verändern. Ein Klick auf den umgebenden Kartenhintergrund löst diesen Fokus wieder.
- Familien erhalten unterscheidbare, auf den dunklen Kartenhintergrund abgestimmte Farbpaletten. Große kompakte Beschriftungen werden in Millionen mit zwei Nachkommastellen dargestellt.
- Die analytische Karte verwendet ausschließlich lokale Assets. Der optionale Modus `Europa Overload` lädt separat zugeschaltete, attribuierte Postkartenbilder von Wikimedia Commons und verändert weder Geometrie noch Kartendaten. Verhalten, Netzwerkzugriffe und lokale Reaktionen sind in [EUROPA_OVERLOAD.md](EUROPA_OVERLOAD.md) beschrieben.
