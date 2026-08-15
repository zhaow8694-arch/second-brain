# Backtest Report Template

## 1. 基本信息

- Task:
- EA Version:
- Commit:
- Git Tag:
- Symbol:
- Chart Timeframe:
- Signal Timeframe:
- Broker / Server:
- Test Date:
- Test Period:
- Test Model:
- Initial Deposit:
- Leverage:
- Loaded Set File:

## 2. 测试目标

说明本次测试要验证什么。

## 3. 输入参数摘要

至少包含：

- InpEaName:
- InpEnableTrading:
- InpEnableEmaSignal:
- InpEnableRiskObservation:
- InpPrintRuntimeSummary:
- 其他关键参数:

## 4. Runtime Summary

### Counters

- totalTicks:
- newBarsDetected:
- signalsEvaluated:
- riskRejected:
- riskApproved:
- executionAttempts:

### Signal Stats

- buySignals:
- sellSignals:
- noneSignals:
- signalDirectionChanges:
- previousSignalDirection:
- lastSignalDirection:
- consecutiveSameDirectionSignals:
- maxConsecutiveSameDirectionSignals:

### Risk Stats

- riskRejectSignalNone:
- riskRejectTradingDisabled:
- riskRejectInvalidPrice:
- riskRejectSpreadTooHigh:
- riskRejectTimeBlocked:
- riskRejectMaxPositions:
- riskRejectObservationMode:

### Risk Log Stats

- totalRiskRejects:
- printedRiskRejectLogs:
- suppressedRiskRejectLogs:

### Core Log Stats

- totalNewBarLogEvents:
- printedNewBarLogs:
- suppressedNewBarLogs:

### Signal Log Stats

- totalSignalLogEvents:
- printedSignalLogs:
- suppressedSignalLogs:

## 5. 安全检查

- riskApproved == 0:
- executionAttempts == 0:
- final balance unchanged:
- orders created:
- positions opened:
- real trading calls observed:

## 6. 测试结论

- Passed / Failed:
- 结论说明:

## 7. 发现的问题

记录发现的问题或待优化点。

## 8. 下一步建议

记录下一步建议。
