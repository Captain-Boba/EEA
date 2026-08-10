# Ergebnisbericht – Arbeitsauftrag 001

## Implementiert

- dependency-freier Python-Datenkern mit SQLite
- Rohdaten-Cache samt Prüfsumme, Request- und Lizenzmetadaten
- quellenunabhängiges Long-Format für kanonische Messgrößen
- normalisierte Erzeugung, Last, Preise, physische Im-/Exporte, bilaterale Flüsse und installierte Leistung
- Monats- und Jahresaggregation mit TWh, Mix, zentralem EE-Anteil, zeitgewichteten Preisstatistiken und Handelsbilanz
- automatische Coverage-, Summary- und Validierungsberichte
- schlichtes lokales UI mit sortierbarer Gesamttabelle und Vergleich von 2–4 Ländern
- automatisierte Tests für Einheiten, Zeitintegration, EE-Anteil, Preise, Handel, Lücken und DST

Verwendete Endpoints: `/v2/public_power`, `/v2/price`, `/v2/cbpf`, `/v2/installed_power`. `/v2/cbet` ist untersucht, wird aber nicht mit physischen Flüssen vermischt. `/v2/total_power` wird wegen DE-only-Coverage nicht verwendet.

## Funktionsstand der zehn Länder

Erzeugung/Mix, physische Grenzflüsse und installierte Leistung funktionieren für DE, FR, ES, IT, PL, NO, SE, DK und NL im kompletten Kalenderjahr 2025. UK ist nur **teilweise** abgedeckt: Energy-Charts liefert dort trotz MW-Deklaration nur wenige Erzeugungsserien (unter anderem fehlen Kernkraft, Offshore-Wind und Solar), und die Lastreihe enthält viele Nullwerte. Diese Zahlen werden nicht hochskaliert; unvollständige aggregierte Kennzahlen werden im UI nicht als präzise Werte ausgegeben. Die Last ist für DE, IT, PL, NO, SE und NL vollständig, für FR/ES/DK wegen gemeldeter Einzel- oder Monatslücken teilweise und für UK stark lückenhaft. Day-Ahead-Preise sind als nachvollziehbarer Landeswert für DE-LU, FR, ES, PL und NL vorhanden. IT, NO, SE und DK sind Mehrzonenmärkte und werden nicht ungewichtet aggregiert; UK fehlt außerdem im API-Preiszonenkatalog. CO₂-Intensität fehlt für alle Länder.

Die aktuelle automatisch erzeugte Detailtabelle steht in [COVERAGE.generated.md](../data/reports/COVERAGE.generated.md).

## Problematische Definitionen

- öffentliche Nettoerzeugung versus gesamte nationale Erzeugung
- DE-LU versus deutsches Staatsgebiet
- Pumpspeicher als Wasser/erneuerbar und separater Pumpverbrauch
- nicht klassifizierte `other_renewables`, Geothermie, Abfall und Batterie
- physischer Fluss versus Handelsfahrplan
- breitere nationale Betreiberzahlen einschließlich Eigenverbrauch/Schätzungen

Diese Unterschiede werden in der Datenbank und den Berichten sichtbar gelassen. Der Primärquellenvergleich für DE, FR und ES steht in [VALIDATION.generated.md](../data/reports/VALIDATION.generated.md).
