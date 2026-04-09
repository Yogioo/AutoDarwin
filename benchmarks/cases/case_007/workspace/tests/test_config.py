from pathlib import Path


def test_example_kept_for_reference():
    text = Path("config.example.yaml").read_text(encoding="utf-8")
    assert "timeout: 10" in text
