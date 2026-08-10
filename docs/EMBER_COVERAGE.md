# Ember coverage notes

Status: local imports on 10 August 2026 for the 32-country Atlas catalog.

- Monthly and yearly generation, demand and carbon-intensity observations are stored separately in `period_observation`.
- The local history is intentionally limited to 2015 and later in the UI.
- Albania has regular monthly coverage gaps; missing values remain empty.
- The yearly demand endpoint may fail. Annual demand is derived only when all twelve monthly Ember values exist.
- National wholesale prices come from Ember's European Wholesale Electricity Price Data monthly CSV.
- Historical annual prices remain empty when fewer than twelve completed months are available.
- Current months are provisional and the current year is reported as YTD.
- API keys are redacted before request metadata is cached.

Ember is the sole application data source. No fallback source is used to fill gaps.
