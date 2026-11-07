"""Clean-energy ETFs via yfinance. A market-sentiment proxy, NOT a measure of investment."""
from config import CLEAN_ENERGY_ETFS


def fetch_etfs(tickers=CLEAN_ENERGY_ETFS):
    """Return a list of ETF dicts matching the schema, or None.

    TODO:
      - import yfinance as yf
      - For each ticker: yf.Ticker(t).history(period="5d") -> last Close, Volume
      - .info may have 'totalAssets' (AUM) — it's flaky; treat as optional (None).
      - Wrap each ticker in try/except so one failure doesn't drop the rest.
    """
    raise NotImplementedError


if __name__ == "__main__":
    print(fetch_etfs())
