# SniperTrendEA v8.6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `SniperTrendEA_v8.6.mq5` by extending v8.5 with validated trendline structure filtering and breakout quality scoring.

**Architecture:** Keep v8.5 as the trading engine. First verify the deterministic structure math in a Python harness, then port the same rules into MQ5 helpers and wire them into the existing pending-entry flow. Static MQ5 tests check that the EA contains the expected v8.6 inputs, helper functions, and entry integration.

**Tech Stack:** MQL5 EA source, PowerShell, bundled Python `C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`, Python `unittest`.

---

## File Structure

- Create: `E:\CODEXMACD\tests\__init__.py`
  Makes the test directory importable for `python -m unittest`.

- Create: `E:\CODEXMACD\tests\test_structure_filter_model.py`
  Unit tests for pure structure math: breakout scoring, swing detection, trendline validation, and no-structure rejection.

- Create: `E:\CODEXMACD\tools\structure_filter_model.py`
  Python reference model for deterministic v8.6 calculations. This is not trading production code; it exists to verify the math before MQ5 implementation.

- Create: `E:\CODEXMACD\tests\test_mq5_static.py`
  Static tests for `SniperTrendEA_v8.6.mq5` content and integration.

- Create: `E:\CODEXMACD\SniperTrendEA_v8.6.mq5`
  New EA source copied from v8.5 and upgraded.

- Create: `E:\CODEXMACD\checkpoints\`
  Local backup snapshots, because `E:\CODEXMACD` is not a git repository.

---

### Task 1: Breakout Score Reference Model

**Files:**
- Create: `E:\CODEXMACD\tests\__init__.py`
- Create: `E:\CODEXMACD\tests\test_structure_filter_model.py`
- Create: `E:\CODEXMACD\tools\structure_filter_model.py`

- [ ] **Step 1: Write the failing score tests**

Create `E:\CODEXMACD\tests\__init__.py` as an empty file.

Create `E:\CODEXMACD\tests\test_structure_filter_model.py` with:

```python
import unittest

from tools.structure_filter_model import score_breakout


