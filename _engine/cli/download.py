from __future__ import annotations

import argparse
import time

from .._utils import _format_time
from ..downloader import TradingViewDataClient
from ._helpers import _resolve


def run_download_data(args: argparse.Namespace, config: dict) -> int:
    exchange = _resolve(args, config, "exchange")
    timeframe = _resolve(args, config, "timeframe")
    session = _resolve(args, config, "session")
    adjustment = _resolve(args, config, "adjustment")
    data_dir = config["data_dir"]

    pairs = [(symbol, exchange) for symbol in args.pairs]

    print(f"\n{'='*60}")
    print("  HyperView - Download Data")
    print(f"  {len(pairs)} pair(s) | {exchange} | {timeframe}")
    if args.start:
        print(f"  Range: {args.start} -> {args.end or 'now'}")
    print(f"{'='*60}\n")

    client = TradingViewDataClient(cache_dir=data_dir)
    t0 = time.time()
    results = client.download_pairs(
        pairs=pairs,
        timeframe=timeframe,
        start=args.start,
        end=args.end,
        session=session,
        adjustment=adjustment,
    )
    print(f"\nDone - {len(results)} pair(s) downloaded ({_format_time(time.time() - t0)})")
    return 0
