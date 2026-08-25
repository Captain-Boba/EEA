# Beta-Datenvalidierung

Prüfauftrag: `K4-BETA-DATA-001`

Prüfdatum: 25. August 2026

Datengate: **REFRESH REQUIRED**

## Kurzentscheidung

Die geprüfte SQLite-Datenbank ist technisch intakt. Der komplette Primärschlüssel ist eindeutig, alle 31 Datenbankländer gehören zum Atlas-Katalog, Albanien und Russland fehlen wie gefordert, und 140 von 140 durchführbaren Ember-Einzelvergleichen bestehen die aus der Quellauflösung abgeleitete Rundungstoleranz. Auch die fünf neuen Kreuzkennzahlen stimmen bei unabhängiger Nachrechnung für Deutschland, Frankreich und Spanien exakt mit den Laufzeitwerten überein.

Nach der Prüfung hat der Projekteigentümer zwei Produktentscheidungen getroffen:

1. Die Türkei ist bewusst kein Bestandteil des 31-Länder-Atlas. Ihre Nennung im ursprünglichen Prüfauftrag war ein Planungsfehler und ist weder Datenlücke noch Freigabebedingung.
2. Aggregierte Werte aus dem **European Energy Storage Inventory** dürfen für die vorläufige nichtkommerzielle Beta bei klarer Attribution sowie Schätzungs- und Unvollständigkeitshinweisen verwendet werden. Eine weitergehende Rechteklärung oder Ablösung durch Ember wird auf Post-Beta verschoben; eine rechtliche Freigabe wird damit ausdrücklich nicht behauptet.

Vor dem finalen Datengate bleiben damit der einmalige kontrollierte Komplett-Refresh und die erneute Validierung des daraus entstehenden Datenbankhashes offen. `data/reports/SUMMARY.generated.json` stimmt noch nicht mit einer frischen Read-only-Ausführung gegen den hier geprüften älteren Datenstand überein. Außerdem verspricht die CLI-Hilfe Coverage, Summary **und** Validation, erzeugt tatsächlich aber nur Coverage und Summary. Der Summary-Bericht wird nach dem Refresh neu erzeugt; der CLI-Vertrag wird separat bereinigt.

## 1. Prüfidentität und Schutzmaßnahmen

| Merkmal | Geprüfter Wert |
|---|---|
| Git-Branch | `main` |
| HEAD | `ec731697edfbdce4c10f58e1a8cbec563a1a38fb` |
| Geforderter Basiscommit | `3b74a44` ist Vorfahr des geprüften HEAD |
| Datenbank | `E:\EEA\data\atlas.sqlite3` |
| Größe | 55.631.872 Byte |
| Änderungsdatum (UTC) | 2026-08-14 08:22:30 |
| SHA-256 | `EDDE470DB65E9EC39C888A858955E731D5FA4F3EC741F6BEC78E52BBB340DDE9` |
| Öffnung | SQLite-URI mit `mode=ro` |
| Schreibschutz | `PRAGMA query_only=ON`, Rückgabewert `1` |
| Integrität | `PRAGMA integrity_check = ok` |

Der Arbeitsbaum war zu Prüfungsbeginn sauber. Während der Prüfung erschienen fremde, nicht von K4 erzeugte Änderungen an README-, CLI-, Server-, Community-, Test- und Deploymentdateien. HEAD und Datenbankfingerabdruck blieben unverändert; die für diese Prüfung verwendeten Aggregations- und Metrikdateien wurden dabei nicht als geändert ausgewiesen. Die dokumentierte CLI-Prüfung bezieht sich auf den zu Beginn sauberen, weiterhin ausgecheckten HEAD; spätere uncommittete Fremdänderungen sind kein akzeptierter Prüfstand. K4 hat die fremden Änderungen weder bearbeitet noch gestaged.

Die Datenbank ist nicht Git-versioniert. Der Auftrag bezeichnet sie als vorgesehenen finalen Kandidaten; eine frühere formale Annahme genau dieses Hashes war im Repository nicht dokumentiert. Dieser Bericht bindet alle Ergebnisse an den oben genannten SHA-256. K1 muss genau diesen Hash für die Beta annehmen. Bei jeder Hashänderung ist die Prüfung zu wiederholen.

K4 hat keine Import-, Refresh-, Migrations- oder Reparaturfunktion aufgerufen. Es gab keine Datenbankänderung und keine breite Ember-Netzabfrage. Die Ember-Stichprobe verwendet ausschließlich die in `api_cache` und `source_cache` gespeicherten, eindeutig zuordenbaren offiziellen Quellantworten.

## 2. Technische Datenbankinventur

### 2.1 Schema

| Tabelle | Zweck | Schlüssel |
|---|---|---|
| `period_observation` | normalisierte Perioden- und Snapshotwerte | `(country_code, period_start, period_end, granularity, source, source_endpoint, source_series, metric)` |
| `api_cache` | gespeicherte Ember-API-Antworten | `id`, zusätzlich eindeutige Kombination aus Endpoint, Ziel und Zeitraum |
| `source_cache` | gespeicherte Dateien/Antworten weiterer Quellen | `(source, endpoint)` |
| `sqlite_stat1` | SQLite-Statistik | kein fachlicher Datenbestand |

