"""Central config. Put URLs and hand-entered numbers here, not scattered in fetchers.

Verify every URL in a browser before relying on it.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "Data" / "dashboard_data.json"
CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_MAX_AGE_HOURS = 24

URLS = {
    "noaa_co2_monthly": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv",
    "noaa_ch4_monthly": "https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_mm_gl.csv",
    "noaa_n2o_monthly": "https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_mm_gl.csv",
    "nasa_gistemp_global": "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    "owid_co2": "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
}

CLEAN_ENERGY_ETFS = ["ICLN", "TAN", "QCLN"]

# TODO: look up the latest published figure + its base year and cite it.
CARBON_BUDGET_1_5C = {
    "gtco2": None,
    "from_year": None,
    "source": "TODO",
}

# Hand-entered: these sources have no API. Always fill as_of + source.
MANUAL = {
    "trees_planted": {"value": None, "unit": "trees", "as_of": None, "source": None},
    "waste_removed": {"value": None, "unit": "lbs", "as_of": None, "source": None},
}
