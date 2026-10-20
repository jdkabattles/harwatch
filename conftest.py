"""Pytest bootstrap for the src layout.

The package lives under src/harwatch/ and the tests import it as
``harwatch.*``. Without this, a plain ``pytest`` run from the repo root
cannot collect the suite (ModuleNotFoundError: No module named 'harwatch').
Inserting src/ here makes the repo's own suite runnable standalone.
"""
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
