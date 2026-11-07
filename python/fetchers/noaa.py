"""NOAA GML greenhouse gases. Start here: simplest source, proves the pipeline works."""
import pandas as pd

from cache import get_cached
from config import URLS


def fetch_co2():
    """Return (indicator_dict, timeseries_list) for CO2, or None on failure.

    TODO:
      - path = get_cached("co2_mm_mlo.csv", URLS["noaa_co2_monthly"])
      - df = pd.read_csv(path, comment="#")   # inspect df.columns first!
      - Use the 'average' column (or 'deseasonalized' — decide and label it).
      - Latest row -> indicator {"id": "co2_ppm", "value": ..., "as_of": "YYYY-MM", ...}
      - All rows -> [{"date": "YYYY-MM", "value": ...}, ...]
    """
    raise NotImplementedError


def fetch_ch4():
    """Same pattern as CO2, unit ppb. Global mean file, lags a few months."""
    raise NotImplementedError


def fetch_n2o():
    raise NotImplementedError


if __name__ == "__main__":
    print(fetch_co2())
