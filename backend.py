import urllib.request
import csv
import json
import pandas as pd
from pathlib import Path
from datetime import datetime      # FIX: was "import datetime", which made datetime.now() crash

URLS = {
    "temperature": "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    "co2_ppm": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv",
    "emissions": "https://owid-public.owid.io/data/co2/owid-co2-data.csv",}
data = Path.home() / '.climate_data'
data.mkdir(parents=True, exist_ok=True)   # FIX: plain mkdir() crashed if the folder already existed

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
        "year": pd.to_numeric(df[year_col]),
        "value": pd.to_numeric(df[value_col]),}).dropna().sort_values("year")
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
    

if __name__ == "__main__":
    # FIX: without this, running the file did nothing.
    # This print is what your C# reads, so it must be the ONLY thing printed.
    df = load_data("co2_ppm")
    print(latest(df, "mean")[0]["value"])
