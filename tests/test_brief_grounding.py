from pipeline import grounding

ROW = {"pcode": "1300000001", "name": "Malanday", "city": "Marikina",
       "population": 21_456, "rank_ncr": 3, "pct_area_mh_5": 0.62,
       "pct_area_mh_25": 0.87, "pct_area_mh_100": 0.95,
       "est_pop_exposed_25": 18_667, "schools_exposed": 4, "health_exposed": 2}


def test_build_payload_rounds_and_renames():
    p = grounding.build_payload(ROW, n_bgys=1700)
    assert p["pct_area_25yr"] == 87 and p["pct_area_5yr"] == 62
    assert p["est_pop_exposed"] == 18_667 and p["n_bgys_ncr"] == 1700


def test_extract_numbers_skips_years_and_rp_labels():
    text = ("In 2020 the barangay had 21,456 residents; the 25-year map shows "
            "87% of its land at risk, ranking 3rd... wait, rank is below 10 so "
            "excluded; 100-year zones cover 95%.")
    nums = grounding.extract_numbers(text)
    assert 21456.0 in nums and 87.0 in nums and 95.0 in nums
    assert 2020.0 not in nums and 25.0 not in nums and 100.0 not in nums


def test_validate_passes_grounded_text():
    p = grounding.build_payload(ROW, 1700)
    ok = "Around 18,667 of 21,456 residents live where 87% of land floods."
    assert grounding.validate(ok, p) == []


def test_validate_catches_hallucinated_number():
    p = grounding.build_payload(ROW, 1700)
    bad = "About 99,999 residents are at risk."
    assert grounding.validate(bad, p) == [99999.0]


def test_template_brief_is_grounded_in_both_languages():
    p = grounding.build_payload(ROW, 1700)
    t = grounding.template_brief(p)
    assert grounding.validate(t["en"], p) == []
    assert grounding.validate(t["tl"], p) == []
    assert "Malanday" in t["en"] and "Malanday" in t["tl"]
