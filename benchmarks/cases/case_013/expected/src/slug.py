def slugify(text: str) -> str:
    normalized = text.strip().lower()
    return "-".join(normalized.split())
