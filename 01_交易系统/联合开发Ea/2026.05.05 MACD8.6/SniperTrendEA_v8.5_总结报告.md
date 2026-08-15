# SniperTrendEA v8.5 总结报告

> 基于威科夫趋势线突破 + Evil MACD 狙击式交易系统  
> v8.5trae - 交易哲学深度融合迭代版  
> 编写日期：2026.05.07

---

## 一、策略概述

v8.5 在 v8.4 多因子框架基础上，融入 Z-Wei 交易体系六大核心理念：

| 编号 | 功能 | 参数 | 哲学来源 |
|:--:|------|------|------|
| 1 | 危险K线过滤 | MaxCandleATR=3.0 | 《危险的K线》 |
| 2 | 单边影线惩罚 | MaxOppositeShadow=0.20 | 《市场结构观察 #26-2-2》 |
| 3 | MA200自适应震荡带 | MA200BufferATR=0.45 | 《分形几何思维解读市场》 |
| 4 | 点火与跟随确认 | RequireFollowThrough=false | 《点火与跟随》 |
| 5 | 多因子过滤 | ADX/时间/波动率/日线 | v8.4 保留 |
| 6 | 动能递增检查 | RequireMomentumShift=true | 《突破质量的深度评估》 |

### 核心逻辑

- **信号触发器**：MACD 柱线（hist）从 ≤0 翻转到 >0（做多）/ 从 ≥0 翻转到 <0（做空）
- **确认窗口**：翻转后 4 根 K 线内等待确认
- **入场确认**：K线实体≥60% + 阳线/阴线 + 不触发三项哲学过滤
- **出场**：纯移动止盈（TrailStart=5.0ATR，TrailStep=2.5ATR），无止盈目标

---

## 二、三个方案对比

### 方案A：全期稳定版（推荐）

| 参数 | 值 |
|------|:--:|
| MA200BufferATR | 0.45 |
| BodyRatio | 0.6 |
| MaxCandleATR | 3.0 |
| MaxOppositeShadow | 0.20 |
| RequireFollowThrough | false |
| ConfirmBars | 4 |
| RequireMomentumShift | true |

### 方案B：趋势增强版

| 参数 | 值 |
|------|:--:|
| MA200BufferATR | 0.60 |
| RequireFollowThrough | true |
| RequireMomentumShift | false |
| 其他 | 同方案A |

### 方案C：激进版

| 参数 | 值 |
|------|:--:|
| BodyRatio | 0.5 |
| MaxOppositeShadow | 0.25 |
| ConfirmBars | 3 |
| 其他 | 同方案A |

---

## 三、十年全期回测对比（2015.01.01-2025.04.30, H4, XAUUSD）

| 指标 | 方案A | 方案B | 方案C |
|------|:--:|:--:|:--:|
| **盈利因子** | **2.37** | 1.87 | 2.10 |
| 总净盈利 | 2,136,753 | 938,365 | 2,297,380 |
| 毛利 | 3,699,935 | 2,022,708 | 4,391,885 |
| 毛损 | -1,563,182 | -1,084,342 | -2,094,505 |
| **净值回撤** | 27.12% | 27.11% | 27.12% |
| 采收率 | 4.65 | 4.59 | 4.83 |
| 夏普比率 | 4.50 | 3.62 | 3.48 |
| 交易总数 | 199 | 204 | 225 |
| 胜率 | 32.66% | 31.86% | 32.00% |
| 最大获利 | 466,136 | 207,048 | 500,922 |
| 最大亏损 | -122,380 | -54,366 | -131,509 |
| AHPR | 3.25% | 2.67% | 2.96% |
| LR 相关性 | 0.69 | 0.80 | 0.76 |

### 结论

- 方案A 综合最优：PF 最高 2.37，夏普最高 4.50
- 三个方案回撤全部精确落在 27.1%，这是结构性天花板——纯移动止盈无 TP 的代价
- 方案B 最差：FollowThrough + 关 MomentumShift 组合导致 PF 仅 1.87
- 方案C 放宽了入场但质量下降：PF 2.10 < 方案A 2.37

---

## 四、粗筛优化报告（2020.01.01-2025.04.30）

优化 7 参数，遍历 156 通行。Top 3：

| Pass | PF | DD% | 利润 | 交易 | 参数组合 |
|:--:|:--:|:--:|------|:--:|------|
| 77 | 2.57 | 59.44 | 151,467 | 59 | Buffer=0.3, Candle=3, Danger=2, Shadow=0.1, FT=false, FTBars=5, MS=true |
| 98 | 2.56 | 55.12 | 172,783 | 63 | Buffer=0.6, Candle=4, Danger=2, Shadow=0.1, FT=false, FTBars=3, MS=true |
| 25 | 2.51 | 27.10 | 439,081 | 104 | Buffer=0.45, Candle=3, Danger=2, Shadow=0.2, FT=false, FTBars=3, MS=true |

### 关键发现

- **Pass 25 的 Shadow=0.20 组合就是后来的方案A**——十年 PF 2.37 的出处
- Shadow 收紧到 0.10 可以在五年窗口拿到 PF 2.57，但能否扛住十年跨度未验证
- FollowThrough=true 在所有 Top 通行中都是 false——在黄金 H4 上无正面贡献
- MomentumShift=true 在所有 Top 通行中一致出现

---

## 五、已知缺陷

| 问题 | 严重性 | 说明 |
|------|:--:|------|
| **结构性 27% 回撤** | 🔴 | 三个方案一个数，纯移动止盈的代价 |
| **无 TP 保护** | 🔴 | req.tp=0，利润完全依赖 Trailing Stop |
| **无盈亏平衡** | 🟡 | 盈利单可能回到亏损 |
| **LR 相关性 0.69** | 🟡 | 资金曲线不够平滑 |
| **ADX/时间/日线过滤闲置** | 🟡 | 代码有但从未启用 |
| **仅测试 XAUUSD H4** | 🟡 | 跨品种未验证 |

---

## 六、v8.5 最终方案A 完整参数

```
InpFastEMA=12
InpSlowEMA=26
InpSignalSMA=9
InpMA200Period=200
InpUseMA200Filter=true
InpMA200BufferATR=0.45
InpBodyRatio=0.6
InpMaxCandleATR=3.0
InpDangerSuddenRatio=2.0
InpMaxOppositeShadow=0.20
InpRequireFollowThrough=false
InpFollowThroughBars=3
InpConfirmBars=4
InpRequireMACDDir=false
InpRequireMomentumShift=true
InpUseADX=false
InpUseTimeFilter=false
InpUseATRFilter=false
InpUseDailyFilter=false
InpRiskPercent=0.5
InpATRMultiplier=1.5
InpATRPeriod=14
InpTrailingStart=5.0
InpTrailingStep=2.5
InpMaxPositions=1
InpMagicNumber=20260506
```