`period_observation` ist eine `WITHOUT ROWID`-Tabelle. Alle fachlichen Felder einschließlich `value` sind `NOT NULL`. Fehlende Daten werden folglich durch eine fehlende Beobachtung und zur Laufzeit durch `null` dargestellt, nicht durch SQL-NULL oder einen erfundenen Nullwert.

### 2.2 Umfang

| Kennzahl | Anzahl |
|---|---:|
| `period_observation` gesamt | 121.908 |
| Länder | 31 |
| Quellen | 5 |
| gespeicherte Raw-Metrik-IDs | 50 |
| Laufzeitkennzahlen im Katalog | 87 |
| `api_cache` | 403 |
| `source_cache` | 27 |
| Primärschlüsselduplikate | 0 |
| SQL-NULL-Felder | 0 |

### 2.3 Perioden

| Granularität | Zeilen | Länder | Raw-Metriken | Frühester Beginn | Spätestes Ende |
|---|---:|---:|---:|---|---|
| monatlich | 106.526 | 31 | 21 | 2015-01-01 | 2026-08-31 |
| jährlich | 15.075 | 31 | 36 | 2015-01-01 | 2026-12-31 |
| Snapshot | 307 | 31 | 12 | 2023-10-25 | 2026-08-12 |

### 2.4 Quellen

| Quelle | Zeilen | Länder | Raw-Metriken | Frühester Beginn | Spätestes Ende | Einordnung |
|---|---:|---:|---:|---|---|---|
| Ember | 114.027 | 31 | 18 | 2015-01-01 | 2026-08-31 | Erzeugung, Nachfrage, CO₂-Intensität, Preise |
| Eurostat | 5.624 | 31 | 19 | 2015-01-01 | 2026-12-31 | Bevölkerung, BIP, Leistung, Preise, Handel, BEV |
| Battery-Charts | 1.680 | 1 | 3 | 2015-01-01 | 2026-08-12 | deutsche Batteriespeicher, monatlich |
| JRC | 307 | 31 | 12 | 2023-10-25 | 2026-08-12 | Projekt-/Anlageninventare, Snapshot |
| EEA | 270 | 27 | 1 | 2015-01-01 | 2024-12-31 | CRT 1.A.1.a Strom und öffentliche Wärme |

Die Quellennamen entsprechen den im Projekt vorgesehenen fünf Quellen. Es gibt keine unerwartete Quelle.

### 2.5 Länder

Vorhanden sind exakt: `AT, BE, BG, CH, CZ, DE, DK, EE, ES, FI, FR, GR, HR, HU, IE, IT, LT, LU, LV, ME, MK, NL, NO, PL, PT, RO, RS, SE, SI, SK, UK`.

- Unerwartete Länder gegenüber dem Laufzeitkatalog: **0**
- Atlas-Länder ohne irgendeine Beobachtung: **0**
- Albanien (`AL`/`ALB`): **nicht vorhanden**
- Russland (`RU`/`RUS`): **nicht vorhanden**
- Türkei (`TR`/`TUR`): **nicht vorhanden und nicht im Laufzeitkatalog**

### 2.6 Null-, Negativ- und Fehlwerte

Raw-Metriken, die in der folgenden Tabelle nicht aufgeführt sind, enthalten weder echte Nullwerte noch negative Werte.

| Raw-Metrik | echte Nullwerte | negative Werte | Bewertung |
|---|---:|---:|---|
| `capacity_nuclear_gw` | 161 | 0 | plausible echte Null bei Ländern/Jahren ohne Kernkraft |
| `capacity_solar_gw` | 17 | 0 | als Quellwert bewahrt |
| `capacity_wind_gw` | 3 | 0 | als Quellwert bewahrt |
| `carbon_intensity` | 1 | 0 | Montenegro 2017-05; beobachteter Quellwert, fachlich auffällig |
| `generation_biomass` | 189 | 0 | als Quellwert bewahrt |
| `generation_coal` | 475 | 0 | als Quellwert bewahrt |
| `generation_fossil` | 77 | 0 | als Quellwert bewahrt |
| `generation_gas` | 325 | 0 | als Quellwert bewahrt |
| `generation_hydro` | 286 | 0 | als Quellwert bewahrt |
| `generation_nuclear` | 343 | 0 | als Quellwert bewahrt |
| `generation_other_fossil` | 509 | 3 | negative Residuen HR/LV/SI 2025 werden zur Laufzeit fehlend |
| `generation_other_renewables` | 976 | 3 | negative Residuen CZ/DE/ES 2025 werden zur Laufzeit fehlend |
| `generation_renewables` | 1 | 0 | als Quellwert bewahrt |
| `generation_solar` | 577 | 0 | als Quellwert bewahrt |
| `generation_wind` | 296 | 0 | als Quellwert bewahrt |
| `net_imports` | 25 | 1.730 | negative Werte sind Nettoexporte, keine Fehler |
| `share_of_generation_pct` | 4.053 | 6 | die sechs negativen Anteile gehören zu denselben Residuen |
| `household_price_taxes_eur_mwh` | 0 | 17 | negative Steuer-/Abgabenkomponente kann Entlastung/Subvention bedeuten |
| `nonhousehold_price_taxes_eur_mwh` | 0 | 3 | negative Steuer-/Abgabenkomponente kann Entlastung/Subvention bedeuten |