class BreakoutScoreTests(unittest.TestCase):
    def test_scores_clean_breakout_without_follow_bonus(self):
        score = score_breakout(
            body_ratio=0.75,
            required_body_ratio=0.60,
            opposite_shadow_ratio=0.10,
            max_opposite_shadow=0.20,
            breakout_distance_atr=0.20,
            min_breakout_distance_atr=0.10,
            dangerous_candle=False,
            follow_through_required=False,
            has_follow_through=False,
        )

        self.assertEqual(score, 80.0)

    def test_dangerous_candle_penalty_reduces_score(self):
        score = score_breakout(
            body_ratio=0.75,
            required_body_ratio=0.60,
            opposite_shadow_ratio=0.10,
            max_opposite_shadow=0.20,
            breakout_distance_atr=0.20,
            min_breakout_distance_atr=0.10,
            dangerous_candle=True,
            follow_through_required=False,
            has_follow_through=False,
        )

        self.assertEqual(score, 50.0)

    def test_follow_through_can_lift_clean_breakout_to_full_score(self):
        score = score_breakout(
            body_ratio=0.75,
            required_body_ratio=0.60,
            opposite_shadow_ratio=0.10,
            max_opposite_shadow=0.20,
            breakout_distance_atr=0.20,
            min_breakout_distance_atr=0.10,
            dangerous_candle=False,
            follow_through_required=True,
            has_follow_through=True,
        )

        self.assertEqual(score, 100.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the score tests to verify RED**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_structure_filter_model -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools'` or `No module named 'tools.structure_filter_model'`.

- [ ] **Step 3: Write the minimal scoring implementation**

Create directory `E:\CODEXMACD\tools`.

Create `E:\CODEXMACD\tools\__init__.py` as an empty file.

Create `E:\CODEXMACD\tools\structure_filter_model.py` with:

```python
from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


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
```

- [ ] **Step 4: Run the score tests to verify GREEN**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_structure_filter_model -v
```

Expected: PASS with 3 passing tests.

---

### Task 2: Trendline Structure Reference Model

**Files:**
- Modify: `E:\CODEXMACD\tests\test_structure_filter_model.py`
- Modify: `E:\CODEXMACD\tools\structure_filter_model.py`

- [ ] **Step 1: Add failing trendline tests**

Append these tests inside `BreakoutScoreTests` in `E:\CODEXMACD\tests\test_structure_filter_model.py`:

```python
    def test_validates_descending_resistance_breakout_for_buy(self):
        from tools.structure_filter_model import Bar, find_valid_trendline

        bars = [
            Bar(open=104, high=107, low=101, close=103),
            Bar(open=106, high=110, low=102, close=105),
            Bar(open=103, high=106, low=100, close=102),
            Bar(open=102, high=105, low=99, close=101),
            Bar(open=104, high=108, low=101, close=103),
            Bar(open=101, high=104, low=98, close=100),
            Bar(open=100, high=103, low=97, close=99),
            Bar(open=102, high=106, low=99, close=101),
            Bar(open=100, high=102, low=97, close=99),
            Bar(open=104, high=107, low=101, close=106),
        ]

        trendline = find_valid_trendline(
            bars=bars,
            direction="buy",
            atr=5.0,
            swing_lookback=1,
            min_touches=3,
            touch_atr=0.25,
            min_breakout_distance_atr=0.10,
        )

        self.assertTrue(trendline.valid)
        self.assertEqual(trendline.touches, 3)
        self.assertGreaterEqual(trendline.breakout_distance_atr, 0.10)

    def test_rejects_buy_when_no_valid_structure_exists(self):
        from tools.structure_filter_model import Bar, find_valid_trendline

        bars = [
            Bar(open=100, high=102, low=99, close=101),
            Bar(open=101, high=103, low=100, close=102),
            Bar(open=102, high=104, low=101, close=103),
            Bar(open=103, high=105, low=102, close=104),
            Bar(open=104, high=106, low=103, close=105),
        ]

        trendline = find_valid_trendline(
            bars=bars,
            direction="buy",
            atr=5.0,
            swing_lookback=1,
            min_touches=3,
            touch_atr=0.25,
            min_breakout_distance_atr=0.10,
        )

        self.assertFalse(trendline.valid)
```

- [ ] **Step 2: Run the trendline tests to verify RED**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_structure_filter_model -v
```

Expected: FAIL with `ImportError` for `Bar` or `find_valid_trendline`.

- [ ] **Step 3: Implement trendline math in the reference model**

Replace `E:\CODEXMACD\tools\structure_filter_model.py` with:

```python
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
```

- [ ] **Step 4: Run all reference-model tests to verify GREEN**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_structure_filter_model -v
```

Expected: PASS with 5 passing tests.

---

### Task 3: Static Tests For v8.6 EA Shell

**Files:**
- Create: `E:\CODEXMACD\tests\test_mq5_static.py`
- Create: `E:\CODEXMACD\SniperTrendEA_v8.6.mq5`

- [ ] **Step 1: Write failing static tests for the v8.6 shell**

Create `E:\CODEXMACD\tests\test_mq5_static.py` with:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "SniperTrendEA_v8.6.mq5"


class Mq5StaticTests(unittest.TestCase):
    def read_ea(self) -> str:
        self.assertTrue(EA.exists(), "SniperTrendEA_v8.6.mq5 must exist")
        return EA.read_text(encoding="utf-8")

    def test_v86_file_has_version_and_comment(self):
        source = self.read_ea()
        self.assertIn('#property version   "8.60"', source)
        self.assertIn('input string InpComment        = "SniperEA_v8.6";', source)
        self.assertIn("SniperTrendEA v8.6", source)

    def test_v86_structure_inputs_exist(self):
        source = self.read_ea()
        required_inputs = [
            "InpUseStructureFilter",
            "InpSwingLookback",
            "InpStructureScanBars",
            "InpMinTrendlineTouches",
            "InpTrendlineTouchATR",
            "InpMinBreakoutDistanceATR",
            "InpMinBreakoutScore",
            "InpRejectNoStructure",
            "InpShowStructureDebug",
        ]
        for name in required_inputs:
            self.assertIn(name, source)

    def test_high_risk_recovery_patterns_are_not_added(self):
        source = self.read_ea().lower()
        banned_tokens = ["martingale", "grid", "averaging down", "recovery multiplier"]
        for token in banned_tokens:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run static tests to verify RED**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_mq5_static -v
```

Expected: FAIL with `SniperTrendEA_v8.6.mq5 must exist`.

- [ ] **Step 3: Create the v8.6 EA shell from v8.5**

Run:

```powershell
Copy-Item -LiteralPath 'E:\CODEXMACD\SniperTrendEA_v8.5.mq5' -Destination 'E:\CODEXMACD\SniperTrendEA_v8.6.mq5'
```

Then update `E:\CODEXMACD\SniperTrendEA_v8.6.mq5`:

```mql5
//|                                          SniperTrendEA_v8.6.mq5 |
//|                    v8.6 - Structure Quality Upgrade             |
```

```mql5
#property copyright "SniperTrendEA v8.6 - Wyckoff + Evil MACD + Z-Wei Structure"
#property version   "8.60"
```

Replace the trade comment input with:

```mql5
input string InpComment        = "SniperEA_v8.6";
```

Insert this input group after `InpRequireMACDDir`:

```mql5
input group "=== Structure Filter (v8.6) ==="
input bool   InpUseStructureFilter      = true;  // Enable validated trendline structure filter
input int    InpSwingLookback           = 3;     // Swing high/low bars on each side
input int    InpStructureScanBars       = 80;    // Historical bars to scan for structure
input int    InpMinTrendlineTouches     = 3;     // Minimum validated trendline touches
input double InpTrendlineTouchATR       = 0.25;  // Touch tolerance in ATR multiples
input double InpMinBreakoutDistanceATR  = 0.10;  // Minimum close distance beyond trendline
input double InpMinBreakoutScore        = 70.0;  // Minimum quality score for entry
input bool   InpRejectNoStructure       = true;  // Reject entries when no valid structure exists
input bool   InpShowStructureDebug      = true;  // Print structure diagnostics
```

- [ ] **Step 4: Run static tests to verify shell GREEN**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_mq5_static -v
```

Expected: PASS with 3 passing tests.

---

### Task 4: MQ5 Structure Helper Functions

**Files:**
- Modify: `E:\CODEXMACD\tests\test_mq5_static.py`
- Modify: `E:\CODEXMACD\SniperTrendEA_v8.6.mq5`

- [ ] **Step 1: Add failing static tests for helper functions**

Append these methods inside `Mq5StaticTests` in `E:\CODEXMACD\tests\test_mq5_static.py`:

```python
    def test_structure_helper_functions_exist(self):
        source = self.read_ea()
        required_snippets = [
            "struct STrendlineInfo",
            "void ResetTrendlineInfo",
            "double ClampDouble",
            "bool IsSwingHigh",
            "bool IsSwingLow",
            "double LineValueAtShift",
            "int CountTrendlineTouches",
            "bool FindValidatedTrendline",
            "double CalculateBreakoutScore",
            "bool PassStructureFilter",
        ]
        for snippet in required_snippets:
            self.assertIn(snippet, source)
```

- [ ] **Step 2: Run static tests to verify RED**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_mq5_static -v
```

Expected: FAIL because `struct STrendlineInfo` is not present.

- [ ] **Step 3: Add the MQ5 structure helper code**

Insert this code in `E:\CODEXMACD\SniperTrendEA_v8.6.mq5` before `GetBodyRatio`:

```mql5
struct STrendlineInfo
{
   bool   valid;
   int    touches;
   int    anchorShiftOld;
   int    anchorShiftNew;
   double anchorPriceOld;
   double anchorPriceNew;
   double lineAtSignal;
   double breakoutDistance;
   double breakoutDistanceATR;
   double score;
};

void ResetTrendlineInfo(STrendlineInfo &info)
{
   info.valid = false;
   info.touches = 0;
   info.anchorShiftOld = -1;
   info.anchorShiftNew = -1;
   info.anchorPriceOld = 0.0;
   info.anchorPriceNew = 0.0;
   info.lineAtSignal = 0.0;
   info.breakoutDistance = 0.0;
   info.breakoutDistanceATR = 0.0;
   info.score = 0.0;
}

double ClampDouble(double value, double minValue, double maxValue)
{
   return MathMax(minValue, MathMin(maxValue, value));
}

bool IsSwingHigh(int shift, int lookback)
{
   if(shift - lookback < 1) return false;
   int bars = Bars(_Symbol, PERIOD_CURRENT);
   if(shift + lookback >= bars) return false;

   double high = iHigh(_Symbol, PERIOD_CURRENT, shift);
   for(int i = 1; i <= lookback; i++)
   {
      if(iHigh(_Symbol, PERIOD_CURRENT, shift - i) >= high) return false;
      if(iHigh(_Symbol, PERIOD_CURRENT, shift + i) >= high) return false;
   }
   return true;
}

bool IsSwingLow(int shift, int lookback)
{
   if(shift - lookback < 1) return false;
   int bars = Bars(_Symbol, PERIOD_CURRENT);
   if(shift + lookback >= bars) return false;

   double low = iLow(_Symbol, PERIOD_CURRENT, shift);
   for(int i = 1; i <= lookback; i++)
   {
      if(iLow(_Symbol, PERIOD_CURRENT, shift - i) <= low) return false;
      if(iLow(_Symbol, PERIOD_CURRENT, shift + i) <= low) return false;
   }
   return true;
}

double LineValueAtShift(int oldShift, double oldPrice, int newShift, double newPrice, int targetShift)
{
   if(newShift == oldShift) return newPrice;
   double slope = (newPrice - oldPrice) / (double)(newShift - oldShift);
   return oldPrice + slope * (double)(targetShift - oldShift);
}

int CountTrendlineTouches(bool forBuy, int oldShift, double oldPrice, int newShift, double newPrice, double atr)
{
   if(atr <= 0) return 0;
   double touchDistance = atr * InpTrendlineTouchATR;
   int touches = 0;

   for(int shift = oldShift; shift >= newShift; shift--)
   {
      double lineValue = LineValueAtShift(oldShift, oldPrice, newShift, newPrice, shift);
      double actual = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, shift) : iLow(_Symbol, PERIOD_CURRENT, shift);
      if(MathAbs(actual - lineValue) <= touchDistance)
         touches++;
   }

   return touches;
}

bool FindValidatedTrendline(bool forBuy, double atr, STrendlineInfo &info)
{
   ResetTrendlineInfo(info);
   if(atr <= 0 || InpSwingLookback < 1 || InpMinTrendlineTouches < 2) return false;

   int bars = Bars(_Symbol, PERIOD_CURRENT);
   int maxShift = MathMin(InpStructureScanBars, bars - InpSwingLookback - 2);
   int minShift = InpSwingLookback + 1;
   if(maxShift <= minShift + InpSwingLookback) return false;

   for(int newShift = minShift; newShift <= maxShift - InpSwingLookback; newShift++)
   {
      bool newSwing = forBuy ? IsSwingHigh(newShift, InpSwingLookback) : IsSwingLow(newShift, InpSwingLookback);
      if(!newSwing) continue;

      double newPrice = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, newShift) : iLow(_Symbol, PERIOD_CURRENT, newShift);

      for(int oldShift = newShift + InpSwingLookback; oldShift <= maxShift; oldShift++)
      {
         bool oldSwing = forBuy ? IsSwingHigh(oldShift, InpSwingLookback) : IsSwingLow(oldShift, InpSwingLookback);
         if(!oldSwing) continue;

         double oldPrice = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, oldShift) : iLow(_Symbol, PERIOD_CURRENT, oldShift);
         if(forBuy && newPrice >= oldPrice) continue;
         if(!forBuy && newPrice <= oldPrice) continue;

         int touches = CountTrendlineTouches(forBuy, oldShift, oldPrice, newShift, newPrice, atr);
         if(touches < InpMinTrendlineTouches) continue;

         double lineAtSignal = LineValueAtShift(oldShift, oldPrice, newShift, newPrice, 1);
         double close = iClose(_Symbol, PERIOD_CURRENT, 1);
         double distance = forBuy ? close - lineAtSignal : lineAtSignal - close;
         double distanceATR = distance / atr;
         if(distanceATR < InpMinBreakoutDistanceATR) continue;

         bool better = (!info.valid ||
                        touches > info.touches ||
                        (touches == info.touches && newShift < info.anchorShiftNew));
         if(better)
         {
            info.valid = true;
            info.touches = touches;
            info.anchorShiftOld = oldShift;
            info.anchorShiftNew = newShift;
            info.anchorPriceOld = oldPrice;
            info.anchorPriceNew = newPrice;
            info.lineAtSignal = lineAtSignal;
            info.breakoutDistance = distance;
            info.breakoutDistanceATR = distanceATR;
         }
      }
   }

   return info.valid;
}

double CalculateBreakoutScore(bool forBuy, double atr, STrendlineInfo &info, bool dangerousCandle)
{
   double bodyRatio = GetBodyRatio(1);
   double bodyScore = (InpBodyRatio <= 0) ? 30.0 : ClampDouble(bodyRatio / InpBodyRatio, 0.0, 1.0) * 30.0;

   double shadow = forBuy ? GetUpperShadowRatio(1) : GetLowerShadowRatio(1);
   double shadowScore = 0.0;
   if(InpMaxOppositeShadow <= 0)
      shadowScore = (shadow <= 0) ? 25.0 : 0.0;
   else if(shadow <= InpMaxOppositeShadow)
      shadowScore = 25.0;
   else
      shadowScore = ClampDouble(1.0 - ((shadow - InpMaxOppositeShadow) / InpMaxOppositeShadow), 0.0, 1.0) * 25.0;

   double distanceTarget = InpMinBreakoutDistanceATR * 2.0;
   double distanceScore = (distanceTarget <= 0) ? 25.0 : ClampDouble(info.breakoutDistanceATR / distanceTarget, 0.0, 1.0) * 25.0;

   double score = bodyScore + shadowScore + distanceScore;
   if(dangerousCandle) score -= 30.0;
   if(InpRequireFollowThrough)
   {
      bool followOk = forBuy ? IsHighestClose(1, InpFollowThroughBars) : IsLowestClose(1, InpFollowThroughBars);
      if(followOk) score += 20.0;
   }

   return ClampDouble(score, 0.0, 100.0);
}

bool PassStructureFilter(bool forBuy, double atr, bool dangerousCandle, STrendlineInfo &info)
{
   ResetTrendlineInfo(info);
   if(!InpUseStructureFilter)
   {
      info.valid = true;
      info.score = 100.0;
      return true;
   }

   bool found = FindValidatedTrendline(forBuy, atr, info);
   if(!found)
   {
      if(InpShowStructureDebug)
         Print("【v8.6结构】", forBuy ? "多" : "空", "：无有效趋势线结构");

      if(!InpRejectNoStructure)
      {
         info.valid = false;
         info.score = 100.0;
         return true;
      }
      return false;
   }

   info.score = CalculateBreakoutScore(forBuy, atr, info, dangerousCandle);
   if(InpShowStructureDebug)
   {
      Print("【v8.6结构】", forBuy ? "多" : "空",
            " | touches:", info.touches,
            " | line:", DoubleToString(info.lineAtSignal, _Digits),
            " | distanceATR:", DoubleToString(info.breakoutDistanceATR, 2),
            " | score:", DoubleToString(info.score, 1));
   }

   return (info.score >= InpMinBreakoutScore);
}
```

- [ ] **Step 4: Run static tests to verify helper GREEN**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_mq5_static -v
```

Expected: PASS with 4 passing tests.

---

### Task 5: Wire Structure Filter Into Entry Flow

**Files:**
- Modify: `E:\CODEXMACD\tests\test_mq5_static.py`
- Modify: `E:\CODEXMACD\SniperTrendEA_v8.6.mq5`

- [ ] **Step 1: Add failing static tests for entry integration**

Append these methods inside `Mq5StaticTests`:

```python
    def test_structure_filter_is_called_for_buy_and_sell_entries(self):
        source = self.read_ea()
        self.assertIn("PassStructureFilter(true, atr1, dangerCandle, structure)", source)
        self.assertIn("PassStructureFilter(false, atr1, dangerCandle, structure)", source)
        self.assertIn("【结构过滤-多】评分不足或无有效结构，放弃", source)
        self.assertIn("【结构过滤-空】评分不足或无有效结构，放弃", source)

    def test_debug_comment_includes_v86_structure_state(self):
        source = self.read_ea()
        self.assertIn("Structure Filter:", source)
        self.assertIn("InpUseStructureFilter ? \"ON\" : \"OFF\"", source)
```

- [ ] **Step 2: Run static tests to verify RED**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_mq5_static -v
```

Expected: FAIL because `PassStructureFilter(true, atr1, dangerCandle, structure)` is not present in entry logic.

- [ ] **Step 3: Add v8.6 debug state to `Comment`**

In the existing debug `Comment(...)` block in `OnTick`, add this line before the持仓 line:

```mql5
               "Structure Filter:", InpUseStructureFilter ? "ON" : "OFF", "\n",
```

- [ ] **Step 4: Wire the buy-side structure filter**

In the buy confirmation branch, keep the existing dangerous-candle, upper-shadow, and follow-through checks. Replace the final open-position `else` block with:

```mql5
                else
                {
                   STrendlineInfo structure;
                   if(!PassStructureFilter(true, atr1, dangerCandle, structure))
                   {
                      Print("【结构过滤-多】评分不足或无有效结构，放弃");
                      g_pendingBuy = false; g_pendingBars = 0;
                   }
                   else
                   {
                      double ep = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
                      double sl = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
                      double lot = CalculateLotSize(ep - sl);
                      Print("【开多】实体:", DoubleToString(bodyRatio*100,1), "%",
                            " | 上影:", DoubleToString(GetUpperShadowRatio(1)*100,1), "%",
                            " | 结构评分:", DoubleToString(structure.score, 1),
                            " | EP:", ep, " SL:", sl, " Lot:", lot);
                      if(lot > 0)
                      {
                         OpenPosition(ORDER_TYPE_BUY, ep, sl, lot);
                         g_pendingBuy = false; g_pendingBars = 0;
                      }
                   }
                }
```

- [ ] **Step 5: Wire the sell-side structure filter**

In the sell confirmation branch, keep the existing dangerous-candle, lower-shadow, and follow-through checks. Replace the final open-position `else` block with:

```mql5
                else
                {
                   STrendlineInfo structure;
                   if(!PassStructureFilter(false, atr1, dangerCandle, structure))
                   {
                      Print("【结构过滤-空】评分不足或无有效结构，放弃");
                      g_pendingSell = false; g_pendingBars = 0;
                   }
                   else
                   {
                      double ep = SymbolInfoDouble(_Symbol, SYMBOL_BID);
                      double sl = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
                      double lot = CalculateLotSize(sl - ep);
                      Print("【开空】实体:", DoubleToString(bodyRatio*100,1), "%",
                            " | 下影:", DoubleToString(GetLowerShadowRatio(1)*100,1), "%",
                            " | 结构评分:", DoubleToString(structure.score, 1),
                            " | EP:", ep, " SL:", sl, " Lot:", lot);
                      if(lot > 0)
                      {
                         OpenPosition(ORDER_TYPE_SELL, ep, sl, lot);
                         g_pendingSell = false; g_pendingBars = 0;
                      }
                   }
                }
```

- [ ] **Step 6: Run static tests to verify integration GREEN**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_mq5_static -v
```

Expected: PASS with 6 passing tests.

---

### Task 6: Local Checkpoint And Verification

**Files:**
- Create: `E:\CODEXMACD\checkpoints\`
- Verify: `E:\CODEXMACD\SniperTrendEA_v8.6.mq5`
- Verify: `E:\CODEXMACD\tests\test_structure_filter_model.py`
- Verify: `E:\CODEXMACD\tests\test_mq5_static.py`

- [ ] **Step 1: Run the full local test suite**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Expected: PASS with 11 passing tests.

- [ ] **Step 2: Check MQ5 file for high-risk strategy patterns**

Run:

```powershell
rg -n "martingale|grid|averaging down|recovery multiplier|加仓摊平|马丁|网格|追回亏损" SniperTrendEA_v8.6.mq5
```

Expected: exit code 1 and no matches.

- [ ] **Step 3: Create a local checkpoint copy**

Run:

```powershell
New-Item -ItemType Directory -Force 'E:\CODEXMACD\checkpoints' | Out-Null
Copy-Item -LiteralPath 'E:\CODEXMACD\SniperTrendEA_v8.6.mq5' -Destination 'E:\CODEXMACD\checkpoints\SniperTrendEA_v8.6.after-structure-filter.mq5'
```

Expected: `E:\CODEXMACD\checkpoints\SniperTrendEA_v8.6.after-structure-filter.mq5` exists.

- [ ] **Step 4: Report MetaTrader verification boundary**

Run:

```powershell
Get-ChildItem -Path 'C:\Program Files','C:\Program Files (x86)' -Recurse -Filter MetaEditor64.exe -ErrorAction SilentlyContinue | Select-Object -First 5 -ExpandProperty FullName
```

Expected: if no path is returned, local MetaEditor compilation is not available from this workspace. If a path is returned, compile `E:\CODEXMACD\SniperTrendEA_v8.6.mq5` in MetaEditor and report compiler errors or success.

---

### Task 7: Deploy To MT5 And Run H4 2020-2025 Backtest

**Files:**
- Read: `D:\MT5测试\MetaTrader 5\MetaEditor64.exe`
- Read: `D:\MT5测试\MetaTrader 5\terminal64.exe`
- Modify: `D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.6.mq5`
- Create: `D:\MT5测试\MetaTrader 5\MQL5\Experts\backup_codex\SniperTrendEA_v8.6.<timestamp>.mq5`
- Create: `D:\MT5测试\MetaTrader 5\Config\sniper_v86_h4_2020_2025.ini`
- Create: `D:\MT5测试\MetaTrader 5\SingleEAReports\sniper_v86_h4_2020_2025_codex\`

- [ ] **Step 1: Back up the existing MT5 v8.6 source**

Run:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
New-Item -ItemType Directory -Force 'D:\MT5测试\MetaTrader 5\MQL5\Experts\backup_codex' | Out-Null
Copy-Item -LiteralPath 'D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.6.mq5' -Destination "D:\MT5测试\MetaTrader 5\MQL5\Experts\backup_codex\SniperTrendEA_v8.6.$stamp.mq5"
```

Expected: a timestamped backup file exists under `D:\MT5测试\MetaTrader 5\MQL5\Experts\backup_codex`.

- [ ] **Step 2: Deploy the generated v8.6 source to MT5 Experts**

Run:

```powershell
Copy-Item -LiteralPath 'E:\CODEXMACD\SniperTrendEA_v8.6.mq5' -Destination 'D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.6.mq5' -Force
```

Expected: `D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.6.mq5` has the same length as `E:\CODEXMACD\SniperTrendEA_v8.6.mq5`.

- [ ] **Step 3: Compile the EA with MetaEditor**

Run:

```powershell
& 'D:\MT5测试\MetaTrader 5\MetaEditor64.exe' /compile:'D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.6.mq5' /log:'E:\CODEXMACD\SniperTrendEA_v8.6.compile.log'
```

Expected: `E:\CODEXMACD\SniperTrendEA_v8.6.compile.log` contains `0 error(s)`.

- [ ] **Step 4: Create the H4 2020-2025 tester config**

Create `D:\MT5测试\MetaTrader 5\Config\sniper_v86_h4_2020_2025.ini` with:

```ini
[Tester]
Expert=SniperTrendEA_v8.6
ExpertParameters=
Symbol=XAUUSD
Period=H4
Model=1
ExecutionMode=0
Optimization=0
FromDate=2020.01.01
ToDate=2025.12.31
ForwardMode=0
Deposit=10000
Currency=USD
Leverage=100
Report=SingleEAReports\sniper_v86_h4_2020_2025_codex\SniperTrendEA_v8.6_XAUUSD_H4_2020_2025
ReplaceReport=1
ShutdownTerminal=1
```

- [ ] **Step 5: Run the MT5 strategy tester**

Run:

```powershell
& 'D:\MT5测试\MetaTrader 5\terminal64.exe' /portable /config:'D:\MT5测试\MetaTrader 5\Config\sniper_v86_h4_2020_2025.ini'
```

Expected: MT5 exits after the test and writes an HTML report under `D:\MT5测试\MetaTrader 5\SingleEAReports\sniper_v86_h4_2020_2025_codex`.

- [ ] **Step 6: Verify the generated report**

Run:

```powershell
Get-ChildItem -LiteralPath 'D:\MT5测试\MetaTrader 5\SingleEAReports\sniper_v86_h4_2020_2025_codex' -Recurse | Select-Object FullName,Length,LastWriteTime
```

Expected: at least one `.htm` or `.html` report exists and has non-zero length.
