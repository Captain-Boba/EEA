# Time-series comparison

The comparison view uses a native SVG chart with no charting library or CDN.
It requests one metric for one to ten Atlas countries through:

```text
/api/timeseries?metric=renewable_share_pct&countries=DE,FR,UK&start=2015-01&end=2026-08
```

Monthly availability in the central metric catalog takes precedence; metrics
without monthly availability use yearly points. Snapshot-only metrics are not
time series. Missing periods remain JSON `null`, empty CSV fields, and gaps in
the SVG paths. They are never interpolated or converted to zero.

For each period the Atlas average is the arithmetic mean of every available
country in the complete Atlas catalog. Missing countries are excluded and
reported zero values are retained. The response and UI intentionally do not
show a coverage count.

The URL stores the selected countries, metric, and range. Invalid URL values
are rejected rather than silently applied. CSV, SVG, and PNG exports are
created locally in the browser.

## Local flag assets

The 31 SVG flag files under `web/assets/flags` come from
[`lipis/flag-icons`](https://github.com/lipis/flag-icons), version 7.4.0. The
project is MIT licensed; its license text is stored alongside the SVG files as
`LICENSE.flag-icons.txt`. The Atlas makes no runtime flag or diagram requests.