Die sechs negativen Erzeugungsresiduen und ihre sechs negativen Anteile werden nicht auf Null gesetzt. Die Laufzeitaggregation entfernt die jeweilige Residualkategorie und liefert dafür `null`; die unveränderten Raw-Werte bleiben nachvollziehbar gespeichert.

Fehlwerte sind mengenmäßig in der Coverage unten dokumentiert. Besonders relevant sind fehlendes nominales BIP für UK, fehlendes BIP pro Kopf für CH und UK, fehlende EEA-Inventaremissionen für ME/MK/RS/UK, lückenhafte 2025-Preise für CH/ME/MK und unvollständige Speicherinventare.

## 3. YTD- und Vorläufigkeitsstatus

| Quelle/Metrik | Status | Zeitraum | Zeilen/Länder |
|---|---|---|---:|
| Ember `day_ahead_price` | `provisional_current_month` | 2026-08-01 bis 2026-08-31 | 31/31 |
| Battery-Charts Leistung | `provisional_current_month` | 2026-08-01 bis 2026-08-12 | 4 Reihen für DE |
| Battery-Charts Energie | `provisional_current_month` | 2026-08-01 bis 2026-08-12 | 4 Reihen für DE |
| Battery-Charts Dauer | `derived_provisional` | 2026-08-01 bis 2026-08-12 | 4 Reihen für DE |

Die Jahresaggregation 2026 ist YTD und summiert nur vorhandene Monatswerte. Beim Preis wird der vorläufige August aus dem Jahresmittel ausgeschlossen. Ember-Erzeugung, Nachfrage und CO₂-Intensität reichen für 27 Länder bis Juli 2026; CH, IE, IT und MK haben für diesen Monat keine entsprechenden Kernwerte. Ein YTD-Wert ist daher nicht mit einem abgeschlossenen Jahreswert gleichzusetzen.

## 4. Coverage der 87 Laufzeitkennzahlen

Die Zählung verwendet für Monatskennzahlen den jüngsten abgeschlossenen Monat `2026-07`, für Jahreskennzahlen das Berichtsjahr `2025` und für Snapshotkennzahlen die jeweils aktuell vom Laufzeitendpunkt ausgewählte Beobachtung. Ein Wert zählt nur, wenn er numerisch und endlich ist.

### 4.1 Monatliche Kennzahlen (31)

| Coverage | Kennzahlen |
|---:|---|
| 31/31 | `price_avg_eur_mwh` |
| 27/31 | `generation_twh`, `consumption_twh`, `low_carbon_share_pct`, `self_sufficiency_pct`, `renewable_twh`, `renewable_share_pct`, `wind_twh`, `wind_share_pct`, `fossil_twh`, `fossil_share_pct`, `nuclear_twh`, `nuclear_share_pct`, `net_imports_twh`, `net_import_share_pct`, `carbon_intensity_gco2eq_kwh`, `estimated_generation_emissions_mtco2eq` |
| 26/31 | `solar_twh`, `solar_share_pct`, `hydro_twh`, `hydro_share_pct`, `gas_twh`, `gas_share_pct` |
| 25/31 | `bioenergy_twh`, `bioenergy_share_pct` |
| 24/31 | `other_fossil_twh`, `other_fossil_share_pct` |
| 21/31 | `coal_twh`, `coal_share_pct` |
| 16/31 | `other_renewables_twh`, `other_renewables_share_pct` |

### 4.2 Jährliche Kennzahlen (78)

