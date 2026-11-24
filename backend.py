import urllib.request
import csv
import io
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
import pandas as pd
import yfinance as yf

IMPACT_SOURCES = {
    # (url, regex whose first group is the number)
    "trees": ("https://teamtrees.org",
              r'id="totalTrees"[^>]*data-count="(\d+)"|data-count="(\d+)"[^>]*id="totalTrees"'),
        "waste": ("https://s3.eu-west-1.amazonaws.com/data.theoceancleanup.com/systems-dashboard/realtime-data-ocean.json",
              r'"debris_extracted_total":\s*(\d+)'),
}

URLS = {
    "temperature": "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    "co2_ppm": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv",
    "emissions": "https://owid-public.owid.io/data/co2/owid-co2-data.csv",
    "green_investment": "https://ourworldindata.org/grapher/investment-in-renewable-energy-by-technology.csv",
    "ev_adoption": "https://ourworldindata.org/grapher/electric-car-sales-share.csv",
    "ev_sales": "https://ourworldindata.org/grapher/electric-car-sales.csv",
    "renewable_electricity": "https://ourworldindata.org/grapher/electricity-mix.csv",
}

ETF_HOLDINGS_SOURCES = {
    "ICLN": (
        "https://www.ishares.com/us/products/239738/"
        "ishares-global-clean-energy-etf/1467271812596.ajax"
        "?fileType=csv&fileName=ICLN_holdings&dataType=fund"
    ),
    "TAN": "https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0?audienceType=Investor&action=download&ticker=TAN",
    "PBW": "https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0?audienceType=Investor&action=download&ticker=PBW",
    "QCLN": "https://www.ftportfolios.com/retail/etf/ETFholdings.aspx?Ticker=QCLN",
}

EXCHANGE_SUFFIX_MAP = {
    "NASDAQ": "", "New York Stock Exchange Inc.": "", "NYSE Arca": "",
    "NYSE": "", "Nasdaq": "", "New York Stock Exchange": "",
    "B3 S.A. - Brasil, Bolsa, Balcao": ".SA",
    "Bolsa De Madrid": ".MC", "Madrid Stock Exchange": ".MC",
    "Nasdaq Omx Copenhagen A/S": ".CO", "Copenhagen Stock Exchange": ".CO",
    "Tokyo Stock Exchange": ".T",
    "Shanghai Stock Exchange": ".SS", "Shenzhen Stock Exchange": ".SZ",
    "Hong Kong Exchanges And Clearing Ltd": ".HK", "Hong Kong Stock Exchange": ".HK",
    "Korea Exchange (Stock Market)": ".KS", "Korea Exchange (Kosdaq)": ".KQ",
    "National Stock Exchange Of India": ".NS", "Bse Ltd": ".BO",
    "Toronto Stock Exchange": ".TO",
    "London Stock Exchange": ".L",
    "Xetra": ".DE", "Deutsche Boerse AG": ".DE",
    "Euronext Paris": ".PA", "Euronext Amsterdam": ".AS", "Euronext Lisbon": ".LS",
    "Borsa Italiana": ".MI", "SIX Swiss Exchange": ".SW",
    "Nasdaq Stockholm Ab": ".ST", "Oslo Bors Asa": ".OL",
    "Wiener Boerse Ag": ".VI", "Tel Aviv Stock Exchange": ".TA",
    "Taiwan Stock Exchange": ".TW", "GreTai Securities Market": ".TWO",
    "Asx - All Markets": ".AX", "New Zealand Exchange Ltd": ".NZ",
    "Bolsa De Comercio De Santiago": ".SN", "Istanbul Stock Exchange": ".IS",
}

NON_PURE_PLAY_BLACKLIST = {
    "NEE", "IBE.MC", "EDP.LS", "EDPR.LS", "SSE.L", "ERG.MI", "ENG.MC",
    "600900.SS", "601985.SS", "003816.SZ",
    "TSLA", "RIVN", "LCID", "NIO", "XPEV", "LI",
    "ON", "MPWR", "AEIS", "ALGM", "OLED", "POWI", "NVTS", "WOLF", "STM", "IFX.DE",
    "ALB", "SQM", "MP", "LAC", "AYI", "ITRI", "ENS", "QBTS",
}

PURE_PLAY_INDUSTRIES = {"Solar", "Utilities - Renewable"}

