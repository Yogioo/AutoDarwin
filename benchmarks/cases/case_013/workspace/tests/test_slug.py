from src.slug import slugify


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_multi_spaces():
    assert slugify("hello   auto   darwin") == "hello-auto-darwin"
