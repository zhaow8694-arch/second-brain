---
tags: [交易系统, EA]
date: 2026-06-20
---

# Omni Futures Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two MT5 Expert Advisors for XAUUSD, SPX500, A50, and USOIL: a stable dual-engine version and an aggressive hedge version.

**Architecture:** Use two entry `.mq5` files with shared `.mqh` modules under `Experts/OmniFuturesSuite/Include`. Shared modules handle account scaling, symbol resolution, profiles, risk, execution, market state, notifications, and position management. Strategy modules differ for stable and aggressive behavior while reusing the same safety layer.

**Tech Stack:** MQL5, MT5 Standard Library `Trade/Trade.mqh`, `Trade/PositionInfo.mqh`, MetaEditor64 compiler.

---

## File Structure

- Create: `Experts/OmniFuturesSuite/OmniStableDualEngine.mq5`
  Stable EA entry point, stable defaults, lifecycle handlers.
- Create: `Experts/OmniFuturesSuite/OmniAggressiveHedgeEngine.mq5`
  Aggressive EA entry point, aggressive defaults, lifecycle handlers.
- Create: `Experts/OmniFuturesSuite/Include/OmniTypes.mqh`
  Shared enums, constants, signal/result structs, symbol state structs.
- Create: `Experts/OmniFuturesSuite/Include/AccountScale.mqh`
  Standard/cent account detection and effective balance conversion.
- Create: `Experts/OmniFuturesSuite/Include/SymbolResolver.mqh`
  Resolve four logical products to broker symbols, including `.c` suffix symbols.
- Create: `Experts/OmniFuturesSuite/Include/SymbolProfile.mqh`
  Product-specific default risk and filter profiles.
- Create: `Experts/OmniFuturesSuite/Include/NotificationCenter.mqh`
  Print and `SendNotification()` wrapper with throttling.
- Create: `Experts/OmniFuturesSuite/Include/RiskManager.mqh`
  Account drawdown, daily loss, exposure limits, adaptive risk, lot sizing via `OrderCalcProfit()`.
- Create: `Experts/OmniFuturesSuite/Include/TradeExecutor.mqh`
  Market orders, SL/TP modification, partial close, close-by-symbol.
- Create: `Experts/OmniFuturesSuite/Include/MarketRegime.mqh`
  H4/H1 indicator handles, state calculation, signal data snapshot.
- Create: `Experts/OmniFuturesSuite/Include/PositionManager.mqh`
  Breakeven, trailing stop, partial close tracking, overnight/range/weekend exits.
- Create: `Experts/OmniFuturesSuite/Include/StableStrategy.mqh`
  Stable dual-engine signal generation and priority scoring.
- Create: `Experts/OmniFuturesSuite/Include/AggressiveStrategy.mqh`
  Aggressive signal generation, trend add-on logic, protective hedge signal logic.
- Verify: compile both EA entry files with `C:\Program Files\MetaTrader 5\MetaEditor64.exe`.

---

### Task 1: Create Shared Types

**Files:**
- Create: `Experts/OmniFuturesSuite/Include/OmniTypes.mqh`

- [ ] **Step 1: Create enums and structs**

Create include guard `OMNI_TYPES_MQH`. Define:

```cpp
enum ENUM_OMNI_PRODUCT { OMNI_GOLD=0, OMNI_SPX500=1, OMNI_A50=2, OMNI_USOIL=3 };
enum ENUM_OMNI_ACCOUNT_SCALE { OMNI_SCALE_AUTO=0, OMNI_SCALE_STANDARD=1, OMNI_SCALE_CENT_100X_BALANCE=2, OMNI_SCALE_CUSTOM=3 };
enum ENUM_OMNI_REGIME { OMNI_REGIME_UNKNOWN=0, OMNI_REGIME_TREND_UP=1, OMNI_REGIME_TREND_DOWN=2, OMNI_REGIME_RANGE=3, OMNI_REGIME_DANGER=4 };
enum ENUM_OMNI_SIGNAL { OMNI_SIGNAL_NONE=0, OMNI_SIGNAL_BUY=1, OMNI_SIGNAL_SELL=-1, OMNI_SIGNAL_CLOSE=2, OMNI_SIGNAL_HEDGE_BUY=3, OMNI_SIGNAL_HEDGE_SELL=-3 };
```

Define `SOmniProfile`, `SOmniSymbol`, `SOmniMarketSnapshot`, `SOmniSignal`, and `SOmniRiskDecision` with explicit fields for symbol, product, risk, stops, confidence, and reason strings.

