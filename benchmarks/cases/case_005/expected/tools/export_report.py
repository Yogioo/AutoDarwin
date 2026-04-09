import json
from pathlib import Path


def export_report(source_path: str, output_path: str) -> Path:
    source = Path(source_path)
    payload = json.loads(source.read_text(encoding="utf-8"))

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"title={payload['title']}",
        f"count={len(payload['items'])}",
    ]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def main() -> None:
    import sys

    if len(sys.argv) != 3:
        raise SystemExit("usage: export_report.py <source.json> <output.txt>")

    export_report(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
