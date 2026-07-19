# CODEXMACD 新窗口交接文件

> 新窗口接手时，请先完整阅读本文件。它是当前项目的启动说明、工作边界、执行方法、记录规范和下一阶段任务清单。

---

## 1. 项目当前总目标

当前项目目标不是单纯增加 EA 功能，也不是盲目追求最高净利润。

核心目标是：

1. 尽量保留 `grok8.6` 的高收益主线。
2. 在不明显破坏交易频率和收益结构的前提下降低回撤。
3. 避免固定年份过拟合、参数过拟合、回测环境过拟合。
4. 后续所有版本、`.set`、回测报告、矩阵、日志都必须可追溯、可回滚、不可覆盖历史。

当前最重要的收益锚点：

- 老版 `grok8.6` 在 `XAUUSD H4 2020.01.01-2026.06.30` 的净利润锚点：`557,505.36 USD`
- 当前主推参数 `v8.66_robust_main_case0010.set` 在同窗口净利润：`556,052.56 USD`
- 收益保留率约：`99.74%`
- 当前结论：`v8.66_robust_main_case0010.set` 是下一阶段开发主线，不应被随意替换。

---

## 2. 项目工作目录

主工作目录：

```text
E:\CODEXMACD
```

MT5 工作目录：

```text
D:\MT5测试\MetaTrader 5
```

重要目录：

```text
E:\CODEXMACD\HCSJ
E:\CODEXMACD\HCSJ\set
E:\CODEXMACD\HCSJ\backtest_archive
E:\CODEXMACD\HCSJ\matrix
E:\CODEXMACD\HCSJ\logs
E:\CODEXMACD\docs\superpowers\plans
```

所有 `.set` 文件必须保存到：

```text
E:\CODEXMACD\HCSJ\set
```

所有回测结果必须保存到：

```text
E:\CODEXMACD\HCSJ\backtest_archive
```

所有总结矩阵/评分/报告建议保存到：

```text
E:\CODEXMACD\HCSJ\matrix
```

---

## 3. 新窗口必须优先阅读的文件

请按顺序阅读：

1. 当前交接文件

```text
E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
```

2. 工作日志

```text
E:\CODEXMACD\WORK_LOG.md
```

3. 已完成参数搜索总结报告

```text
E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_summary.md
```

4. 已完成参数搜索主矩阵

```text
E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_matrix.csv
```

5. 已完成参数组评分表

```text
E:\CODEXMACD\HCSJ\matrix\robust_parameter_group_scores.csv
```

6. 上一阶段正式执行方案

```text
E:\CODEXMACD\docs\superpowers\plans\2026-06-19-v86-v866-robust-parameter-search.md
```

---

## 4. 当前 EA 与参数状态

### 4.1 当前主推源码

```text
E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.mq5
```

对应行数：`1354` 行。

输入属性设定数量：`77` 个 `input` 参数。

### 4.2 当前主推参数

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_robust_main_case0010.set
```

用途：下一阶段主线开发、压力测试、v8.67 默认参数参考。

### 4.3 高收益观察参数

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_aggressive_case0005.set
```

注意：该参数在 `2020-2026.06.30` 净利润达到 `716,968.27`，但回撤明显升高。不能直接作为主线，只能作为高收益观察对象。

### 4.4 保守风控观察参数

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_conservative_case0401.set
```

用途：研究降低回撤的风控方向。

### 4.5 v8.6 参考参数

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_robust_main_case0502.set
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_aggressive_case0005.set
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_conservative_case0002.set
```

用途：作为旧版收益弹性、保守参数、对照参数，不建议替代 v8.66 主线。

---

## 5. 已完成的重要工作

### 5.1 已完成 v8.6 与 v8.66 多周期参数搜索

已按以下方案执行完成：

```text
E:\CODEXMACD\docs\superpowers\plans\2026-06-19-v86-v866-robust-parameter-search.md
```

完成内容包括：

1. 三段固定基线：`2012-2014`、`2015-2019`、`2017-2023`
2. v8.6 有界参数搜索
3. v8.66 风控层搜索
4. v8.66 结构层搜索
5. 敏感性验证
6. 年度拆解：`2012-2023`
7. 可选控制窗口：`2020-2025`、`2020-2026.06.30`

完成回测记录：`102 / 102`。

### 5.2 已完成总结文件

总结报告：

```text
E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_summary.md
```

主矩阵：

```text
E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_matrix.csv
```

评分表：

```text
E:\CODEXMACD\HCSJ\matrix\robust_parameter_group_scores.csv
```

最终候选参数目录：

```text
E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search
```

---

## 6. 当前关键结论

### 6.1 主线结论

当前主线应继续围绕：

```text
v8.66_robust_main_case0010.set
```

原因：

