from __future__ import annotations

import pandas as pd

from .constants import INTERVAL_MAP, TIMEFRAME_SECONDS


def normalize_interval(timeframe: str) -> str:
    return INTERVAL_MAP.get(timeframe.strip().lower(), timeframe)


def timeframe_seconds(timeframe: str) -> int:
    lowered = timeframe.strip().lower()
    if lowered not in TIMEFRAME_SECONDS:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return TIMEFRAME_SECONDS[lowered]


def to_timestamp(value: str | None) -> int | None:
    if value is None:
        return None
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return int(timestamp.timestamp())


def estimate_bar_count(timeframe: str, start: str | None, end: str | None) -> int:
    if start is None or end is None:
        return 10_000
    start_ts = to_timestamp(start)
    end_ts = to_timestamp(end)
    if start_ts is None or end_ts is None or end_ts <= start_ts:
        return 10_000
    seconds = timeframe_seconds(timeframe)
    return min(max(int(((end_ts - start_ts) / seconds) * 1.5) + 100, 500), 20_000)


def backfill_chunk_size(timeframe: str) -> int:
    return max(1_000, min(5_000, int(30 * 86_400 / timeframe_seconds(timeframe))))


def max_backfill_requests(timeframe: str, start: str | None, end: str | None) -> int:
    if start is None or end is None:
        return 10

    start_ts = to_timestamp(start)
    end_ts = to_timestamp(end)
    if start_ts is None or end_ts is None or end_ts <= start_ts:
        return 10

    bars_needed = max(1, int((end_ts - start_ts) / timeframe_seconds(timeframe)))
    return max(1, min(25, int(bars_needed / backfill_chunk_size(timeframe)) + 2))
