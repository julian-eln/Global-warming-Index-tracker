# Global Warming Index Tracker

A desktop dashboard that shows where the planet stands on climate, with "doomsday" thresholds (1.5 °C, 2 °C, the remaining carbon budget) pinned at the top so every number has something to compare against.

**Team split**
- **Python (data side):** fetches, cleans and caches data, then writes one JSON file: `Data/dashboard_data.json`.
- **C# (app side):** a desktop UI that reads that JSON and draws it.

```
 NOAA / NASA / OWID / yfinance ...      Python fetchers            C# desktop app
 ─────────────────────────────────►  python/build_dashboard.py ─► Data/dashboard_data.json ─► csharp/ (UI)
```

The JSON file is **the contract** between you two. Agree on its shape first (see `Data/SCHEMA.md`), then you can each work without blocking the other: C# builds against the sample file, Python makes the real data match it.

## Repo layout

| Path | Owner | What it is |
|---|---|---|
| `Data/dashboard_data.json` | both | Sample data in the agreed shape. C# develops against this. |
| `Data/SCHEMA.md` | both | Field-by-field description of the JSON contract. |
| `python/` | partner | Fetchers + the script that builds the JSON. |
| `csharp/` | you | Desktop app. Not generated yet — see `csharp/README.md`. |
| `docs/DATA_SOURCES.md` | both | Which sources actually have usable APIs (several on the wish list don't). |
| `docs/PLAN.md` | both | MVP vs stretch goals, suggested order of work. |

## Quick start

**Python**
```bash
cd python
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python build_dashboard.py          # writes ../Data/dashboard_data.json
```

**C#** — follow `csharp/README.md` to create the project (you'll learn more running the `dotnet new` commands yourself than from generated files).

## Git workflow for two people
- Never commit straight to `main` during the hackathon. Each of you works on a branch (`csharp-ui`, `python-fetchers`) and merges via pull request.
- Because you touch different folders, merge conflicts should be rare. The one shared file is `Data/dashboard_data.json` — if you change its shape, update `Data/SCHEMA.md` in the same commit and tell your partner.
