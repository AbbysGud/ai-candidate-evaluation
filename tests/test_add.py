from app.hello import add  # pyright: ignore[reportMissingImports]


def test_add():
    assert add(2, 3) == 5
