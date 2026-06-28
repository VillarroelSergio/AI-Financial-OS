def test_economic_data_module_deleted():
    """economic_data module must not be importable."""
    try:
        import app.modules.economic_data  # noqa: F401
        assert False, "economic_data should not be importable"
    except ModuleNotFoundError:
        pass


def test_market_data_module_deleted():
    """investments.market_data module must not be importable."""
    try:
        import app.modules.investments.market_data  # noqa: F401
        assert False, "investments.market_data should not be importable"
    except ModuleNotFoundError:
        pass


def test_main_imports_cleanly():
    """main.py must import without errors after legacy removal."""
    import app.main  # noqa: F401