| Coverage 2025 | Kennzahlen |
|---:|---|
| 31/31 | `generation_twh`, `consumption_twh`, `generation_per_capita_mwh`, `consumption_per_capita_mwh`, `low_carbon_share_pct`, `self_sufficiency_pct`, `renewable_twh`, `renewable_share_pct`, `renewable_per_capita_mwh`, `wind_twh`, `wind_share_pct`, `wind_per_capita_mwh`, `solar_twh`, `solar_share_pct`, `solar_per_capita_mwh`, `hydro_twh`, `hydro_share_pct`, `hydro_per_capita_mwh`, `bioenergy_twh`, `bioenergy_share_pct`, `bioenergy_per_capita_mwh`, `fossil_twh`, `fossil_share_pct`, `fossil_per_capita_mwh`, `gas_twh`, `gas_share_pct`, `gas_per_capita_mwh`, `nuclear_twh`, `nuclear_share_pct`, `nuclear_per_capita_mwh`, `net_imports_twh`, `net_import_share_pct`, `carbon_intensity_gco2eq_kwh`, `estimated_generation_emissions_mtco2eq`, `decarbonization_rate_pct`, `population` |
| 30/31 | `coal_twh`, `coal_share_pct`, `coal_per_capita_mwh`, `gdp_current_billion_eur`, `generation_gdp_intensity_kwh_eur`, `consumption_gdp_intensity_kwh_eur`, `bev_stock`, `ev_battery_nominal_capacity_est_gwh` |
| 29/31 | `gdp_per_capita_pps`, vier Haushalts-, vier Nicht-Haushaltspreiskennzahlen, `gross_imports_twh`, `gross_exports_twh`, `electricity_trade_throughput_pct`, `bev_new_registrations` |
| 28/31 | drei Kennzahlen „sonstige Erneuerbare“, drei Kennzahlen „sonstige Fossile“, `price_avg_eur_mwh` |
| 27/31 | `household_wholesale_price_gap_ct_kwh` |
| 0/31 | `eea_public_electricity_heat_emissions_mtco2eq`, `electricity_heat_emissions_gdp_t_million_eur`, sechs installierte Leistungskennzahlen und fünf Kapazitätsfaktoren |

Die 13 Kennzahlen mit 0/31 sind für 2025 nicht durch Nullen ersetzt worden: EEA-Emissionen und Eurostat-Leistungen enden 2024. Für 2024 liegen EEA-Emissionen und deren BIP-Relation für 27/31 Länder sowie die sechs Leistungsmessgrößen und vier nicht-nukleare Kapazitätsfaktoren für 29/31 Länder vor. Der Kernenergie-Kapazitätsfaktor ist 2024 nur für 12/31 Länder definiert; bei fehlender oder nuller installierter Kernenergieleistung bleibt er `null`.

### 4.3 Snapshotkennzahlen (9)

| Coverage | Kennzahlen |
|---:|---|
| 28/31 | `battery_power_gw`, `battery_energy_gwh`, `battery_duration_hours` |
| 27/31 | `hydro_plant_capacity_gw` |
| 23/31 | `pumped_storage_power_gw`, `pumped_storage_energy_gwh`, `pumped_storage_duration_hours` |
| 21/31 | `hydro_reservoir_energy_gwh` |
| 19/31 | `hydro_pumping_power_gw` |

Raw observations und Laufzeitkatalog sind nicht identisch: Die Datenbank speichert 50 normalisierte Raw-Metriken. Der Katalog stellt daraus 87 Kennzahlen bereit, darunter Summen, Anteile, Pro-Kopf-Werte, Kapazitätsfaktoren und die fünf Kreuzkennzahlen. Die drei alten kombinierten `storage_*`-Raw-Metriken sind nicht als eigene Laufzeitkennzahlen katalogisiert.

## 5. Manuelle Ember-Stichproben

### 5.1 Methode und Toleranz

Verwendet wurden ausschließlich gespeicherte offizielle Antworten mit HTTP-Status 200:

- `ember/electricity-generation/yearly`
- `ember/electricity-generation/monthly`
- `ember/electricity-demand/monthly`
- `ember/carbon-intensity/yearly`
- `ember/carbon-intensity/monthly`
- `wholesale-electricity-price/monthly-csv`

Die API-Payloads wurden am 10. und 11. August 2026 gespeichert; die Preis-CSV wurde am 10. August 2026 gespeichert. Der Datenbankhash bindet diese Payloads an die Prüfung.

Quellwerte werden mit zwei Dezimalstellen geliefert. Für direkt übernommene TWh-, gCO₂/kWh- und EUR/MWh-Werte gilt deshalb eine absolute Toleranz von `0,005` in der jeweiligen Einheit. Der Atlas berechnet den EE-Anteil aus den auf 0,01 TWh gerundeten Quellwerten neu. Seine Toleranz ist je Zeile `0,005 Prozentpunkte +` die aus `±0,005 TWh` für Zähler und Nenner fortgepflanzte Unsicherheit. Der Jahrespreis ist das mit den Kalendertagen jedes Monats gewichtete Mittel der zwölf gespeicherten Monatswerte.

Notation: `Quelle→Atlas`; `G` Erzeugung, `V` Nachfrage/Verbrauch, `EE` erneuerbare Erzeugung, `EE%` Anteil, `CI` CO₂-Intensität, `P` Großhandelspreis. Alle nicht als Anteil ausgewiesenen Abweichungen sind exakt null. `Δmax` und die relative Abweichung beziehen sich daher auf `EE%`.

