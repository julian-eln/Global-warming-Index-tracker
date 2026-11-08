import urllib.request
import csv
import json
import pandas as pd
from pathlib import Path
from datetime import datetime      # FIX: was "import datetime", which made datetime.now() crash

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
impact_data = data / 'impact.csv'

def load_data(name):
    file = data / f"{name}.csv"
    age = datetime.now().timestamp() - file.stat().st_mtime if file.exists() else None
    if age is None or age > 86400:
        # FIX: save the raw file exactly as downloaded. The old version parsed it first,
        # which fails on NOAA's "#" comment lines and NASA's title line.
        urllib.request.urlretrieve(URLS[name], file)

    # Each source needs different options to read correctly.
    # FIX: every source now gets a branch. Before, "emissions" crashed when cached.
    if name == "temperature":
        return pd.read_csv(file, skiprows=1, na_values="***")   # skip title line; NASA uses *** for missing
    if name == "co2_ppm":
        return pd.read_csv(file, comment="#")   # FIX: was skiprows=56, which breaks if NOAA edits its header
    return pd.read_csv(file)


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
    trees =  0
    waste = 0.0
    if impact_data.exists():
        with open(impact_data, 'r') as data:
            for row in csv.DictReader(data):
                trees += int(row.get('trees', 0))
                waste += float(row.get('waste', 0))
    waste_plant_ratio = {"trees planted": trees, "waste picked up": round(waste,3)} 
    return waste_plant_ratio


def get_world_data(name):
    df = load_data(name)
    if "Entity" in df.columns:
        df = df[df["Entity"].isin(["World", "Global"])]
    if df.empty:
        print(f"No global data found for {name}")
    year_col = "Year" if "Year" in df.columns else "year"
    if year_col not in df.columns:
       print('Year column not found')
    df = df.copy()
    df[year_col] = pd.to_numeric(df[year_col])  
    return df.dropna(subset=[year_col]).sort_values(year_col)


def get_dataset_values(name):
    df = get_world_data(name)
    year_col = "Year" if "Year" in df.columns else "year"
    columns = [c for c in df.columns if c not in ["Entity", "Code", "Year", "year"]]
    result = {}
    for column in columns:
        series = df[[year_col, column]].copy()
        series[column] = pd.to_numeric(series[column])
        series = series.dropna()
        if series.empty:
            continue
        result[column] = {
            "latest_year": int(series.iloc[-1][year_col]),
            "latest_value": float(series.iloc[-1][column]),
            "history": [{"year": int(row[year_col]),"value": float(row[column]) } for _, row in series.iterrows()]}
    if not result:
        print(f"No numeric values found in {name}")
    return result


def green_energy_investment():
    return {"metric": "Renewable-energy investment by technology",
            "data": get_dataset_values("green_investment"),"source": URLS["green_investment"]}


def top_countries(metric="total", count=20):
    df = load_data("emissions")
    column = "co2" if metric == "total" else "co2_per_capita"
    df = df[df["iso_code"].str.len() == 3]
    df = df[df["iso_code"].str.startswith("OWID")]
    df = df.sort_values("year").drop_duplicates(subset="country", keep="last")
    df = df.dropna(subset=[column])
    df = df.nlargest(count, column)

    return [{"country": row["country"],"year": int(row["year"]),"value": float(row[column])}for _, row in df.iterrows()]




if __name__ == "__main__":
    import sys

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
    elif what in COLUMNS:
        # "python backend.py temperature" -> latest value only
        # This print is what your C# reads, so it must be the ONLY thing printed.
        value_col, year_col = COLUMNS[what]
        print(latest(load_data(what), value_col, year_col)[0]["value"])
    else:
        sys.exit(f"Unknown source: {what}")
