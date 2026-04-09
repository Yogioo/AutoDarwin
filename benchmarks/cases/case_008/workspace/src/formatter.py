def format_price(value: float) -> str:
    return f"${value:.1f}"


def format_items(items: list[str]) -> str:
    return ", ".join(items)
