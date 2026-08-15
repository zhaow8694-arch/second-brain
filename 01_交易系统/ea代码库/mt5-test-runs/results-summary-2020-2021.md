# Gold/XAUUSD EA Backtest And Diagnosis Summary

MT5 root: `D:\MT5测试\MetaTrader 5`

Date range: `2020.01.01 - 2021.12.31`

Symbol: `XAUUSD`

Deposit: `10,000 USD`

Leverage: `1:100`

Important correction: the three repositories were selected by GitHub popularity/stars, not by audited profitability ranking. GitHub does not provide a reliable "highest win-rate EA" ranking.

## Compile Results

| EA | Compile result | Notes |
| --- | --- | --- |
| GOLD_ORB | 0 errors, 18 warnings | Local compatibility fixes plus risk-management brace fix. |
| EA_SCALPER_XAUUSD | 0 errors, 1 warning | Public study/demo snapshot; ML is disabled by default. |
| GoldTraderEA | 0 errors, 0 warnings | Fixed MQL5 `iMA()` handle/value bug in main trend filter. |

## Original Backtest Results

| EA | Period | Net profit | Profit factor | Trades | Win rate | Max equity drawdown | Report |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| GOLD_ORB | H1 | 0.00 | 0.00 | 0 | 0.00% | 0.00 (0.00%) | `D:\MT5测试\MetaTrader 5\BatchReports\CodexGoldEA_01_GOLD_ORB_2020_2021.htm` |
| EA_SCALPER_XAUUSD | M5 | -33.85 | 0.29 | 3 | 66.67% | 101.17 (1.01%) | `D:\MT5测试\MetaTrader 5\BatchReports\CodexGoldEA_02_EA_SCALPER_XAUUSD_2020_2021.htm` |
| GoldTraderEA | H1 | -2,706.20 | 0.85 | 263 | 32.32% | 5,089.96 (41.83%) | `D:\MT5测试\MetaTrader 5\BatchReports\CodexGoldEA_03_GoldTraderEA_2020_2021.htm` |

## Diagnostic Backtest Results

| EA / Variant | Net profit | Profit factor | Trades | Sell trades | Buy trades | Win rate | Max equity drawdown | Report |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| GOLD_ORB fixed, source defaults | -1,825.50 | 0.00 | 2 | 1 (0.00%) | 1 (0.00%) | 0.00% | 2,658.00 (24.54%) | `D:\MT5测试\MetaTrader 5\BatchReports\CodexGoldEA_01_GOLD_ORB_FIXED_2020_2021.htm` |
| GOLD_ORB fixed, author `default_input.set` | -9,983.06 | 0.91 | 585 | 281 (32.38%) | 304 (30.26%) | 31.28% | 19,926.19 (99.93%) | `D:\MT5测试\MetaTrader 5\BatchReports\CodexGoldEA_01_GOLD_ORB_FIXED_AUTHORSET_2020_2021.htm` |
| GoldTraderEA fixed | -1,351.78 | 0.96 | 441 | 192 (32.81%) | 249 (33.33%) | 33.11% | 4,074.74 (32.31%) | `D:\MT5测试\MetaTrader 5\BatchReports\CodexGoldEA_03_GoldTraderEA_FIXED_2020_2021.htm` |

## Root Causes Found

1. GOLD_ORB had a missing-braces bug in `RiskManagementModule()`. With `MaxEquityDrawdownPercent != 0`, `execute_trade = false` ran every tick, so real orders were suppressed. This explains the original 0-trade report.
2. GOLD_ORB also has an author `.set` file that sets `MaxEquityDrawdownPercent=0.0`. The first run did not explicitly load that file. Loading it restores trade count, but the 2020-2021 result is still poor and nearly wipes out the account on MetaQuotes-Demo data.
3. GoldTraderEA used `iMA()` as if it returned an MA price. In MQL5 it returns an indicator handle. That made `current_close > ma_main_trend` almost always true and `current_close < ma_main_trend` almost always false, which explains the original 263 buys and 0 sells.
4. EA_SCALPER_XAUUSD README says the public repository is a study/demo snapshot and does not include proprietary rules, parameters, or go-live wiring. Its default gates generated only 3 trades in 2020-2021, so the result is not a meaningful performance sample.

## Files Changed

| File | Reason |
| --- | --- |
| `github-gold-ea-top3\01-GOLD_ORB\GOLD_ORB\GOLD_ORB.mq5` | Fixed missing braces around drawdown-stop condition. |
| `D:\MT5测试\MetaTrader 5\MQL5\Experts\CodexGoldEA_GitTop3\GOLD_ORB\GOLD_ORB.mq5` | Same fix in MT5 test copy. |
| `github-gold-ea-top3\03-GoldTraderEA\GoldTraderEA.mq5` | Replaced `iMA()` handle comparison with copied `ma_200[0]` value. |
| `D:\MT5测试\MetaTrader 5\MQL5\Experts\CodexGoldEA_GitTop3\GoldTraderEA\GoldTraderEA.mq5` | Same fix in MT5 test copy. |