1. 基本保住 grok8.6 的 `557,505.36 USD` 收益锚点。
2. `2020-2026.06.30` 净利润为 `556,052.56`。
3. PF 为 `2.27`。
4. 交易数为 `203`。
5. 结构参数扰动后没有明显断崖。
6. 没有通过明显减少交易次数来制造低回撤。

### 6.2 风险结论

不能说 v8.66 完全没有固定年份优化痕迹。

更准确判断：

```text
v8.66 robust case0010 = 有 2020-2026 收益锚点选择偏差，但暂时没有严重单一年份过拟合证据。
```

### 6.3 aggressive 参数结论

```text
v8.66_aggressive_case0005.set
```

收益很高，但回撤明显升高。不能直接作为主线。后续必须做压力测试。

### 6.4 v8.6 结论

v8.6 在早期分段可以找到高收益参数，但参数敏感性更强，不建议替代当前 v8.66 主线。

---

## 7. 下一阶段核心任务

下一阶段不是继续盲目优化，而是执行“固定年份过拟合排查 + 实盘压力测试”。

需要拆分并执行以下 6 大模块：

1. 固定点差放大测试
2. 滑点压力测试
3. 不同起止日期平移测试
4. 月度/季度拆解
5. 只用 `2012-2019` 找参数，再去 `2020-2026` 验证
6. 反过来，只用 `2020-2026` 找参数，再去 `2012-2019` 验证

注意：这些测试在上一窗口只完成了方案拆分，没有执行。

---

## 8. 下一阶段推荐测试对象

建议先测试 4 个对象：

| 编号 | 对象 | 用途 |
|---|---|---|
| A | v8.6 原始基线参数 | 旧版收益锚点对照 |
| B | v8.66 robust main case0010 | 当前主推稳健参数 |
| C | v8.66 aggressive case0005 | 高收益观察参数 |
| D | v8.66 conservative case0401 | 低回撤观察参数 |

主推对象是 B。

C 只能作为观察对象，不能直接升级为主线。

---

## 9. 下一阶段详细测试拆分

### 9.1 固定点差放大测试

目的：判断 EA 对交易成本是否敏感。

测试窗口：

```text
2012.01.01-2019.12.31
2020.01.01-2026.06.30
```

点差等级：

| 等级 | 含义 |
|---|---|
| Spread_1.0x | 当前正常点差 |
| Spread_1.5x | 中等成本压力 |
| Spread_2.0x | 高成本压力 |
| Spread_2.5x | 极端成本压力 |
| Spread_3.0x | 极限压力 |

预计回测数量：

```text
4 个对象 × 5 个点差等级 × 2 个窗口 = 40 次
```

统计字段：

- 净利润
- 净利润保留率
- PF
- 最大净值回撤
- 最大净值回撤比例
- 交易次数
- 平均每单利润
- 结论：低敏感 / 中敏感 / 高敏感

通过建议：

- `1.5x`：净利润保留 ≥ 85%，PF ≥ 1.8
- `2.0x`：净利润保留 ≥ 70%，PF ≥ 1.5
- `2.5x`：不能爆亏，最大回撤不超过基准约 1.3 倍
- `3.0x`：允许下降，但不能系统性失效

注意：当前项目尚未验证 MT5 固定点差配置字段。执行前必须先用单条小测试确认 MT5 是否真的加载固定点差设置。

### 9.2 滑点压力测试

目的：判断成交偏差对策略收益的影响。

测试窗口：

```text
2012.01.01-2019.12.31
2020.01.01-2026.06.30
```

滑点等级：

| 等级 | 含义 |
|---|---|
| Slippage_0 | 无滑点基准 |
| Slippage_1 | 轻微滑点 |
| Slippage_2 | 中等滑点 |
| Slippage_3 | 高滑点 |
| Slippage_5 | 极端滑点 |

预计回测数量：

```text
4 个对象 × 5 个滑点等级 × 2 个窗口 = 40 次
```

注意：MT5 策略测试器不一定能通过 `.ini` 稳定模拟滑点。如果不能直接设置，可能需要创建临时测试版 EA，例如：

```text
SniperTrendEA_v8.67_slippage_test.mq5
```

该版本只能用于压力测试，不作为正式交易版。

### 9.3 起止日期平移测试

目的：判断结果是否依赖精确开始/结束日期。

测试窗口：

```text
2012.01.01-2019.12.31
2020.01.01-2026.06.30
```

日期平移方案：

| 编号 | 方案 |
|---|---|
| Shift_00 | 原始日期 |
| Shift_01 | 开始日期后移 1 个月 |
| Shift_02 | 开始日期后移 3 个月 |
| Shift_03 | 结束日期前移 1 个月 |
| Shift_04 | 结束日期前移 3 个月 |
| Shift_05 | 开始后移 1 个月 + 结束前移 1 个月 |
| Shift_06 | 开始后移 3 个月 + 结束前移 3 个月 |
| Shift_07 | 开始后移 6 个月 + 结束前移 6 个月 |

