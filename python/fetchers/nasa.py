"""NASA GISTEMP global temperature anomaly."""


def fetch_temp_anomaly():
    """Return (indicator_dict, yearly_timeseries) or None.

    TODO:
      - read_csv(path, skiprows=1, na_values="***")
      - Column 'J-D' is the Jan–Dec annual mean; the current year is incomplete (NaN).
      - Baseline is 1951-1980, NOT pre-industrial. Before comparing to 1.5 °C,
        either apply a documented offset or switch datasets — and say which in `source`.
    """
    raise NotImplementedError


if __name__ == "__main__":
    print(fetch_temp_anomaly())
