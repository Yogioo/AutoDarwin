class RegionResolver:
    def __init__(self, default_region: str = "us-east-1") -> None:
        self.default_region = default_region

    def resolve(self, value: str | None) -> str:
        if value:
            return value
        return self.default_region
