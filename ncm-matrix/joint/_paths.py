"""Import roots for the official Matrix tree and the cloned NCM, resolved once."""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
MATRIX_ROOT = Path(os.environ.get("MATRIX_ROOT", str(EXPERIMENT.parent)))
NCM_ROOT = EXPERIMENT / "ncm"

for root in (MATRIX_ROOT, NCM_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