| Land | Zeitraum | Quelle→Atlas | Δmax absolut | Δmax relativ | Ergebnis |
|---|---|---|---:|---:|---|
| DE | 2025 | G 499,890→499,890 TWh; V 519,380→519,380 TWh; EE 295,160→295,160 TWh; Wind 136,030→136,030 TWh; CI 330,020→330,020; P 89,478→89,478; EE% 59,040→59,045 | 0,00499 %-Pkt. | 0,00845 % | PASS |
| DE | 2025-01 | G 45,120→45,120; V 45,200→45,200; EE 23,780→23,780; Wind 15,540→15,540 TWh; CI 380,230→380,230; P 114,190→114,190; EE% 52,700→52,704 | 0,00390 %-Pkt. | 0,00740 % | PASS |
| DE | 2025-07 | G 37,100→37,100; V 40,010→40,010; EE 23,360→23,360; Wind 7,690→7,690 TWh; CI 332,940→332,940; P 87,550→87,550; EE% 62,960→62,965 | 0,00496 %-Pkt. | 0,00788 % | PASS |
| DE | 2026-07 | G 41,720→41,720; V 41,640→41,640; EE 29,390→29,390; Wind 9,870→9,870 TWh; CI 273,250→273,250; P 106,790→106,790; EE% 70,450→70,446 | 0,00417 %-Pkt. | 0,00592 % | PASS |
| FR | 2025 | G 570,140→570,140; V 476,340→476,340; EE 148,720→148,720; Kernenergie 392,070→392,070 TWh; CI 41,450→41,450; P 62,908→62,908; EE% 26,080→26,085 | 0,00482 %-Pkt. | 0,01849 % | PASS |
| FR | 2025-01 | G 55,510→55,510; V 48,910→48,910; EE 13,240→13,240; Kernenergie 38,620→38,620 TWh; CI 45,140→45,140; P 102,440→102,440; EE% 23,850→23,852 | 0,00156 %-Pkt. | 0,00653 % | PASS |
| FR | 2025-07 | G 40,890→40,890; V 31,960→31,960; EE 10,280→10,280; Kernenergie 29,430→29,430 TWh; CI 27,710→27,710; P 57,960→57,960; EE% 25,140→25,141 | 0,00062 %-Pkt. | 0,00247 % | PASS |
| FR | 2026-07 | G 42,310→42,310; V 34,320→34,320; EE 11,060→11,060; Kernenergie 29,690→29,690 TWh; CI 31,960→31,960; P 96,610→96,610; EE% 26,140→26,140 | 0,00039 %-Pkt. | 0,00150 % | PASS |
| UK | 2025 | G 292,410→292,410; V 321,480→321,480; EE 152,020→152,020; Wind 85,940→85,940 TWh; CI 217,330→217,330; P 94,146→94,146; EE% 51,990→51,989 | 0,00135 %-Pkt. | 0,00260 % | PASS |
| UK | 2025-01 | G 29,280→29,280; V 31,380→31,380; EE 12,940→12,940; Wind 8,290→8,290 TWh; CI 265,630→265,630; P 141,290→141,290; EE% 44,180→44,194 | 0,01399 %-Pkt. | 0,03166 % | PASS |
| UK | 2025-07 | G 21,360→21,360; V 23,190→23,190; EE 10,990→10,990; Wind 4,680→4,680 TWh; CI 221,760→221,760; P 91,630→91,630; EE% 51,470→51,451 | 0,01869 %-Pkt. | 0,03631 % | PASS |
| UK | 2026-07 | G 20,030→20,030; V 22,230→22,230; EE 11,380→11,380; Wind 5,310→5,310 TWh; CI 209,130→209,130; P 125,370→125,370; EE% 56,830→56,815 | 0,01522 %-Pkt. | 0,02679 % | PASS |
| ES | 2025 | G 287,920→287,920; V 275,130→275,130; EE 160,810→160,810; Solar 62,920→62,920 TWh; CI 153,580→153,580; P 66,799→66,799; EE% 55,850→55,852 | 0,00232 %-Pkt. | 0,00415 % | PASS |
| ES | 2025-01 | G 22,840→22,840; V 21,740→21,740; EE 13,170→13,170; Solar 2,510→2,510 TWh; CI 126,800→126,800; P 96,690→96,690; EE% 57,660→57,662 | 0,00200 %-Pkt. | 0,00346 % | PASS |
| ES | 2025-07 | G 24,000→24,000; V 22,580→22,580; EE 14,000→14,000; Solar 7,740→7,740 TWh; CI 132,540→132,540; P 69,940→69,940; EE% 58,330→58,333 | 0,00333 %-Pkt. | 0,00571 % | PASS |
| ES | 2026-07 | G 24,880→24,880; V 23,280→23,280; EE 13,890→13,890; Solar 8,260→8,260 TWh; CI 152,450→152,450; P 104,790→104,790; EE% 55,830→55,828 | 0,00203 %-Pkt. | 0,00363 % | PASS |
| NO | 2025 | G 160,840→160,840; V 138,040→138,040; EE 159,230→159,230; Wasser 144,780→144,780 TWh; CI 28,060→28,060; P 44,842→44,842; EE% 99,000→98,999 | 0,00099 %-Pkt. | 0,00100 % | PASS |
| NO | 2025-01 | G 16,850→16,850; V 14,260→14,260; EE 16,720→16,720; Wasser 15,270→15,270 TWh; CI 26,410→26,410; P 47,870→47,870; EE% 99,230→99,228 | 0,00151 %-Pkt. | 0,00153 % | PASS |
| NO | 2025-07 | G 11,060→11,060; V 8,850→8,850; EE 10,990→10,990; Wasser 10,510→10,510 TWh; CI 27,120→27,120; P 38,410→38,410; EE% 99,370→99,367 | 0,00291 %-Pkt. | 0,00293 % | PASS |
| NO | 2026-07 | G 10,040→10,040; V 9,160→9,160; EE 9,900→9,900; Wasser 9,040→9,040 TWh; CI 29,780→29,780; P 92,220→92,220; EE% 98,610→98,606 | 0,00442 %-Pkt. | 0,00448 % | PASS |
Ergebnis der durchführbaren Stichprobe: **140/140 Einzelprüfungen PASS**. Die größte absolute Differenz beträgt 0,01869 Prozentpunkte, die größte relative Differenz 0,03631 Prozent; beide entstehen ausschließlich durch die Neuberechnung des Anteils aus auf zwei Dezimalstellen gerundeten TWh-Werten.

