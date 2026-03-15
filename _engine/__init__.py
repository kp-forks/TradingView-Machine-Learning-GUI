"""HyperView — CLI-driven TradingView strategy backtester and hyper-optimizer."""

import os as _os
import sys as _sys
from pathlib import Path as _Path

# Redirect __pycache__ folders into a single .pycache/ directory at the project root.
_root = _Path(__file__).resolve().parent.parent
_os.environ.setdefault("PYTHONPYCACHEPREFIX", str(_root / ".pycache"))
_sys.pycache_prefix = _os.environ["PYTHONPYCACHEPREFIX"]

from .backtest import TradingViewLikeBacktester
from .downloader import TradingViewDataClient
from strategy import get_strategy, list_strategies

__all__ = [
    "TradingViewDataClient",
    "TradingViewLikeBacktester",
    "get_strategy",
    "list_strategies",
]
