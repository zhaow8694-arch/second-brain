---
tags: [交易系统, EA]
date: 2026-06-20
---

# Omni Mature Regime Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the existing range, trend, and master EAs with mature non-grid filters: Bollinger Z-Score for range entries, overextension protection for trend entries, and stronger market-regime snapshot data.

**Architecture:** Keep the three EA entrypoints unchanged. Extend the shared market snapshot with Bollinger-derived values, then use those values in `RangeStrategy.mqh`, `TrendStrategy.mqh`, and existing static verification.

**Tech Stack:** MQL5, MetaEditor64 compiler, Python static verifier.

---

### Task 1: Verification Coverage

**Files:**
- Modify: `E:\ea代码库\tools\verify_omni_suite.py`

- [ ] Require `SOmniMarketSnapshot` fields `h1BandStdDev`, `h1ZScore`, and `h1BandWidthAtrRatio`.
- [ ] Require `MarketRegime.mqh` to compute Z-Score and band-width/ATR ratio.
- [ ] Require `RangeStrategy.mqh` to use Z-Score and minimum mean-reversion deviation.
- [ ] Require `TrendStrategy.mqh` to use RSI bands and overextension checks.

### Task 2: Market Snapshot Enhancements

**Files:**
- Modify: `E:\ea代码库\Experts\OmniFuturesSuite\Include\OmniTypes.mqh`
- Modify: `E:\ea代码库\Experts\OmniFuturesSuite\Include\MarketRegime.mqh`

- [ ] Add `h1BandStdDev`, `h1ZScore`, and `h1BandWidthAtrRatio`.
- [ ] Calculate standard deviation from Bollinger middle/upper/lower values.
- [ ] Treat unusually wide bands versus ATR as danger.

### Task 3: Strategy Filters

**Files:**
- Modify: `E:\ea代码库\Experts\OmniFuturesSuite\Include\RangeStrategy.mqh`
- Modify: `E:\ea代码库\Experts\OmniFuturesSuite\Include\TrendStrategy.mqh`

- [ ] Range entries must require Z-Score extremes in the expected direction.
- [ ] Trend entries must avoid overextended entries and require RSI to remain in a healthy trend band.

### Task 4: Compile And Verify

**Files:**
- Compile: `OmniRangeEngine.mq5`, `OmniTrendEngine.mq5`, `OmniRegimeMasterEngine.mq5`, `OmniStableDualEngine.mq5`, `OmniAggressiveHedgeEngine.mq5`

- [ ] Run static verification.
- [ ] Compile all affected EA files.
- [ ] Confirm every compile log reports `0 errors, 0 warnings`.
