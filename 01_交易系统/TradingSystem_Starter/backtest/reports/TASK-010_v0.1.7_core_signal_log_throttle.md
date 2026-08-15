# TASK-010 Backtest Report - v0.1.7 Core / Signal Log Throttle

## 1. 基本信息

- Task: TASK-010
- EA Version: v0.1.7-core-signal-log-throttle
- EA Name: TradingSystem_v0.1.7_core_signal_log_throttle
- Commit: ecf8ab4 TASK-010 optimize core and signal logging
- Git Tag: v0.1.7-core-signal-log-throttle
- Symbol: XAUUSD
- Chart Timeframe: H1
- Signal Timeframe: PERIOD_M5
- Broker / Server: Not recorded
- Test Date: Not recorded
- Test Period: 2024.01.01 00:00 to 2025.04.30 00:00
- Test Model: Every tick
- Initial Deposit: 10000.00 USD
- Leverage: 1:100

## 2. 测试目标

验证 CORE New bar 日志和 SIGNAL Signal evaluated 日志节流是否生效，同时确认 RiskManager 仍然阻止交易，ExecutionManager 不执行订单。

## 3. 测试 A：默认 CORE / SIGNAL 日志节流

### Loaded Set File

backtest/sets/TASK-010_A_default_core_signal_throttle.set

### 输入参数摘要

- InpEaName=TradingSystem_v0.1.7_core_signal_log_throttle
- InpEnableTrading=false
- InpEnableNewBarLog=true
- InpPrintNewBarLog=true
- InpNewBarLogEveryN=1000
- InpPrintSignalLog=true
- InpPrintSignalLogOnlyOnDirectionChange=true
- InpSignalLogEveryN=1000
- InpPrintRuntimeSummary=true

### Runtime Summary

#### Core Log Stats

- totalNewBarLogEvents=94013
- printedNewBarLogs=95
- suppressedNewBarLogs=93918

#### Signal Log Stats

- totalSignalLogEvents=94013
- printedSignalLogs=1844
- suppressedSignalLogs=92169

#### Safety Counters

- riskApproved=0
- executionAttempts=0
- final balance=10000.00 USD

### 测试结论

- Passed / Failed: Passed
- 结论说明: 默认节流模式下，CORE / SIGNAL 日志没有每根 K 线刷屏，summary 统计仍然完整。

## 4. 测试 B：关闭 CORE / SIGNAL 单条日志

### Loaded Set File

backtest/sets/TASK-010_B_core_signal_logs_off.set

### 输入参数摘要

- InpEaName=TradingSystem_v0.1.7_core_signal_log_throttle
- InpEnableTrading=false
- InpEnableNewBarLog=false
- InpPrintNewBarLog=false
- InpNewBarLogEveryN=0
- InpPrintSignalLog=false
- InpSignalLogEveryN=0
- InpPrintRuntimeSummary=true

### Runtime Summary

#### Core Log Stats

- totalNewBarLogEvents=94013
- printedNewBarLogs=0
- suppressedNewBarLogs=94013

#### Signal Log Stats

- totalSignalLogEvents=94013
- printedSignalLogs=0
- suppressedSignalLogs=94013

#### Safety Counters

- riskApproved=0
- executionAttempts=0
- final balance=10000.00 USD

### 测试结论

- Passed / Failed: Passed
- 结论说明: 关闭 CORE / SIGNAL 单条日志后，日志明显减少，但 Runtime summary 仍保留完整统计。

## 5. 测试 C：verbose CORE / SIGNAL 日志

### Loaded Set File

backtest/sets/TASK-010_C_verbose_core_signal_logs.set

### 输入参数摘要

- InpEaName=TradingSystem_v0.1.7_core_signal_log_throttle
- InpEnableTrading=false
- InpEnableNewBarLog=true
- InpPrintNewBarLog=true
- InpNewBarLogEveryN=1
- InpPrintSignalLog=true
- InpPrintSignalLogOnlyOnDirectionChange=false
- InpSignalLogEveryN=1
- InpPrintRuntimeSummary=true

### Runtime Summary

#### Core Log Stats

- totalNewBarLogEvents=94013
- printedNewBarLogs=94013
- suppressedNewBarLogs=0

#### Signal Log Stats

- totalSignalLogEvents=94013
- printedSignalLogs=94013
- suppressedSignalLogs=0

#### Safety Counters

- riskApproved=0
- executionAttempts=0
- final balance=10000.00 USD

### 测试结论

- Passed / Failed: Passed
- 结论说明: Verbose 模式下，CORE / SIGNAL 单条日志恢复完整输出，适合短回测排查。

## 6. 安全结论

- 三组测试 riskApproved 均为 0。
- 三组测试 executionAttempts 均为 0。
- 三组测试 final balance 均保持 10000.00 USD。
- 未观察到订单。
- 未观察到持仓。
- 当前系统仍然不允许真实交易。
- EMA 信号仍然只是观察信号，不代表可实盘策略。

## 7. 发现的问题

- 测试报告目前仍依赖人工从 MT5 日志复制 Runtime summary。
- 后续可以考虑进一步自动化报告生成，但当前阶段先建立报告模板和手工结构化流程。
- C 组 verbose 模式日志非常多，只建议短时间排查使用。

## 8. 下一步建议

下一步建议进入：

TASK-DOC-009：更新项目状态，标记 TASK-011 已完成。

之后可以考虑：

TASK-012：回测报告自动化辅助脚本或日志解析工具。

但当前阶段仍然不进入真实交易。
