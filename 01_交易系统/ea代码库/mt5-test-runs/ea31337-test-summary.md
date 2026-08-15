# EA31337 Local Test Summary

MT5 root: `D:\MT5测试\MetaTrader 5`

Source copy: `D:\MT5测试\MetaTrader 5\MQL5\Experts\EA31337`

Official release binaries: `D:\MT5测试\MetaTrader 5\MQL5\Experts\EA31337_release`

## Compile Check

Compiled source file:

`D:\MT5测试\MetaTrader 5\MQL5\Experts\EA31337\src\EA31337.mq5`

Result:

`Result: 100 errors, 60 warnings`

Log:

`E:\ea代码库\mt5-test-runs\compile-logs-d-mt5\EA31337-Lite-D.log`

Finding:

The source includes resolve correctly. Errors are concentrated in EA31337's class library (`DateTime`, `Dict`, `Order` structures), which points to source/compiler incompatibility with local MetaEditor build 5836. The upstream Makefile references MetaTrader `5.0.0.2361`, but the MT-Platforms repository used by the Makefile is blocked on GitHub, so this local environment cannot easily reproduce the upstream compiler.

## Official Ex5 Test

Downloaded official stable release `v2.013.1`:

| File | Size |
| --- | ---: |
| `EA31337-Lite-v2.013.1.ex5` | 2,146,348 |
| `EA31337-Advanced-v2.013.1.ex5` | 2,267,222 |
| `EA31337-Rider-v2.013.1.ex5` | 2,207,714 |

## Smoke Tests

| Test | Model | Period | Result |
| --- | ---: | --- | --- |
| Lite default smoke | 0 | 2020.01.01 - 2020.01.03 | Report generated; 0 trades |
| Lite model 1 smoke | 1 | 2020.01.01 - 2020.01.03 | Report generated; 18 bars, 4290 ticks |
| Lite model 2 full | 2 | 2020.01.01 - 2021.12.31 | Invalid for ranking; report has 0 bars and 0 ticks |
| Lite model 3 smoke | 3 | 2020.01.01 - 2020.01.03 | Invalid for ranking; 0 bars and 0 ticks |
| Lite model 4 smoke | 4 | 2020.01.01 - 2020.01.03 | Report generated; 18 bars, 82063 ticks |

## Completed Diagnostic Backtest

EA: `EA31337-Lite-v2.013.1.ex5`

Mode: H1-only diagnostic (`Strategy_H1=17`, all other strategy timeframes disabled)

Model: `1`

Period: `2020.01.01 - 2020.03.31`

Report:

`D:\MT5测试\MetaTrader 5\BatchReports\EA31337_Lite_MODEL1_H1ONLY_Q1_2020_XAUUSD_H1.htm`

| Metric | Value |
| --- | ---: |
| Net profit | 605.93 |
| Profit factor | 11.78 |
| Total trades | 84 |
| Sell trades | 4 (25.00%) |
| Buy trades | 80 (27.50%) |
| Profit trades | 23 (27.38%) |
| Max equity drawdown | 372.08 (3.53%) |
| Bars | 1421 |
| Ticks | 337663 |

## Timeouts

These runs were stopped because they exceeded the practical local test window:

| Test | Limit | Outcome |
| --- | ---: | --- |
| Lite default, Model 0, 2020-2021 | 20 min | Timed out |
| Lite default, Model 1, 2020-2021 | 10 min | Timed out |
| Lite default, Model 1, Q1 2020 | 15 min | Timed out |
| Lite H1-only, Model 1, 2020-2021 | 32 min | Stopped, no report |

## Current Conclusion

EA31337 is a serious EA framework, but it is too heavy to run broad two-year XAUUSD tests with default multi-timeframe settings on this local MT5 setup. The official `Lite` binary can run, and an H1-only diagnostic for Q1 2020 was profitable, but a full 2020-2021 report was not completed.

Recommended next step:

Run quarterly H1-only segments and aggregate the reports, or optimize a smaller EA31337 strategy subset for XAUUSD before attempting full-period tick testing.

