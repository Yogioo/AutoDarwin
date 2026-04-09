def build_release_note(version: str, changes: list[str]) -> str:
    header = f"Release {version}"
    lines = [header, "=" * len(header), ""]
    lines.extend(f"- {change}" for change in changes)
    return "\n".join(lines)
