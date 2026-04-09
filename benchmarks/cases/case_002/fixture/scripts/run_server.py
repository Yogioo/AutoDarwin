from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def main() -> None:
    env = load_env(Path("config/dev.env"))
    port = env.get("PORT", "8000")
    print(f"starting server on :{port}")


if __name__ == "__main__":
    main()
