import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from pipeline import joins

SQ = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])


def _bgy():
    return gpd.GeoDataFrame(
        {"pc": ["1300000001", "1300000002", "0400000001"],
         "nm": ["A", "B", "C"], "ct": ["X", "X", "Y"]},
        geometry=[SQ, SQ, SQ], crs="EPSG:32651")


def test_filter_ncr_keeps_only_prefixed(monkeypatch):
    monkeypatch.setattr("pipeline.joins.NCR_PCODE_PREFIXES", ("13",))
    out = joins.filter_ncr(_bgy(), "pc")
    assert out["pc"].tolist() == ["1300000001", "1300000002"]


def test_join_population_reports_orphans():
    census = pd.DataFrame({"pc": ["1300000001"], "pop": [500]})
    joined, qa = joins.join_population(_bgy().iloc[:2], census, "pc", "pc", "pop")
    assert qa["n_bgy"] == 2 and qa["n_matched"] == 1
    assert qa["orphan_bgys"] == ["1300000002"]
    assert qa["pop_total"] == 500
    assert joined.loc[joined["pc"] == "1300000002", "population"].iloc[0] == 0


def test_join_strips_whitespace_and_types():
    census = pd.DataFrame({"pc": [" 1300000001 "], "pop": ["500"]})
    _, qa = joins.join_population(_bgy().iloc[:1], census, "pc", "pc", "pop")
    assert qa["n_matched"] == 1 and qa["pop_total"] == 500


def test_join_carries_extra_columns():
    census = pd.DataFrame({"pc": ["1300000001"], "pop": [500],
                           "Mun_City": ["Marikina"]})
    joined, _ = joins.join_population(_bgy().iloc[:1], census, "pc", "pc", "pop",
                                      carry_cols=("Mun_City",))
    assert joined["Mun_City"].iloc[0] == "Marikina"


def test_reconcile():
    assert joins.reconcile(13_400_000, 13_484_462)
    assert not joins.reconcile(12_000_000, 13_484_462)
