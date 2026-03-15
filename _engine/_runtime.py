from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_pycache() -> None:
    """Redirect Python bytecode cache to a single project-level directory."""
    if sys.dont_write_bytecode:
        return

    root = Path(__file__).resolve().parent.parent
    pycache_prefix = Path(os.environ.get("PYTHONPYCACHEPREFIX", root / ".pycache"))
    pycache_prefix.mkdir(parents=True, exist_ok=True)

    os.environ["PYTHONPYCACHEPREFIX"] = str(pycache_prefix)
    sys.pycache_prefix = str(pycache_prefix)