PURE_PLAY_WHITELIST = {
    "FSLR", "ENPH", "RUN", "NXT", "ARRY", "SHLS", "CSIQ", "JKS", "DQ", "SEDG",
    "MAXN", "NOVA", "SPWR", "AMRC", "STEM", "FLNC", "NRGV", "EOSE", "ENVX",
    "BE", "PLUG", "FCEL", "BLDP", "NEL.OL", "ITM.L", "CWR.L",
    "VWS.CO", "NDX1.DE", "NKT.CO", "SGRE.MC", "ORSTED.CO",
    "BEP", "BEPC", "CWEN", "CWEN-A", "ORA", "ENLT", "RNW", "HASI", "XIFR",
    "AESI", "REX", "GEVO", "AMTX", "CLNE", "OPAL", "MONT.PA",
}

data = Path.home() / '.climate_data'
data.mkdir(parents=True, exist_ok=True)
impact_data = data / 'impact.csv'
stock_cache = data / 'pure_play_stock.json'


def _fetch_text(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def scrape_count(url, pattern):
    text = _fetch_text(url, timeout=10)
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"Couldn't find the counter on {url}; the site may have changed")
    return int(next(g for g in m.groups() if g))


def load_data(name):
    file = data / f"{name}.csv"
    age = datetime.now().timestamp() - file.stat().st_mtime if file.exists() else None
    if age is None or age > 86400:
        req = urllib.request.Request(URLS[name], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            file.write_bytes(r.read())
    if name == "temperature":
        return pd.read_csv(file, skiprows=1, na_values="***")
    if name == "co2_ppm":
        return pd.read_csv(file, comment="#")
    return pd.read_csv(file)


def history(df, value_col, year_col="year"):
    if value_col not in df or year_col not in df:
        return []
    clean = pd.DataFrame({
        "year": pd.to_numeric(df[year_col], errors="coerce"),
        "value": pd.to_numeric(df[value_col], errors="coerce"),
    }).dropna().sort_values("year")
    return [{"year": int(y), "value": round(float(v), 3)} for y, v in clean.itertuples(index=False, name=None)]


def latest(df, value_col, year_col="year"):
    """Just the most recent year's value."""
    return history(df, value_col, year_col)[-1:]


def impact():
    saved = {"trees": 0, "waste": 0.0}
    if impact_data.exists():
        with open(impact_data, 'r', newline='') as f:
            for row in csv.DictReader(f):
                saved["trees"] = int(float(row.get('trees') or 0))
                saved["waste"] = float(row.get('waste') or 0)

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

    return {"trees planted": trees, "waste picked up": round(waste, 3)}


def get_world_data(name):
    df = load_data(name)
    if "Entity" in df.columns:
        df = df[df["Entity"].isin(["World", "Global"])]
    if df.empty:
        print(f"No global data found for {name}", file=sys.stderr)
    year_col = "Year" if "Year" in df.columns else "year"
    if year_col not in df.columns:
        raise ValueError(f"Year column not found in {name}")
    df = df.copy()
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    return df.dropna(subset=[year_col]).sort_values(year_col)


def get_dataset_values(name):
    df = get_world_data(name)
    year_col = "Year" if "Year" in df.columns else "year"
    columns = [c for c in df.columns if c not in ["Entity", "Code", "Year", "year"]]
    result = {}
    for column in columns:
        series = df[[year_col, column]].copy()
        series[column] = pd.to_numeric(series[column], errors="coerce")
        series = series.dropna()
        if series.empty:
            continue
        result[column] = {
            "latest_year": int(series.iloc[-1][year_col]),
            "latest_value": float(series.iloc[-1][column]),
            "history": [{"year": int(row[year_col]), "value": float(row[column])} for _, row in series.iterrows()],
        }
    if not result:
        print(f"No numeric values found in {name}", file=sys.stderr)
    return result


def green_energy_investment():
    return {
        "metric": "Renewable-energy investment by technology",
        "data": get_dataset_values("green_investment"),
        "source": URLS["green_investment"],
    }


def ev_sales():
    return {
        "metric": "Electric cars sold",
        "data": get_dataset_values("ev_sales"),
        "source": URLS["ev_sales"],
    }


def top_countries(metric="total", count=20):
    df = load_data("emissions")
    column = "co2" if metric == "total" else "co2_per_capita"
    df = df[df["iso_code"].str.len() == 3]
    df = df[~df["iso_code"].str.startswith("OWID", na=False)]
    df = df.dropna(subset=[column])
    df = df.sort_values("year").drop_duplicates(subset="country", keep="last")
    df = df.nlargest(count, column)
    return [{"country": row["country"], "year": int(row["year"]), "value": float(row[column])} for _, row in df.iterrows()]


def fetch_clean_energy_money() -> dict:
    """
    Aggregates holdings across ICLN, TAN, QCLN, and PBW, filters to pure-play
    clean energy companies, and sums two numbers over the last 4 quarters (USD):
      - total_invested_usd: capital RAISED (equity + debt issued)
      - total_capex_usd:    capital SPENT on building things (capital expenditure)
    Both come from the same cash-flow table, so one pass collects both.
    Cached daily to ~/.climate_data/pure_play_stock.json.
    """
    age = datetime.now().timestamp() - stock_cache.stat().st_mtime if stock_cache.exists() else None
    if age is not None and age <= 86400:
        try:
            cached = json.loads(stock_cache.read_text(encoding="utf-8"))
            # Old caches only have the raised number; refetch so capex gets filled in
            if cached.get("total_invested_usd", 0) > 0 and "total_capex_usd" in cached:
                return cached
        except Exception:
            pass

    raw_tickers = set()

    # 1. ICLN (iShares CSV)
    try:
        lines = _fetch_text(ETF_HOLDINGS_SOURCES["ICLN"]).splitlines()
        idx = next(i for i, l in enumerate(lines) if l.startswith("Ticker,Name,"))
        df_icln = pd.read_csv(io.StringIO("\n".join(lines[idx:])))
        for _, row in df_icln[df_icln["Asset Class"] == "Equity"].iterrows():
            t = str(row["Ticker"]).strip().replace(" ", "-")
            suffix = EXCHANGE_SUFFIX_MAP.get(str(row["Exchange"]).strip(), "")
            if t and t != "-":
                if suffix in {".SS", ".SZ"} and t.isdigit():
                    t = t.zfill(6)
                elif suffix == ".HK" and t.isdigit():
                    t = t.zfill(4)
                raw_tickers.add(f"{t}{suffix}")
    except Exception as e:
        print(f"ICLN holdings fetch warning: {e}", file=sys.stderr)

    # 2. TAN & PBW (Invesco CSVs)
    for etf in ("TAN", "PBW"):
        try:
            df_inv = pd.read_csv(io.StringIO(_fetch_text(ETF_HOLDINGS_SOURCES[etf])))
            ticker_col = next((c for c in df_inv.columns if "Ticker" in c), None)
            if ticker_col:
                for val in df_inv[ticker_col].dropna():
                    t = str(val).strip().replace(" ", "-")
                    if t and t != "-" and not t.startswith("Cash"):
                        raw_tickers.add(t)
        except Exception as e:
            print(f"{etf} holdings fetch warning: {e}", file=sys.stderr)

    # 3. QCLN (First Trust HTML holdings table)
    try:
        tables = pd.read_html(io.StringIO(_fetch_text(ETF_HOLDINGS_SOURCES["QCLN"])))
        for tbl in tables:
            if "Identifier" in tbl.columns:
                for val in tbl["Identifier"].dropna():
                    t = str(val).strip().replace(" ", "-")
                    if t and t != "-":
                        raw_tickers.add(t)
                break
    except Exception as e:
        print(f"QCLN holdings fetch warning: {e}", file=sys.stderr)

    candidate_tickers = (raw_tickers | PURE_PLAY_WHITELIST) - NON_PURE_PLAY_BLACKLIST

    # Pre-fetch FX rates to USD
    fx_rates = {"USD": 1.0}
    for curr in ["EUR", "DKK", "CAD", "GBP", "CNY", "HKD", "JPY", "KRW", "INR", "BRL", "NOK", "SEK", "CHF", "AUD", "ILS", "TWD"]:
        try:
            rate = yf.Ticker(f"{curr}USD=X").fast_info.last_price
            if rate:
                fx_rates[curr] = float(rate)
        except Exception:
            pass

    def first_row_sum(cf, names) -> float:
        """Sum of the first row in `names` that exists in the cash-flow table, else 0."""
        for k in names:
            if k in cf.index:
                return float(cf.loc[k].fillna(0).sum())
        return 0.0

    def process_company(symbol: str) -> tuple:
        """Returns (capital raised, capex) in USD for one company, or (0, 0) if skipped."""
        try:
            t = yf.Ticker(symbol)
            info = t.info or {}
            industry = info.get("industry", "")

            if symbol not in PURE_PLAY_WHITELIST and industry not in PURE_PLAY_INDUSTRIES:
                return (0.0, 0.0)

            q_cf = t.quarterly_cashflow
            if q_cf is None or q_cf.empty:
                q_cf = (
                    t.cashflow.iloc[:, :1]
                    if (t.cashflow is not None and not t.cashflow.empty)
                    else None
                )
            if q_cf is None or q_cf.empty:
                return (0.0, 0.0)

            recent_4q = q_cf.iloc[:, :4]

            equity_in = first_row_sum(recent_4q, ("Issuance Of Capital Stock", "Common Stock Issuance"))
            debt_in = first_row_sum(recent_4q, ("Issuance Of Debt", "Long Term Debt Issuance"))
            raised = max(equity_in + debt_in, 0.0)

            # Capex is stored as a NEGATIVE number (cash going out), so flip it with abs()
            capex = abs(first_row_sum(recent_4q, ("Capital Expenditure",)))

            if raised == 0.0 and capex == 0.0:
                return (0.0, 0.0)

            curr = info.get("financialCurrency") or t.fast_info.currency or "USD"
            fx = fx_rates.get(curr)
            if fx is None:
                rate = yf.Ticker(f"{curr}USD=X").fast_info.last_price
                fx = float(rate) if rate else 1.0

            return (raised * fx, capex * fx)
        except Exception as e:
            print(f"Skipping {symbol}: {e}", file=sys.stderr)
            return (0.0, 0.0)

    total_raised = 0.0
    total_capex = 0.0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_company, sym) for sym in candidate_tickers]
        for future in as_completed(futures):
            raised, capex = future.result()
            total_raised += raised
            total_capex += capex

    result = {
        "updated_at": datetime.now().isoformat(),
        "total_invested_usd": round(total_raised, 2),
        "total_capex_usd": round(total_capex, 2),
    }

    if total_raised > 0 or total_capex > 0:
        stock_cache.write_text(json.dumps(result), encoding="utf-8")
    elif stock_cache.exists():
        # Every network call failed: fall back to the last saved numbers
        return json.loads(stock_cache.read_text(encoding="utf-8"))

    return result


