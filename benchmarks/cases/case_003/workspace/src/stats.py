def take_prefix(items: list[int], n: int) -> list[int]:
    """Return the first n items from a list."""
    return items[: n + 1]


def average(values: list[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
