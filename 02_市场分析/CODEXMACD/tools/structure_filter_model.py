from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Direction = Literal["buy", "sell"]


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Trendline:
    valid: bool
    direction: Direction
    touches: int = 0
    older_index: int = -1
    newer_index: int = -1
    older_price: float = 0.0
    newer_price: float = 0.0
    line_at_signal: float = 0.0
    breakout_distance: float = 0.0
    breakout_distance_atr: float = 0.0


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def line_value(older_index: int, older_price: float, newer_index: int, newer_price: float, target_index: int) -> float:
    if newer_index == older_index:
        return newer_price
    slope = (newer_price - older_price) / (newer_index - older_index)
    return older_price + slope * (target_index - older_index)


def is_swing_high(bars: list[Bar], index: int, lookback: int) -> bool:
    if index - lookback < 0 or index + lookback >= len(bars):
        return False
    high = bars[index].high
    return all(high > bars[i].high for i in range(index - lookback, index + lookback + 1) if i != index)


def is_swing_low(bars: list[Bar], index: int, lookback: int) -> bool:
    if index - lookback < 0 or index + lookback >= len(bars):
        return False
    low = bars[index].low
    return all(low < bars[i].low for i in range(index - lookback, index + lookback + 1) if i != index)


def count_touches(
    *,
    bars: list[Bar],
    direction: Direction,
    older_index: int,
    older_price: float,
    newer_index: int,
    newer_price: float,
    touch_distance: float,
) -> int:
    touches = 0
    for index in range(older_index, newer_index + 1):
        expected = line_value(older_index, older_price, newer_index, newer_price, index)
        actual = bars[index].high if direction == "buy" else bars[index].low
        if abs(actual - expected) <= touch_distance:
            touches += 1
    return touches


def find_valid_trendline(
    *,
    bars: list[Bar],
    direction: Direction,
    atr: float,
    swing_lookback: int,
    min_touches: int,
    touch_atr: float,
    min_breakout_distance_atr: float,
) -> Trendline:
    if atr <= 0 or len(bars) < swing_lookback * 2 + 4:
        return Trendline(valid=False, direction=direction)

    signal_index = len(bars) - 1
    touch_distance = atr * touch_atr
    best = Trendline(valid=False, direction=direction)

    swing_indexes: list[int] = []
    for index in range(swing_lookback, signal_index - swing_lookback):
        if direction == "buy" and is_swing_high(bars, index, swing_lookback):
            swing_indexes.append(index)
        if direction == "sell" and is_swing_low(bars, index, swing_lookback):
            swing_indexes.append(index)

    for older_index in swing_indexes:
        for newer_index in swing_indexes:
            if newer_index <= older_index:
                continue

            older_price = bars[older_index].high if direction == "buy" else bars[older_index].low
            newer_price = bars[newer_index].high if direction == "buy" else bars[newer_index].low

            if direction == "buy" and newer_price >= older_price:
                continue
            if direction == "sell" and newer_price <= older_price:
                continue

            touches = count_touches(
                bars=bars,
                direction=direction,
                older_index=older_index,
                older_price=older_price,
                newer_index=newer_index,
                newer_price=newer_price,
                touch_distance=touch_distance,
            )
            if touches < min_touches:
                continue

            line_at_signal = line_value(older_index, older_price, newer_index, newer_price, signal_index)
            close = bars[signal_index].close
            distance = close - line_at_signal if direction == "buy" else line_at_signal - close
            distance_atr = distance / atr
            if distance_atr < min_breakout_distance_atr:
                continue

            candidate = Trendline(
                valid=True,
                direction=direction,
                touches=touches,
                older_index=older_index,
                newer_index=newer_index,
                older_price=older_price,
                newer_price=newer_price,
                line_at_signal=line_at_signal,
                breakout_distance=distance,
                breakout_distance_atr=distance_atr,
            )

            if not best.valid or candidate.touches > best.touches or (
                candidate.touches == best.touches and candidate.newer_index > best.newer_index
            ):
                best = candidate

    return best


def score_breakout(
    *,
    body_ratio: float,
    required_body_ratio: float,
    opposite_shadow_ratio: float,
    max_opposite_shadow: float,
    breakout_distance_atr: float,
    min_breakout_distance_atr: float,
    dangerous_candle: bool,
    follow_through_required: bool,
    has_follow_through: bool,
) -> float:
    body_score = 30.0 if required_body_ratio <= 0 else clamp(body_ratio / required_body_ratio, 0.0, 1.0) * 30.0

    if max_opposite_shadow <= 0:
        shadow_score = 25.0 if opposite_shadow_ratio <= 0 else 0.0
    elif opposite_shadow_ratio <= max_opposite_shadow:
        shadow_score = 25.0
    else:
        excess_ratio = (opposite_shadow_ratio - max_opposite_shadow) / max_opposite_shadow
        shadow_score = clamp(1.0 - excess_ratio, 0.0, 1.0) * 25.0

    distance_target = min_breakout_distance_atr * 2.0
    distance_score = 25.0 if distance_target <= 0 else clamp(breakout_distance_atr / distance_target, 0.0, 1.0) * 25.0

    score = body_score + shadow_score + distance_score
    if dangerous_candle:
        score -= 30.0
    if follow_through_required and has_follow_through:
        score += 20.0

    return round(clamp(score, 0.0, 100.0), 2)
