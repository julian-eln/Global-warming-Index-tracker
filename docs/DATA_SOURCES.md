# Data sources — what's actually usable

Several sources on the original wish list don't have a public API. Plan around that now, not at hour 20.

> URLs below were written from memory and could not be tested from the setup environment. **Open each one in a browser before writing code against it.**

## Tier 1 — reliable, free, no key (build the MVP on these)

| Data | Source | How to get it | Update frequency |
|---|---|---|---|
| CO₂ (Mauna Loa, monthly) | NOAA GML | CSV: `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv` (skip `#` comment lines) | Monthly (daily file also exists) |
| CH₄, N₂O (global monthly) | NOAA GML | CSV: `.../trends/ch4/ch4_mm_gl.csv`, `.../trends/n2o/n2o_mm_gl.csv` | Monthly, lags a few months |
| Global temperature anomaly | NASA GISTEMP v4 | CSV: `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv` (first line is a title — skip it) | Monthly |
| Country CO₂: total, per capita, other GHGs, history | Our World in Data | CSV on GitHub: `https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv` (codebook in same repo) | Yearly |
| Clean-energy ETF price/volume | `yfinance` (Python) | `yf.Ticker("ICLN").history(period="1mo")` | Live-ish |

**Use OWID instead of Worldometer.** Worldometer has no API (you'd be scraping, which is fragile and against their terms), and its CO₂ country figures largely come from the same underlying datasets OWID publishes cleanly.

Note on "current global temperature": what agencies publish is an **anomaly** (difference from a baseline), not an absolute temperature. GISTEMP's baseline is 1951–1980, which is *not* the pre-industrial baseline the 1.5 °C target uses — comparing them directly understates warming. Either use a dataset that reports vs. 1850–1900, or add a documented offset and show it in the UI.

## Tier 2 — usable, but slower or messier

| Data | Source | Catch |
|---|---|---|
| Renewable capacity / generation by country | IRENA (IRENASTAT, PxWeb API) | Annual data; PxWeb query format takes some fiddling. OWID's energy dataset (`owid/energy-data` on GitHub) is an easier substitute. |
| Environmental protection expenditure, green finance | OECD Data Explorer (SDMX API) | SDMX is verbose; find the dataset in the Data Explorer UI first, then copy its generated API URL. OECD countries only. |
| Simple climate JSON | global-warming.org API | Convenient JSON wrapper, but a hobby project — fine as a fallback, don't make it your only source. |
| Natural disasters (stretch) | NASA EONET v3, USGS earthquake GeoJSON feeds | Both are good and free. EONET = wildfires, storms, volcanoes; USGS = earthquakes. |

## Tier 3 — no API; enter manually or drop

| Wish-list item | Reality | Recommendation |
|---|---|---|
| Bloomberg green investment | Terminal/enterprise product, paid. | Drop. Use the ETF proxy + a cited annual figure (e.g. BloombergNEF's yearly energy-transition investment number from their public press release) typed into config. |
| Arbor Day / Team Trees totals | No public API. | Hand-enter the number with an `as_of` date in a config file. |
| "Lbs of waste picked up" (Team Seas etc.) | No public API. | Same: manual entry with date + source. |
| Government climate spending | No unified source; every government reports differently. | Use OECD for a few countries, or cut. |

## Honest caveats to show in the UI
- **ETF price is not investment.** Price moves reflect sentiment, interest rates and stock performance, not money flowing into new solar farms. Label it "market sentiment proxy", not "green investment".
- Every number needs an "as of" date. Most of this data is months or a year old; that's normal and fine if you say so.

## Caching (do this from day one)
Download each source once, save the raw file to `python/cache/`, and parse from the cache. You'll avoid rate limits, work offline, and — most importantly — **your demo won't die on bad hackathon Wi-Fi.** Commit one known-good `Data/dashboard_data.json` before you present.
