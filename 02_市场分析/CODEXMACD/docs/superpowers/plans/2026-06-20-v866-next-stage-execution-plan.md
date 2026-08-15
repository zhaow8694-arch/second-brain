# v8.67 下一阶段执行计划（v1.0）

> 生成时间：2026-06-20
> 目标：验证当前主线参数 `v8.66_robust_main_case0010` 的跨窗口稳健性与抗过拟合能力

## 0. 关键立场（我的判断）

1. 本阶段目标不是继续提高净利润，而是验证“可落地稳健性”。
2. `v8.66_robust_main_case0010` 作为主线，不作为候选筛选对象替代，不允许未经验证直接替换。
3. 优先级顺序按“最快暴露问题 -> 扩大验证范围”执行，默认每批都可中止。
4. 失败（含无交易、加载失败、单边崩溃）必须归档，不得只保留好样本。

## 1. 本阶段对象

- A：v8.6 原始基线（对照）
- B：v8.66_robust_main_case0010（主线）
- C：v8.66_aggressive_case0005（观察）
- D：v8.66_conservative_case0401（观察）

## 2. 文件路径与归档规则（不可覆盖）

- 计划文件
  - `E:\CODEXMACD\docs\superpowers\plans\2026-06-20-v866-next-stage-execution-plan.md`

