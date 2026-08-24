from pipeline.sources import is_mm_flood


def test_matches_metro_manila_flood_zips_any_spelling():
    assert is_mm_flood("Flood/25yr/MetroManila.zip")
    assert is_mm_flood("Flood/100yr/Metro Manila.zip")
    assert is_mm_flood("flood/5yr/metro_manila.zip")


def test_rejects_other_provinces_and_hazards():
    assert not is_mm_flood("Flood/25yr/Quezon.zip")      # Quezon PROVINCE, not QC
    assert not is_mm_flood("Flood/5yr/Rizal.zip")
    assert not is_mm_flood("Landslide/MetroManila.zip")
    assert not is_mm_flood("StormSurge/ssa4/MetroManila.zip")
