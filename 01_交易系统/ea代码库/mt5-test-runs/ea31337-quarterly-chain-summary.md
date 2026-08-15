# EA31337 Lite XAUUSD H1-only quarterly chain summary

- EA: EA31337-Lite-v2.013.1
- Symbol/timeframe: XAUUSD / H1
- Test period: 2020.01.01 - 2021.12.31, split into 8 quarters
- Strategy inputs: Strategy_H1=17, all other Strategy_* timeframes disabled, EA_LotSize=0, Model=1
- Chain method: next quarter used previous quarter ending balance as intended deposit; MT5 reports rounded/truncated deposits to whole dollars

## Aggregate

- Initial deposit: 10000.00
- Total net profit by summing quarters: 621.35
- Ending balance by summed net profit: 10621.35
- Last quarter report ending balance: 10621.00
- Deposit rounding gap from quarterly restarts: -0.35
- Aggregate gross profit / gross loss: 1084.28 / -462.93
- Aggregate profit factor: 2.34
- Total trades: 279
- Profit trades / loss trades: 101 / 178
- Win rate: 36.20%
- Max quarterly equity drawdown: 434.85 (4.08%) in 2020Q2
- Active quarters: 2020Q1, 2020Q2, 2021Q2, 2021Q3
- Zero-trade quarters: 2020Q3, 2020Q4, 2021Q1, 2021Q4

## Quarterly Results

| Quarter | Report initial | Net profit | Report ending | PF | Trades | Win trades | Max equity DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020Q1 | 10000.00 | 605.93 | 10605.93 | 11.78 | 84 | 23 (27.38%) | 372.08 (3.53%) |
| 2020Q2 | 10605.00 | 136.90 | 10741.90 | 2.76 | 66 | 30 (45.45%) | 434.85 (4.08%) |
| 2020Q3 | 10742.00 | 0.00 | 10742.00 | 0.00 | 0 | 0 (0.00%) | 0.00 (0.00%) |
| 2020Q4 | 10742.00 | 0.00 | 10742.00 | 0.00 | 0 | 0 (0.00%) | 0.00 (0.00%) |
| 2021Q1 | 10742.00 | 0.00 | 10742.00 | 0.00 | 0 | 0 (0.00%) | 0.00 (0.00%) |
| 2021Q2 | 10742.00 | -117.65 | 10624.35 | 0.59 | 103 | 33 (32.04%) | 118.71 (1.11%) |
| 2021Q3 | 10625.00 | -3.83 | 10621.17 | 0.92 | 26 | 15 (57.69%) | 29.82 (0.28%) |
| 2021Q4 | 10621.00 | 0.00 | 10621.00 | 0.00 | 0 | 0 (0.00%) | 0.00 (0.00%) |

## Notes

- This is not mathematically identical to one continuous 2020-2021 backtest, because quarterly restarts do not carry open positions, indicator warm-up state, or EA internal state across quarter boundaries.
- It is closer than testing every quarter with the same fixed initial deposit, because each segment attempts to carry balance forward.
- MT5 rounded/truncated decimal deposits in reports, so the final report balance differs slightly from summed net profit.
