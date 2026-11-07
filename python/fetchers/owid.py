"""Our World in Data: country emissions (total + per capita) and world totals."""


def fetch_top_emitters(n: int = 10, min_population: int = 1_000_000):
    """Return {"total": [...], "per_capita": [...]} or None.

    TODO:
      - Columns to look at: country, year, iso_code, population, co2, co2_per_capita
        (check the codebook in the owid/co2-data repo for units — co2 is in MtCO2).
      - Drop rows where iso_code is NaN or starts with "OWID_" (those are regions/aggregates).
      - Use the latest year that has data for most countries, not just max(year).
      - Apply min_population for the per-capita list.
    """
    raise NotImplementedError


def fetch_world_annual_emissions():
    """World row, latest year -> indicator 'co2_emissions_annual' in GtCO2 (divide Mt by 1000)."""
    raise NotImplementedError


if __name__ == "__main__":
    print(fetch_top_emitters())