预计回测数量：

```text
4 个对象 × 8 个日期方案 × 2 个窗口 = 64 次
```

统计字段：

- 净利润均值
- 净利润标准差
- 最差平移结果
- PF 均值
- 最大回撤最大值
- 交易数波动
- 日期边界敏感性评级

### 9.4 季度/月度拆解

目的：判断利润是否集中在少数月份或少数季度。

季度拆解：

```text
2012 Q1 到 2023 Q4 = 48 个季度
4 个对象 × 48 = 192 次
```

月度拆解建议分两档：

核心月度：

```text
v8.66 robust + v8.66 aggressive
2 个对象 × 144 个月 = 288 次
```

完整月度：

```text
4 个对象 × 144 个月 = 576 次
```

统计字段：

- 盈利月份比例
- 盈利季度比例
- 最差月份
- 最差季度
- 连续亏损月数
- 单月最大利润占比
- 单季度最大利润占比
- 年度利润分布

### 9.5 只用 2012-2019 找参数，再去 2020-2026 验证

目的：检查早期样本中找到的参数是否能泛化到后期主锚点。

训练期：

```text
2012.01.01-2019.12.31
```

验证期：

```text
2020.01.01-2026.06.30
```

建议候选数量：

| 版本 | 训练候选 | 验证 finalist | 敏感性扰动 | 合计 |
|---|---:|---:|---:|---:|
| v8.6 | 12 | 3 | 6 | 21 |
| v8.66 | 18 | 3 | 6 | 27 |
| 合计 | 30 | 6 | 12 | 48 |

重点结论：

- 训练期好，验证期也好：稳健性强
- 训练期好，验证期差：早期样本过拟合
- 训练期一般，验证期很好：可能偏向后期行情，需警惕选择偏差

### 9.6 只用 2020-2026 找参数，再去 2012-2019 验证

目的：检验 v8.66 是否按固定年份 `2020-2026` 优化出来。

训练期：

```text
2020.01.01-2026.06.30
```

验证期：

```text
2012.01.01-2019.12.31
```

建议候选数量：

| 版本 | 训练候选 | 验证 finalist | 敏感性扰动 | 合计 |
|---|---:|---:|---:|---:|
| v8.6 | 12 | 3 | 6 | 21 |
| v8.66 | 18 | 3 | 6 | 27 |
| 合计 | 30 | 6 | 12 | 48 |

重点结论：

- 2020-2026 训练优秀，2012-2019 也稳定：不是明显固定年份拟合
- 2020-2026 训练优秀，2012-2019 明显差：固定年份过拟合风险高
- aggressive 参数后期极好、早期明显差：不能作为主线
- robust 参数两边都平稳：可继续作为 v8.67 默认方向

---

## 10. 下一阶段预计回测数量

核心执行包：

| 测试模块 | 回测数量 |
|---|---:|
| 固定点差放大测试 | 40 |
| 滑点压力测试 | 40 |
| 起止日期平移测试 | 64 |
| 季度拆解 | 192 |
| 月度拆解，核心 2 个对象 | 288 |
| 2012-2019 找参数，2020-2026 验证 | 48 |
| 2020-2026 找参数，2012-2019 验证 | 48 |
| 合计 | 720 |

完整执行包：

| 测试模块 | 回测数量 |
|---|---:|
| 固定点差放大测试 | 40 |
| 滑点压力测试 | 40 |
| 起止日期平移测试 | 64 |
| 季度拆解 | 192 |
| 月度拆解，4 个对象 | 576 |
| 2012-2019 找参数，2020-2026 验证 | 48 |
| 2020-2026 找参数，2012-2019 验证 | 48 |
| 合计 | 1008 |

---

## 11. 推荐执行顺序

建议不要一上来跑 720 或 1008 次。

推荐顺序：

1. 起止日期平移测试
2. 2020-2026 找参数，2012-2019 验证
3. 2012-2019 找参数，2020-2026 验证
4. 固定点差放大测试
5. 滑点压力测试
6. 季度/月度拆解

原因：

1. 日期平移最快暴露固定年份边界问题。
2. 双向 walk-forward 最能判断是否过拟合。
3. 点差和滑点属于实盘压力。
4. 月度/季度拆解数量最大，适合最后做详细分析。

---

## 12. 新窗口具体工作方式

### 12.1 开始工作前

每次新窗口开始时必须先做：

1. 阅读本交接文件。
2. 阅读 `WORK_LOG.md` 最新部分。
3. 阅读当前阶段对应的 summary/report/matrix。
4. 明确本轮只做哪个任务模块。
5. 不要同时大规模执行多个不同性质任务。

