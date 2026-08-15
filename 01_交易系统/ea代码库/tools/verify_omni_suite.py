from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "Experts" / "OmniFuturesSuite"
INCLUDE = BASE / "Include"


REQUIRED_FILES = [
    BASE / "OmniStableDualEngine.mq5",
    BASE / "OmniAggressiveHedgeEngine.mq5",
    BASE / "OmniRangeEngine.mq5",
    BASE / "OmniTrendEngine.mq5",
    BASE / "OmniRegimeMasterEngine.mq5",
    INCLUDE / "OmniTypes.mqh",
    INCLUDE / "AccountScale.mqh",
    INCLUDE / "SymbolResolver.mqh",
    INCLUDE / "SymbolProfile.mqh",
    INCLUDE / "NotificationCenter.mqh",
    INCLUDE / "RiskManager.mqh",
    INCLUDE / "TradeExecutor.mqh",
    INCLUDE / "MarketRegime.mqh",
    INCLUDE / "PositionManager.mqh",
    INCLUDE / "EntryGuard.mqh",
    INCLUDE / "StableStrategy.mqh",
    INCLUDE / "AggressiveStrategy.mqh",
    INCLUDE / "RangeStrategy.mqh",
    INCLUDE / "TrendStrategy.mqh",
]


REQUIRED_PATTERNS = {
    INCLUDE / "OmniTypes.mqh": [
        "enum ENUM_OMNI_PRODUCT",
        "enum ENUM_OMNI_ACCOUNT_SCALE",
        "struct SOmniSignal",
        "struct SOmniMarketSnapshot",
        "h1BandStdDev",
        "h1ZScore",
        "h1BandWidthAtrRatio",
    ],
    INCLUDE / "AccountScale.mqh": [
        "class COmniAccountScale",
        "EffectiveBalance",
        "ToBrokerMoney",
        "CENT_100X",
    ],
    INCLUDE / "SymbolResolver.mqh": [
        "class COmniSymbolResolver",
        "ResolveAll",
        "AllowsAutoFallback",
        'Upper(inputSymbol) == "AUTO"',
        "CandidateMatches(product, _Symbol)",
        "XAUUSD",
        "USOIL",
    ],
    INCLUDE / "RiskManager.mqh": [
        "class COmniRiskManager",
        "OrderCalcProfit",
        "CanOpen",
        "CalculateVolume",
    ],
    INCLUDE / "TradeExecutor.mqh": [
        "class COmniTradeExecutor",
        "SetExpertMagicNumber",
        "PositionClosePartial",
        "OpenMarket",
    ],
    INCLUDE / "MarketRegime.mqh": [
        "class COmniMarketRegime",
        "iBands",
        "PERIOD_H4",
        "PERIOD_H1",
        "h1BandStdDev",
        "h1ZScore",
        "h1BandWidthAtrRatio",
        "MathAbs(snapshot.h1ZScore)",
    ],
    INCLUDE / "PositionManager.mqh": [
        "class COmniPositionManager",
        "GlobalVariableSet",
        "Friday",
        "Manage",
    ],
    INCLUDE / "EntryGuard.mqh": [
        "class COmniEntryGuard",
        "ShouldBlockAllNewEntries",
        "ShouldBlockRangeNewEntry",
        "AllowInitialEntry",
        "MarkInitialEntry",
    ],
    INCLUDE / "StableStrategy.mqh": [
        "class COmniStableStrategy",
        "BuildSignal",
        "OMNI_REGIME_RANGE",
    ],
    INCLUDE / "AggressiveStrategy.mqh": [
        "class COmniAggressiveStrategy",
        "BuildSignal",
        "OMNI_SIGNAL_HEDGE",
        "allowAddOn",
    ],
    INCLUDE / "RangeStrategy.mqh": [
        "class COmniRangeStrategy",
        "BuildSignal",
        "OMNI_REGIME_RANGE",
        "h1BandLower",
        "h1BandUpper",
        "h1Rsi",
        "minMeanReversionZScore",
        "snapshot.h1ZScore",
        "OmniRange RANGE",
    ],
    INCLUDE / "TrendStrategy.mqh": [
        "class COmniTrendStrategy",
        "BuildSignal",
        "OMNI_REGIME_TREND_UP",
        "OMNI_REGIME_TREND_DOWN",
        "h1FastEma",
        "h1SlowEma",
        "maxTrendEntryZScore",
        "snapshot.h1ZScore",
        "snapshot.h1Rsi",
        "OmniTrend TREND",
    ],
    BASE / "OmniStableDualEngine.mq5": [
        'input bool   InpEnableTrading = true',
        '#include "Include/EntryGuard.mqh"',
        "COmniEntryGuard g_entryGuard",
        "ShouldBlockAllNewEntries",
        "ShouldBlockRangeNewEntry",
        "AllowInitialEntry",
        "MarkInitialEntry",
        "COmniStableStrategy",
        "OnTimer",
        "XAUUSD.c",
    ],
    BASE / "OmniAggressiveHedgeEngine.mq5": [
        'input bool   InpEnableTrading = true',
        '#include "Include/EntryGuard.mqh"',
        "COmniEntryGuard g_entryGuard",
        "ShouldBlockAllNewEntries",
        "ShouldBlockRangeNewEntry",
        "AllowInitialEntry",
        "MarkInitialEntry",
        "COmniAggressiveStrategy",
        "InpEnableProtectiveHedge",
        "OnTimer",
    ],
    BASE / "OmniRangeEngine.mq5": [
        'input bool   InpEnableTrading = true',
        '#include "Include/RangeStrategy.mqh"',
        "COmniRangeStrategy g_strategy",
        "ShouldBlockRangeNewEntry",
        "AllowInitialEntry",
        "OmniRangeEngine",
        "OnTimer",
    ],
    BASE / "OmniTrendEngine.mq5": [
        'input bool   InpEnableTrading = true',
        '#include "Include/TrendStrategy.mqh"',
        "COmniTrendStrategy g_strategy",
        "AllowInitialEntry",
        "OmniTrendEngine",
        "OnTimer",
    ],
    BASE / "OmniRegimeMasterEngine.mq5": [
        'input bool   InpEnableTrading = true',
        '#include "Include/RangeStrategy.mqh"',
        '#include "Include/TrendStrategy.mqh"',
        "COmniRangeStrategy g_rangeStrategy",
        "COmniTrendStrategy g_trendStrategy",
        "snapshot.regime == OMNI_REGIME_RANGE",
        "snapshot.regime == OMNI_REGIME_TREND_UP",
        "snapshot.regime == OMNI_REGIME_TREND_DOWN",
        "OmniRegimeMasterEngine",
        "OnTimer",
    ],
}


FORBIDDEN_PATTERNS = ["TODO", "TBD", "implement later", "PLACEHOLDER"]


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8")


def main() -> int:
    failures = []

    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"missing file: {path.relative_to(ROOT)}")

    for path, patterns in REQUIRED_PATTERNS.items():
        if not path.exists():
            continue
        text = read_text(path)
        for pattern in patterns:
            if pattern not in text:
                failures.append(f"missing pattern {pattern!r} in {path.relative_to(ROOT)}")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in text.lower():
                failures.append(f"forbidden pattern {pattern!r} in {path.relative_to(ROOT)}")

    if failures:
        print("Omni suite verification failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("Omni suite static verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