Die ursprünglich zusätzlich genannte Türkei war eine irrtümliche Prüfvorgabe. Sie gehört bewusst nicht zum Atlas und ist daher weder Stichprobenland noch fehlender Testfall.

## 6. Nachrechnung der fünf Kreuzkennzahlen

Alle fünf Kennzahlen wurden für das gemeinsame vollständige Kalenderjahr 2024 nachgerechnet. Das BIP ist `gdp_current_billion_eur`, also nominales BIP zu laufenden Preisen. Die EEA-Zeitreihe ist CRT `1.A.1.a` und umfasst öffentliche Strom- **und Wärmeerzeugung**. Das Preisjahresmittel verwendet die Anzahl Kalendertage jedes Monats als Gewicht.

| Land | Kennzahl | Eingänge und Umrechnung | Nachrechnung | Atlas | Abweichung |
|---|---|---|---:|---:|---:|
| DE | Erzeugung je BIP | 495,99 TWh / 4.328,97 Mrd. EUR | 0,114574599 kWh/EUR | 0,114574599 | 0 |
| DE | Verbrauch je BIP | 522,26 TWh / 4.328,97 Mrd. EUR | 0,120643017 kWh/EUR | 0,120643017 | 0 |
| DE | Strom-/Wärmeemissionen je BIP | 155,25507142 Mt / 4.328,97 Mrd. EUR × 1.000 | 35,864205901 t/Mio. EUR | 35,864205901 | 0 |
| DE | Endkunde–Großhandel | (165,4 + 114,7 + 114,7 − 77,798634) EUR/MWh × 0,1 | 31,700136612 ct/kWh | 31,700136612 | 0 |
| DE | Handelsdurchsatz | (81,658 + 55,389) / 522,26 TWh × 100 | 26,241144258 % | 26,241144258 | 0 |
| FR | Erzeugung je BIP | 561,94 TWh / 2.935,2362 Mrd. EUR | 0,191446262 kWh/EUR | 0,191446262 | 0 |
| FR | Verbrauch je BIP | 471,96 TWh / 2.935,2362 Mrd. EUR | 0,160791149 kWh/EUR | 0,160791149 | 0 |
| FR | Strom-/Wärmeemissionen je BIP | 21,32117123 Mt / 2.935,2362 Mrd. EUR × 1.000 | 7,263868996 t/Mio. EUR | 7,263868996 | 0 |
| FR | Endkunde–Großhandel | (152,3 + 69,8 + 66,5 − 57,978060) EUR/MWh × 0,1 | 23,062193989 ct/kWh | 23,062193989 | 0 |
| FR | Handelsdurchsatz | (15,130539 + 105,106682) / 471,96 TWh × 100 | 25,476146495 % | 25,476146495 | 0 |
| ES | Erzeugung je BIP | 280,94 TWh / 1.594,33 Mrd. EUR | 0,176211951 kWh/EUR | 0,176211951 | 0 |
| ES | Verbrauch je BIP | 270,71 TWh / 1.594,33 Mrd. EUR | 0,169795463 kWh/EUR | 0,169795463 | 0 |
| ES | Strom-/Wärmeemissionen je BIP | 26,30448026 Mt / 1.594,33 Mrd. EUR × 1.000 | 16,498767670 t/Mio. EUR | 16,498767670 | 0 |
| ES | Endkunde–Großhandel | (110,8 + 70,1 + 57,4 − 63,049126) EUR/MWh × 0,1 | 17,525087432 ct/kWh | 17,525087432 | 0 |
| ES | Handelsdurchsatz | (14,354137 + 24,581131) / 270,71 TWh × 100 | 14,382648591 % | 14,382648591 | 0 |

Zähler und Nenner stammen in allen 15 Rechnungen aus demselben Kalenderjahr. UK 2024 besitzt kein nominales BIP; die drei BIP-basierten Laufzeitwerte bleiben deshalb `null`. Im Kandidaten gibt es weder ein BIP noch einen Nachfrage-/Verbrauchsnenner mit Wert null. Der geprüfte Laufzeitpfad gibt bei Nenner `0` oder fehlendem Eingang ausdrücklich `None` zurück; es wird kein Nullwert ergänzt.