### 12.2 执行前必须建立目标文件

如果要执行下一阶段压力测试，建议先生成正式计划文件，例如：

```text
E:\CODEXMACD\docs\superpowers\plans\2026-06-19-v866-pressure-walkforward-validation.md
```

计划中必须包含：

- 测试对象
- 测试窗口
- 参数候选范围
- 回测数量
- 归档目录
- CSV 字段
- 通过/淘汰标准
- 每一步如何写日志

### 12.3 每次执行必须记录

每一批回测完成后，都要追加到：

```text
E:\CODEXMACD\WORK_LOG.md
```

记录格式建议：

```text
## yyyy-MM-dd HH:mm:ss - <任务名称>
- 类型：回测 / 编译 / 参数生成 / 报告生成 / 问题修复
- 输入文件：...
- 输出文件：...
- 时间窗口：...
- 参数对象：...
- 回测数量：...
- 成功数量：...
- 失败数量：...
- 关键结果：净利润、PF、最大净值回撤、交易次数
- 初步结论：...
- 下一步：...
```

### 12.4 每次回测必须归档

每一次回测都必须保存：

- `.set`
- `.ini`
- `.htm` 报告
- `_metrics.csv`
- `_notes.md`
- 矩阵行记录

不允许只保存“好结果”。

失败、亏损、无交易、超时、加载失败也必须保存。

### 12.5 版本命名规则

不要覆盖旧文件。

新 EA 源码版本建议这样命名：

```text
SniperTrendEA_v8.67_grokbase_robust.mq5
SniperTrendEA_v8.67_grokbase_robust_fix1.mq5
SniperTrendEA_v8.67_slippage_test.mq5
```

新 `.set` 命名建议：

```text
v866_<window>_<stage>_round<NN>_case<NNNN>.set
```

例如：

```text
v866_2020-2026_dateshift_round01_case0007.set
```

新报告命名建议：

```text
v866_2020-2026_dateshift_round01_case0007.htm
```

---

## 13. 严格禁止事项

新窗口不要做这些事：

1. 不要覆盖旧 `.mq5`、`.ex5`、`.set`、`.htm`、`.csv` 文件。
2. 不要把 aggressive 参数直接设为主线。
3. 不要只看净利润选参数。
4. 不要只跑 `2020-2026` 一个窗口就下结论。
5. 不要全量优化 77 个 input 参数。
6. 不要不记录失败结果。
7. 不要在没有确认 MT5 加载 `.set` 的情况下批量回测。
8. 不要随意修改 grok8.6 核心入场逻辑。
9. 不要为了降低回撤而让交易次数大幅塌缩。
10. 不要没有工作日志就开始新一轮迭代。

---

## 14. 如果下一步要开发 v8.67

v8.67 不是优先追求新功能，而是工程化、参数治理、风控增强。

建议方向：

1. 从 v8.66 r68 复制新文件：

```text
E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_robust.mq5
```

2. 默认参数对齐：

```text
v8.66_robust_main_case0010.set
```

3. 整理 77 个 input 参数：

- 核心交易参数
- 风控参数
- 结构评分参数
- 调试参数
- 不建议普通优化的参数

4. 增加可选 debug 输出：

- 是否出现信号
- 是否被趋势过滤
- 是否被结构评分影响
- 是否被风控阀门影响
- 实际 lot 缩放原因

5. 编译后必须用以下窗口复测：

```text
2012-2014
2015-2019
2017-2023
2020-2025
2020-2026.06.30
```

6. v8.67 通过标准：

- 2020-2026.06.30 净利润尽量接近或超过 `557,505.36`
- PF ≥ `2.0`
- 交易数不能明显减少
- 最大净值回撤不能明显恶化
- 三段历史窗口不能出现灾难性样本外失败

---

## 15. 新窗口可直接使用的启动指令

如果用户开新窗口，可以直接发送：

```text
请先读取 E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md，然后继续接手项目。
当前主线参数是 E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_robust_main_case0010.set。
下一步请先制定并落地压力测试与 walk-forward 验证计划，不要直接跑回测；计划确认后再执行。
所有 .set 保存到 E:\CODEXMACD\HCSJ\set，所有回测报告保存到 E:\CODEXMACD\HCSJ\backtest_archive，每次操作都更新 E:\CODEXMACD\WORK_LOG.md，不允许覆盖历史文件。
```

如果用户希望新窗口直接执行，可以发送：

```text
请读取 E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md，并按照其中“推荐执行顺序”从起止日期平移测试开始执行。每一批回测都要归档 .set、ini、html、metrics.csv、notes.md，并更新 WORK_LOG.md。旧文件不得覆盖。
```

