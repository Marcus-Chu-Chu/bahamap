import pandas as pd

from pipeline import rainfall


def _daily():
    dates = pd.date_range("2000-01-01", "2001-12-31", freq="D")
    mm = pd.Series(1.0, index=range(len(dates)))
    mm.iloc[10] = 120.0   # one extreme day in 2000
    mm.iloc[400] = 60.0   # one heavy day in 2001
    return pd.DataFrame({"date": dates, "mm": mm.values})


def test_annual_metrics():
    out = rainfall.annual_metrics(_daily())
    assert out.loc[2000, "max_daily_mm"] == 120.0
    assert out.loc[2000, "days_ge_100"] == 1
    assert out.loc[2001, "days_ge_50"] == 1
    assert out.loc[2001, "days_ge_100"] == 0


def test_trend_detects_increase():
    annual = pd.DataFrame({"days_ge_50": range(30)}, index=range(1990, 2020))
    t = rainfall.trend(annual, "days_ge_50")
    assert t["slope_per_decade"] == 10.0
    assert t["p_value"] < 0.001
