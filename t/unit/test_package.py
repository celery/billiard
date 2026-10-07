import billiard


def test_has_version():
    assert billiard.__version__
    assert isinstance(billiard.__version__, str)
