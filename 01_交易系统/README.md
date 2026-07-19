---
tags: [index, ea, trading-system]
date: 2026-07-03
---

# 📊 交易系统源码索引

> 知识库 `01_交易系统/` 总览 — 所有 EA 项目一览
> 源码原始位置在 E 盘各工作目录，已复制到本库归档

---

## 🔴 SniperTrendEA — 趋势狙击 EA

| 项目 | 状态 |
|------|------|
| **最新版本** | v8.77 (execution_audit_candidate) |
| **活跃版本** | v8.5（5层过滤，见 CLAUDE.md） |
| **源码数量** | 63 个 .mq5 文件 |
| **原始位置** | `E:/CODEXMACD/` |
| **库内位置** | `[[01_交易系统/SniperTrendEA/]]` |

### 版本演进

| 阶段 | 版本范围 | 说明 |
|------|---------|------|
| 早期 | v8.2 ~ v8.5 | 基础趋势狙击策略 |
| 体系构建 | v8.6 ~ v8.67 | 5层过滤 + grokbase 风控 |
| 风控强化 | v8.68 ~ v8.69 | dynamic_risk_governor, regime_gate |
| 上下文感知 | v8.70 ~ v8.77 | spread_cost_governor, context_scaling, execution_audit |

### 关键版本文件

- `SniperTrendEA_v8.5.mq5` — CLAUDE.md 记录的标准版
- `SniperTrendEA_v8.6.mq5` — 2560 战法联动版本
- `SniperTrendEA_v8.67_grokbase_production_ready.mq5` — 生产就绪候选
- `SniperTrendEA_v8.77_execution_audit_candidate.mq5` — 最新版

---

## 🟡 2560 战法 — 多空双向版

| 项目 | 状态 |
|------|------|
| **源码数量** | 2 个 .mq5 |
| **原始位置** | `E:/2560战法多空双向版/` |
| **库内位置** | `[[01_交易系统/2560战法/]]` |

### 文件清单

- `EA_2560_Strategy.mq5` — 2560 战法核心策略
- `SniperTrendEA_v8.6.mq5` — 与 SniperTrendEA 联动版本

> ⚠️ 该目录还包含大量回测报告（HTML/PNG），已保留在原位

---

## 🟢 华尔街对冲通讯版

| 项目 | 状态 |
|------|------|
| **源码数量** | 2 个 .mq5 |
| **原始位置** | `E:/GPT/MT5测试/MetaTrader 5/MQL5/Experts/` |
| **库内位置** | `[[01_交易系统/华尔街对冲通讯版/]]` |

### 文件清单

- `华尔街对冲通讯版.mq5` — 核心 EA
- `华尔街高级量化架构师定制 - 黄金顺势对冲系统.mq5` — 黄金专版

---

## 🟣 Vegas Trend Master

| 项目 | 状态 |
|------|------|
| **最新版本** | H4_Multi4.0 |
| **源码数量** | 3 个 .mq5 |
| **原始位置** | `E:/Ea/` + `E:/GPT/MT5测试/` |
| **库内位置** | `[[01_交易系统/Vegas_Trend_Master/]]` |

### 文件清单

- `Vegas_Trend_Master_H4.mq5` — H4 基础版
- `Vegas_Trend_Master_H4_Multi.MQ5.mq5` — 多品种版
- `Vegas_Trend_Master_H4_Multi4.0.mq5` — 4.0 多品种版（最新）

---

## 🔵 Gemini Starfleet EA

| 项目 | 状态 |
|------|------|
| **最新版本** | V4.50 Multi-Symbol |
| **源码数量** | 2 个 .mq5 + 1 个 .ex5 |
| **原始位置** | `E:/Ea/2026.04.22/` + `E:/GPT/MT5测试/` |
| **库内位置** | `[[01_交易系统/Gemini_Starfleet/]]` |

### 文件清单

- `GEMINI Starfleet EA V4.32.mq5` — V4.32 版本
- `GEMINI Starfleet EA V4.50 Multi-Symbol.MQ5.mq5` — V4.50 多品种版

---

## ⚪ WallStreet Sniper

| 项目 | 状态 |
|------|------|
| **源码数量** | 2 个 .mq5 |
| **原始位置** | `E:/GPT/MT5测试/` |
| **库内位置** | `[[01_交易系统/WallStreet_Sniper/]]` |

---

## 📁 其他 EA 与备份

### 其他 EA（18个）
`[[01_交易系统/其他EA/]]` — 包含：
- `Guardian_Earth_EA.mq5` — 地球守护者
- `星际重装铁骑版 - 海龟推进融合版.mq5` — 三大经典策略结晶
- `CE_RSI_Matrix_Trading.mq5` — RSI 矩阵交易
- `Universal_Range_Oscillation_EA_v3_2_Fixed.mq5` — 通用震荡 EA
- `TRAE均线价格动量交易策略.mq5` — 均线动量
- 等

### EA 研究备份（10个）
`[[01_交易系统/EA研究_备份/]]` — 包含 EA 研究过程中的备份文件

### 旧导入目录（未整理）
| 目录 | 说明 |
|------|------|
| `来自D盘_MT5测试/` | 494 个 .mq5（旧批量导入） |
| `来自D盘_DJQMT5/` | 153 个 .mq5 |
| `来自D盘_V9/` | 149 个 .mq5 |
| `ea代码库/` | GitHub EA 候选及 EA31337 相关 |

---

## 📌 待办事项

- [ ] 确认 SniperTrendEA 当前实盘用的是哪个版本 → 更新 CLAUDE.md
- [ ] 清理旧导入目录中的重复文件（来自D盘_*）
- [ ] 为每个项目添加架构说明笔记
