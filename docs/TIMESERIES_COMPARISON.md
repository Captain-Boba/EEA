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

The URL stores the selected countries, metric, range, and Y-axis mode. Invalid
URL values are rejected rather than silently applied. CSV, SVG, and PNG exports
are created locally in the browser.

Metric families are selected through a grouped Atlas menu. Within a family,
variants keep the order absolute value, share, and yearly per-capita value when
all three exist. The actual metric catalog remains the source of truth; the
menu does not maintain a second hard-coded availability list.

The Y-axis offers two modes. The full mode starts non-diverging absolute
metrics at zero, shows ordinary shares from 0 to 100%, and keeps diverging
metrics symmetric around zero. The visible-data-range mode uses the observed
minimum and maximum, except that ordinary percentage metrics retain 100% as
their upper bound. The selected mode is included in direct links and local
SVG and PNG output.

Each country response also contains `baseline_values`. The baseline year is the
first year of the requested range. Yearly metrics use that annual value;
monthly metrics use the matching calendar month in that baseline year. The
live ranking reports the relative change
`(current - baseline) / baseline * 100`. Missing and reported-zero baselines
produce no percentage instead of a division or fallback value. A range that
starts in 2015 therefore retains the original same-calendar-month 2015
comparison.

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
dims individual country lines. Pointer movement remains continuous, but ranking
updates are limited to one leading and one trailing update per 120 milliseconds
so dense Max views do not flicker through periods unreadably. A click pins the
selected period immediately. Pending hover updates are cancelled when the
pointer leaves, a period is pinned, or the chart is rebuilt.

The document title follows the active Atlas section and reads `EEA · Zeitvergleich`
in the comparison view. Direct links restore the comparison state without
performing a data import.

## Local flag assets

The 31 SVG flag files under `web/assets/flags` come from
[`lipis/flag-icons`](https://github.com/lipis/flag-icons), version 7.4.0. The
project is MIT licensed; its license text is stored alongside the SVG files as
`LICENSE.flag-icons.txt`. The Atlas makes no runtime flag or diagram requests.
