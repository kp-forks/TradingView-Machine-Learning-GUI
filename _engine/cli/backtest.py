from __future__ import annotations

import argparse
import time

from .._utils import _format_time
from ..models import CandleRequest
from ._helpers import _resolve, load_candles, generate_signals
from strategy import list_strategies


def run_backtest(args: argparse.Namespace, config: dict) -> int:
    from ..backtest.engine import TradingViewLikeBacktester
    from ..models import RiskParameters
    from .._utils import build_risk

    exchange = _resolve(args, config, "exchange")
    timeframe = _resolve(args, config, "timeframe")
    session = _resolve(args, config, "session")
    adjustment = _resolve(args, config, "adjustment")
    strategy_name = _resolve(args, config, "strategy")
    if strategy_name is None:
        available = ", ".join(list_strategies()) or "(none)"
        print(f"Error: No strategy specified. Use --strategy NAME or set 'strategy' in config.json.")
        print(f"Available strategies: {available}")
        return 1
    initial_capital = config["initial_capital"]
    data_dir = config["data_dir"]

    candle_request = CandleRequest(
        symbol=args.symbol,
        exchange=exchange,
        timeframe=timeframe,
        start=args.start,
        end=args.end,
        session=session,
        adjustment=adjustment,
    )

    print(f"\n{'='*60}")
    print("  HyperView - Backtest")
    print(f"  {exchange}:{args.symbol} | {timeframe} | mode={args.mode}")
    print(f"  Strategy: {strategy_name} | SL={args.sl}% TP={args.tp}%")
    print(f"{'='*60}")

    # 1. Load data
    candles = load_candles(candle_request, data_dir, step="1/3")

    # 2. Generate signals
    signal_frame, strategy = generate_signals(
        strategy_name, candles, args.mode, args.start, args.end, step="2/3",
    )

    # 3. Run backtest
    print("\n[3/3] Running backtest...")
    t0 = time.time()
    risk = build_risk(args.mode, args.sl, args.tp)
    backtester = TradingViewLikeBacktester(candle_request=candle_request, initial_equity=initial_capital)
    result = backtester.run(signal_frame, risk, args.mode)
    m = result.metrics
    print(f"      Done ({_format_time(time.time() - t0)})")

    print(f"\n{'-'*60}")
    print(f"  Net Profit:    {m.net_profit_pct:>10.2f}%")
    print(f"  Max Drawdown:  {m.max_drawdown_pct:>10.2f}%")
    print(f"  Win Rate:      {m.win_rate_pct:>10.2f}%")
    print(f"  Profit Factor: {m.profit_factor:>10.2f}")
    print(f"  Trades:        {m.trade_count:>10d}")
    print(f"  Final Equity:  ${m.equity_final:>12,.2f}")
    print(f"{'-'*60}")
    return 0
