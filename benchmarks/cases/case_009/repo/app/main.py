from config.settings import SERVICE_REGION


def boot() -> str:
    return f"service region={SERVICE_REGION}"


if __name__ == "__main__":
    print(boot())