---

## 16. 当前最佳下一步

推荐下一步不是马上跑 720 次压力测试，而是先建立正式执行计划：

```text
E:\CODEXMACD\docs\superpowers\plans\2026-06-19-v866-pressure-walkforward-validation.md
```

该计划应把下一阶段分成小批次：

1. 日期平移小批次
2. 双向 walk-forward 小批次
3. 点差压力小批次
4. 滑点压力小批次
5. 季度拆解
6. 月度拆解

每批完成后先生成阶段报告，再决定是否继续下一批。

---

## 17. 当前交接结论

新窗口接手后应该明确：

1. 现在不是从零开始。
2. 已经完成 v8.6 vs v8.66 的第一轮稳健参数寻找。
3. 当前主线是 `v8.66_robust_main_case0010.set`。
4. 下一阶段核心任务是确认它是否存在固定年份优化风险。
5. 后续必须通过日期平移、双向 walk-forward、点差/滑点、月度/季度拆解来验证。
6. 所有工作必须可追溯、可回滚、可复查。
7. 不允许覆盖历史文件。
8. 每次改动、每次回测、每次失败都必须写入 `WORK_LOG.md`。
---

## 2026-06-20 01:54:45 +08:00 - Five-hour unattended pressure validation Stage 1

Completed modules:
1. Smoke test
2. Date-shift test
3. Reverse walk-forward 2020-2026 -> 2012-2019
4. Forward walk-forward 2012-2019 -> 2020-2026
5. Spread feasibility check
6. Stage summary

Important paths:

`	ext
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_master_matrix.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\date_shift_summary.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2020_2026_to_2012_2019.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2012_2019_to_2020_2026.csv
E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\spread_feasibility_summary.csv
`

Known blocker:

Fixed-spread feasibility is inconclusive. The current proven runner does not have a verified MT5 fixed-spread config hook, so metadata-only spread runs must not be used as real spread-stress evidence.

Next step:

Review Stage 1 summary. Then either verify true fixed-spread configuration or proceed to quarterly breakdown. Do not modify EA source before reviewing this stage.
---

# 2026-06-20 Latest Handoff: Production Readiness Wrap-up

Read this section first in a new window.

## Current decision

- Current system status: **Level 2 - demo / forward-test ready**.
- Full real-money live trading: **not approved yet**.
- Reason: the v8.67 candidate preserves the main profit anchor, but fixed-spread and slippage pressure tests are still unresolved.

## Current main files

- EA source: E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
- Compiled EX5: D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5
- Recommended set: E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
- Production readiness report: E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_report.md
- Release candidate folder: Not created (execution-risk closure-only continuation completed)
- SET manifest: E:\CODEXMACD\HCSJ\set\SET_MANIFEST.md

## Key results

- v8.67 2020-2026: net profit 556,052.56, PF 2.27, trades 203.
- v8.67 2020-2025: net profit 355,945.87, PF 2.02, trades 189.
- v8.67 near-term 2024.01.01-2026.06.30: net profit 161514.75, PF 2.70, trades 70, max equity DD 24.02%.
- Quarterly stability 2012Q1-2023Q4: 30/48 profitable quarters across A/B/C/D objects.
- Monthly stability 2012.01-2023.12: main robust candidate B has 66/144 profitable months, 45.83%.

## What the next window should do

1. Do not modify core entry logic first.
2. Continue with execution-risk closure: fixed-spread pressure test and slippage simulation.
3. If running demo forward test, use the forward monitor files in E:\CODEXMACD\HCSJ\forward_monitor.
4. Record every action in E:\CODEXMACD\WORK_LOG.md.
5. Save every new .set under E:\CODEXMACD\HCSJ\set.
6. Save every MT5 report under E:\CODEXMACD\HCSJ\backtest_archive.
7. Never overwrite old EA, set, report, or matrix files.

## Blockers that remain

- Fixed-spread testing could not be verified through current MT5 CLI configuration.
- Slippage pressure testing requires a temporary simulation harness or external execution model.
- Monthly profitable ratio is below 50%, so forward observation needs discipline and patience.

## 2026-06-20 Current continuity note (parser follow-up)
- Parser upgrade completed: E:\CODEXMACD\HCSJ\scripts\robust_search_runner.ps1
- New parser fields are now available for future runs (long/short split + consecutive loss count).
- Parser evidence note: E:\CODEXMACD\HCSJ\matrix\production_readiness\report_parser_enhancement.md
- Remaining execution-risk tasks are now explicitly planned in:
  - E:\CODEXMACD\docs\superpowers\plans\2026-06-20-fixed-spread-slippage-execution-continuation-plan.md
- No historical file overwrite occurred.

## 2026-06-20 v8.67 滑点配置级探针补跑（无人值守续）

