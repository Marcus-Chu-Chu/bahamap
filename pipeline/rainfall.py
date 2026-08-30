"""Annual rainfall metrics and linear trend from daily precipitation."""
import pandas as pd
from scipy.stats import linregress


def annual_metrics(daily: pd.DataFrame) -> pd.DataFrame:
    d = daily.copy()
    d["year"] = pd.to_datetime(d["date"]).dt.year
    g = d.groupby("year")["mm"]
    return pd.DataFrame({
        "max_daily_mm": g.max(),
        "days_ge_50": g.apply(lambda s: int((s >= 50).sum())),
        "days_ge_100": g.apply(lambda s: int((s >= 100).sum())),
        "total_mm": g.sum().round(1),
    })


def trend(annual: pd.DataFrame, col: str) -> dict:
    r = linregress(annual.index.values.astype(float), annual[col].values.astype(float))
    return {"slope_per_decade": round(r.slope * 10, 3), "p_value": round(r.pvalue, 5)}
