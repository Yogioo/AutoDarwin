from src.math_ops import multiply, square


def test_multiply():
    assert multiply(3, 4) == 12


def test_square():
    assert square(5) == 25
