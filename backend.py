import csv
import json
import pandas as pd
from pathlib import Path
import datetime

URLS = {
    "temperature": "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    "co2_ppm": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv",
    "emissions": "https://owid-public.owid.io/data/co2/owid-co2-data.csv",}
data = Path.home() / '.climate_data'
data.mkdir()

def load_data(name):
    file = data / f"{name}.csv"
    age = datetime.now().timestamp() - file.stat().st_mtime if file.exists() else None
    if age is None or age > 86400:
        df = pd.read_csv(URLS[name])
        df.to_csv(file, index=False)
    if name == "temperature":
        df = pd.read_csv(file)
    if name == "co2_ppm":
        df = pd.read_csv(file, skiprows=56)
    return df

def history(df, value_col, year_col="year"):
    if value_col not in df or year_col not in df:
        return []
    clean = pd.DataFrame({
        "year": pd.to_numeric(df[year_col]),
        "value": pd.to_numeric(df[value_col]),}).dropna().sort_values("year")
    sets = [{"year": int(y), "value": round(float(v), 3)} for y, v in clean.itertuples(index=False, name=None)]
    return sets
    
def latest(df, value_col, year_col="year"):
    if value_col not in df or year_col not in df:
            return []
    clean = pd.DataFrame({
        "year": pd.to_numeric(df[year_col]),
        "value": pd.to_numeric(df[value_col])}).dropna().sort_values("year")
    if clean.empty:
        return []
    latest_row = clean.iloc[-1]
    return [{"year": int(latest_row[year_col]), "value": round(float(latest_row[value_col]), 3)}]
