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
