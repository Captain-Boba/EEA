# Validierungsbericht DE/FR/ES 2025

> **Historischer Bericht der früheren Energy-Charts-Architektur.** Dieses
> Dokument wird vom aktuellen `eea report`-Befehl nicht neu erzeugt und ist
> nicht als Validierung des heutigen Ember-Datenkerns zu verwenden. Es bleibt
> ausschließlich zur Nachvollziehbarkeit der damaligen Prüfmethode erhalten.

| Land | Erzeugung TWh | Verbrauch TWh | EE TWh | EE % | Intervalle | max. Identitätsabweichung MW | mittl. EE-Abweichung %-Pkt. | Ergebnis |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| DE | 425.128 | 465.818 | 263.966 | 62.09 | 35040 | 0.000000 | 1.354 | INTERNAL_PASS |
| FR | 533.907 | — | 141.492 | 26.50 | 35021 | 0.000000 | 1.005 | INTERNAL_PASS |
| ES | 259.031 | — | 151.120 | 58.34 | 35039 | 0.000000 | 1.607 | INTERNAL_PASS |

## Methode und Grenze

Die Jahreswerte werden aus den offiziellen 15-/60-Minuten-Leistungswerten integriert. Zusätzlich werden je Intervall Kategoriensumme und der von Energy-Charts gemeldete EE-Anteil geprüft. Dies validiert Transformation und Aggregation, ist aber keine unabhängige Zweitquelle.
Die mittlere EE-Abweichung von rund 1 bis 1,6 Prozentpunkten ist kein Rundungsfehler, sondern ein Definitionssignal: Der Atlas zählt gemäß Arbeitsauftrag die gesamte gemeldete Wasserkrafterzeugung einschließlich Pumpspeicher als erneuerbar; Energy-Charts und nationale Berichte behandeln Speicher und weitere Kategorien anders.

## Vergleich mit unabhängigen offiziellen Jahresdarstellungen

| Land | Kennzahl | Atlas | offizielle Referenz | Abweichung | Definitionshinweis |
|---|---|---:|---:|---:|---|
| DE | EE TWh | 263.966 | 256.000 | +7.966 | ins öffentliche Netz eingespeiste Erneuerbare; Atlas-Definition enthält Pumpspeichererzeugung |
| DE | Wind TWh | 131.167 | 132.000 | -0.833 | öffentliche Nettoerzeugung, gerundet |
| DE | Solar TWh | 70.123 | 71.000 | -0.877 | Netzeinspeisung ohne 16,9 TWh Eigenverbrauch |
| FR | Erzeugung TWh | 533.907 | 547.500 | -13.593 | gesamte Festland-Erzeugung; breiter als öffentliche Energy-Charts-Reihe |
| FR | EE % | 26.501 | 27.000 | -0.499 | RTE nationale Definition |
| FR | Kernkraft TWh | 371.455 | 373.000 | -1.545 | RTE nationale Definition |
| ES | Erzeugung TWh | 259.031 | 272.201 | -13.170 | nationales System; Energy-Charts-Reihe ist enger |
| ES | EE TWh | 151.120 | 150.988 | +0.132 | ohne geschätzten Eigenverbrauch |
| ES | EE % | 58.340 | 55.500 | +2.840 | nationale Definition; Pumpspeicher/sonstige EE abweichend |

### Primärquellen
- DE: [Fraunhofer ISE Jahresauswertung 2025](https://www.ise.fraunhofer.de/en/press-media/press-releases/2026/german-public-electricity-generation-in-2025-wind-and-solar-power-take-the-lead.html)
- FR: [RTE Annual Electricity Review 2025](https://analysesetdonnees.rte-france.com/en/annual-review-2025/generation)
- ES: [Red Eléctrica, Spanish Electricity System 2025](https://www.sistemaelectrico-ree.es/en/spanish-electricity-system/generation/total-electricity-generation)

Bewertung: Die Transformationsidentität besteht in allen drei Ländern. Die unabhängigen Jahreswerte sind plausibel nah, aber wegen öffentlicher Nettoerzeugung versus breiter nationaler Erzeugung und abweichender Speicher-/Eigenverbrauchsdefinitionen nicht austauschbar. Diese Differenz wird nicht wegkorrigiert.