- Completed: un_v867_slippage_probe.ps1
- Probe outputs:
  - E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_probe_v867_20260620_045032.csv
  - E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_probe_v867_20260620_045032.md
- Decision: equires_temp_ea_or_external_model
- Data effect: Slippage=3 / Deviation=3 对两窗格（2012-2019、2020-2026）未改变关键指标；不能替代真实滑点压力验证。
- Next action: continue with execution-risk closure via external execution model or temporary slippage test EA.
## 2026-06-20 追加无人值守续跑（v8.67 wf + execution-risk补测）

- 完成项：
  - `run_v867_next_stage.ps1 -Module wf20 -Objects C`（`20260620_0455_wf20`，2例，均PASS）
  - `run_v867_next_stage.ps1 -Module wf12 -Objects C`（`20260620_0455_wf12`，2例，均GREEN）
  - `run_v867_next_stage.ps1 -Module wf20 -Objects B`（`20260620_0459_wf20`，2例，均PASS）
  - `run_v867_next_stage.ps1 -Module wf12 -Objects B`（`20260620_0459_wf12`，2例，均PASS）
  - `run_v867_spread_probe.ps1`（`spread_probe_v867_20260620_045613.csv` / `spread_probe_v867_20260620_045613.md`）
  - `run_v867_slippage_probe.ps1`（`slippage_probe_v867_20260620_045744.csv` / `slippage_probe_v867_20260620_045744.md`）

- 关键结果：
  - B 与 C 的 `wf20/wf12` 最近批次显示可复现，B 主线仍维持 `2020-2026` 锚点：`556052.56`，`PF 2.27`，`203` 交易；C 作为挑战者继续保留高收益特征，但尚未替换主线。
  - 固定点差与滑点配置级探针输出仍无显著差异，属于 execution-risk 结构性阻塞，尚未形成可复核的真实压力证明。
  - 整体系统状态继续建议 `Level 2（demo/forward）`，非实盘全量。

- 下一窗口建议（继续无人值守）：
  - 继续执行 `E:\CODEXMACD\docs\superpowers\plans\2026-06-20-fixed-spread-slippage-execution-continuation-plan.md` 中“Phase B”。
  - 使用临时滑点模拟 EA（不改生产 EA）跑 0/1/2/3/5 水平，输出并归档完整 CSV/HTM/INI/SET/日志（保留历史不覆盖）。
  - 每次动作同步写入 `E:\CODEXMACD\WORK_LOG.md`，并在 `E:\CODEXMACD\HCSJ\matrix\production_readiness` 与 `E:\CODEXMACD\HCSJ\backtest_archive` 归档产物。


## 12. 2026-06-20 12h 无人值守续跑（Task 9 / Task 10 收尾）

### 当前状态

- 结论：当前进入 **生产就绪 Level 2（只允许 demo/forward 观察）**。
- 保持主线：`v8.66_robust_case0010` 线，工程体由 `v8.67_grokbase_production_ready` 接管。
- 主执行文件：`D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5`
- 主 set：`E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set`

### 本轮新增产物

- 生产就绪报告（新增版本，不覆盖历史）：
  - `E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_report_20260620_051710.md`
- 继续保留的历史版（勿覆盖）：
  - `E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_report.md`

### 当前结论

- v8.67 回归已跑完且通过：`2012-2014 / 2015-2019 / 2017-2023 / 2020-2025 / 2020-2026`
- 2012-2023 四档季度稳定性：A/B/C/D 均为 `good`
- 2012.01-2023.12 B/C 月度稳定性：`watch`
- 固定点差与滑点测试：仍为执行风险阻塞，未形成可核验证据

### 后续无歧义任务（接力窗口继续执行）

1. 优先处理执行风险闭环（真实固定点差 + 滑点模拟）
2. 完成临时滑点测试 EA（按 `2026-06-20-slippage-test-ea-design.md`）后复跑验证
3. 在证据闭环后评估是否允许微盘实验
4. 若无误，进入 `12-12` 参数治理清理与前端监控指标接入

### 严格要求（续接窗口必须遵循）

- 不修改历史文件路径命名方式，不覆盖历史文件。
- 每个执行动作都追加写入 `WORK_LOG.md`。
- 每次回测产物写入：
  - set -> `E:\CODEXMACD\HCSJ\set`
  - 报告/htm -> `E:\CODEXMACD\HCSJ\backtest_archive`
  - matrix -> `E:\CODEXMACD\HCSJ\matrix\production_readiness` 或对应版本子目录
- 新窗口第一条先读：`E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md` 与最新 `production_readiness_report_20260620_051710.md`
- 触发级联规则：如果再出现阻塞点（无覆盖条件、关键脚本失败），先更新日志再继续。

