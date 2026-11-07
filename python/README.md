# Python data side

Job: fetch → clean → write `../Data/dashboard_data.json` matching `../Data/SCHEMA.md`.

```
python/
├── build_dashboard.py   # entry point: calls each fetcher, assembles the JSON
├── config.py            # URLs, thresholds, manual numbers (trees, waste, carbon budget)
├── cache.py             # download-once helper so you don't hammer APIs
└── fetchers/
    ├── noaa.py          # CO2 / CH4 / N2O   ← start here
    ├── nasa.py          # temperature anomaly
    ├── owid.py          # top emitters
    └── markets.py       # yfinance ETFs
```

Every fetcher has the same shape: **return a dict/list that matches part of the schema, or `None` if it failed.** `build_dashboard.py` stitches them together, so one broken source never kills the whole file.

## Pointers
- **pandas `read_csv` does most of the work.** NOAA files have `#` comment lines → `comment="#"`. GISTEMP has a title line → `skiprows=1`. NASA uses `***` for missing values → `na_values="***"`.
- **OWID's CSV includes regions** ("World", "Asia", "High-income countries") alongside countries. Filter to rows with a real 3-letter `iso_code` before ranking, or "World" will be your #1 emitter.
- **Per-capita rankings are dominated by tiny petro-states** (Qatar, etc.). That's real, but consider a population cutoff (e.g. > 1M people) so the list is meaningful.
- **yfinance is an unofficial scraper of Yahoo.** It breaks and rate-limits sometimes. Wrap it in try/except and fall back to the cached result.
- Use `json.dump(data, f, indent=2, ensure_ascii=False)` so `°C` doesn't come out as `°C`.
- Write to a temp file then rename it over the real one, so C# never reads a half-written file.
- Run `python -m fetchers.noaa` style tests: give each fetcher an `if __name__ == "__main__":` block that prints its output.