## 7. Bestehende Berichte und CLI

Die vorhandenen Dateien wurden nicht überschrieben.

| Artefakt | Prüfung | Ergebnis |
|---|---|---|
| `COVERAGE.generated.md` | SHA-256 vorhandene gegen frische Read-only-Ausgabe | identisch: `DE65159043A161EF3EE045A5CD83DFF93502F3A4CD2546B0E97306286A3BBE20` |
| `SUMMARY.generated.json` | SHA-256 vorhandene gegen frische Read-only-Ausgabe | **nicht identisch**; vorhanden 113.527 Byte / `A2FC1ABF...`, frisch 138.491 Byte / `6FDBFE40...` |
| `VALIDATION.generated.md` | Inhalt und Erzeugungsvertrag | klar als historischer Energy-Charts-Bericht markiert; wird nicht neu erzeugt |
| CLI `report` | Hilfe gegen tatsächliche Ausgabe | Hilfe nennt Coverage, Summary und Validation; tatsächlich entstehen nur Coverage und Summary |

Der historische Energy-Charts-Bericht erscheint nicht als aktuelle Ember-Validierung; seine Warnkennzeichnung ist eindeutig. Die Berichtskette ist trotzdem nicht freigabefähig, weil die vorhandene Summary veraltet ist und der CLI-Vertrag nicht mit der Ausgabe übereinstimmt. K4 hat weder die Berichte ersetzt noch den CLI-Code geändert.

## 8. JRC-Einordnung und Eigentümerentscheidung

### 8.1 JRC Hydro-power database

