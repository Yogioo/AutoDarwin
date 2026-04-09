from src.stats import average, take_prefix


def test_take_prefix_exact_count():
    assert take_prefix([1, 2, 3, 4], 2) == [1, 2]


def test_take_prefix_zero():
    assert take_prefix([1, 2, 3], 0) == []


def test_average_basic():
    assert average([2, 4, 6]) == 4
