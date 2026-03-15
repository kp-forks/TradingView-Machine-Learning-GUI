from __future__ import annotations

from typing import Any

import pandas as pd

from ._lib.base import BaseStrategy
from . import register_strategy
from ._lib.indicators import barssince, crossed_above, crossed_below, macd, rsi, to_unix_timestamp


@register_strategy
class MacdRsiStrategy(BaseStrategy):
    """Pure-Python MACD-RSI strategy matching the TradingView Pine Script reference."""

    strategy_name = "macd_rsi"

    def default_settings(self) -> dict[str, Any]:
        return {
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "rsi_length": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "signal_lookback_bars": 10,
            "enable_long": True,
            "enable_short": True,
            "start": None,
            "end": None,
        }

    def required_columns(self) -> list[str]:
        return ["time", "open", "high", "low", "close"]

    def generate_signals(self, candles: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
        s = {**self.default_settings(), **settings}
        dataframe = self.prepare_candles(candles)

        dataframe["rsi"] = rsi(dataframe["close"], s["rsi_length"])
        dataframe["macd_line"], dataframe["signal_line"], dataframe["hist_line"] = macd(
            dataframe["close"],
            s["macd_fast"],
            s["macd_slow"],
            s["macd_signal"],
        )

        rsi_oversold_hit = dataframe["rsi"] <= s["rsi_oversold"]
        rsi_overbought_hit = dataframe["rsi"] >= s["rsi_overbought"]
        dataframe["bars_since_oversold"] = barssince(rsi_oversold_hit)
        dataframe["bars_since_overbought"] = barssince(rsi_overbought_hit)
        dataframe["was_oversold"] = dataframe["bars_since_oversold"] <= s["signal_lookback_bars"]
        dataframe["was_overbought"] = dataframe["bars_since_overbought"] <= s["signal_lookback_bars"]
        dataframe["crossover_bull"] = crossed_above(dataframe["macd_line"], dataframe["signal_line"])
        dataframe["crossover_bear"] = crossed_below(dataframe["macd_line"], dataframe["signal_line"])
        dataframe["buy_signal"] = dataframe["was_oversold"] & dataframe["crossover_bull"]
        dataframe["sell_signal"] = dataframe["was_overbought"] & dataframe["crossover_bear"]

        start_ts = to_unix_timestamp(s["start"])
        end_ts = to_unix_timestamp(s["end"])
        if start_ts is None and end_ts is None:
            dataframe["in_date_range"] = True
        else:
            lower = dataframe["time"] >= (start_ts if start_ts is not None else dataframe["time"].min())
            upper_bound = end_ts if end_ts is not None else (dataframe["time"].max() + 1)
            upper = dataframe["time"] < upper_bound
            dataframe["in_date_range"] = lower & upper

        dataframe["enable_long"] = s["enable_long"]
        dataframe["enable_short"] = s["enable_short"]
        return dataframe
