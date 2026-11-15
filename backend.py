import urllib.request
import csv
import json
import re
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime      # FIX: was "import datetime", which made datetime.now() crash

IMPACT_SOURCES = {
    # (url, regex whose first group is the number)
    "trees": ("https://teamtrees.org",
              r'id="totalTrees"[^>]*data-count="(\d+)"|data-count="(\d+)"[^>]*id="totalTrees"'),
    "waste": ("https://teamseas.org/assets/js/page.js",
              r'set_live_counter\((\d+)\)'),
}

URLS = {
    "temperature": "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    "co2_ppm": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv",
    "emissions": "https://owid-public.owid.io/data/co2/owid-co2-data.csv",
    "green_investment":"https://ourworldindata.org/grapher/investment-in-renewable-energy-by-technology.csv",
    "ev_adoption":"https://ourworldindata.org/grapher/electric-car-sales-share.csv",
    "ev_sales":"https://ourworldindata.org/grapher/electric-car-sales.csv",
    "renewable_electricity":"https://ourworldindata.org/grapher/electricity-mix.csv"}
data = Path.home() / '.climate_data'
data.mkdir(parents=True, exist_ok=True)   # FIX: plain mkdir() crashed if the folder already existed
impact_data = data / 'impact.csv'          # holds the last good live numbers (fallback)

def scrape_count(url, pattern):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        text = r.read().decode("utf-8", errors="ignore")
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"Couldn't find the counter on {url}; the site may have changed")
    return int(next(g for g in m.groups() if g))   # first group that matched


