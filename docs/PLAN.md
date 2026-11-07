# Plan: MVP first, stretch later

The full feature list is more than two people finish in a hackathon. Build the MVP end-to-end first (real data → JSON → visible in the app), *then* add features. A thin working app beats a wide broken one.

## MVP (must demo)
1. **Doomsday banner** — temperature anomaly vs 1.5 °C / 2 °C as progress bars.
2. **Carbon budget countdown** — remaining 1.5 °C budget minus emissions since its base year, ticking down live in the UI at the current annual rate (budget ÷ seconds-per-year). *This is the most memorable thing you can show — prioritize it.*
3. **Greenhouse gas cards** — CO₂, CH₄, N₂O current values + a CO₂ line chart (the Keeling curve).
4. **Top 10 emitters** — total and per-capita, toggle between them (OWID).

## Stretch (in this order)
5. Clean-energy ETF panel (yfinance), clearly labeled as a sentiment proxy.
6. Renewable share / capacity by country (OWID energy data or IRENA).
7. Trees planted / waste removed (manual config values).
8. Natural disaster feed (EONET + USGS) — honestly a separate app; only if 1–6 are solid.

## Suggested order of work

| Step | Python (partner) | C# (you) |
|---|---|---|
| 1 | Agree on `Data/SCHEMA.md` together (30 min, don't skip) | same |
| 2 | NOAA CO₂ fetcher → writes real `co2_ppm` | Create project, load `dashboard_data.json` into C# model classes, print values to a basic window |
| 3 | NASA temp + CH₄/N₂O | Doomsday banner + indicator cards |
| 4 | OWID top emitters | Charts (LiveCharts2 or ScottPlot) |
| 5 | Carbon budget calc | Live countdown with a `DispatcherTimer` |
| 6 | Caching + error handling | "Last updated" label, null handling, Refresh button that runs the Python script |
| 7 | Stretch items | Polish |

## Integration checkpoint
Aim to have step 2 working on **both** sides early — real NOAA data showing in the C# window. Once that pipe works once, everything else is just more of the same.
