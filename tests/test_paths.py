from pipeline import paths


def test_weights_sum_to_one():
    assert abs(sum(paths.WEIGHTS.values()) - 1.0) < 1e-9


def test_constants_shape():
    assert paths.HEADLINE_RP in paths.RETURN_PERIODS
    assert len(paths.NCR_CITY_TOKENS) == 17
    assert len(paths.RAIN_POINTS) == 4
    assert paths.POP_NCR_2020 == 13_484_462
