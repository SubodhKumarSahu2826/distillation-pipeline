"""Phase 0 smoke test: the package imports and its config loads. No network, no GPU."""

from pathlib import Path


def test_package_imports():
    import distill

    assert distill.__version__


def test_config_loads():
    from distill.config import CONFIG

    assert isinstance(CONFIG.paths.root, Path)
    # Paths are derived consistently from the repo root.
    assert CONFIG.paths.splits == CONFIG.paths.data / "splits"
    # Pricing knobs default to 0.0 (unset) and are floats for the Phase 6 model.
    assert isinstance(CONFIG.teacher_input_usd_per_mtok, float)


def test_logger_setup():
    from distill.logging import get_logger

    assert get_logger("distill.test").name == "distill.test"
