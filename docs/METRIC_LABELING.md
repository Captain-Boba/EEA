# Einheitliches Beschriftungssystem

Jede Kennzahl im zentralen Katalog `src/electricity_atlas/metrics.py` hat drei
rein redaktionelle Felder. Sie ändern weder Datenbank, Berechnung, API-IDs noch
CSV- oder URL-Parameter.

| Feld | Zweck |
|---|---|
| `display_topic` | fachlicher Kontext |
| `display_metric` | konkrete Kennzahl |
| `display_basis` | Bezugsgröße beziehungsweise Einheit |

Karte, Zeitvergleich, Ländersteckbrief und SVG-/PNG-Export verwenden diese drei
Felder. Tabellen und Auswahllisten verwenden daraus abgeleitete Kurzformen.
`group`, `family`, `representation`, `label_de` und `unit` behalten ihre
bisherige technische Bedeutung für Gruppierung, Auswahl und Berechnung.

## Vollständige Matrix

Verfügbarkeit: `M` = monatlich, `J` = jährlich, `S` = Snapshot.

| ID | Thema | Kennzahl | Grundlage | Einheit | Verfügbar |
|---|---|---|---|---|---|
| `generation_twh` | Stromerzeugung | Erzeugung absolut | in TWh | TWh | M, J |
| `consumption_twh` | Stromverbrauch | Verbrauch absolut | in TWh | TWh | M, J |
| `generation_per_capita_mwh` | Stromerzeugung | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `consumption_per_capita_mwh` | Stromverbrauch | Verbrauch pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `low_carbon_share_pct` | CO₂-arme Erzeugung | Erneuerbare und Kernenergie | Anteil in % an der Gesamterzeugung | % | M, J |
| `self_sufficiency_pct` | Stromsystem | Eigenversorgung | Erzeugung im Verhältnis zum Verbrauch in % | % | M, J |
| `renewable_twh` | Erneuerbare gesamt | Erzeugung absolut | in TWh | TWh | M, J |
| `renewable_share_pct` | Erneuerbare gesamt | Anteil | in % an der Gesamterzeugung | % | M, J |
| `renewable_per_capita_mwh` | Erneuerbare gesamt | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `wind_twh` | Wind | Erzeugung absolut | in TWh | TWh | M, J |
| `wind_share_pct` | Wind | Anteil | in % an der Gesamterzeugung | % | M, J |
| `wind_per_capita_mwh` | Wind | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `solar_twh` | Solar | Erzeugung absolut | in TWh | TWh | M, J |
| `solar_share_pct` | Solar | Anteil | in % an der Gesamterzeugung | % | M, J |
| `solar_per_capita_mwh` | Solar | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `hydro_twh` | Wasserkraft | Erzeugung absolut | in TWh | TWh | M, J |
| `hydro_share_pct` | Wasserkraft | Anteil | in % an der Gesamterzeugung | % | M, J |
| `hydro_per_capita_mwh` | Wasserkraft | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `bioenergy_twh` | Bioenergie | Erzeugung absolut | in TWh | TWh | M, J |
| `bioenergy_share_pct` | Bioenergie | Anteil | in % an der Gesamterzeugung | % | M, J |
| `bioenergy_per_capita_mwh` | Bioenergie | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `other_renewables_twh` | Sonstige Erneuerbare | Erzeugung absolut | in TWh | TWh | M, J |
| `other_renewables_share_pct` | Sonstige Erneuerbare | Anteil | in % an der Gesamterzeugung | % | M, J |
| `other_renewables_per_capita_mwh` | Sonstige Erneuerbare | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `fossil_twh` | Fossile gesamt | Erzeugung absolut | in TWh | TWh | M, J |
| `fossil_share_pct` | Fossile gesamt | Anteil | in % an der Gesamterzeugung | % | M, J |
| `fossil_per_capita_mwh` | Fossile gesamt | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `coal_twh` | Kohle | Erzeugung absolut | in TWh | TWh | M, J |
| `coal_share_pct` | Kohle | Anteil | in % an der Gesamterzeugung | % | M, J |
| `coal_per_capita_mwh` | Kohle | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `gas_twh` | Gas | Erzeugung absolut | in TWh | TWh | M, J |
| `gas_share_pct` | Gas | Anteil | in % an der Gesamterzeugung | % | M, J |
| `gas_per_capita_mwh` | Gas | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `other_fossil_twh` | Sonstige Fossile | Erzeugung absolut | in TWh | TWh | M, J |
| `other_fossil_share_pct` | Sonstige Fossile | Anteil | in % an der Gesamterzeugung | % | M, J |
| `other_fossil_per_capita_mwh` | Sonstige Fossile | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `nuclear_twh` | Kernenergie | Erzeugung absolut | in TWh | TWh | M, J |
| `nuclear_share_pct` | Kernenergie | Anteil | in % an der Gesamterzeugung | % | M, J |
| `nuclear_per_capita_mwh` | Kernenergie | Erzeugung pro Kopf | in MWh je Einwohner | MWh/Einwohner | J |
| `net_imports_twh` | Stromhandel | Nettoimporte absolut | in TWh | TWh | M, J |
| `net_import_share_pct` | Stromhandel | Nettoimporte | Anteil in % am Stromverbrauch | % | M, J |
| `price_avg_eur_mwh` | Großhandelsstrompreis | Durchschnittlicher Day-Ahead-Preis | in EUR/MWh | EUR/MWh | M, J |
| `carbon_intensity_gco2eq_kwh` | Emissionen der Stromerzeugung | CO₂-Intensität | in gCO₂eq/kWh | gCO₂eq/kWh | M, J |
| `estimated_generation_emissions_mtco2eq` | Emissionen der Stromerzeugung | Geschätzte Emissionen | in Mt CO₂eq | Mt CO₂eq | M, J |
| `decarbonization_rate_pct` | Emissionen der Stromerzeugung | Dekarbonisierung | Veränderung in % gegenüber dem Vorjahr | % | J |
| `eea_public_electricity_heat_emissions_mtco2eq` | Klima | Emissionen öffentliche Strom- und Wärmeerzeugung | CRT 1.A.1.a; Strom und Wärme · in Mt CO₂eq | Mt CO₂eq | J |
| `population` | Sozioökonomie | Bevölkerung | in Einwohnern | Einwohner | J |
| `gdp_current_billion_eur` | Sozioökonomie | BIP | in Mrd. EUR | Mrd. EUR | J |
| `gdp_per_capita_pps` | Sozioökonomie | BIP pro Kopf | in PPS je Einwohner | PPS/Einwohner | J |
| `generation_gdp_intensity_kwh_eur` | Stromerzeugung | Erzeugung je BIP | in kWh/EUR | kWh/EUR | J |
| `consumption_gdp_intensity_kwh_eur` | Stromverbrauch | Verbrauch je BIP | in kWh/EUR | kWh/EUR | J |
| `electricity_heat_emissions_gdp_t_million_eur` | Emissionen der Stromerzeugung | Strom- und Wärmeemissionen je BIP | in t CO₂eq/Mio. EUR | t CO₂eq/Mio. EUR | J |
| `capacity_total_gw` | Installierte Leistung | Gesamtleistung | in GW | GW | J |
| `capacity_wind_gw` | Installierte Leistung | Windleistung | in GW | GW | J |
| `capacity_solar_gw` | Installierte Leistung | Solarleistung | in GW | GW | J |
| `capacity_hydro_gw` | Installierte Leistung | Wasserkraftleistung | in GW | GW | J |
| `capacity_fossil_gw` | Installierte Leistung | Fossile Leistung | in GW | GW | J |
| `capacity_nuclear_gw` | Installierte Leistung | Kernenergieleistung | in GW | GW | J |
| `capacity_factor_wind_pct` | Wind | Kapazitätsfaktor | in % der installierten Leistung | % | J |
| `capacity_factor_solar_pct` | Solar | Kapazitätsfaktor | in % der installierten Leistung | % | J |
| `capacity_factor_hydro_pct` | Wasserkraft | Kapazitätsfaktor | in % der installierten Leistung | % | J |
| `capacity_factor_fossil_pct` | Fossile gesamt | Kapazitätsfaktor | in % der installierten Leistung | % | J |
| `capacity_factor_nuclear_pct` | Kernenergie | Kapazitätsfaktor | in % der installierten Leistung | % | J |
| `household_electricity_price_eur_mwh` | Endkundenpreise | Haushaltsstrompreis | Gesamtpreis (2.500–4.999 kWh/Jahr) · in ct/kWh | ct/kWh | J |
| `household_price_energy_eur_mwh` | Endkundenpreise | Haushalt: Energie und Vertrieb | Energie und Vertrieb (Preisbestandteil) · in ct/kWh | ct/kWh | J |
| `household_price_network_eur_mwh` | Endkundenpreise | Haushalt: Netzentgelte | Netzentgelte (Preisbestandteil) · in ct/kWh | ct/kWh | J |
| `household_price_taxes_eur_mwh` | Endkundenpreise | Haushalt: Steuern, Abgaben und Umlagen | Steuern, Abgaben und Umlagen (Preisbestandteil) · in ct/kWh | ct/kWh | J |
| `household_wholesale_price_gap_ct_kwh` | Endkundenpreise | Endkunden–Großhandelspreis-Abstand | Haushaltspreis minus Großhandelspreis · in ct/kWh | ct/kWh | J |
| `nonhousehold_electricity_price_eur_mwh` | Endkundenpreise | Nicht-Haushaltsstrompreis | Band IC, Jahreskomponenten · in EUR/MWh | EUR/MWh | J |
| `nonhousehold_price_energy_eur_mwh` | Endkundenpreise | Nicht-Haushalt: Energie und Vertrieb | Energie und Vertrieb, Band IC · in EUR/MWh | EUR/MWh | J |
| `nonhousehold_price_network_eur_mwh` | Endkundenpreise | Nicht-Haushalt: Netzkosten | Netzkosten, Band IC · in EUR/MWh | EUR/MWh | J |
| `nonhousehold_price_taxes_eur_mwh` | Endkundenpreise | Nicht-Haushalt: Steuern und Abgaben | Steuern und Abgaben, Band IC · in EUR/MWh | EUR/MWh | J |
| `gross_imports_twh` | Stromhandel | Bruttoimporte | in TWh | TWh | J |
| `gross_exports_twh` | Stromhandel | Bruttoexporte | in TWh | TWh | J |
| `electricity_trade_throughput_pct` | Handel | Stromhandelsdurchsatz | Importe plus Exporte im Verhältnis zum Verbrauch in % | % | J |
| `bev_stock` | Elektromobilität | Batterieelektrische Pkw im Bestand | in Fahrzeugen | Fahrzeuge | J |
| `bev_new_registrations` | Elektromobilität | Neue batterieelektrische Pkw | in Fahrzeugen | Fahrzeuge | J |
| `ev_battery_nominal_capacity_est_gwh` | Elektromobilität | Theoretische EV-Batteriekapazität | in GWh | GWh | J |
| `hydro_plant_capacity_gw` | Wasserkraftinventar | Kraftwerksleistung | in GW | GW | S |
| `hydro_pumping_power_gw` | Wasserkraftinventar | Pumpleistung | in GW | GW | S |
| `hydro_reservoir_energy_gwh` | Wasserkraftinventar | Speicherenergie | in GWh | GWh | S |
| `battery_power_gw` | Batteriespeicher | Installierte Entladeleistung | in GW | GW | S |
| `battery_energy_gwh` | Batteriespeicher | Installierte Speicherkapazität | in GWh | GWh | S |
| `battery_duration_hours` | Batteriespeicher | Äquivalente Entladedauer | in Stunden | h | S |
| `pumped_storage_power_gw` | Pumpspeicher | Installierte Entladeleistung | in GW | GW | S |
| `pumped_storage_energy_gwh` | Pumpspeicher | Installierte Speicherkapazität | in GWh | GWh | S |
| `pumped_storage_duration_hours` | Pumpspeicher | Äquivalente Entladedauer | in Stunden | h | S |

## Redaktionelle Regeln

- Energie und Leistung werden stets getrennt: `in TWh` beziehungsweise
  `in GWh` für Energie, `in GW` für Leistung.
- Anteilssätze nennen ihren Nenner ausdrücklich. Veränderungen verwenden
  `Veränderung in % gegenüber dem Vorjahr`.
- Die Einheit erscheint in der Grundlage genau einmal. Sie wird nicht noch
  einmal hinter dem sichtbaren Text angehängt.
- Fehlende Werte bleiben fehlend; die Beschriftung erzeugt keine Werte und
  verändert keine Verfügbarkeit.
