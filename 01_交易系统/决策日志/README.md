---
tags: [decision, trading, system]
date: 2026-07-20
---

# 📋 交易决策日志

> 每条交易决策独立成笔记，结构化记录依据和结果

## 使用方法

1. 每次交易决策前，从模板创建笔记
2. 填写决策依据（趋势线、MACD、共振信号）
3. 执行后补充结果和复盘
4. 用 Dataview 汇总分析

## 决策汇总

```dataview
TABLE 
  日期 as "日期",
  信号等级 as "信号",
  品种 as "品种",
  周期 as "周期",
  status as "状态"
FROM "01_交易系统/决策日志"
WHERE type = "trade-decision"
SORT 日期 DESC
```

## 违规统计

```dataview
TABLE 
  日期 as "日期",
  品种 as "品种",
  违规细节 as "违规内容",
  经验教训 as "教训"
FROM "01_交易系统/决策日志"
WHERE 是否遵守规则 = "⚠️ 违规"
SORT 日期 DESC
```

## 关联规则

每次复盘对照 [[CLAUDE.md#交易规则]] 检测清单逐条检查。