def load_data(name):
    file = data / f"{name}.csv"
    age = datetime.now().timestamp() - file.stat().st_mtime if file.exists() else None
    if age is None or age > 86400:
        req = urllib.request.Request(URLS[name], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            file.write_bytes(r.read())
    # Each source needs different options to read correctly.
    # FIX: every source now gets a branch. Before, "emissions" crashed when cached.
    if name == "temperature":
        return pd.read_csv(file, skiprows=1, na_values="***")   # skip title line; NASA uses *** for missing
    if name == "co2_ppm":
        return pd.read_csv(file, comment="#")   # NOAA's file starts with "#" comment lines
    return pd.read_csv(file)                    # OWID files: header on line 1, works as-is


def history(df, value_col, year_col="year"):
    if value_col not in df or year_col not in df:
        return []
    clean = pd.DataFrame({
        "year": pd.to_numeric(df[year_col], errors="coerce"),
        "value": pd.to_numeric(df[value_col], errors="coerce"),}).dropna().sort_values("year")
    sets = [{"year": int(y), "value": round(float(v), 3)} for y, v in clean.itertuples(index=False, name=None)]
    return sets


def latest(df, value_col, year_col="year"):
    """Just the most recent year's value."""
    # FIX: reuses history() instead of repeating its code. The old version looked up
    # latest_row[value_col] (e.g. "mean"), a column that no longer existed: KeyError.
    return history(df, value_col, year_col)[-1:]


def impact():
    # Last saved numbers, used for whichever live fetch fails
    saved = {"trees": 0, "waste": 0.0}
    if impact_data.exists():
        with open(impact_data, 'r', newline='') as f:
            for row in csv.DictReader(f):
                saved["trees"] = int(float(row.get('trees') or 0))
                saved["waste"] = float(row.get('waste') or 0)

    # FIX: each number is fetched on its own, so one broken site no longer wipes out the other
    def live_or_saved(key):
        try:
            return scrape_count(*IMPACT_SOURCES[key])
        except Exception as e:
            print(f"Live {key} failed, using saved number: {e}", file=sys.stderr)
            return saved[key]

    trees = int(live_or_saved("trees"))
    waste = float(live_or_saved("waste"))

    with open(impact_data, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['trees', 'waste'])
        writer.writerow([trees, waste])

    waste_plant_ratio = {"trees planted": trees, "waste picked up": round(waste,3)}
    return waste_plant_ratio


def get_world_data(name):
    df = load_data(name)
    if "Entity" in df.columns:
        df = df[df["Entity"].isin(["World", "Global"])]
    if df.empty:
        print(f"No global data found for {name}", file=sys.stderr)   # FIX: stderr, so C# output stays clean
    year_col = "Year" if "Year" in df.columns else "year"
    if year_col not in df.columns:
        raise ValueError(f"Year column not found in {name}")         # FIX: was a print, then crashed anyway
    df = df.copy()
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")       # FIX: bad cells become NaN instead of crashing
    return df.dropna(subset=[year_col]).sort_values(year_col)


def get_dataset_values(name):
    df = get_world_data(name)
    year_col = "Year" if "Year" in df.columns else "year"
    columns = [c for c in df.columns if c not in ["Entity", "Code", "Year", "year"]]
    result = {}
    for column in columns:
        series = df[[year_col, column]].copy()
        series[column] = pd.to_numeric(series[column], errors="coerce")   # FIX: same as above
        series = series.dropna()
        if series.empty:
            continue
        result[column] = {
            "latest_year": int(series.iloc[-1][year_col]),
            "latest_value": float(series.iloc[-1][column]),
            "history": [{"year": int(row[year_col]),"value": float(row[column]) } for _, row in series.iterrows()]}
    if not result:
        print(f"No numeric values found in {name}", file=sys.stderr)
    return result


def green_energy_investment():
    return {"metric": "Renewable-energy investment by technology",
            "data": get_dataset_values("green_investment"),"source": URLS["green_investment"]}
def ev_sales():
    return {"metric": "Electric cars sold",
            "data": get_dataset_values("ev_sales"),
            "source": URLS["ev_sales"]}


def top_countries(metric="total", count=20):
    df = load_data("emissions")
    column = "co2" if metric == "total" else "co2_per_capita"
    df = df[df["iso_code"].str.len() == 3]
    df = df[~df["iso_code"].str.startswith("OWID", na=False)]   # real countries only
    df = df.dropna(subset=[column])                              # FIX: drop missing values FIRST...
    df = df.sort_values("year").drop_duplicates(subset="country", keep="last")  # ...then take each country's latest
    df = df.nlargest(count, column)

    return [{"country": row["country"],"year": int(row["year"]),"value": float(row[column])}for _, row in df.iterrows()]


if __name__ == "__main__":
    # Which column holds the value and which holds the year, for each source
    COLUMNS = {"co2_ppm": ("mean", "year"), "temperature": ("J-D", "Year")}

    # The first word after "backend.py" says what C# wants. No word = latest CO2.
    what = sys.argv[1] if len(sys.argv) > 1 else "co2_ppm"

    if what == "history":
        # "python backend.py history co2_ppm" -> one "year,value" line per year (for the chart)
        source = sys.argv[2]
        value_col, year_col = COLUMNS[source]
        for point in history(load_data(source), value_col, year_col):
            print(f"{point['year']},{point['value']}")
    elif what == "trees":
        print(impact()["trees planted"])
    elif what == "waste":
        print(impact()["waste picked up"])
    elif what == "money_total":
        # total renewable investment in the latest year, in billions of USD
        values = green_energy_investment()["data"].values()
        print(round(sum(v["latest_value"] for v in values) / 1e9, 1))
    elif what == "money_bars":
        # One line per technology, biggest first: "Wind Energy|142.7"  ($ billions, latest year)
        techs = green_energy_investment()["data"]
        rows = sorted(techs.items(), key=lambda kv: kv[1]["latest_value"], reverse=True)
        for name, info in rows:
            print(f"{name}|{info['latest_value'] / 1e9:.1f}")
    elif what == "evsales":
        # One line per year: "2025|21200000"
        for name, info in ev_sales()["data"].items():
            for point in info["history"]:
                print(f"{point['year']}|{point['value']:.0f}")
    elif what == "evadoption":
        # Latest World share of new cars that are electric, as two pie slices
        col = "Share of new cars that are electric"
        df = get_world_data("ev_adoption").dropna(subset=[col])
        latest_row = df.iloc[-1]
        share = float(latest_row[col])
        print(f"Electric ({int(latest_row['Year'])})|{share}")
        print(f"Not electric|{100 - share}")
    elif what == "world":
        # "python backend.py world ev_adoption" -> CSV: Year,<col1>,<col2>,...  (for looking at data)
        if len(sys.argv) < 3 or sys.argv[2] not in URLS:
            sys.exit(f"Usage: python backend.py world <{'|'.join(URLS)}>")
        df = get_world_data(sys.argv[2]).drop(columns=["Entity", "Code"], errors="ignore")
        print(df.to_csv(index=False), end="")
    elif what in COLUMNS:
        # "python backend.py temperature" -> latest value only
        # This print is what your C# reads, so it must be the ONLY thing printed.
        value_col, year_col = COLUMNS[what]
        print(latest(load_data(what), value_col, year_col)[0]["value"])
    elif what == "top":
        # "python backend.py top total 20" -> "China|11903.0" ... (largest first)
        metric = sys.argv[2] if len(sys.argv) > 2 else "total"
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        for c in top_countries(metric, count):
            print(f"{c['country']}|{c['value']}")
    else:
        sys.exit(f"Unknown source: {what}")
