"""Entry point: run every fetcher, assemble the JSON contract, write it atomically.

Run from the python/ folder:  python build_dashboard.py
"""
import json
import os
from datetime import datetime, timezone

from config import OUTPUT_FILE, MANUAL


def safe(fn, *args, **kwargs):
    """Call a fetcher; on any error print it and return None so the build continues."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:  # broad on purpose: one bad source must not kill the file
        print(f"[warn] {fn.__module__}.{fn.__name__} failed: {e}")
        return None


def build() -> dict:
    data = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "thresholds": [],      # TODO: from config (1.5 °C, 2 °C, carbon budget)
        "indicators": [],
        "timeseries": {},
        "top_emitters": {"total": [], "per_capita": []},
        "green_investment": {"etfs": [], "official_spending": []},
        "cleanup": MANUAL,
        "disasters": [],
    }

    # TODO: call each fetcher through safe(...) and slot results into `data`, e.g.
    # from fetchers import noaa
    # co2 = safe(noaa.fetch_co2)
    # if co2:
    #     indicator, series = co2
    #     data["indicators"].append(indicator)
    #     data["timeseries"]["co2_ppm"] = series

    return data


def write_atomic(data: dict) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, OUTPUT_FILE)  # atomic: C# never sees a half-written file


if __name__ == "__main__":
    write_atomic(build())
    print(f"Wrote {OUTPUT_FILE}")
