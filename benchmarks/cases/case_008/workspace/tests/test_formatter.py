from src.formatter import format_items, format_price


def test_format_price_two_decimals():
    assert format_price(12) == "$12.00"


def test_format_price_rounding():
    assert format_price(3.456) == "$3.46"


def test_format_items():
    assert format_items(["apples", "oranges"]) == "apples, oranges"
