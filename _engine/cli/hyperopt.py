from __future__ import annotations

import argparse
import time
from pathlib import Path

from .._utils import _format_time
from ..models import CandleRequest, OptimizationRequest
from ._helpers import _resolve, load_candles, generate_signals
from strategy import list_strategies


def run_hyperopt(args: argparse.Namespace, config: dict) -> int:
    from ..hyperopt import run_optimization

    exchange = _resolve(args, config, "exchange")
    timeframe = _resolve(args, config, "timeframe")
    session_type = _resolve(args, config, "session")
    adjustment = _resolve(args, config, "adjustment")
    strategy_name = _resolve(args, config, "strategy")
    if strategy_name is None:
        available = ", ".join(list_strategies()) or "(none)"
        print(f"Error: No strategy specified. Use --strategy NAME or set 'strategy' in config.json.")
        print(f"Available strategies: {available}")
        return 1
    initial_capital = config["initial_capital"]
    data_dir = config["data_dir"]
    output_dir_base = config["output_dir"]

    opt_cfg = config.get("optimization", {})
    sl_range = opt_cfg.get("sl_range", {})
    tp_range = opt_cfg.get("tp_range", {})
    sl_min = args.sl_min if args.sl_min is not None else sl_range.get("min")
    sl_max = args.sl_max if args.sl_max is not None else sl_range.get("max")
    sl_step = args.sl_step if args.sl_step is not None else sl_range.get("step")
    tp_min = args.tp_min if args.tp_min is not None else tp_range.get("min")
    tp_max = args.tp_max if args.tp_max is not None else tp_range.get("max")
    tp_step = args.tp_step if args.tp_step is not None else tp_range.get("step")
    objective = args.objective or opt_cfg.get("objective")
    top_n = args.top_n if args.top_n is not None else opt_cfg.get("top_n")
    search_method = args.search_method or opt_cfg.get("search_method")
    n_trials = args.n_trials if args.n_trials is not None else opt_cfg.get("n_trials")
    fine_factor = opt_cfg.get("fine_factor")

    candle_request = CandleRequest(
        symbol=args.symbol,
        exchange=exchange,
        timeframe=timeframe,
        start=args.start,
        end=args.end,
        session=session_type,
        adjustment=adjustment,
    )

    print(f"\n{'='*60}")
    print("  HyperView - Hyper-Optimization")
    print(f"  {exchange}:{args.symbol} | {timeframe} | mode={args.mode}")
    print(f"  Strategy: {strategy_name}")
    print(f"  SL range: {sl_min}-{sl_max} (step {sl_step})")
    print(f"  TP range: {tp_min}-{tp_max} (step {tp_step})")
    method_label = "Bayesian (Optuna TPE)" if search_method == "bayesian" else "Two-stage grid"
    print(f"  Search:   {method_label}")
    if search_method == "bayesian":
        print(f"  Trials:   {n_trials}")
    print(f"{'='*60}")

    # 1. Load data
    candles = load_candles(candle_request, data_dir, step="1/4")

    # 2. Generate signals
    signal_frame, strategy = generate_signals(
        strategy_name, candles, args.mode, args.start, args.end, step="2/4",
    )
    buy_count = int(signal_frame["buy_signal"].sum())
    sell_count = int(signal_frame["sell_signal"].sum())
    total_signals = buy_count + sell_count
    in_range_bars = int(signal_frame["in_date_range"].sum())
    density_per_1k = total_signals / max(in_range_bars, 1) * 1000
    if density_per_1k < 5:
        density_label = "low"
    elif density_per_1k < 20:
        density_label = "medium"
    else:
        density_label = "high"
    print(f"      Signal density: {density_label} ({density_per_1k:.2f}/1k bars) "
          f"over {in_range_bars} in-range bars")

    print("\n[3/4] Running optimization...")
    t_opt = time.time()
    request = OptimizationRequest(
        candle_request=candle_request,
        mode=args.mode,
        objective=objective,
        sl_min=sl_min,
        sl_max=sl_max,
        sl_step=sl_step,
        tp_min=tp_min,
        tp_max=tp_max,
        tp_step=tp_step,
        top_n=top_n,
        search_method=search_method,
        n_trials=n_trials,
        fine_factor=fine_factor,
        initial_equity=initial_capital,
    )
    output_path = Path(output_dir_base) / f"{strategy_name}_{exchange}_{args.symbol}_{timeframe}_{args.mode}.json"
    bundle = run_optimization(
        signal_frame=signal_frame,
        candle_request=candle_request,
        strategy=strategy,
        request=request,
        output_path=output_path,
        initial_equity=initial_capital,
    )
    print(f"      Optimization complete ({_format_time(time.time() - t_opt)})")

    print("\n[4/4] Results")
    print("\nTop candidates:")
    for rank, metrics in enumerate(bundle.results, start=1):
        print(
            f"{rank:>2}. SL={metrics.sl_pct:.4f}% TP={metrics.tp_pct:.4f}% "
            f"net={metrics.net_profit_pct:.4f}% dd={metrics.max_drawdown_pct:.4f}% "
            f"win={metrics.win_rate_pct:.4f}% pf={metrics.profit_factor} trades={metrics.trade_count}"
        )
    print(f"\nResults written to {output_path}")
    return 0
