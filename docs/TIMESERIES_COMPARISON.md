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

Each country response also contains `baseline_values`. Yearly metrics use the
2015 annual value. Monthly metrics use the matching calendar month in 2015,
even when the visible range starts later. The live ranking reports the relative
change `(current - baseline) / baseline * 100`. Missing and reported-zero
baselines produce no percentage instead of a division or fallback value.

The standard chart and fullscreen chart use the same `15:8` plot aspect ratio,
the same internal SVG geometry and equally prominent ranking typography. The
ranking scrolls internally when necessary. Native fullscreen includes the
complete control bar, chart and ranking; the selected countries, metric, date
range and pinned period remain unchanged when entering or leaving fullscreen.
The browser's Escape action exits fullscreen.

Country colors are derived from prominent non-neutral colors in the bundled
flag SVGs. If a flag color is too dark or conflicts with an already assigned
line, the chart chooses a high-contrast fallback. Hover selects only the
nearest period for the guide and live ranking; it no longer locks onto or
dims individual country lines.

## Local flag assets

The 31 SVG flag files under `web/assets/flags` come from
[`lipis/flag-icons`](https://github.com/lipis/flag-icons), version 7.4.0. The
project is MIT licensed; its license text is stored alongside the SVG files as
`LICENSE.flag-icons.txt`. The Atlas makes no runtime flag or diagram requests.
