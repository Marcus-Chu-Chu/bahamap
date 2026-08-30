import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from pipeline import hazards

SQ = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
SQ2 = Polygon([(20, 0), (30, 0), (30, 10), (20, 10)])


def _gdf(levels, col="Var", geoms=None):
    return gpd.GeoDataFrame({col: levels},
                            geometry=geoms or [SQ] * len(levels),
                            crs="EPSG:32651")


def test_detect_level_col_finds_var():
    assert hazards.detect_level_col(_gdf([1.0])) == "Var"


def test_detect_level_col_raises_with_columns_listed():
    bad = _gdf([1.0], col="mystery")
    with pytest.raises(ValueError, match="mystery"):
        hazards.detect_level_col(bad)


def test_normalize_casts_levels_to_int_and_keeps_only_level_geometry():
    out = hazards.normalize(_gdf([1.0, 2.0, 3.0]))
    assert list(out.columns) == ["level", "geometry"]
    assert sorted(out["level"].tolist()) == [1, 2, 3]
    assert str(out.crs) == "EPSG:32651"


def test_normalize_repairs_invalid_geometry():
    bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])  # self-intersecting
    out = hazards.normalize(_gdf([2.0], geoms=[bowtie]))
    assert out.geometry.is_valid.all()


def test_dissolve_medhigh_drops_low_and_returns_single_row():
    gdf = hazards.normalize(_gdf([1.0, 2.0, 3.0], geoms=[SQ, SQ, SQ2]))
    out = hazards.dissolve_medhigh(gdf)
    assert len(out) == 1
    assert out.geometry.iloc[0].area == pytest.approx(200.0)  # SQ + SQ2, not Low