- [ ] **Step 2: Static check**

Run:

```powershell
Select-String -Path 'Experts\OmniFuturesSuite\Include\OmniTypes.mqh' -Pattern 'enum ENUM_OMNI_PRODUCT','struct SOmniSignal'
```

Expected: both patterns appear once.

### Task 2: Create Account Scaling

**Files:**
- Create: `Experts/OmniFuturesSuite/Include/AccountScale.mqh`

- [ ] **Step 1: Implement `COmniAccountScale`**

Create a class with:

- `bool Init(ENUM_OMNI_ACCOUNT_SCALE mode, double customScale)`
- `double EffectiveBalance()`
- `double EffectiveEquity()`
- `double ToBrokerMoney(double effectiveMoney)`
- `double FromBrokerMoney(double brokerMoney)`
- `string Summary()`

AUTO mode detects `USC`, `CENT`, and balances that look 100x scaled. Custom scale clamps to `>= 1.0`.

- [ ] **Step 2: Static check**

Run:

```powershell
Select-String -Path 'Experts\OmniFuturesSuite\Include\AccountScale.mqh' -Pattern 'class COmniAccountScale','EffectiveBalance','ToBrokerMoney'
```

Expected: all patterns appear.

### Task 3: Create Symbol Resolution And Profiles

**Files:**
- Create: `Experts/OmniFuturesSuite/Include/SymbolResolver.mqh`
- Create: `Experts/OmniFuturesSuite/Include/SymbolProfile.mqh`

- [ ] **Step 1: Implement symbol resolver**

`COmniSymbolResolver` resolves four products from default inputs and candidate keywords. It first tries exact input symbols, then scans `SymbolsTotal(false)`, then `SymbolsTotal(true)`. It calls `SymbolSelect(symbol, true)` before accepting a symbol.

- [ ] **Step 2: Implement profiles**

`BuildOmniProfile(product)` returns tuned defaults:

- Gold: wider ATR filters, max spread 350 points, trend focus.
- SPX500: lower range aggression, max spread 300 points.
- A50: strict signal confidence, max spread 400 points.
- USOIL: strong danger ATR filter, max spread 350 points.

- [ ] **Step 3: Static check**

Run:

```powershell
Select-String -Path 'Experts\OmniFuturesSuite\Include\SymbolResolver.mqh','Experts\OmniFuturesSuite\Include\SymbolProfile.mqh' -Pattern 'ResolveAll','BuildOmniProfile','XAUUSD','USOIL'
```

Expected: all patterns appear.

### Task 4: Create Notification, Risk, And Execution Modules

**Files:**
- Create: `Experts/OmniFuturesSuite/Include/NotificationCenter.mqh`
- Create: `Experts/OmniFuturesSuite/Include/RiskManager.mqh`
- Create: `Experts/OmniFuturesSuite/Include/TradeExecutor.mqh`

- [ ] **Step 1: Implement notifications**

`COmniNotificationCenter` exposes `Info`, `Warn`, `Trade`, and `Daily`. It always prints, and only calls `SendNotification()` when push is enabled.

- [ ] **Step 2: Implement risk manager**

`COmniRiskManager` checks daily drawdown, total drawdown, spread, active product limits, max positions, account trade permissions, and lot sizing. Lot sizing must use `OrderCalcProfit()` with 1 lot at entry/SL to estimate real loss.

- [ ] **Step 3: Implement trade executor**

`COmniTradeExecutor` wraps `CTrade` with methods `OpenMarket`, `ModifyStops`, `ClosePositionTicket`, `ClosePartialTicket`, `CloseSymbolPositions`, and `CountPositions`.

- [ ] **Step 4: Static check**

Run:

```powershell
Select-String -Path 'Experts\OmniFuturesSuite\Include\RiskManager.mqh','Experts\OmniFuturesSuite\Include\TradeExecutor.mqh' -Pattern 'OrderCalcProfit','PositionClosePartial','SetExpertMagicNumber'
```

Expected: all patterns appear.

### Task 5: Create Market And Position Management

**Files:**
- Create: `Experts/OmniFuturesSuite/Include/MarketRegime.mqh`
- Create: `Experts/OmniFuturesSuite/Include/PositionManager.mqh`

- [ ] **Step 1: Implement market context**

`COmniMarketRegime` creates H4/H1 handles for EMA fast, EMA slow, ADX, ATR, RSI, and Bollinger Bands. It exposes `Refresh(snapshot)` and releases handles on deinit.

- [ ] **Step 2: Implement position manager**

