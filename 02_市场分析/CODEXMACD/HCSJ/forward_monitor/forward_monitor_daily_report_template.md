# 交易监控期标准日报表模板（v8.67 demo/forward）

> 目的：在不改 EA 核心的前提下，统一每日监控记录，兼顾可审计性与自动化识别。

## 1. 日志文件与更新频率

- 文件：`forward_test_daily_equity.csv`
- 更新频率：每个交易日 1 次（每天收盘后）
- 记录原则：只记录真实值，不补齐、不估算

## 2. CSV 标准列（固定不变）

```text
date,account_type,balance,equity,margin,free_margin,open_positions,daily_profit,daily_drawdown_pct,max_intraday_drawdown_pct,notes
```

## 3. 记录规则

| 列名 | 说明 | 计算要求 |
|---|---|---|
| date | 日期（`YYYY-MM-DD`） | 交易日日期 |
| account_type | account/demo/forward | 固定值 |
| balance | 账户余额 | 账号中 Balance 真实值 |
| equity | 当前净值 | 账号中 Equity 真实值 |
| margin | 已用保证金 | 账号中 Margin 使用量 |
| free_margin | 可用保证金 | 账号中 Free Margin |
| open_positions | 当前持仓手数/单数 | 该时点持仓数量 |
| daily_profit | 当日已实现盈亏 | 当日净 realized P/L |
| daily_drawdown_pct | 当日回撤（对余额） | `(Balance - Equity) / Balance * 100` ，保留 2 位 |
| max_intraday_drawdown_pct | 日内最大回撤（对资产高点） | 截止当日统计值 |
| notes | 当日要点 | 仅填写异常、关键事件、平台状态 |

## 4. 日常可视化示例

```text
date,account_type,balance,equity,margin,free_margin,open_positions,daily_profit,daily_drawdown_pct,max_intraday_drawdown_pct,notes
2026-06-21,demo,20000.00,19980.50,1200.00,18780.50,1,-19.50,0.10,0.85,开始观察：spread 2.5，EA正常无手工干预
```

## 5. 质量检查（每条记录提交前）

- `balance >= 0`、`equity >= 0`
- `open_positions >= 0`
- `margin <= free_margin + margin + 1e-6`（仅用于一致性自检）
- `-99 <= daily_drawdown_pct <= 100`
- 备注至少在异常日写入一句（如“异常触发原因”）

---

## 6. 固定触发接续字段（供无人工交接）

- 如果出现告警，必须同步补写：`forward_test_incident_log.csv`
- 若触发红色规则，则先停机、补日志、再等待下一次人工确认