if __name__ == "__main__":
    COLUMNS = {"co2_ppm": ("mean", "year"), "temperature": ("J-D", "Year")}
    what = sys.argv[1] if len(sys.argv) > 1 else "co2_ppm"

    if what == "history":
        source = sys.argv[2]
        value_col, year_col = COLUMNS[source]
        for point in history(load_data(source), value_col, year_col):
            print(f"{point['year']},{point['value']}")
    elif what == "trees":
        print(impact()["trees planted"])
    elif what == "waste":
        print(impact()["waste picked up"])
    elif what == "money_total":
        values = green_energy_investment()["data"].values()
        print(round(sum(v["latest_value"] for v in values)))
    elif what == "Stock":
        # Capital RAISED by pure-play clean-energy companies, last 4 quarters, in $ billions
        print(round(fetch_clean_energy_money().get("total_invested_usd", 0)))
    elif what == "capex":
        # Capital SPENT (capex) by the same companies, last 4 quarters, in $ billions
        print(fetch_clean_energy_money().get("total_capex_usd", 0))
    elif what == "money_bars":
        techs = green_energy_investment()["data"]
        rows = sorted(techs.items(), key=lambda kv: kv[1]["latest_value"], reverse=True)
        for name, info in rows:
            print(f"{name}|{info['latest_value'] / 1e9:.1f}")
    elif what == "evsales":
        for name, info in ev_sales()["data"].items():
            for point in info["history"]:
                print(f"{point['year']}|{point['value']:.0f}")
    elif what == "evadoption":
        col = "Share of new cars that are electric"
        df = get_world_data("ev_adoption").dropna(subset=[col])
        latest_row = df.iloc[-1]
        share = float(latest_row[col])
        print(f"Electric ({int(latest_row['Year'])})|{share}")
        print(f"Not electric|{100 - share}")
    elif what == "world":
        if len(sys.argv) < 3 or sys.argv[2] not in URLS:
            sys.exit(f"Usage: python backend.py world <{'|'.join(URLS)}>")
        df = get_world_data(sys.argv[2]).drop(columns=["Entity", "Code"], errors="ignore")
        print(df.to_csv(index=False), end="")
    elif what in COLUMNS:
        value_col, year_col = COLUMNS[what]
        print(latest(load_data(what), value_col, year_col)[0]["value"])
    elif what == "top":
        metric = sys.argv[2] if len(sys.argv) > 2 else "total"
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        for c in top_countries(metric, count):
            print(f"{c['country']}|{c['value']}")
    else:
        sys.exit(f"Unknown source: {what}")
