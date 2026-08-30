import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

from pipeline import scoring

CRS = "EPSG:32651"
UNIT = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])          # 100m square
HALF = Polygon([(0, 0), (50, 0), (50, 100), (0, 100)])            # covers left half
FAR = Polygon([(900, 900), (950, 900), (950, 950), (900, 950)])


def _bgy():
    return gpd.GeoDataFrame({"pcode": ["p1", "p2"]},
                            geometry=[UNIT, FAR], crs=CRS)


def _hazard(geom=HALF):
    return gpd.GeoDataFrame({"geometry": [geom]}, crs=CRS)


def test_pct_area_in_half_covered():
    pct = scoring.pct_area_in(_bgy(), _hazard())
    assert pct["p1"] == pytest.approx(0.5)
    assert pct["p2"] == pytest.approx(0.0)


def test_pct_area_capped_at_one_even_with_overlapping_hazard():
    hz = gpd.GeoDataFrame({"geometry": [UNIT, UNIT]}, crs=CRS)  # duplicated cover
    pct = scoring.pct_area_in(_bgy(), hz)
    assert pct["p1"] == pytest.approx(1.0)


def test_points_in_per_bgy():
    pts = gpd.GeoDataFrame({"kind": ["school", "school", "hospital"]},
                           geometry=[Point(10, 10), Point(910, 910), Point(2000, 2000)],
                           crs=CRS)
    counts = scoring.points_in_per_bgy(pts, _bgy())
    assert counts["p1"] == 1 and counts["p2"] == 1


def test_count_points_in_hazard():
    pts = gpd.GeoDataFrame(geometry=[Point(10, 10), Point(80, 80)], crs=CRS)
    assert scoring.count_points_in(pts, _hazard()) == 1


def test_minmax_handles_constant_series():
    s = pd.Series([5.0, 5.0, 5.0])
    assert scoring.minmax(s).tolist() == [0.0, 0.0, 0.0]


def test_exposure_score_weighting():
    df = pd.DataFrame({
        "est_pop_exposed": [0, 100],
        "pct_area_mh": [0.0, 1.0],
        "infra_exposed": [0, 10],
    })
    s = scoring.exposure_score(df, {"pop": 0.5, "area": 0.3, "infra": 0.2})
    assert s.tolist() == [0.0, 100.0]


def test_sensitivity_returns_high_corr_for_stable_ranking():
    df = pd.DataFrame({
        "est_pop_exposed": range(50),
        "pct_area_mh": [x / 50 for x in range(50)],
        "infra_exposed": range(50),
    })
    out = scoring.sensitivity(df, {"pop": 0.5, "area": 0.3, "infra": 0.2})
    assert (out["spearman_rank_corr"] > 0.99).all()
    assert len(out) == 6  # ±10pp on each of three weights