- 当日实验根目录（每次运行创建唯一 run_id）
  - `E:\CODEXMACD\HCSJ\v8.67_validation_runs\<run_id>\`

- `.set` 集中目录
  - `E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\<run_id>\`

- 回测报告/原始归档
  - `E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\<run_id>\`

- 矩阵汇总
  - `E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\<run_id>\`

- 强制输出文件（每次回测）
  - `<id>.set`
  - `<id>.ini`
  - `<id>.htm`
  - `<id>_metrics.csv`
  - `<id>_notes.md`

- 全局禁止
  - 禁止覆盖已有 `.mq5/.ex5/.set/.ini/.htm/.csv/.md`
  - 任何失败也要写完整 5 件套（失败可注明失败原因）

## 3. 命名规则（含批次与场景）

命名约定：

`v866_<对象>_<模块>_<窗口或窗口签名>_<场景>_r<批次>_case<4位序号>`

示例：
- `v866_B_dateshift_2020-2026_shift03_r01_case0007`
- `v866_B_spread_2020-2026_s2.0x_r01_case0012`
- `v866_B_slippage_2012-2019_s5_r01_case0001`
- `v866_B_quarter_q2020-Q3_r02_case0009`

对象编码：
- `A/B/C/D`

模块编码：
- `dateshift`
- `wf12`（2012-2019 找参数，2020-2026 验证）
- `wf20`（2020-2026 找参数，2012-2019 验证）
- `spread`
- `slippage`
- `quarter`
- `month_core`（v8.66 robust / aggressive）
- `month_full`（A/B/C/D 全量）

## 4. run_id 与批次约定

- `run_id`：`YYYYMMDD_HHMM_<stage>`，例如 `20260620_0900_dateshift`
- `rNN`：同一模块同一 run_id 内的执行批次，例如 `r01`
- `caseNNNN`：同场景下递增

## 5. 执行顺序（门控式）

### 5.1 小规模预检（环境有效性）
- 先验证 MT5 是否正确读取：
  - 对象 B、A
  - 两个窗口 `2012-2019`、`2020-2026`
- 通过条件：
  - `.htm/.csv` 均成功生成
  - 参数文件与窗口在日志中可核对
- 不通过：停止该阶段后续执行，排查模板与 MT5 运行链路

### 5.2 dateshift
- 先只跑 B 全场景（8 个 shift × 2 窗口）
- 仅在 B 通过后再补 A/C/D
- 若 B 出现任一级别出现系统性失败（无交易或净利全面崩塌），暂停扩展，先复核时段与交易时段切片

### 5.3 walk-forward（双向）
- 先跑 `wf20`（2020-2026 训练 -> 2012-2019 验证）
- 再跑 `wf12`（2012-2019 训练 -> 2020-2026 验证）
- 两个方向都通过后，才进入大规模成本压力测试

### 5.4 压力测试
- spread -> slippage，均先以 B 为主线跑完整级别，再扩展到 A/C/D

### 5.5 拆解测试（最后执行）
- quarter：A/B/C/D 全量
- month_core：B/C 核心月度先做
- month_full：core 通过后再全量

## 6. 阈值规则（通过/淘汰）

以下为默认阈值；出现与基线冲突时需在 notes 中说明。

### 6.1 核心基准
- 主线基准（来自交接）：
  - 利润：`556,052.56`
  - PF：`2.27`
  - 交易数：`203`
  - （窗口 `2020-2026`）

### 6.2 全局通过线（所有模块共用）
- 回测成功且完整产物齐备
- `profit_retention >= 0.60`（相对对应基准，优先对 B 使用严格值）
- `PF >= 1.2`
- 交易数不出现明显塌缩：
  - B：`>=130`
  - A/C/D：`>=80`
- MDD 与基线非极端劣化：`<= 1.8x` 基线 MDD（默认）

### 6.3 模块阈值

#### dateshift
- 各场景：B 的 `profit_retention >= 0.70`
- 所有场景中位数：`>= 0.80`
- `shift00` 与 `shift07` 同向失真不应超过 `15%` 的累计回撤惩罚

#### walk-forward
- 每个方向验证期：
  - `profit_retention >= 0.75`
  - `PF >= 1.5`
  - 验证期交易数不低于训练期的 `45%`

#### spread
- `1.5x`: `profit_retention >= 0.85` 且 `PF >= 1.8`
- `2.0x`: `profit_retention >= 0.70` 且 `PF >= 1.5`
- `2.5x`: `profit_retention >= 0.55` 且 MDD `<= 1.5x` 基线
- `3.0x`: 不出现连续失效；允许利润降较多，但不可系统性失败

#### slippage
- `1`: `profit_retention >= 0.90`
- `2`: `profit_retention >= 0.80`
- `3`: `profit_retention >= 0.65` 且 `PF >= 1.4`
- `5`: 不允许“纯模型故障”，允许低收益但需保留交易连续性（B 不少于基准 `70%`）

#### quarter / month
- 季度盈利比例 >= 58%
- 月度盈利比例 >= 42%（B）
- 连续亏损：
  - 季度 <=2
  - 月度 <=3（核心月度）
- 单月收益占比或单季占比 > 60% 时，标记“集中风险”不自动淘汰但必须复核

## 7. 触发退出条件（Kill Switch）

一旦满足任意一条，暂停模块并复盘：

- 同一模块中 B 发生 2 次及以上 `profit_retention < 0.50`
- B 任意窗口 MDD > `2.0x` 基线
- B 任意窗口交易数 `<120`
- 连续 2 次 MT5 级别回测失败/解析失败/空报告

## 8. WORK_LOG 记录模板（必须每批追加）

```text
## yyyy-MM-dd HH:mm:ss - <任务名称>
类型：回测 / 编译 / 参数生成 / 报告生成 / 失败重测
run_id: <run_id>
模块：dateshift / wf12 / wf20 / spread / slippage / quarter / month_core / month_full
任务目标：<一句话>
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A/B/C/D
输入窗口：2012-2019 或 2020-2026
输入参数：<case 或 .set 路径>
场景配置：<shift/窗口等级/训练-验证组合>
回测数量：<n>
成功：<n>
失败：<n>
关键指标：
- profit
- profit_retention
- pf
- max_dd
- max_dd_pct
- trade_count
- avg_trade_profit
- notes
初筛结论：通过 / 边缘 / 淘汰
原因代码：R01参数崩塌 / C01成本模型未生效 / D01回测失败 / E01数据边界异常
下一步：<继续/中止并复盘/改场景>
输出路径：
- set: ...
- ini: ...
- htm: ...
- metrics: ...
- notes: ...
- matrix: ...
```

## 9. 矩阵字段（最低）

`run_id,module,object,case_id,window,scenario,profit,pf,max_dd,max_dd_pct,trade_count,profit_retention,trade_retention,pass_fail,notes,artifact_set,artifact_ini,artifact_html,artifact_metrics,artifact_notes`

## 10. 交付节点（阶段性）

- 阶段 1 完成后：输出 dateshift 报告（建议文件）
  - `HCSJ/matrix/v8.67_validation_runs/<run_id>/dateshift_stage_report.md`
- 阶段 2 完成后：输出 walk-forward 报告
- 阶段 3 完成后：输出成本压力报告
- 阶段 4 完成后：输出 split 报告
- 每阶段都更新 `WORK_LOG.md`

---

## 11. 备注

- 本计划可根据第一批预检结果调整；但命名与归档规则不得改动。
- 如出现关键异常（交易成本模型不生效、交易号突然变0、窗口加载空值），先补齐失败样本与日志，再扩展下批测试。
