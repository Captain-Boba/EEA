# Ember 2025 source comparison

Status: local probe import on 2026-08-10 for all ten pilot countries.

## Probe result

- All ten countries have 12 Ember months with generation, demand and carbon intensity.
- All ten annual Ember summaries are complete.
- The Ember yearly demand endpoint returned HTTP 500 for every tested country. The import reports these failures and exits non-zero. Annual demand is therefore transparently summed from exactly 12 Ember monthly values.
- The Ember cache contains no occurrence of the local API key. All stored Ember request URLs contain `api_key=REDACTED`.
- In the source-specific Ember API view, price, gross imports, gross exports and net trade remain unavailable.

## Annual values

Values are TWh except renewable share (percentage points) and carbon intensity (gCO2/kWh).

| Country | Source | Generation | Demand | Renewables | Renewable share | Wind | Solar | Nuclear | Fossil | Carbon intensity |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DE | Energy-Charts | 425.13 | 465.82 | 263.97 | 62.09 | 131.17 | 70.12 | 0.00 | 150.29 | unavailable |
| DE | Ember | 499.89 | 488.73 | 295.16 | 59.04 | 136.03 | 89.62 | 0.00 | 204.73 | 330.02 |
| FR | Energy-Charts | 533.91 | unavailable | 141.49 | 26.50 | 48.58 | 30.26 | 371.46 | 17.83 | unavailable |
| FR | Ember | 570.14 | 434.63 | 148.72 | 26.08 | 46.46 | 32.01 | 392.07 | 29.35 | 41.45 |
| ES | Energy-Charts | 259.03 | unavailable | 151.12 | 58.34 | 55.57 | 52.52 | 51.91 | 53.69 | unavailable |
| ES | Ember | 287.92 | 243.30 | 160.81 | 55.85 | 58.76 | 62.92 | 54.10 | 73.01 | 153.58 |
| UK | Energy-Charts | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |
| UK | Ember | 292.41 | 307.68 | 152.02 | 51.99 | 85.94 | 19.32 | 36.38 | 104.01 | 217.33 |

## Differences to Energy-Charts

- DE: Ember generation is 74.76 TWh higher, demand 22.91 TWh higher, renewables 31.19 TWh higher and fossil generation 54.44 TWh higher. Ember's renewable share is 3.05 percentage points lower.
- FR: Ember generation is 36.23 TWh higher, renewables 7.23 TWh higher, nuclear 20.61 TWh higher and fossil generation 11.52 TWh higher. The renewable share differs by -0.42 percentage points.
- ES: Ember generation is 28.89 TWh higher, renewables 9.69 TWh higher, solar 10.40 TWh higher and fossil generation 19.32 TWh higher. The renewable share differs by -2.49 percentage points.
- UK: Energy-Charts has no usable 2025 annual generation or demand summary in the current local dataset. Ember supplies generation, demand, mix and carbon intensity for all 12 months and the annual view.

The differences are not treated as errors. Energy-Charts represents operational public-net-generation data, while Ember publishes curated nationally comparable period totals with its own source coverage and technology classifications. Storage and source-specific API views remain separate. The combined UI prefers a coherent Energy-Charts generation/mix group, falls back to a coherent Ember generation/mix group when needed, fills missing consumption and carbon intensity from Ember, and never sums values from the two sources.
