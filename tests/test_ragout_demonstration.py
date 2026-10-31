"""test_ragout_demonstration.py

Unit test for the end-to-end Ragout de Champiñones demonstration.
"""

from examples.ragout_demonstration import run_ragout_demo


def test_ragout_demonstration_executes_cleanly() -> None:
    """Verifies that the 5-stage cooking domain demonstration runs without errors."""
    run_ragout_demo()
