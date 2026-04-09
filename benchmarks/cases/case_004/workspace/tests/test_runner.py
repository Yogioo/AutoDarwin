from package.runner import run


def test_run_trims_space():
    assert run("  auto darwin ") == "Hello, Auto Darwin!"
