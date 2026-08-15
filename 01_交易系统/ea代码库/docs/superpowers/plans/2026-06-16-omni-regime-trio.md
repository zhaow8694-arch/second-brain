---
tags: [交易系统, EA]
date: 2026-06-20
---

# Omni Regime Trio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three MT5 EA programs: one range-only EA, one trend-only EA, and one master EA that selects range or trend logic from the current market regime.

**Architecture:** Reuse the existing OmniFuturesSuite shared modules for symbols, market regime detection, risk, execution, position management, and entry guarding. Add two focused strategy modules, then wire three EA entrypoints around them.

**Tech Stack:** MQL5, MetaEditor64 compiler, existing Python static verifier.

---

### Task 1: Static Verification Rules

**Files:**
- Modify: `E:\ea代码库\tools\verify_omni_suite.py`

- [ ] Add required files for `OmniRangeEngine.mq5`, `OmniTrendEngine.mq5`, `OmniRegimeMasterEngine.mq5`, `RangeStrategy.mqh`, and `TrendStrategy.mqh`.
- [ ] Add required patterns proving the master EA branches on `OMNI_REGIME_RANGE`, `OMNI_REGIME_TREND_UP`, and `OMNI_REGIME_TREND_DOWN`.
- [ ] Run `python tools/verify_omni_suite.py` and confirm it fails before the new files exist.

### Task 2: Strategy Modules

**Files:**
- Create: `E:\ea代码库\Experts\OmniFuturesSuite\Include\RangeStrategy.mqh`
- Create: `E:\ea代码库\Experts\OmniFuturesSuite\Include\TrendStrategy.mqh`

- [ ] Implement `COmniRangeStrategy::BuildSignal()` so it only emits signals during `OMNI_REGIME_RANGE`.
- [ ] Implement `COmniTrendStrategy::BuildSignal()` so it only emits signals during `OMNI_REGIME_TREND_UP` or `OMNI_REGIME_TREND_DOWN`.
- [ ] Use existing `SOmniSignal`, `SOmniProfile`, and `SOmniMarketSnapshot` structures.

### Task 3: EA Entrypoints

**Files:**
- Create: `E:\ea代码库\Experts\OmniFuturesSuite\OmniRangeEngine.mq5`
- Create: `E:\ea代码库\Experts\OmniFuturesSuite\OmniTrendEngine.mq5`
- Create: `E:\ea代码库\Experts\OmniFuturesSuite\OmniRegimeMasterEngine.mq5`

- [ ] Wire each EA to the shared account, symbol, market, risk, trade, position, and entry guard modules.
- [ ] `OmniRangeEngine` must only call `COmniRangeStrategy`.
- [ ] `OmniTrendEngine` must only call `COmniTrendStrategy`.
- [ ] `OmniRegimeMasterEngine` must choose range or trend strategy from `snapshot.regime`.

### Task 4: Compile And Verify

**Files:**
- Compile outputs: `E:\ea代码库\Experts\OmniFuturesSuite\*.ex5`

- [ ] Run the static verifier and confirm it passes.
- [ ] Compile all three new `.mq5` files with MetaEditor64.
- [ ] Confirm each compile log reports `Result: 0 errors, 0 warnings`.
