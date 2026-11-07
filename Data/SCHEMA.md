# `dashboard_data.json` contract

Python writes this file; C# reads it. Change it only together.

Rules that save you pain:
- **Every number carries its unit, date and source.** Climate data is mostly monthly or yearly, so the UI must show "as of" dates or it will look like it's lying.
- **Field names are `snake_case`.** In C#, map them with `JsonNamingPolicy.SnakeCaseLower` (System.Text.Json, .NET 8+) instead of renaming every property.
- **Missing data = `null`, never `0`.** A zero CO₂ reading is a bug the UI can't detect; a null it can show as "unavailable".
- Bump `schema_version` when you change the shape.

## Top level

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | Start at 1. |
| `generated_at` | ISO-8601 string (UTC) | When Python ran. Show "last updated" in the UI. |
| `thresholds` | array of Threshold | The "doomsday" numbers for the banner. |
| `indicators` | array of Indicator | Current values (CO₂ ppm, CH₄, N₂O, temp anomaly...). |
| `timeseries` | object of name → array of Point | For charts. |
| `top_emitters` | object with `total` and `per_capita` arrays of Country | |
| `green_investment` | object | ETF proxy + any official spending numbers. |
| `cleanup` | object | Trees planted, waste removed (manual/scraped — see DATA_SOURCES). |
| `disasters` | array of Event | Stretch goal; empty array until built. |

## Shapes

**Threshold** — `{ id, label, value, unit, compare_to, source, note }`
`compare_to` is the `id` of an indicator, so the UI can show "1.3 °C of 1.5 °C" as a progress bar.

**Indicator** — `{ id, label, value, unit, as_of, source, source_url }`

**Point** — `{ date, value }` (`date` as `YYYY-MM` or `YYYY`)

**Country** — `{ iso_code, name, value, unit, year }`

See `dashboard_data.json` for a filled example. **Its values are placeholders, not real data** — they're marked `"source": "SAMPLE"` so nobody demos them by accident.