## 2026-06-20 最新无人值守执行更新（v8.67 执行风险闭环）

- 最新执行：
  - 完成临时滑点压力闭环：`E:\CODEXMACD\HCSJ\scripts\run_v867_slippage_harness.ps1`
  - 全量参数：对象 B/C，窗口 2012-2019 / 2020-2026，滑点 0/1/2/3/5
  - 结果文件：`E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074910\slippage_harness_v867_20260620_074910.csv`
  - 完整度：20/20 完成（无失败）
  - 决议：`completed`；B 与 C 对象在滑点注入下关键指标不变
- 补充固定点差 probe：
  - 完成：`E:\CODEXMACD\HCSJ\scripts\run_v867_spread_probe.ps1`
  - 结果文件：`E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_v867_20260620_075408.csv`
  - 决议：`inconclusive`（1.0/1.5/2.0 均与基线一致，无可复核差异）
- 当前主线与级别：
  - v8.66/8.67 主线稳健候选继续有效（2020-2026：净利 556,052.56，PF 2.27，交易 203）
  - 当前对外建议仍为 **Level 2（demo/forward）**
- 下一窗口优先任务：
  - 将 fixed spread 不敏感性结论转为可验证 blockers 文档（确认字段是否真实生效）
  - 若确认无法验证，保持其为 blocker 并推进 `v8.67` 参数治理与监控运维收口
  - 继续保持“无覆盖历史文件、全量归档、每次测试入 log”原则
## 2026-06-20 08:00:00 +08:00 - 无人值守续跑：执行风险闭环更新

### 已完成
- fixed spread 扩展探针（0/1/20/100）双窗口 8/8 完成。
- 结果与既有一致：未形成可复核固定点差差异，fixed-spread blocker 持续打开。
- 滑点临时 EA（0/1/2/3/5）20/20 完成，核心指标基本不变。

### 现状
- Readiness 再次确认：Level 2（demo/forward）
- 微盘观察与实盘：仍不建议启动

### 下一步
1. 接着执行 forward-monitor 操作清单与风控巡检流程（不改动 EA 核心逻辑）。
2. 有外部执行模型时再补跑固定点差和滑点压力复核。
3. 交付文件更新：E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_report_20260620_080000.md
## 2026-06-20 08:02:01 +08:00 - 无人值守阶段切换（执行 risk 关闭 -> forward-monitor 运维启动）

### 当前状态更新
- 结论维持：`Level 2（demo/forward）`，不启动微盘/实盘。
- fixed-spread / slippage 的验证仍为 block，但不影响当前 forward-monitor 记录流程。

### 本阶段动作
- 已创建并挂起 forward monitor 会话文件：
  - `E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_session_20260620_0802.md`
- 已更新 `WORK_LOG.md`：新增 forward-monitor stage kickoff 记录。
- 目标改为：
  1. 用现有模板接管 demo/forward 日常巡检，确保每次操作可追溯。
  2. 任何异常或紧急停机事件写入 incident_log。
  3. 每次操作仍继续追加 WORK_LOG 与回测归档日志（无覆盖）。

### 下一步建议（立即可执行）
1. 在 demo/forward 账户挂载 EA 前完成以下三项预检：
   - `forward_test_checklist.md`（上机前）
   - `live_micro_observation_rules.md`（微观条件）
   - 当前 readyness 报告 `production_readiness_report_20260620_080000.md`
2. 连接后记录首条 `forward_test_daily_equity.csv` 基线行（余额/权益/持仓/风险）。
3. 按需开启交易后，按日/每周维护上述监控 CSV 与 incident 日志。
4. 一旦出现阻塞：先停机、补齐 incident，再提交新的 handoff+WORK_LOG 说明。

## 2026-06-20 08:24:00 +08:00 - 下一窗口无人值守继续点（v8.67 forward monitor）

- 任务阶段：从验证阶段切入 demo/forward 运维（不新增回测）
- 当前状态核验：	erminal64.exe 未运行；SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5 已在 MT5 Experts 目录
- 继续原则：仅在账户挂载后执行以下动作，禁止改动 EA 源码和回测参数
  1. 按 E:\CODEXMACD\HCSJ\forward_monitor\forward_test_checklist.md 完成上机前清单
  2. 连接后记录 \\forward_test_daily_equity.csv 基线行
  3. 按日记录交易与异常，异常写入 \\forward_test_incident_log.csv
  4. 每次事件继续追加 E:\CODEXMACD\WORK_LOG.md
- 可直接执行的下一条命令（无交互）
  - Add-Content -Path E:\CODEXMACD\HCSJ\forward_monitor\forward_test_daily_equity.csv -Value "{date},{account_type},{balance},{equity},{margin},{free_margin},{open_positions},{daily_profit},{daily_drawdown_pct},{max_intraday_drawdown_pct},{notes}"
  - 注：该命令仅用于建立字段模板，真实数据需在交易运行后更新，不可虚构

