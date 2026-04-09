from src.region import RegionResolver


def bootstrap() -> str:
    resolver = RegionResolver("ap-south-1")
    return resolver.resolve(None)


if __name__ == "__main__":
    print(bootstrap())
