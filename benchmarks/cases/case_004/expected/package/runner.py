from package.parser import parse_name


def run(raw: str) -> str:
    return f"Hello, {parse_name(raw)}!"