## 2026-06-20 无人值守交接固定段（v8.67 交易监控期）

### 固定执行入口（无需再次确认）
- 标准日报模板：E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_daily_report_template.md
- 触发规则汇总：E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_trigger_rules_summary.md
- 日志文件：E:\CODEXMACD\HCSJ\forward_monitor\forward_test_daily_equity.csv

### 下一窗口无人工交接标准流程
1. 先确认 	erminal64.exe 挂载状态
2. 若已挂载：先补当日 \\forward_test_daily_equity.csv
3. 按 \\forward_monitor_trigger_rules_summary.md 评估：红色则停机，橙色继续观察，黄色仅记录
4. 无论执行结果，每条动作补 1 行 WORK_LOG.md
5. 一旦出现红色规则，先写 \\forward_test_incident_log.csv，再更新 handoff 与 log

### 规则优先级
- 红色（Stop）> 橙色（Observe）> 黄色（Record）
- 红色触发项：
  - 日内最大回撤 >= 5%
  - 日回撤>=3%且连续2天累加
  - 连续3日无交易且非平台停市
  - 交易错误/平台异常导致执行链路不可确认
- 停止条件满足即中断继续运行，直到异常修复与人工确认。

### 持续性约束（沿用）
- 每次动作保留历史，不覆盖 set、ini、htm、csv、md
- 任何测试/监控变更都需追加到 WORK_LOG.md
"@;

='E:\CODEXMACD\WORK_LOG.md';
Add-Content -Path  -Value @"
## 2026-06-20 14:57:22 +08:00 - v8.67 无人值守交接交接文件落地：日报模板与触发规则
- 动作类型：文档交付 / 流程固化
- 文件新增：
  - E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_daily_report_template.md
  - E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_trigger_rules_summary.md
- 文件更新：
  - E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_session_20260620_0802.md（新增下一窗口可执行固定段）
  - E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md（新增无人值守固定交接段）
- 要点：
  - 定义固定日报列与校验规则
  - 定义红/橙/黄触发规则与停机优先级
  - 规定下窗口仅按交接段“当日更新→判定→停机/观察/记录”执行
- 结论：交接内容已固化为无人值守可直接执行模板

## 2026-06-20 14:57:42 +08:00 - Next-window fixed handoff checkpoint (Monitoring)
- New operator should not ask clarifications. Use this exact sequence:
  1) Verify MT5 attach state and symbol/timeframe/EA-set match.
  2) Fill one row into HCSJ/forward_monitor/forward_test_daily_equity.csv for the current trading day.
  3) Read and apply:
     - HCSJ/forward_monitor/forward_monitor_trigger_rules_summary.md
     - HCSJ/forward_monitor/forward_monitor_daily_report_template.md
  4) If red rule: stop trading immediately, log incident, and wait for recovery.
  5) Log every action in WORK_LOG.md.
- Output files should not be overwritten.

## 2026-06-20 17:05 +08:00 - 24h unattended continuation checkpoint
- Runner issue repaired: HCSJ\scripts\run_v867_next_stage.ps1 now has A/D WF baselines and treats completed zero-trade month_cluster rows as NO_TRADE instead of hard failure.
- Clean WF evidence:
  - E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1635_wf12\wf_stage_report.md
  - E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1636_wf20\wf_stage_report.md
- Clean month_cluster evidence:
  - E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1645_month_cluster\month_cluster_stage_report.md
  - E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1653_month_cluster\month_cluster_stage_report.md
- Latest continuation report: E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_unattended_continuation_20260620_170308.md
- Latest artifact audit: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_validation_real_artifact_audit_20260620_170211.md
- Latest A/B/C/D month-cluster summary: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_month_cluster_abcd_summary_20260620_170142.md
- Current decision remains Level 2 demo/forward only. Do not approve real-money live until fixed-spread/slippage execution-model blockers are resolved and month-cluster weakness has an explicit mitigation plan.
## 2026-06-20 17:22 +08:00 - 24h remaining progress continued
- Latest remaining-progress index: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_24h_remaining_progress_index_20260620_172044.md
- Latest execution go/no-go matrix: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_execution_risk_go_no_go_matrix_20260620_172021.md
- Latest near-boundary regression: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_near_boundary_regression_20260620_171828.md
- Current state: task flow recovered; continue demo/forward only; real-money live remains No-Go.

## 2026-06-20 17:23 +08:00 - Forward monitor readiness audit
- Audit: E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_readiness_audit_20260620_172104.md
- Monitoring structure is ready; do not fabricate account baseline. First equity row requires actual MT5 demo/forward account data after EA attach.