Die [offizielle JRC-Datensatzseite](https://data.jrc.ec.europa.eu/dataset/52b00441-d3e0-44e0-8281-fda86a63546d) nennt ausdrücklich **CC BY 4.0**, Zugriff ohne Einschränkung, Änderungsdatum 25. Oktober 2023 und unbekannte Aktualisierungsfrequenz. Öffentliche Anzeige und Weitergabe sind damit bei korrekter Attribution grundsätzlich gedeckt.

Der Bestand beschreibt sich als Sammlung grundlegender Informationen zu europäischen Wasserkraftwerken und ist kein Vollständigkeitsnachweis. Im Atlas ist er korrekt mit `source_inventory_incomplete` markiert:

- Anlagenleistung: 27/31 Länder
- Pumpleistung: 19/31 Länder
- direkt berichtete Reservoirenergie: 21/31 Länder

Die Reservoirenergie ist eine direkt berichtete Größe des unvollständigen Anlageninventars. Sie darf nicht als vollständige nationale Reservoirenergie und nicht als Pumpspeicherenergie ausgegeben werden.

### 8.2 European Energy Storage Inventory

Die [offizielle Projektseite](https://ses.jrc.ec.europa.eu/storage-inventory) erklärt, dass der Bestand hauptsächlich auf öffentlichen Daten **und Daten von Wood Mackenzie** beruht. Sie weist außerdem darauf hin, dass ein Teil der MWh-Kapazitäten geschätzt ist. Die [offizielle JRC-Ankündigung](https://joint-research-centre.ec.europa.eu/jrc-news-and-updates/new-tool-maps-europes-real-time-sustainable-energy-storage-data-2025-03-20_en) beschreibt eine nahezu echtzeitfähige Projektübersicht und Downloadmöglichkeiten, aber keine eindeutige Lizenz für die Weitergabe des gesamten Datenbestands. Der [allgemeine Rechtsvermerk der Kommission](https://commission.europa.eu/legal-notice_en) erlaubt CC-BY-Nutzung nur für EU-eigene Inhalte, soweit nichts anderes angegeben ist, und verlangt bei Drittwerken gegebenenfalls eine gesonderte Rechteklärung.

Damit ist öffentliche Sichtbarkeit oder Downloadbarkeit nicht gleichbedeutend mit einer eindeutigen Erlaubnis, die aggregierten Wood-Mackenzie-/Drittanbieterwerte in einem eigenen öffentlichen Beta-Datensatz weiterzugeben. Dies ist keine Rechtsberatung; ohne ausdrückliche Klärung darf keine rechtliche Sicherheit behauptet werden.

Stichtage und Qualität im Kandidaten:

| Teilbestand | Stichtag | Beobachtet | Geschätzt/abgeleitet | Coverage |
|---|---|---|---|---:|
| Batterie, Projektinventar | 2026-08-12 | Leistung 27 Länder; Energie 20 Länder | Energie 7 Länder geschätzt; Dauer daraus abgeleitet | Laufzeit nach Quellenkombination 28/31 |
| Pumpspeicher, Projektinventar | 2026-08-12 | Leistung 23 Länder; Energie 9 Länder | Energie 14 Länder geschätzt; Dauer daraus abgeleitet | 23/31 |
| kombinierter manueller Export | 2026-08-11 | Leistung/Energie als quellenberichtet einschließlich Schätzungen | Dauer berechnet | 30/31 Raw, nicht eigene Katalogkennzahl |
| Hydro-Anlageninventar | 2023-10-25 | berichtete Anlagenwerte | keine Ergänzung fehlender Reservoirenergie | 19–27/31 je Metrik |

Die offizielle Kommunikation bezeichnet das Storage Inventory als nahezu echtzeitfähig beziehungsweise kontinuierlich weiterentwickelt; eine feste formale Aktualisierungsfrequenz oder versionierte Releasefolge ist nicht angegeben. Der Hydro-Datensatz nennt die Frequenz ausdrücklich als unbekannt.

Die Trennung im Laufzeitkatalog ist technisch vorhanden:

- Batterie: `battery_power_gw`, `battery_energy_gwh`, `battery_duration_hours`
- Pumpspeicher: `pumped_storage_power_gw`, `pumped_storage_energy_gwh`, `pumped_storage_duration_hours`
- allgemeine/berichtete Wasserkraft-Reservoirenergie: `hydro_reservoir_energy_gwh`

**JRC-Entscheidung:** Die CC-BY-4.0-Werte der JRC Hydro-power database bleiben mit Attribution und deutlichem Unvollständigkeitshinweis enthalten. Der Projekteigentümer akzeptiert außerdem die vorläufige nichtkommerzielle Beta-Nutzung aggregierter Werte aus dem European Energy Storage Inventory bei klarer Attribution sowie Schätzungs- und Unvollständigkeitshinweisen. Die oben dokumentierte Rechteunsicherheit bleibt als bewusst akzeptiertes Restrisiko bestehen und wird nicht als rechtlich geklärt dargestellt.

## 9. Bekannte Datenlücken und offene Abweichungen

1. CH, IE, IT und MK fehlen bei den Ember-Kernwerten für Juli 2026; weitere Technologien haben länderspezifisch geringere Monatsabdeckung.
2. 2025-Preise sind für CH, ME und MK unvollständig; der Jahreswert bleibt fehlend.
3. UK hat kein nominales BIP und keinen BEV-Bestand; CH und UK fehlen bei mehreren Eurostat-Zusatzreihen.
4. EEA CRT 1.A.1.a endet 2024 und fehlt für ME, MK, RS und UK. Die Kennzahl umfasst öffentliche Wärme und ist keine reine Stromemission.
5. Installierte Leistungen enden 2024 und fehlen für CH und UK. 2025 wird nicht künstlich befüllt.
6. Negative Ember-Residualkategorien 2025 werden nachvollziehbar als fehlend ausgegeben; sie sind keine echten Nullwerte.
7. Der beobachtete CO₂-Intensitätswert `0,0` für Montenegro 2017-05 ist fachlich auffällig und sollte bei der nächsten kontrollierten Quellenaktualisierung erneut gegen Ember geprüft werden; er wurde nicht verändert.
8. JRC-Projektinventare sind lückenhaft, enthalten Schätzungen und haben für den Storage-Inventory-Bestand keine eindeutig belegte Weitergabelizenz; die vorläufige nichtkommerzielle Beta-Nutzung ist eine bewusste Produktentscheidung.
9. Pumpspeicherdauern bis 865,61 Stunden und kombinierte Speicherdauern bis 855,38 Stunden entstehen aus berichteter Energie dividiert durch Leistung. Sie sind als äquivalente Dauer des unvollständigen Projektbestands zu verstehen, nicht als netzverfügbare Vollzyklen oder gesicherte Betriebsdauer.
10. Die vorhandene `SUMMARY.generated.json` ist gegenüber einer frischen Ausgabe veraltet; die CLI-Hilfe überschätzt den tatsächlichen Reportumfang.

Ungeklärte numerische Abweichungen oberhalb der Rundungstoleranz wurden in den durchführbaren Ember-Stichproben und Kreuznachrechnungen nicht gefunden.

## 10. Freigabebedingungen

Vor dem finalen Datengate sind folgende Arbeiten erforderlich:

1. K4 aktualisiert alle vorgesehenen Datenpfade einmal kontrolliert auf einer gesicherten Kandidatenkopie.
2. K4 wiederholt Integritäts-, Coverage-, Ember-Stichproben- und Kreuzkennzahlenprüfung gegen den neuen Kandidaten.
3. Coverage, Summary und dieser Validierungsbericht werden neu erzeugt und an den finalen Datenbankhash gebunden.
4. K2 beziehungsweise der zuständige Implementierungsauftrag gleicht anschließend die CLI-Hilfe mit den tatsächlich erzeugten Reports ab, ohne die geprüften Daten fachlich zu verändern.
5. K1 bestätigt den neuen exakten Datenbankhash als Beta-Kandidat.

Bis zur Erfüllung dieser Bedingungen lautet das Datengate **REFRESH REQUIRED**. Türkei und JRC-Risikoentscheidung sind keine offenen Gates mehr.
