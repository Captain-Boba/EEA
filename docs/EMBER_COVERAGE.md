# Ember coverage notes

Status: current 31-country Atlas architecture as documented on 22 August 2026.

- Monthly and yearly generation, demand and carbon-intensity observations are stored separately in `period_observation`.
- The local history is intentionally limited to 2015 and later in the UI.
- Albania is not part of the Atlas catalog. Vendor raw files may still contain it, but normalized Atlas observations do not.
- The yearly demand endpoint may fail. Annual demand is derived only when all twelve monthly Ember values exist.
- National wholesale prices come from Ember's European Wholesale Electricity Price Data monthly CSV.
- Historical annual prices remain empty when fewer than twelve completed months are available.
- Current months are provisional and the current year is reported as YTD.
- API keys are redacted before request metadata is cached.

Ember remains the sole source for electricity-system metrics and national wholesale prices. Eurostat supplies annual socioeconomic denominators as well as installed capacity, retail-price components, gross electricity trade, and battery-electric passenger-car values. Battery-Charts and JRC storage data are exposed as separately dated stock values; the JRC hydro inventory and EEA emissions inventory remain distinct datasets. None of these auxiliary sources silently fills Ember gaps.

The map may select an earlier available Eurostat year for installed-capacity metrics and displays that effective year explicitly. This is a presentation fallback only: it neither creates observations nor fills gaps in Ember or any other dataset.
