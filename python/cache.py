"""Download-once helper. Every fetcher should get raw files through here."""
import time
from pathlib import Path

import requests

from config import CACHE_DIR, CACHE_MAX_AGE_HOURS


def get_cached(name: str, url: str) -> Path:
    """Return a local path to the file at `url`, downloading only if the cache is stale.

    TODO (partner):
      1. Build the path: CACHE_DIR / name  (make CACHE_DIR if missing)
      2. If it exists and is younger than CACHE_MAX_AGE_HOURS, return it.
      3. Otherwise requests.get(url, timeout=30), raise_for_status(), write bytes, return path.
      4. If the download FAILS but an old cached copy exists, return the old copy
         (stale data beats no data during a demo). Print a warning.
    """
    raise NotImplementedError
