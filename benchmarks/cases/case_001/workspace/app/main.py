from app.notes import build_release_note


def render_release(version: str, changes: list[str]) -> str:
    return build_release_note(version, changes)


if __name__ == "__main__":
    print(render_release("1.2.0", ["Improve logging", "Fix parser bug"]))