`COmniPositionManager` handles breakeven, trailing stops, partial close once per ticket via global variables, range forced close, and Friday close.

- [ ] **Step 3: Static check**

Run:

```powershell
Select-String -Path 'Experts\OmniFuturesSuite\Include\MarketRegime.mqh','Experts\OmniFuturesSuite\Include\PositionManager.mqh' -Pattern 'iBands','GlobalVariableSet','Friday'
```

Expected: all patterns appear.

### Task 6: Create Stable Strategy And Entry EA

**Files:**
- Create: `Experts/OmniFuturesSuite/Include/StableStrategy.mqh`
- Create: `Experts/OmniFuturesSuite/OmniStableDualEngine.mq5`

- [ ] **Step 1: Implement stable strategy**

`COmniStableStrategy` generates signals:

- trend buy/sell from H4 direction plus H1 confirmation;
- range buy/sell from Bollinger edge plus RSI;
- confidence score from trend strength, spread safety, ATR normality, and product profile.

- [ ] **Step 2: Implement stable entry**

Entry EA declares stable inputs with `InpEnableTrading=true`, stable magic number, four default `.c` symbols, account scale, Friday/range close times, and stable drawdown limits.

- [ ] **Step 3: Static check**

Run:

```powershell
Select-String -Path 'Experts\OmniFuturesSuite\OmniStableDualEngine.mq5','Experts\OmniFuturesSuite\Include\StableStrategy.mqh' -Pattern 'InpEnableTrading = true','COmniStableStrategy','OnTimer'
```

Expected: all patterns appear.

### Task 7: Create Aggressive Strategy And Entry EA

**Files:**
- Create: `Experts/OmniFuturesSuite/Include/AggressiveStrategy.mqh`
- Create: `Experts/OmniFuturesSuite/OmniAggressiveHedgeEngine.mq5`

- [ ] **Step 1: Implement aggressive strategy**

`COmniAggressiveStrategy` generates initial signals, trend add-on signals, and protective hedge signals. It must not add to losing positions in the same direction. It only adds when floating profit and ATR distance thresholds are met.

- [ ] **Step 2: Implement aggressive entry**

Entry EA declares aggressive inputs with `InpEnableTrading=true`, aggressive magic number, max add-on layers, max hedge layers, 50% hard drawdown, 8%-10% daily loss cap, and hedge enabled for hedging accounts only.

- [ ] **Step 3: Static check**

Run:

```powershell
Select-String -Path 'Experts\OmniFuturesSuite\OmniAggressiveHedgeEngine.mq5','Experts\OmniFuturesSuite\Include\AggressiveStrategy.mqh' -Pattern 'InpEnableTrading = true','InpEnableProtectiveHedge','OMNI_SIGNAL_HEDGE'
```

Expected: all patterns appear.

### Task 8: Compile And Verify

**Files:**
- Verify: `Experts/OmniFuturesSuite/OmniStableDualEngine.mq5`
- Verify: `Experts/OmniFuturesSuite/OmniAggressiveHedgeEngine.mq5`

- [ ] **Step 1: Compile stable EA**

Run:

```powershell
& 'C:\Program Files\MetaTrader 5\MetaEditor64.exe' /compile:'E:\ea代码库\Experts\OmniFuturesSuite\OmniStableDualEngine.mq5' /log:'E:\ea代码库\Experts\OmniFuturesSuite\stable-compile.log'
```

Expected: compile log contains no `error`.

- [ ] **Step 2: Compile aggressive EA**

Run:

```powershell
& 'C:\Program Files\MetaTrader 5\MetaEditor64.exe' /compile:'E:\ea代码库\Experts\OmniFuturesSuite\OmniAggressiveHedgeEngine.mq5' /log:'E:\ea代码库\Experts\OmniFuturesSuite\aggressive-compile.log'
```

Expected: compile log contains no `error`.

- [ ] **Step 3: Verify output files**

Run:

```powershell
Get-ChildItem -LiteralPath 'Experts\OmniFuturesSuite' -Filter '*.ex5'
```

Expected: both `OmniStableDualEngine.ex5` and `OmniAggressiveHedgeEngine.ex5` exist.

## Self-Review

- Spec coverage: two EA entries, four product support, cent accounts, hedging accounts, adaptive sizing, notifications, stable/aggressive strategy differences, Friday/range exits, compile verification are covered.
- Placeholder scan: no `TBD`, no `TODO`, no "implement later".
- Type consistency: all shared types use `OMNI_` prefixes and strategy classes use `COmni` prefixes.
