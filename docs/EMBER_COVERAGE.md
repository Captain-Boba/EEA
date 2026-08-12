# Ember coverage notes

Status: local imports on 10 August 2026 before the catalog migration to 31 countries.

- Monthly and yearly generation, demand and carbon-intensity observations are stored separately in `period_observation`.
- The local history is intentionally limited to 2015 and later in the UI.
- Albania is not part of the Atlas catalog. Vendor raw files may still contain it, but normalized Atlas observations do not.
- The yearly demand endpoint may fail. Annual demand is derived only when all twelve monthly Ember values exist.
- National wholesale prices come from Ember's European Wholesale Electricity Price Data monthly CSV.
- Historical annual prices remain empty when fewer than twelve completed months are available.
- Current months are provisional and the current year is reported as YTD.
- API keys are redacted before request metadata is cached.

Ember remains the sole source for electricity-system and price metrics. Eurostat is used only for annual socioeconomic denominators. Battery-Charts and JRC storage data are exposed as separately dated stock values; none of these auxiliary sources silently fills Ember gaps.
