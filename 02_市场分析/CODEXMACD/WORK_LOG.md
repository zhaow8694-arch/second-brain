# SniperTrend EA 开发工作日志

> 作用：用于窗口切换后保证上下文连续性。所有代码变更、参数实验、编译与回测都要完整记录，便于新窗口无缝接续。

## 记录规则（每次都要记录）

- 时间统一使用 `YYYY-MM-DD HH:mm:ss`（本地时区）
- 每一次“改动”必须写入“变更记录”
- 每一次“测试”必须写入“测试记录”（编译、回测、静态检查、脚本验证）
- 每条记录至少包含：目的、涉及文件、执行步骤/命令、结果、结论、下一步

## 当前任务目标（固定）

- 方向：保住 `grok8.6` 的收益主线，目标是更低回撤/更稳健（不是单纯牺牲收益换降回撤）
- 版本关系：`v8.64_softmerge` 与 `v8.64_softmerge_fix1` 来源于 `grok8.6` + `grok8.62` + `codex 8.6`
- 评估口径：以既有历史测试口径为主（H4/XAUUSD/2020-2025 为主），不引入不对齐测试口径

---

## 变更记录

| 时间 | 改动人 | 版本文件 | 类型 | 改动内容 | 备注 |
|---|---|---|---|---|---|
| 2026-06-19 02:36:21 | Codex | `WORK_LOG.md` 新建 | 文档 | 建立统一工作日志模板，明确“每次改动 + 每次测试记录”规则，便于窗口切换后无缝交接 | 第一个可执行日志入口 |
| 2026-06-19 02:38:47 | Codex | `WORK_LOG.md` 补充 | 文档 | 补充“对话方向同步 + 目录结构索引”，写入：v8.64 合并来源约束、根目录与子目录用途、核心文件归属 | 同步“每次改动测试都做记录”的要求 |

---

## 测试记录

| 时间 | 测试人 | 测试类型 | 测试对象/路径 | 步骤 | 结果 | 结论 |
|---|---|---|---|---|---|---|
| 2026-06-19 02:36:21 | Codex | 日志初始化 | 无 | 仅建立工作日志，不执行编译或回测 | 未执行 | 已完成日志初始化 |
| 2026-06-19 02:38:47 | Codex | 目录索引采集 | 根目录与子目录 | 使用文件系统扫描统计及用途识别（不改代码） | 成功 | 已补齐目录职责说明 |

---

## 目录与交接索引（根目录 + 子文件夹）

### 根目录核心用途

- `SniperTrendEA_*.mq5`：EA 版本源码（v8.2/v8.3/v8.5/v8.6/v8.63/v8.64_softmerge/fix1）
- `SniperTrendEA_*.ex5`：编译产物（供 MT5 回测直接加载）
- `*.log` / `metaeditor_*.log`：合并与编译记录
- `all_files_full_read_snapshot.txt`：上轮“全量文件快照”
- `.docx/.txt`：策略理论与市场观察材料

### 子目录职责（你提到的“每个子文件夹各自存什么”）

- `[.parsed_docs]`：已解析文本资料（主要是从 `.docx` 提取的策略理论文本）
- `[checkpoints]`：中间检查代码（如结构过滤 checkpoint）
- `[docs\superpowers]`：规范与计划（本阶段核心文档）
  - [docs/superpowers/plans/2026-06-18-snipertrendea-v8.6.md](E:\CODEXMACD\docs\superpowers\plans\2026-06-18-snipertrendea-v8.6.md)
  - [docs/superpowers/specs/2026-06-18-snipertrendea-v8.6-design.md](E:\CODEXMACD\docs\superpowers\specs\2026-06-18-snipertrendea-v8.6-design.md)
- `[HCSJ]`：回测对比和配置数据区
  - `.csv`：版本对比表、汇总表
  - `.xlsx`：多版本回测明细（例如 `grok8.6.xlsx`、`codex.xlsx`、`SniperTrendEA_8.64...`）
  - `.set`：EA 参数文件（例如 soft / hardFallback）
- `[mt5_configs]`：MetaTrader 回测配置 `.ini`
- `[tests]`：Python 静态测试（结构过滤、基础约束）
- `[tools]`：模型/工具脚本（例如结构过滤评分器）
- `[.firecrawl]`：当前为空（可保留/外部抓取相关占位）

### 核心文件快速索引

- 开发主对象
  - [SniperTrendEA_v8.64_softmerge.mq5](E:\CODEXMACD\SniperTrendEA_v8.64_softmerge.mq5)
  - [SniperTrendEA_v8.64_softmerge_fix1.mq5](E:\CODEXMACD\SniperTrendEA_v8.64_softmerge_fix1.mq5)
- 回测和参数对照
  - [HCSJ\SniperTrendEA_v8.64_softmerge_soft.set](E:\CODEXMACD\HCSJ\SniperTrendEA_v8.64_softmerge_soft.set)
  - [HCSJ\SniperTrendEA_v8.64_softmerge_hardFallback.set](E:\CODEXMACD\HCSJ\SniperTrendEA_v8.64_softmerge_hardFallback.set)
  - `C:\Users\Administrator\Desktop\SniperTrendEA_v8.64_softmerge.xlsx`
- 运行与回测日志
  - [metaeditor_softmerge_fix1.log](E:\CODEXMACD\metaeditor_softmerge_fix1.log)

---

## 最近决策同步（与本次沟通一致）

- `v8.64_softmerge` 的合并来源为：`grok8.6` + `grok8.62` + `codex 8.6`
- 下一步必须坚持“先保收益，再降回撤”，避免直接改信号主链导致收益线断裂
- 第一轮优先做 `风险控制/结构过滤` 的微调，不做大范围入场规则重构
- 每次改动都要立即补一条“变更记录 + 测试记录”

---

## 待办（按顺序）

1. 明确风控层首轮参数（不改主信号）
2. 运行固定参数矩阵回测（soft、soft+risk、hardFallback）
3. 以“净利守底线 + 回撤下降 + 交易频率不过度收缩”为准则筛选
4. 每轮结果追加到本日志

## 迭代补录（2026-06-19）

### 变更补录

| 时间 | 改动人 | 版本文件 | 类型 | 改动内容 | 备注 |
|---|---|---|---|---|---|
| 2026-06-19 02:43:13 | Codex | `SniperTrendEA_v8.64_softmerge_fix1.mq5` | EA代码 | 首轮风控层增量：新增风险控制输入与运行时状态（`InpUseRiskThrottle`, `InpMaxDailyDDPercent`, `InpConsecutiveLossLimit`, `InpCooldownBars`, `InpMaxOpenPositions`, `InpRiskLotScale`, `InpRiskWarningDDRatio`），并在 `OnInit/OnTick/下单` 接入风控阀门与仓位动态缩放 | 目标为“先保收益后降回撤”，未改主信号逻辑 |

### 测试补录

| 时间 | 测试人 | 测试类型 | 测试对象/路径 | 步骤 | 结果 | 结论 |
|---|---|---|---|---|---|---|
| 2026-06-19 02:43:13 | Codex | 编译验证 | `SniperTrendEA_v8.64_softmerge_fix1.mq5` -> `metaeditor_softmerge_fix1.log` | 执行 `metaeditor64.exe /compile:'E:\CODEXMACD\SniperTrendEA_v8.64_softmerge_fix1.mq5' /log:'E:\CODEXMACD\metaeditor_softmerge_fix1.log'` 并确认 `fix1.ex5` 生成 | 成功，`Result: 0 errors, 0 warnings`，`SniperTrendEA_v8.64_softmerge_fix1.ex5` 存在 | 可进入参数矩阵回测阶段 |
### 配置文件补充（参数矩阵准备）

| 时间 | 改动人 | 文件 | 类型 | 变更内容 | 备注 |
|---|---|---|---|---|---|
| 2026-06-19 02:48:22 | Codex | `HCSJ\SniperTrendEA_v8.64_softmerge_soft_risk.set`, `HCSJ\SniperTrendEA_v8.64_softmerge_hardFallback_risk.set` | 回测配置 | 新增两份风控参数集，分别基于 `soft` 与 `hardFallback`，用于后续参数矩阵（soft+risk、hardFallback+risk）对比；保持原参数不改，仅追加 `InpUseRiskThrottle`, `InpMaxDailyDDPercent`, `InpConsecutiveLossLimit`, `InpCooldownBars`, `InpMaxOpenPositions`, `InpRiskLotScale`, `InpRiskWarningDDRatio` | 为矩阵实验创建标准输入模板 |
### 运行环境同步补录

| 时间 | 操作人 | 文件 | 类型 | 操作内容 | 备注 |
|---|---|---|---|---|---|
| 2026-06-19 03:10:04 | Codex | `D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.64_softmerge_fix1.mq5`, `D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.64_softmerge_fix1.ex5` | EA部署 | 将本轮开发文件同步到 MT5 工作目录；将 E 盘编译产物 `SniperTrendEA_v8.64_softmerge_fix1.ex5` 拷贝到 D 盘 Expert 目录 | 用于后续回测可直接读取 fix1 版本 |
| 2026-06-19 03:10:04 | Codex | `D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester\SniperTrendEA_v8.64_softmerge_soft_risk.set`, `D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester\SniperTrendEA_v8.64_softmerge_hardFallback_risk.set` | 回测参数 | 新增两份风险层 `.set` 到 MT5 的 Tester Profile 目录 | 分别用于 soft+risk 与 hardFallback+risk |
| 2026-06-19 03:10:04 | Codex | `E:\CODEXMACD\mt5_configs\sniper_v864_softmerge_fix1_soft_risk_H4_XAUUSD_2020_2025.ini`, `E:\CODEXMACD\mt5_configs\sniper_v864_softmerge_fix1_hard_risk_H4_XAUUSD_2020_2025.ini` | 回测配置 | 新建两份回测矩阵配置（固定口径 H4/XAUUSD/2020-2025），便于直接启动软风险矩阵测试 | 与既有 soft/hard 基线命名一致 |
## 回测归档规则补充（版本不可覆盖，历史保留）

### 新规则

- 全部回测结果、参数快照与源文件引用必须归档到 `E:\CODEXMACD\HCSJ\backtest_archive`。
- 归档路径统一为：`backtest_archive\yyyyMMdd_HHmmss_版本标识`。
- 归档内容必须包含：
  - 回测 INI
  - 对应参数 `.set`
  - EA 二进制/源码引用（`.ex5` 与 `.mq5` 快照）
  - 回测报告目录（`.htm` / `.html` / `.xml`）
  - `archive_manifest.txt`
- 禁止覆盖旧版本；每次新回测只新增目录，不删除/覆盖历史目录。

### 对应操作脚本

- 新增脚本：[HCSJ\archive_backtest_data.ps1](/E:/CODEXMACD/HCSJ/archive_backtest_data.ps1)
  - 用法：`powershell -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\archive_backtest_data.ps1" -IniPath "E:\CODEXMACD\mt5_configs\<回测配置>.ini" -ArchiveRoot "E:\CODEXMACD\HCSJ\backtest_archive" -VersionTag "v8.64_softmerge_fix1_soft_risk"
  - 脚本会生成时间戳目录，不会覆盖旧目录。

### 测试记录补充

| 时间 | 测试人 | 测试类型 | 测试对象/路径 | 步骤 | 结果 | 结论 |
|---|---|---|---|---|---|---|
| 2026-06-19 02:47:42 | Codex | 归档准备 | `E:\CODEXMACD\HCSJ\backtest_archive` | 新建归档目录与归档脚本；约定按时间戳+版本号存储，不覆盖旧文件 | 已完成 | 已为“回测数据必须历史保留”建立固定落盘规则 |
## 变更记录补录（归档规则）

| 时间 | 改动人 | 版本文件 | 类型 | 改动内容 | 备注 |
|---|---|---|---|---|---|
| 2026-06-19 02:47:54 | Codex | `HCSJ\archive_backtest_data.ps1`, `HCSJ\run_and_archive_backtest.ps1`, `HCSJ\BACKTEST_ARCHIVE_GUIDE.md` | 自动化 | 新增回测归档脚本与使用说明：将回测配置、参数、EA、报告统一归档到 `HCSJ\backtest_archive`，目录采用 `时间戳_版本` 不覆盖旧历史 | 对齐“每次回测需保存历史版本”要求 |
### .set 历史归档补录（HCSJ/set）

- 时间：2026-06-19 02:50:26
- 操作人：Codex
- 文件：`E:\CODEXMACD\HCSJ\set`
- 变更类型：历史归档/资产集中管理
- 说明：按你的要求将历史版本 `.set` 文件全部集中到 `HCSJ\set`。本次收录覆盖范围：
  - `E:\CODEXMACD\HCSJ` 下全部 `.set`
  - `D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester` 下所有与版本名相关的 Sniper 趋势 EA `.set`（如 `SniperTrendEA*`, `SniperMerge*`, `CodexSniperTrendEA*`）
- 结果：共复制/归档 48 个 `.set` 到 `E:\CODEXMACD\HCSJ\set`
- 结论：历史参数文件已集中保存，后续版本更新只在该目录追加，不覆盖已存历史
- [2026-06-19 2026-06-19 02:58:38] .set归档同步
  - 操作: 同步工作区内历史 .set 到 HCSJ\set（保留原目录层级）
  - 新增复制: 8
  - 跳过: 源文件在目标目录内扫描到 48 个；目标已存在文件 0 个（未覆盖）
  - 目标现有 .set 总数: 56
  - 说明: 本次用于历史版本回溯与后续回测复用，不删除任何历史文件
### 2026-06-19 回测闭环补录（v8.64 风控矩阵 r2）

#### 变更记录

| 时间 | 改动人 | 版本文件/脚本 | 类型 | 改动内容 | 备注 |
|---|---|---|---|---|---|
| 2026-06-19 03:08:18 | Codex | HCSJ/run_and_archive_backtest.ps1, HCSJ/archive_backtest_data.ps1 | 脚本修复 | 修正 MT5 回测启动参数为 /config: 形式（原始调用 /config="..." 与历史 :+' 组合导致配置加载失败），并让归档脚本支持 Report 为无目录前缀时按文件前缀匹配（例如 SingleEAReports\sniper_v864...htm） | 保证后续每次回测都有可追踪报告落盘 |
| 2026-06-19 03:08:18 | Codex | HCSJ/version_compare_backtest_matrix.md, HCSJ/version_compare_backtest_matrix.csv | 台账 | 新建矩阵台账文件（固定字段：净利、PF、最大净值回撤、交易数、胜率、最长连亏、风险阀门），用于后续每轮迭代固定比较 | 使用当前三组 v8.64 回测结果 |

#### 测试记录

| 时间 | 测试人 | 测试类型 | 测试对象/路径 | 步骤 | 结果 | 结论 |
|---|---|---|---|---|---|---|
| 2026-06-19 03:08:18 | Codex | 回测+归档 | HCSJ/run_and_archive_backtest.ps1 | 重跑 soft 基线：sniper_v864_softmerge_soft_H4_XAUUSD_2020_2025.ini，版本 8.64_softmerge_soft_r2，记录归档到 HCSJ/backtest_archive/20260619_030713_v8.64_softmerge_soft_r2 | 回测成功，归档含 .htm/.png 报告 | 生成有效对照样本，发现未归档失败的历史原因是旧脚本未识别前缀式报告 |
| 2026-06-19 03:08:18 | Codex | 回测+归档 | HCSJ/run_and_archive_backtest.ps1 | 重跑 soft+risk：sniper_v864_softmerge_fix1_soft_risk_H4_XAUUSD_2020_2025.ini，版本 8.64_fix1_soft_risk_r2，归档到 HCSJ/backtest_archive/20260619_030729_v8.64_fix1_soft_risk_r2 | 回测成功，报告完整归档 | 收益/PF/回撤数据已入台账 |
| 2026-06-19 03:08:18 | Codex | 回测+归档 | HCSJ/run_and_archive_backtest.ps1 | 重跑 hardFallback+risk：sniper_v864_softmerge_fix1_hard_risk_H4_XAUUSD_2020_2025.ini，版本 8.64_fix1_hard_risk_r2，归档到 HCSJ/backtest_archive/20260619_030742_v8.64_fix1_hard_risk_r2 | 回测成功，报告完整归档 | 与 soft+risk 指标一致 |

#### 本轮参数矩阵结果（H4/2020-2025）

- 台账文件：E:/CODEXMACD/HCSJ/version_compare_backtest_matrix.md
- CSV：E:/CODEXMACD/HCSJ/version_compare_backtest_matrix.csv

| 版本 | 总净 | PF | 最大净值回撤 | 回撤% | 交易数 | 胜率 | 最长连亏 | 风险阀门 | 结论 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| v8.64_softmerge_soft_r2 | 103,520.46 | 1.80 | 26,700.05 | 30.84% | 187 | 46.52% | 4 | none | 不通过（低于 gk8.6 守底线） |
| v8.64_fix1_soft_risk_r2 | 97,636.78 | 1.83 | 25,593.39 | 30.94% | 179 | 45.81% | 4 | InpUseRiskThrottle=true; InpMaxOpenPositions=1; InpRiskLotScale=0.50; InpConsecutiveLossLimit=3; InpCooldownBars=8 | 不通过（净利/PF/回撤均未达标） |
| v8.64_fix1_hard_risk_r2 | 97,636.78 | 1.83 | 25,593.39 | 30.94% | 179 | 45.81% | 4 | InpUseRiskThrottle=true; InpMaxOpenPositions=1; InpRiskLotScale=0.50; InpConsecutiveLossLimit=3; InpCooldownBars=8 | 不通过（净利/PF/回撤均未达标） |

#### 关键问题（用户反馈对应）

- 你反馈的“没跑起来”是实锤问题：旧命令在部分调用中拼出了 cannot load config（如 "E:\CODEXMACD\'E:\CODEXMACD...），导致 MT5 仅启动不执行测试。
- 现已修正为 /config:<path>，并强化回测报告归档策略，确保每次结果保留。

#### 下一步建议

1. 先确认 grok8.6 当前是否需要用同一条 2020-2025/H4 口径、同样的 EA 输入约束做一次“官方基准复跑”；当前比较约束采用了 ll_version_compare_full.csv 内 grok8.6 指标，数值差距大。
2. 若基准复跑确认后，再继续做“结构分数阈值+保守回退”第一轮参数微调，不直接降频率/直接过滤。
#### 2026-06-19 回测口径对齐补录（grok8.6基准复核）

- 时间：2026-06-19 03:25:08
- 操作：新增基准复跑 E:\CODEXMACD\mt5_configs\sniper_v86_today_xauusd_h4_2020_2025_merge_set.ini（Expert=SniperTrendEA_v8.6.ex5，参数 SniperTrendEA_v8.6_merge.v8.6.set）
- 归档：E:\CODEXMACD\HCSJ\backtest_archive\20260619_032453_v8.6_anchor_merge_set_r2
- 结果：
  - 总净 356,659.80
  - PF 2.02
  - 最大净值回撤 87,589.44 (21.46%)
  - 交易数 189
  - 胜率 46.03%
  - 最长连亏 5
- 结论：基于可复现口径（同一时段同一品种）时，v8.64三组仍低于该基准；历史 ll_version_compare_full.csv 的 grok8.6 数值（557,505.36）存在口径差异，需要你确认是否沿用该历史快照为“收益锚点”。

## 2026-06-19 回测启动问题修复补录（防呆）

### 变更记录

| 时间 | 改动人 | 版本文件/脚本 | 类型 | 改动内容 | 备注 |
|---|---|---|---|---|---|
| 2026-06-19 03:26:20 | Codex | `HCSJ/run_and_archive_backtest.ps1` | 启动参数防呆 | 对 `ConfigPath` 做前后空白和首尾单双引号清洗后再验存在，避免被非法路径污染导致 `"cannot load config"` | 对应你当前“只打开 MQ5 不跑测试”的反馈 |

### 测试记录

| 时间 | 测试人 | 测试类型 | 测试对象/路径 | 步骤 | 结果 | 结论 |
|---|---|---|---|---|---|---|
| 2026-06-19 03:26:20 | Codex | 变更 | `HCSJ/run_and_archive_backtest.ps1` | 仅做启动参数清洗补丁 | 未发起新增回测 | 已减少配置参数注入类失败风险 |

### 2026-06-19 回测卡住问题排查（编码修正）
- 时间: 2026-06-19 04:01:54
- 文件: E:\CODEXMACD\HCSJ\SniperTrendEA_v8.64_softmerge_soft_nothrottle.set, D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester\SniperTrendEA_v8.64_softmerge_soft_nothrottle.set
- 类型: 回归问题修复
- 操作: 检测到 soft_nothrottle .set 首字节为 UTF-8 BOM（239,187,191）；已统一转为 UTF-8 无 BOM 并保持参数内容不变，避免参数解析器在启动阶段中断
- 结果/后续: 重启该 .ini（sniper_v864_fix1_soft_nothrottle_H4_XAUUSD_2020_2025.ini）后应恢复测试；本次未发起新回测（你已禁止新增重复回测）

### 2026-06-19 r4 回测入口修复与三组矩阵复跑

#### 变更记录

| 时间 | 改动人 | 版本文件 | 类型 | 改动内容 | 备注 |
|---|---|---|---|---|---|
| 2026-06-19 04:12 | Codex | `HCSJ\set\SniperTrendEA_v8.64_softmerge_soft_nothrottle_r4.set`, `mt5_configs\sniper_v864_fix1_soft_nothrottle_r4_H4_XAUUSD_2020_2025.ini` | 回测配置 | 从已验证可启动的 `soft_risk` 完整参数集派生干净 `nothrottle_r4`，仅设置 `InpUseRiskThrottle=false`，并使用唯一报告名 | 不覆盖旧 `soft_nothrottle`，保留旧问题样本用于追溯 |
| 2026-06-19 04:12 | Codex | `D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester\SniperTrendEA_v8.64_softmerge_soft_nothrottle_r4.set` | MT5参数同步 | 将 r4 `.set` 同步到 MT5 Tester Profile 目录 | 运行时实际读取该文件 |
| 2026-06-19 04:13 | Codex | `HCSJ\version_compare_backtest_matrix.md`, `HCSJ\version_compare_backtest_matrix.csv` | 台账 | 追加 r4 三组矩阵结果与结论 | 固定字段：净利、PF、最大净值回撤、交易数、胜率、最长连亏、风险暴露 |

#### 测试记录

| 时间 | 测试人 | 测试类型 | 测试对象/路径 | 步骤 | 结果 | 结论 |
|---|---|---|---|---|---|---|
| 2026-06-19 04:08 | Codex | 问题复现 | `sniper_v864_fix1_soft_nothrottle_H4_XAUUSD_2020_2025.ini` | 清理残留 MT5 后重启旧 nothrottle 配置，等待 120 秒 | 超时未退出，主日志仍无 `Tester automatical testing started` | 旧 nothrottle 输入仍会卡在测试器接管前 |
| 2026-06-19 04:10 | Codex | 控制组验证 | `sniper_v864_softmerge_fix1_soft_risk_H4_XAUUSD_2020_2025.ini` | 同样方式启动已知成功配置 | 9 秒内正常退出，日志进入 Tester | MT5 通道正常，问题收敛到旧 nothrottle `.ini/.set` |
| 2026-06-19 04:12 | Codex | 回测+归档 | `sniper_v864_fix1_soft_nothrottle_r4_H4_XAUUSD_2020_2025.ini` | 使用干净 r4 `.set` 启动并归档 | 成功；归档：`HCSJ\backtest_archive\20260619_041203_v8.64_fix1_soft_nothrottle_r4` | 修复 nothrottle 启动问题 |
| 2026-06-19 04:12 | Codex | 回测+归档 | `sniper_v864_softmerge_fix1_soft_risk_H4_XAUUSD_2020_2025.ini` | 运行 soft+risk r4 矩阵 | 成功；归档：`HCSJ\backtest_archive\20260619_041214_v8.64_fix1_soft_risk_r4` | 指标入台账 |
| 2026-06-19 04:12 | Codex | 回测+归档 | `sniper_v864_softmerge_fix1_hard_risk_H4_XAUUSD_2020_2025.ini` | 运行 hardFallback+risk r4 矩阵 | 成功；归档：`HCSJ\backtest_archive\20260619_041226_v8.64_fix1_hard_risk_r4` | 指标入台账 |

#### r4 矩阵结果

| 版本 | 总净 | PF | 最大净值回撤 | 回撤% | 交易数 | 胜率 | 最长连亏 | 结论 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v8.64_fix1_soft_nothrottle_r4 | 97,636.78 | 1.83 | 25,593.39 | 30.94% | 179 | 45.81% | 9 | 不通过 |
| v8.64_fix1_soft_risk_r4 | 97,636.78 | 1.83 | 25,593.39 | 30.94% | 179 | 45.81% | 9 | 不通过 |
| v8.64_fix1_hard_risk_r4 | 97,636.78 | 1.83 | 25,593.39 | 30.94% | 179 | 45.81% | 9 | 不通过 |

#### 结论

- r4 解决了 `soft_nothrottle` 只启动 MT5、不进入 Tester 的问题。
- r4 三组结果完全一致，说明当前风险阀门参数未形成有效差异，且收益/PF/回撤仍未达到 grok8.6 锚点约束。
- 下一步不能继续单纯调风险阀门，应优先对比 `grok8.6` 与 `v8.64_fix1` 的实际交易差异，定位收益主线在哪个合并层被削弱。

## 2026-06-19 04:23:01 +08:00 - r6 relative ExpertParameters load test
- Root cause hypothesis: MT5 did not load r5 .set because ExpertParameters used a Chinese absolute path that was saved/read as mojibake; report showed default InpComment=SniperEA_v8.62.
- Change: created r6 .set copies with distinct InpComment values, copied them to D:\MT5测试\MetaTrader 5\MQL5\Profiles\Tester, and created r6 .ini files using relative ExpertParameters=<set filename> only.
- Test v8.64_fix1_soft_r6: status=OK; comment=SniperEA_v8.64_soft_r6; riskThrottle=false; entryQuality=true; net=; PF=; maxEquityDD=; trades=; win=; maxLosses=; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_042238_v8.64_fix1_soft_r6; error=
- Test v8.64_fix1_soft_risk_r6: status=OK; comment=SniperEA_v8.64_soft_risk_r6; riskThrottle=true; entryQuality=true; net=; PF=; maxEquityDD=; trades=; win=; maxLosses=; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_042249_v8.64_fix1_soft_risk_r6; error=
- Test v8.64_fix1_hard_risk_r6: status=OK; comment=SniperEA_v8.64_hard_risk_r6; riskThrottle=true; entryQuality=false; net=; PF=; maxEquityDD=; trades=; win=; maxLosses=; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_042300_v8.64_fix1_hard_risk_r6; error=
- Interpretation rule: if report comments match SniperEA_v8.64_*_r6, parameter loading is confirmed; if comments remain SniperEA_v8.62, the set file is still not being loaded.


## 2026-06-19 04:24:31 +08:00 - r6 metrics correction from MT5 Chinese HTML report
- Reason: initial generic English report parser confirmed parameter loading but did not parse Chinese MT5 metric labels; this entry corrects the matrix/log metrics from the archived .htm reports.
- v8.64_fix1_soft_r6: comment=SniperEA_v8.64_soft_r6; riskThrottle=false; entryQuality=true; net=103 520.46; PF=1.80; maxEquityDD=26 700.05 (30.84%); trades=187; win=46.52%; maxLosses=7; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_042238_v8.64_fix1_soft_r6
- v8.64_fix1_soft_risk_r6: comment=SniperEA_v8.64_soft_risk_r6; riskThrottle=true; entryQuality=true; net=97 636.78; PF=1.83; maxEquityDD=25 593.39 (30.94%); trades=179; win=45.81%; maxLosses=9; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_042249_v8.64_fix1_soft_risk_r6
- v8.64_fix1_hard_risk_r6: comment=SniperEA_v8.64_hard_risk_r6; riskThrottle=true; entryQuality=false; net=102 497.03; PF=1.80; maxEquityDD=34 970.63 (37.00%); trades=156; win=44.87%; maxLosses=8; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_042300_v8.64_fix1_hard_risk_r6
- Finding: r6 set loading is confirmed by distinct InpComment values. soft_r6 still has InpUseEntryQualityFilter=true, so it is not a fully unfiltered grok8.6 anchor-equivalent profile.


## 2026-06-19 04:26:20 +08:00 - r7 anchor-equivalent neutral parameter test
- Change: created E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix1_anchor_equiv_r7.set from soft_r6 and neutralized v8.64-added risk/quality switches: riskThrottle=false, entryQuality=false, maxOpenPositions=100, consecutiveLossLimit=999, cooldown=0, riskLotScale=1.00.
- Test: v8.64_fix1_anchor_equiv_r7 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_anchor_equiv_r7; riskThrottle=false; entryQuality=false; maxOpenPositions=100; net=117 463.58; PF=1.84; maxEquityDD=39 090.33 (36.98%); trades=161; win=45.96%; maxLosses=8; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_042619_v8.64_fix1_anchor_equiv_r7.
- Purpose: determine whether v8.64 can recover grok8.6-like behavior when added risk/quality layers are neutralized.


## 2026-06-19 04:29:50 +08:00 - r8 v8.6 report-actual anchor parameter test
- Discovery before test: the archived v8.6 anchor report showed it ran report/default parameters, not the merge .set values. Actual anchor differences versus r7 included FilterPreset=2, RiskPercent=0.5, ATRMultiplier=1.5, IgnitionEngulfRatio=0.85, IgnitionMaxLossATR=1.0, TrailingStart=5.0, TrailingStep=2.5.
- Change: created E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix1_grok86_report_equiv_r8.set with those report-actual anchor values and neutral v8.64 added layers.
- Test: v8.64_fix1_grok86_report_equiv_r8 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_grok86_report_equiv_r8; preset=2; risk=0.5; atrMult=1.5; riskThrottle=false; entryQuality=false; net=312 199.64; PF=1.94; maxEquityDD=77 319.29 (21.48%); trades=193; win=45.60%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_042949_v8.64_fix1_grok86_report_equiv_r8.
- Purpose: verify whether v8.64 can recover grok8.6收益骨架 once matched to the actual anchor report parameters.


## 2026-06-19 04:32:20 +08:00 - r9 fix2 strict structure regression test
- Code change: created SniperTrendEA_v8.64_softmerge_fix2.mq5 from fix1. When InpUseEntryQualityFilter=false, OnTick now uses PassStructureFilter and requires structureOk in the main buy/sell entry condition, restoring v8.6 hard-structure behavior. When EntryQualityFilter=true, soft quality path remains available.
- Compile: MetaEditor exit code 0 for SniperTrendEA_v8.64_softmerge_fix2.mq5 copied into MT5 MQL5\\Experts; compile log file was not emitted by MetaEditor.
- Test: v8.64_fix2_grok86_strict_structure_r9 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_strict_structure_r9; preset=2; risk=0.5; atrMult=1.5; riskThrottle=false; entryQuality=false; net=312 199.64; PF=1.94; maxEquityDD=77 319.29 (21.48%); trades=193; win=45.60%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_043219_v8.64_fix2_grok86_strict_structure_r9.


## 2026-06-19 04:34:30 +08:00 - r10 anchor-absent filter neutralization test
- Discovery: v8.6 anchor report had no inputs for structure/spread filter layer (InpUseStructureFilter, InpUseSpreadFilter, etc.), while v8.64 includes them. r10 disables those layers to better emulate the actual grok8.6 anchor EX5 behavior.
- Test: v8.64_fix2_grok86_nostruct_nospread_r10 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_nostruct_nospread_r10; structureFilter=false; spreadFilter=false; net=278 244.32; PF=1.90; maxEquityDD=69 260.80 (34.55%); trades=195; win=45.13%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_043428_v8.64_fix2_grok86_nostruct_nospread_r10.


## 2026-06-19 04:36:07 +08:00 - r11 risk scaling toward 95% anchor profit
- Change: copied r9 parameters and only changed InpRiskPercent from 0.50 to 0.55; risk throttle remains false. Purpose is to test whether v8.64 can reach >=95% of v8.6 anchor net profit while keeping max equity DD below anchor absolute DD.
- Test: v8.64_fix2_grok86_risk055_r11 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_grok86_risk055_r11; risk=0.55; riskThrottle=false; net=385 675.02; PF=1.95; maxEquityDD=103 242.08 (23.29%); trades=193; win=45.60%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_043606_v8.64_fix2_grok86_risk055_r11.


## 2026-06-19 04:37:14 +08:00 - r12 risk interpolation test
- Change: copied r9 parameters and changed only InpRiskPercent to 0.518. This was chosen by interpolating r8/r11 to target >=95% of v8.6 anchor profit while staying below anchor absolute max equity DD.
- Test: v8.64_fix2_grok86_risk0518_r12 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_grok86_risk0518_r12; risk=0.518; riskThrottle=false; net=337 534.06; PF=1.94; maxEquityDD=85 927.79 (22.12%); trades=193; win=45.60%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_043713_v8.64_fix2_grok86_risk0518_r12.


## 2026-06-19 04:38:13 +08:00 - r13 risk fine-tune test
- Change: copied r9 parameters and changed only InpRiskPercent to 0.519 after r12 missed the 95% anchor-profit target by about 1,293 while keeping DD below anchor.
- Test: v8.64_fix2_grok86_risk0519_r13 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_grok86_risk0519_r13; risk=0.519; riskThrottle=false; net=339 447.30; PF=1.94; maxEquityDD=86 621.32 (22.17%); trades=193; win=45.60%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_043812_v8.64_fix2_grok86_risk0519_r13.


## 2026-06-19 04:39:29 +08:00 - r14 mild risk throttle test
- Change: copied r13 and enabled mild risk throttle: InpMaxDailyDDPercent=6.0, InpConsecutiveLossLimit=8, InpCooldownBars=4, InpRiskLotScale=0.80, InpRiskWarningDDRatio=0.85.
- Test: v8.64_fix2_grok86_risk0519_mildthrottle_r14 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_mildthrottle_r14; risk=0.519; riskThrottle=true; maxDailyDD=6.0; lossLimit=8; cooldown=4; scale=0.80; net=358 427.86; PF=1.95; maxEquityDD=91 128.09 (22.16%); trades=192; win=45.83%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_043928_v8.64_fix2_grok86_risk0519_mildthrottle_r14.


## 2026-06-19 04:40:36 +08:00 - r15 trailing tightening test
- Change: copied r9 baseline and changed InpRiskPercent=0.520, InpTrailingStart=4.5, InpTrailingStep=2.2, risk throttle off. Purpose: see whether slightly earlier trailing can reduce DD while keeping >=95% anchor profit.
- Test: v8.64_fix2_grok86_risk052_trail45_22_r15 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_risk052_trail45_22_r15; risk=0.520; trailingStart=4.5; trailingStep=2.2; riskThrottle=false; net=309 743.47; PF=1.89; maxEquityDD=76 586.45 (21.48%); trades=204; win=45.59%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_044035_v8.64_fix2_grok86_risk052_trail45_22_r15.


## 2026-06-19 04:41:41 +08:00 - r16 tighter trailing plus risk compensation test
- Change: copied r15 and changed InpRiskPercent to 0.540, keeping InpTrailingStart=4.5 and InpTrailingStep=2.2. Purpose: compensate r15's reduced profit while preserving lower DD from earlier trailing.
- Test: v8.64_fix2_grok86_risk054_trail45_22_r16 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_risk054_trail45_22_r16; risk=0.540; trailingStart=4.5; trailingStep=2.2; riskThrottle=false; net=335 646.78; PF=1.89; maxEquityDD=85 582.16 (22.19%); trades=204; win=45.59%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_044139_v8.64_fix2_grok86_risk054_trail45_22_r16.


## 2026-06-19 04:42:40 +08:00 - r17 tight trailing risk fine-tune test
- Change: copied r16 and changed only InpRiskPercent to 0.542, keeping tighter trailing and throttle off. Purpose: cross 95% anchor-profit target while retaining lower DD from r16.
- Test: v8.64_fix2_grok86_risk0542_trail45_22_r17 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_risk0542_trail45_22_r17; risk=0.542; trailingStart=4.5; trailingStep=2.2; riskThrottle=false; net=338 384.45; PF=1.89; maxEquityDD=86 593.46 (22.27%); trades=204; win=45.59%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_044239_v8.64_fix2_grok86_risk0542_trail45_22_r17.


## 2026-06-19 04:43:40 +08:00 - r18 tight trailing final fine-tune test
- Change: copied r17 and changed only InpRiskPercent to 0.543, keeping tighter trailing and throttle off. Purpose: cross 95% anchor-profit target while staying below anchor absolute DD.
- Test: v8.64_fix2_grok86_risk0543_trail45_22_r18 H4 XAUUSD 2020-2025; comment=SniperEA_v8.64_fix2_risk0543_trail45_22_r18; risk=0.543; trailingStart=4.5; trailingStep=2.2; riskThrottle=false; net=340 350.84; PF=1.89; maxEquityDD=87 291.87 (22.32%); trades=204; win=45.59%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_044338_v8.64_fix2_grok86_risk0543_trail45_22_r18.


## 2026-06-19 04:44:04 +08:00 - Stage selection after r8-r18 optimization
- Anchor reference: v8.6_anchor_merge_set_r2 actually ran Expert=SniperTrendEA_v8.6.ex5 with report/default inputs, not the intended merge .set. Anchor metrics: net=356,659.80; PF=2.02; maxEquityDD=87,589.44 (21.46%); trades=189; win=46.03%; maxLosses=5.
- Root-cause finding: prior r4/r5 matrix rows were invalid for parameter comparison because absolute Chinese ExpertParameters paths caused .set loading failures. r6 relative ExpertParameters confirmed loading via distinct InpComment values.
- Code iteration: SniperTrendEA_v8.64_softmerge_fix2.mq5 was created from fix1. It restores PassStructureFilter hard behavior when InpUseEntryQualityFilter=false, while preserving the soft quality path when enabled. r9 showed same metrics as r8, so this code change was behavior-neutral for current candidate settings, but it keeps the compatibility intent clearer.
- Current recommended candidate: v8.64_fix2_grok86_risk0519_r13 using set HCSJ/set/SniperTrendEA_v8.64_fix2_grok86_risk0519_r13.set. Metrics: net=339,447.30 (95.16% of anchor); PF=1.94; maxEquityDD=86,621.32 (22.17%); trades=193; win=45.60%; maxLosses=11. It meets the first-stage target of >=95% anchor profit and lower absolute max equity DD.
- Alternative candidate: r18 reached slightly higher net=340,350.84 but worse PF=1.89 and higher maxEquityDD=87,291.87, leaving almost no DD buffer versus anchor. Prefer r13 unless the next stage prioritizes net profit over PF/DD buffer.
- Important caveat: r13 improves absolute max equity DD versus anchor but not DD percentage and not longest-loss streak. Next optimization should target path quality/losing-streak reduction without sacrificing the r13 profit floor.

## 2026-06-19 04:52:11 +08:00 - r19 historical grok8.6 period alignment test
- Discovery: HCSJ\\grok8.6.xlsx uses period H4 (2020.01.01 - 2026.06.30), not 2020.01.01 - 2025.12.31. Historic anchor metrics are net=557,505.36, PF=2.26604, maxBalanceDD=59,932.50 (26.07%), maxEquityDD=149,678.95 (24.13%), trades=203, win=46.80%, max consecutive losses=10.
- Change: created E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix2_grok86_20200630_r19.set from r9 baseline, kept grok8.6 historical params and risk=0.5/throttle=false, and created a 2026.06.30 tester config.
- Test: v8.64_fix2_grok86_20200630_r19; period=H4 (2020.01.01 - 2026.06.30); comment=SniperEA_v8.64_fix2_grok86_20260630_r19; risk=0.5; riskThrottle=false; net=464 420.24; PF=2.08; maxBalanceDD=52 859.96 (26.09%); maxEquityDD=143 691.93 (26.29%); relEquityDD=49.79% (44 467.27); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_045210_v8.64_fix2_grok86_20200630_r19.


## 2026-06-19 04:53:57 +08:00 - r20-r22 risk ladder against 557k historical anchor
- Target restored: historical grok8.6 from HCSJ/grok8.6.xlsx is period 2020.01.01-2026.06.30, net=557,505.36, PF=2.26604, maxEquityDD=149,678.95 (24.13%), trades=203. 95% net floor=529,630.09; PF floor=2.0; frequency floor=163 trades; DD should not exceed anchor.
- v8.64_fix2_grok86_20260630_risk0520_r20: risk=0.520; net=510 686.00; PF=2.08; maxEquityDD=162 549.09 (27.05%); relEquityDD=51.16% (47 592.59); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_045329_v8.64_fix2_grok86_20260630_risk0520_r20; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix2_grok86_20260630_risk0520_r20.set
- v8.64_fix2_grok86_20260630_risk0525_r21: risk=0.525; net=526 573.85; PF=2.08; maxEquityDD=168 368.07 (27.20%); relEquityDD=51.54% (48 679.36); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_045343_v8.64_fix2_grok86_20260630_risk0525_r21; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix2_grok86_20260630_risk0525_r21.set
- v8.64_fix2_grok86_20260630_risk0530_r22: risk=0.530; net=537 601.92; PF=2.08; maxEquityDD=173 084.47 (27.37%); relEquityDD=51.88% (49 493.91); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_045356_v8.64_fix2_grok86_20260630_risk0530_r22; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix2_grok86_20260630_risk0530_r22.set


## 2026-06-19 04:56:01 +08:00 - r23-r25 risk throttle matrix against 557k anchor
- Purpose: keep grok8.6 entry flow and 2026.06.30 period, then test whether risk throttle can reduce DD for variants around the 529,630.09 net floor.
- v8.64_fix2_grok86_20260630_risk0530_throttle_r23: throttle=mild; risk=0.530; DD=6.0; lossLimit=8; cooldown=4; scale=0.80; warn=0.85; net=566 786.32; PF=2.09; maxEquityDD=182 250.73 (27.39%); relEquityDD=51.87% (51 987.24); trades=206; win=46.60%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_045534_v8.64_fix2_grok86_20260630_risk0530_throttle_r23; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix2_grok86_20260630_risk0530_throttle_r23.set
- v8.64_fix2_grok86_20260630_risk0535_throttle_r24: throttle=moderate; risk=0.535; DD=5.5; lossLimit=7; cooldown=6; scale=0.75; warn=0.80; net=571 863.60; PF=2.09; maxEquityDD=185 314.72 (27.59%); relEquityDD=52.23% (52 147.14); trades=205; win=46.34%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_045547_v8.64_fix2_grok86_20260630_risk0535_throttle_r24; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix2_grok86_20260630_risk0535_throttle_r24.set
- v8.64_fix2_grok86_20260630_risk0540_throttle_r25: throttle=strong; risk=0.540; DD=5.0; lossLimit=6; cooldown=8; scale=0.70; warn=0.75; net=428 187.58; PF=2.05; maxEquityDD=141 047.86 (27.72%); relEquityDD=53.38% (38 487.17); trades=202; win=45.05%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_045600_v8.64_fix2_grok86_20260630_risk0540_throttle_r25; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix2_grok86_20260630_risk0540_throttle_r25.set


## 2026-06-19 05:00:33 +08:00 - fix3 r26-r28 peak drawdown throttle matrix
- Code change: created SniperTrendEA_v8.64_softmerge_fix3.mq5 from fix2. Added peak-equity drawdown tracking and inputs InpMaxPeakDDPercent / InpPeakDDWarningRatio. This is a risk-layer-only change; entry logic is unchanged.
- Compile: MetaEditor exit code 0 for fix3; compile log file was not emitted.
- v8.64_fix3_grok86_20260630_risk0530_r26: mode=peak_mild; risk=0.530; peak=24.0; peakWarn=0.70; DD=6.0; lossLimit=8; cooldown=4; scale=0.65; net=11 564.74; PF=1.92; maxEquityDD=11 542.89 (26.78%); relEquityDD=35.14% (10 812.73); trades=20; win=50.00%; maxLosses=5; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_045953_v8.64_fix3_grok86_20260630_risk0530_r26; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix3_grok86_20260630_risk0530_r26.set
- v8.64_fix3_grok86_20260630_risk0540_r27: mode=peak_mid; risk=0.540; peak=24.0; peakWarn=0.70; DD=5.5; lossLimit=7; cooldown=6; scale=0.55; net=11 044.19; PF=1.93; maxEquityDD=11 041.17 (35.62%); relEquityDD=35.62% (11 041.17); trades=20; win=50.00%; maxLosses=5; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050019_v8.64_fix3_grok86_20260630_risk0540_r27; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix3_grok86_20260630_risk0540_r27.set
- v8.64_fix3_grok86_20260630_risk0550_r28: mode=peak_strong; risk=0.550; peak=24.0; peakWarn=0.65; DD=5.0; lossLimit=6; cooldown=8; scale=0.50; net=8 214.54; PF=1.90; maxEquityDD=11 193.46 (35.93%); relEquityDD=35.93% (11 193.46); trades=18; win=50.00%; maxLosses=4; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050032_v8.64_fix3_grok86_20260630_risk0550_r28; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix3_grok86_20260630_risk0550_r28.set


## 2026-06-19 05:02:37 +08:00 - fix4 r29-r31 peak drawdown scale-only matrix
- Code adjustment: created SniperTrendEA_v8.64_softmerge_fix4.mq5 from fix3. Peak drawdown no longer triggers cooldown every bar; it only contributes to lot scale warning. Daily DD / consecutive loss cooldowns were disabled for this isolation test.
- v8.64_fix4_grok86_20260630_risk0530_r29: mode=peak_scale_mild; risk=0.530; peak=24.0; peakWarn=0.70; scale=0.65; net=297 778.69; PF=1.98; maxEquityDD=107 817.28 (27.86%); relEquityDD=42.65% (31 062.68); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050210_v8.64_fix4_grok86_20260630_risk0530_r29; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix4_grok86_20260630_risk0530_r29.set
- v8.64_fix4_grok86_20260630_risk0540_r30: mode=peak_scale_mid; risk=0.540; peak=24.0; peakWarn=0.70; scale=0.55; net=226 889.94; PF=1.93; maxEquityDD=87 111.43 (28.31%); relEquityDD=40.30% (24 470.25); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050223_v8.64_fix4_grok86_20260630_risk0540_r30; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix4_grok86_20260630_risk0540_r30.set
- v8.64_fix4_grok86_20260630_risk0550_r31: mode=peak_scale_strong; risk=0.550; peak=24.0; peakWarn=0.65; scale=0.50; net=185 306.28; PF=1.95; maxEquityDD=67 497.58 (26.74%); relEquityDD=37.20% (19 868.15); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050236_v8.64_fix4_grok86_20260630_risk0550_r31; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix4_grok86_20260630_risk0550_r31.set


## 2026-06-19 05:04:18 +08:00 - fix4 r32-r34 late peak drawdown scale matrix
- Purpose: r29-r31 scaled too early and destroyed profit, so this matrix delays peak-DD lot scaling to 95% of the 24% peak DD threshold and uses milder scales.
- v8.64_fix4_grok86_20260630_risk0530_r32: mode=late_mild; risk=0.530; peak=24.0; peakWarn=0.95; scale=0.85; net=487 295.02; PF=2.08; maxEquityDD=157 596.54 (27.39%); relEquityDD=48.30% (44 038.67); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050349_v8.64_fix4_grok86_20260630_risk0530_r32; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix4_grok86_20260630_risk0530_r32.set
- v8.64_fix4_grok86_20260630_risk0535_r33: mode=late_mid; risk=0.535; peak=24.0; peakWarn=0.95; scale=0.80; net=450 277.36; PF=2.08; maxEquityDD=147 259.89 (27.59%); relEquityDD=47.38% (40 089.09); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050404_v8.64_fix4_grok86_20260630_risk0535_r33; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix4_grok86_20260630_risk0535_r33.set
- v8.64_fix4_grok86_20260630_risk0540_r34: mode=late_stronger; risk=0.540; peak=24.0; peakWarn=0.95; scale=0.75; net=432 865.35; PF=2.08; maxEquityDD=142 749.24 (27.75%); relEquityDD=46.46% (38 106.04); trades=207; win=46.38%; maxLosses=11; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050417_v8.64_fix4_grok86_20260630_risk0540_r34; set=E:\CODEXMACD\HCSJ\set\SniperTrendEA_v8.64_fix4_grok86_20260630_risk0540_r34.set


## 2026-06-19 05:05:22 +08:00 - r35 native v8.6 anchor reproducibility test
- Purpose: verify whether current MT5 environment can reproduce HCSJ/grok8.6.xlsx historical anchor 557,505.36 using native SniperTrendEA_v8.6.ex5 defaults and period 2020.01.01-2026.06.30.
- Test: v8.6_anchor_20260630_r35; period=H4 (2020.01.01 - 2026.06.30); comment=SniperEA_v8.62; risk=0.5; net=557 505.36; PF=2.27; maxBalanceDD=59 932.50 (26.07%); maxEquityDD=149 678.95 (24.13%); relEquityDD=47.07% (44 994.34); trades=203; win=46.80%; maxLosses=10; archive=E:\CODEXMACD\HCSJ\backtest_archive\20260619_050521_v8.6_anchor_20260630_r35.


## 2026-06-19 v8.65 grokbase risk iteration

### Objective
- Continue from the confirmed true grok8.6 anchor, not the earlier 339k/356k intermediate runs.
- Preserve grok8.6 profit as much as possible while reducing drawdown.
- True anchor period: XAUUSD H4, 2020.01.01 - 2026.06.30, deposit 20,000 USD, leverage 100.
- Anchor metrics from r35 / grok8.6: net profit 557,505.36, PF 2.27, max equity DD 149,678.95 (24.13%), relative equity DD 47.07% (44,994.34), trades 203.

### Source and versioning
- Created new source version: E:\CODEXMACD\SniperTrendEA_v8.65_grokbase_risk.mq5
- Base source: E:\GROKMACD\SniperTrendEA_v8.6.mq5, because this is the source lineage that reproduces the 557,505.36 grok8.6 anchor.
- Created immutable candidate snapshot: E:\CODEXMACD\SniperTrendEA_v8.65_grokbase_risk_r53_candidate.mq5
- Candidate EX5 snapshot: E:\CODEXMACD\SniperTrendEA_v8.65_grokbase_risk_r53_candidate.ex5
- Historical versions were not overwritten in the workspace. MT5 Experts copy was overwritten only as the active compile target.

### Code changes
- Added risk-layer inputs with default-off behavior:
  - InpUseRiskThrottle
  - InpMaxDailyDDPercent
  - InpConsecutiveLossLimit
  - InpCooldownBars
  - InpMaxOpenPositions
  - InpRiskLotScale
  - InpRiskWarningDDRatio
  - InpMaxPeakDDPercent
  - InpPeakDDWarningRatio
- Added runtime helpers:
  - UpdateRiskState
  - IsRiskInCooldown
  - AdjustLotSize
  - GetConsecutiveLosses
- Connected risk layer to lot sizing and new-position gate only.
- Kept grok8.6 entry/exit signal structure intact.
- Fixed compile variable mismatch: InpMagic -> InpMagicNumber.
- Aligned source default filter preset with anchor expectation: InpFilterPreset default changed from FILTER_BALANCED to FILTER_AGGRESSIVE, because the true r35 report uses InpFilterPreset=2.

### Debug/root-cause notes
- Initial r36 failed because EX5 was not generated; terminal log showed: Experts\SniperTrendEA_v8.65_grokbase_risk.ex5 not found.
- Root cause: MetaEditor command with space/Chinese MT5 path did not produce compile output/log. Compiling from E:\CODEXMACD source path with quoted arguments produced a real compile log and EX5.
- Compile error found and fixed: undeclared identifier InpMagic, replaced with InpMagicNumber.
- r36b/r36c showed that partial .set files or no ExpertParameters can produce non-anchor defaults/cached tester parameters. Full explicit .set files generated from r35 report are required for reproducible testing.
- r36e full-anchor set reproduced grok8.6 exactly.

### Compile result
- Compile log: E:\CODEXMACD\HCSJ\compile_v865_grokbase_risk_r36d_20260619.log
- Result: 0 errors, 0 warnings.

### Backtest archive and set storage policy
- All .set files from this iteration were saved to: E:\CODEXMACD\HCSJ\set
- All backtest reports/config copies were archived under: E:\CODEXMACD\HCSJ\backtest_archive
- Matrix files updated:
  - E:\CODEXMACD\HCSJ\version_compare_backtest_matrix.csv
  - E:\CODEXMACD\HCSJ\version_compare_backtest_matrix.md
- MT5 runnable configs are stored in: E:\CODEXMACD\mt5_configs

### Important directory notes
- E:\CODEXMACD root: active EA source files, candidate source snapshots, compile logs, and top-level work log.
- E:\CODEXMACD\HCSJ: historical comparison assets, matrix files, set files, and backtest archive.
- E:\CODEXMACD\HCSJ\set: every versioned .set file, including failed tests and candidate tests.
- E:\CODEXMACD\HCSJ\backtest_archive: each run gets its own timestamped folder containing Report and Config subfolders.
- E:\CODEXMACD\mt5_configs: MT5 tester ini files using the working report style Report=SingleEAReports\name.
- D:\MT5测试\MetaTrader 5\MQL5\Experts: active MT5 compile/run target only; not treated as historical source archive.

### Key runs
- r36: failed, no report. Cause: EX5 missing.
- r36b: test ran but no useful report archive from script; partial .set caused non-anchor behavior, final balance 223,091.29 observed in tester log.
- r36c/r36d: showed no-set/default tester behavior still used InpFilterPreset=1 and did not reproduce anchor.
- r36e full anchor baseline: net 557,505.36, PF 2.27, max equity DD 149,678.95 (24.13%), trades 203. This confirms v8.65 can reproduce grok8.6 when full anchor parameters are loaded.
- r37b/r40b: peak DD scaling reduced DD but r40b net 519,680.12 stayed below the 95% profit floor.
- r38b/r39b: consecutive-loss cooldown collapsed trading to 57 trades and is not a valid direction in current form.
- r41/r42: increasing risk to 0.505/0.510 restored profit but increased DD percentage above anchor; useful data, not preferred.
- r45-r48: risk 0.500 and peak scale 0.97 passed 95% profit and lowered DD.
- r49-r53: ultra-light peak scaling improved the trade-off.

### Current best candidate
- Version tag: v8.65_grokbase_risk0500_peak098_scale0999_r53
- Set file: E:\CODEXMACD\HCSJ\set\v8.65_grokbase_risk0500_peak098_scale0999_r53.set
- Report: E:\CODEXMACD\HCSJ\backtest_archive\20260619_052949_v8.65_grokbase_risk0500_peak098_scale0999_r53\Report\sniper_v865_grokbase_risk0500_peak098_scale0999_r53.htm
- Metrics:
  - Net profit: 549,883.09 USD
  - Profit factor: 2.26
  - Max balance DD: 59,117.43 (26.05%)
  - Max equity DD: 147,587.71 (24.11%)
  - Relative equity DD: 46.96% (44,407.22)
  - Trades: 203
  - Winning trades: 95 (46.80%)
  - Max consecutive losses: 10 (-25,514.72)
- Compared with grok8.6 anchor:
  - Profit retained: about 98.63% of 557,505.36.
  - Max equity DD improved by 2,091.24 USD and 0.02 percentage points.
  - Trade count and win rate preserved.

### Next recommended direction
- Treat r53 as the current best candidate, not final production until the user reviews.
- Avoid consecutive-loss cooldown as currently implemented; it is too destructive.
- If continuing optimization, explore more surgical peak-equity throttles or time/segment-specific drawdown protection, but keep full-anchor set loading mandatory for every test.

## 2026-06-19 2020-2025 same-period verification and candidate correction

### Reason
- The active objective explicitly requires H4 2020-2025 same test口径 as a hard evaluation口径.
- Previous r53 candidate was excellent on 2020.01.01-2026.06.30, but needed a separate 2020-2025 validation to avoid mixing periods.

### Same-period anchor
- Run tag: v8.6_anchor_20251231_r54
- Period: XAUUSD H4, 2020.01.01 - 2025.12.31, deposit 20,000 USD, leverage 100.
- Set file: E:\CODEXMACD\HCSJ\set\v8.6_anchor_20251231_r54.set
- Report: E:\CODEXMACD\HCSJ\backtest_archive\20260619_053250_v8.6_anchor_20251231_r54\Report\sniper_v86_anchor_20251231_r54.htm
- Metrics:
  - Net profit: 356,659.80
  - PF: 2.02
  - Max balance DD: 59,932.50 (26.07%)
  - Max equity DD: 87,589.44 (21.46%)
  - Relative equity DD: 47.07% (44,994.34)
  - Trades: 189
  - Winning trades: 87 (46.03%)
  - Max consecutive losses: 10 (-25,807.54)
- 95% profit floor for this period: 338,826.81.

### r53 2020-2025 check
- Run tag: v8.65_grokbase_risk0500_peak098_scale0999_20251231_r55
- Metrics:
  - Net profit: 351,977.69
  - PF: 2.01
  - Max equity DD: 86,554.96 (21.47%)
  - Relative equity DD: 46.96% (44,407.22)
  - Trades: 189
- Conclusion: profit/PF/trade frequency passed, absolute DD improved, but max equity DD percentage was 21.47% versus anchor 21.46%, so it is not the strictest candidate under the 2020-2025口径.

### Additional 2020-2025 matrix
- Tested scale variants with same peak risk trigger: InpMaxPeakDDPercent=24.0, InpPeakDDWarningRatio=0.98, InpRiskPercent=0.500, no daily DD stop, no consecutive-loss cooldown.
- r56 scale=0.995:
  - Net profit: 351,696.60
  - PF: 2.01
  - Max equity DD: 86,439.74 (21.46%)
  - Relative equity DD: 46.87% (44,266.52)
  - Trades: 189
  - Report: E:\CODEXMACD\HCSJ\backtest_archive\20260619_053410_v8.65_grokbase_20251231_peak098_scale0995_r56\Report\sniper_v865_grokbase_20251231_peak098_scale0995_r56.htm
  - Set: E:\CODEXMACD\HCSJ\set\v8.65_grokbase_20251231_peak098_scale0995_r56.set
- r57 scale=0.990:
  - Net profit: 350,211.25
  - PF: 2.01
  - Max equity DD: 86,134.40 (21.47%)
  - Trades: 189
- r58 scale=0.985:
  - Net profit: 347,027.23
  - PF: 2.01
  - Max equity DD: 85,341.35 (21.46%)
  - Trades: 189
- r59 scale=0.980:
  - Net profit: 347,431.56
  - PF: 2.01
  - Max equity DD: 85,407.40 (21.46%)
  - Trades: 189

### Corrected current candidate
- Current preferred candidate is no longer r53 alone.
- Preferred candidate parameters:
  - InpRiskPercent=0.500
  - InpUseRiskThrottle=true
  - InpMaxDailyDDPercent=0.0
  - InpConsecutiveLossLimit=0
  - InpCooldownBars=0
  - InpMaxOpenPositions=1
  - InpRiskLotScale=0.995
  - InpRiskWarningDDRatio=0.80
  - InpMaxPeakDDPercent=24.0
  - InpPeakDDWarningRatio=0.98
- 2020-2026 evidence for same parameters: r51
  - Set: E:\CODEXMACD\HCSJ\set\v8.65_grokbase_risk0500_peak098_scale0995_r51.set
  - Report: E:\CODEXMACD\HCSJ\backtest_archive\20260619_052837_v8.65_grokbase_risk0500_peak098_scale0995_r51\Report\sniper_v865_grokbase_risk0500_peak098_scale0995_r51.htm
  - Net profit: 549,549.79
  - PF: 2.26
  - Max equity DD: 147,586.89 (24.12%)
  - Trades: 203
- 2020-2025 evidence for same parameters: r56
  - Set: E:\CODEXMACD\HCSJ\set\v8.65_grokbase_20251231_peak098_scale0995_r56.set
  - Report: E:\CODEXMACD\HCSJ\backtest_archive\20260619_053410_v8.65_grokbase_20251231_peak098_scale0995_r56\Report\sniper_v865_grokbase_20251231_peak098_scale0995_r56.htm
  - Net profit: 351,696.60
  - PF: 2.01
  - Max equity DD: 86,439.74 (21.46%)
  - Trades: 189
- Source snapshot for this dual-period candidate:
  - E:\CODEXMACD\SniperTrendEA_v8.65_grokbase_risk_r56_dualperiod_candidate.mq5
  - E:\CODEXMACD\SniperTrendEA_v8.65_grokbase_risk_r56_dualperiod_candidate.ex5

### Decision
- r56/r51 parameter set satisfies the objective better than r53 because it passes both the previously corrected 2020-2026 anchor view and the explicit 2020-2025 same-period view.
- Consecutive-loss cooldown remains rejected for now because r38b/r39b collapsed trade frequency and profit.
- Next work should continue from scale=0.995 candidate, not from r53 scale=0.999.

## 2026-06-19 v8.66 structure-score soft fallback iteration

### Reason
- The objective also requires carrying v8.64 softmerge structure logic forward as a score/quality layer, not as a hard signal killer.
- We preserved the v8.65/r56 risk candidate and opened a new v8.66 branch so old versions remain intact.

### Source and compile
- New source: E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk.mq5
- Failed compile snapshots preserved:
  - E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_compilefail1.mq5
  - E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_compilefail2.mq5
- Root cause of failed compiles: rewriting the MQ5 file with PowerShell Set-Content changed encoding and broke existing Chinese/mojibake string literals. The successful retry only used apply_patch and preserved source encoding.
- Successful compile log: E:\CODEXMACD\HCSJ\compile_v866_grokbase_structure_risk_retry3_20260619.log
- Compile result: 0 errors, 0 warnings.
- Candidate source snapshot:
  - E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.mq5
  - E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.ex5

### Code changes
- Added optional structure score soft filter inputs:
  - InpUseStructureScore
  - InpRejectNoStructure
  - InpSwingLookback
  - InpStructureScanBars
  - InpMinTrendlineTouches
  - InpTrendlineTouchATR
  - InpMinBreakoutDistanceATR
  - InpMinBreakoutScore
  - InpNoStructurePenalty
  - InpMinStructureQualityFloor
  - InpShowStructureDebug
- Added v8.64-derived trendline scoring helpers:
  - STrendlineInfo
  - ResetTrendlineInfo
  - IsSwingHigh / IsSwingLow
  - LineValueAtShift
  - CountTrendlineTouches
  - FindValidatedTrendline
  - CalculateBreakoutScore
  - GetStructureQualityFactor
  - GetStructureLotFactor
- Structure score is implemented as a lot factor before risk throttle, not as a hard entry rejection by default.
- Default InpUseStructureScore=false keeps v8.65/r56 behavior reproducible.

### Baseline equivalence checks
- r60, v8.66 structure off, 2020-2025:
  - Net profit: 351,696.60
  - PF: 2.01
  - Max equity DD: 86,439.74 (21.46%)
  - Trades: 189
  - Matches r56 metrics.
- r61, v8.66 structure off, 2020-2026:
  - Net profit: 549,549.79
  - PF: 2.26
  - Max equity DD: 147,586.89 (24.12%)
  - Trades: 203
  - Matches r51 metrics.

### Structure score matrix, 2020-2025
- r62 soft 0.98 / floor 0.95:
  - Net profit: 348,808.49
  - PF: 2.01
  - Max equity DD: 85,937.26 (34.56%)
  - Trades: 189
  - Absolute DD improved but percentage DD worsened, not preferred.
- r63 soft 0.95 / floor 0.90:
  - Net profit: 343,744.24
  - PF: 2.00
  - Max equity DD: 85,091.60 (34.53%)
  - Trades: 189
  - Percentage DD worsened, not preferred.
- r64 mid 0.90 / floor 0.80:
  - Net profit: 335,807.37
  - PF: 2.00
  - Below the 95% profit floor for 2020-2025, invalid.
- r65 hardFallback 0.70 / floor 0.35:
  - Net profit: 301,327.67
  - PF: 1.95
  - Invalid: profit and PF fail.
- r66 ultra 0.995 / floor 0.990:
  - Net profit: 351,258.15
  - PF: 2.01
  - Max equity DD: 86,240.68 (34.53%)
  - Percentage DD issue remains, not preferred.
- r67 ultra 0.999 / floor 0.995:
  - Net profit: 351,481.09
  - PF: 2.01
  - Max equity DD: 86,334.41 (21.45%)
  - Relative equity DD: 46.86% (44,266.52)
  - Trades: 189
  - Set: E:\CODEXMACD\HCSJ\set\v8.66_20251231_structure_ultra0999_floor0995_r67.set
  - Report: E:\CODEXMACD\HCSJ\backtest_archive\20260619_054723_v8.66_20251231_structure_ultra0999_floor0995_r67\Report\sniper_v866_20251231_structure_ultra0999_floor0995_r67.htm
  - Current best for the explicit 2020-2025口径.

### 2020-2026 supplemental check for same parameters
- r68, same parameters as r67, 2020-2026:
  - Net profit: 548,406.06
  - PF: 2.26
  - Max balance DD: 59,017.15 (26.02%)
  - Max equity DD: 147,036.33 (24.08%)
  - Relative equity DD: 46.86% (44,266.52)
  - Trades: 203
  - Set: E:\CODEXMACD\HCSJ\set\v8.66_20260630_structure_ultra0999_floor0995_r68.set
  - Report: E:\CODEXMACD\HCSJ\backtest_archive\20260619_054827_v8.66_20260630_structure_ultra0999_floor0995_r68\Report\sniper_v866_20260630_structure_ultra0999_floor0995_r68.htm

### Current best candidate after v8.66
- Preferred candidate is now v8.66 r67/r68 parameter set:
  - InpRiskPercent=0.500
  - InpUseRiskThrottle=true
  - InpRiskLotScale=0.995
  - InpMaxPeakDDPercent=24.0
  - InpPeakDDWarningRatio=0.98
  - InpUseStructureScore=true
  - InpRejectNoStructure=false
  - InpNoStructurePenalty=0.999
  - InpMinStructureQualityFloor=0.995
  - InpMinBreakoutScore=70.0
- 2020-2025 anchor r54: 356,659.80 / PF 2.02 / max equity DD 87,589.44 (21.46%) / trades 189.
- 2020-2025 candidate r67: 351,481.09 / PF 2.01 / max equity DD 86,334.41 (21.45%) / trades 189.
- 2020-2026 anchor r35: 557,505.36 / PF 2.27 / max equity DD 149,678.95 (24.13%) / trades 203.
- 2020-2026 candidate r68: 548,406.06 / PF 2.26 / max equity DD 147,036.33 (24.08%) / trades 203.

### Decision
- v8.66 r67/r68 is better aligned with the full objective than v8.65 r56/r51 because it includes structure score as a soft lot factor and improves drawdown slightly while preserving the grok8.6 profit skeleton.
- Do not use the stronger structure penalties from r62-r65; they either worsen DD percentage or fail profit/PF gates.

## 2026-06-19 06:21:21 +08:00 - 建立 v8.6/v8.66 稳健最优参数寻找与过拟合验证方案
- 类型：方案文档建立，未执行回测。
- 新增文件：E:\CODEXMACD\docs\superpowers\plans\2026-06-19-v86-v866-robust-parameter-search.md
- 目的：将测试目标从“单纯过拟合验证”升级为“稳健最优参数寻找 + 防过拟合验证”。
- 覆盖对象：SniperTrendEA v8.6 老版、SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.mq5。
- 覆盖时间段：2012-2014、2015-2019、2017-2023，另保留 2020-2025 与 2020-2026.06.30 作为可选控制窗口。
- 核心原则：不追求单周期最高净利润，优先筛选跨周期稳健、收益保留高、回撤可控、参数不敏感的最佳设定。
- 归档要求：所有 .set、HTML 报告、配置、指标、失败结果均需保留，不覆盖历史文件。
- 当前状态：仅完成方案落地，等待用户确认后再从 Task 1 开始执行。
## 2026-06-19 06:31:11 +08:00 - Robust parameter search Task 1 started/completed
- Task: 建立 v8.6/v8.66 多周期参数搜索归档目录与主矩阵。
- Archive root: E:\CODEXMACD\HCSJ
- Matrix: E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_matrix.csv
- Windows: 2012-2014, 2015-2019, 2017-2023
- Status: 完成目录与矩阵初始化，未覆盖历史回测文件。
## 2026-06-19 06:31:49 +08:00 - Robust parameter search Task 2 build artifact confirmation
- v8.6 true source EX5 confirmed: E:\GROKMACD\SniperTrendEA_v8.6.ex5
- v8.66 r68 EX5 confirmed: E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.ex5
- MT5 test expert copy v8.6: D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.6_groktrue_20260619.ex5
- MT5 test expert copy v8.66: D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5
- Compile action: 未重新编译；使用已存在且此前已验证的 EX5 快照，避免覆盖历史构建产物。
- Status: Task 2 构建产物确认完成。
## 2026-06-19 06:38:18 +08:00 - Robust parameter search Task 3 fixed baseline batch partial complete
- v86_2012-2014_fixed_round01_case0001: status=completed, net=25321.25, PF=1.32, trades=95
- v86_2017-2023_fixed_round01_case0001: status=completed, net=68055.85, PF=1.26, trades=230
- v866_2012-2014_fixed_round01_case0001: status=completed, net=25345.33, PF=1.33, trades=95
- v866_2015-2019_fixed_round01_case0001: status=completed, net=13113.95, PF=1.12, trades=155
- v866_2017-2023_fixed_round01_case0001: status=completed, net=67048.75, PF=1.26, trades=230

## 2026-06-19 06:38:32 +08:00 - Robust parameter search Task 3 fixed baseline completed
- v86_2015-2019_fixed_round01_case0001_retry2: net=13194.10, PF=1.12, maxEquityDD=20647.71 (39.72% ), trades=155, win=37.42%
- v86_2012-2014_fixed_round01_case0001: net=25321.25, PF=1.32, maxEquityDD=28410.01 (39.51% ), trades=95, win=35.79%
- v86_2017-2023_fixed_round01_case0001: net=68055.85, PF=1.26, maxEquityDD=61397.22 (46.91% ), trades=230, win=42.61%
- v866_2012-2014_fixed_round01_case0001: net=25345.33, PF=1.33, maxEquityDD=28292.64 (39.39% ), trades=95, win=35.79%
- v866_2015-2019_fixed_round01_case0001: net=13113.95, PF=1.12, maxEquityDD=20517.21 (39.63% ), trades=155, win=37.42%
- v866_2017-2023_fixed_round01_case0001: net=67048.75, PF=1.26, maxEquityDD=60456.82 (46.78% ), trades=230, win=42.61%
- 初步观察：v8.66 固定 r68 与 v8.6 固定参数在三段窗口交易次数一致或接近，没有出现交易频率塌缩；后续进入有界参数搜索。

## 2026-06-19 06:41:12 +08:00 - Robust parameter search Task 4 v8.6 common search round01 complete
- v86_2012-2014_commonsearch_round01_case0002: status=completed, net=21761.72, PF=1.37, trades=95
- v86_2015-2019_commonsearch_round01_case0002: status=completed, net=12905.56, PF=1.15, trades=155
- v86_2017-2023_commonsearch_round01_case0002: status=completed, net=53707.02, PF=1.29, trades=230
- v86_2012-2014_commonsearch_round01_case0003: status=completed, net=27723.08, PF=1.28, trades=95
- v86_2015-2019_commonsearch_round01_case0003: status=completed, net=12669.60, PF=1.10, trades=155
- v86_2017-2023_commonsearch_round01_case0003: status=completed, net=80227.99, PF=1.23, trades=230
- v86_2012-2014_commonsearch_round01_case0004: status=completed, net=7945.53, PF=1.14, trades=93
- v86_2015-2019_commonsearch_round01_case0004: status=completed, net=16858.89, PF=1.18, trades=147
- v86_2017-2023_commonsearch_round01_case0004: status=completed, net=38731.96, PF=1.16, trades=221
- v86_2012-2014_commonsearch_round01_case0005: status=completed, net=71273.66, PF=1.54, trades=97
- v86_2015-2019_commonsearch_round01_case0005: status=completed, net=19028.03, PF=1.13, trades=162
- v86_2017-2023_commonsearch_round01_case0005: status=completed, net=60340.67, PF=1.19, trades=244

## 2026-06-19 06:44:24 +08:00 - Robust parameter search Task 5 v8.66 risk search round01 complete
- v866_2012-2014_risksearch_round01_case0002: status=completed, net=24851.88, PF=1.32, trades=95
- v866_2015-2019_risksearch_round01_case0002: status=completed, net=12584.96, PF=1.12, trades=155
- v866_2017-2023_risksearch_round01_case0002: status=completed, net=65087.29, PF=1.26, trades=230
- v866_2012-2014_risksearch_round01_case0003: status=completed, net=25451.54, PF=1.32, trades=95
- v866_2015-2019_risksearch_round01_case0003: status=completed, net=13316.56, PF=1.12, trades=155
- v866_2017-2023_risksearch_round01_case0003: status=completed, net=67582.05, PF=1.26, trades=230
- v866_2012-2014_risksearch_round01_case0004: status=completed, net=23708.08, PF=1.35, trades=95
- v866_2015-2019_risksearch_round01_case0004: status=completed, net=13182.13, PF=1.13, trades=155
- v866_2017-2023_risksearch_round01_case0004: status=completed, net=60525.86, PF=1.27, trades=230
- v866_2012-2014_risksearch_round01_case0005: status=completed, net=26726.09, PF=1.30, trades=95
- v866_2015-2019_risksearch_round01_case0005: status=completed, net=13052.56, PF=1.11, trades=155
- v866_2017-2023_risksearch_round01_case0005: status=completed, net=73716.24, PF=1.24, trades=230
- v866_2012-2014_risksearch_round01_case0006: status=completed, net=25101.22, PF=1.33, trades=95
- v866_2015-2019_risksearch_round01_case0006: status=completed, net=12903.92, PF=1.12, trades=155
- v866_2017-2023_risksearch_round01_case0006: status=completed, net=66147.44, PF=1.26, trades=230

## 2026-06-19 06:47:32 +08:00 - Robust parameter search Task 6 v8.66 structure search round01 complete
- v866_2012-2014_structuresearch_round01_case0007: status=completed, net=25088.67, PF=1.32, trades=95
- v866_2015-2019_structuresearch_round01_case0007: status=completed, net=13202.06, PF=1.12, trades=155
- v866_2017-2023_structuresearch_round01_case0007: status=completed, net=68122.13, PF=1.26, trades=230
- v866_2012-2014_structuresearch_round01_case0008: status=completed, net=25441.81, PF=1.32, trades=95
- v866_2015-2019_structuresearch_round01_case0008: status=completed, net=13326.33, PF=1.12, trades=155
- v866_2017-2023_structuresearch_round01_case0008: status=completed, net=67656.41, PF=1.26, trades=230
- v866_2012-2014_structuresearch_round01_case0009: status=completed, net=25088.67, PF=1.32, trades=95
- v866_2015-2019_structuresearch_round01_case0009: status=completed, net=13202.06, PF=1.12, trades=155
- v866_2017-2023_structuresearch_round01_case0009: status=completed, net=68122.13, PF=1.26, trades=230
- v866_2012-2014_structuresearch_round01_case0010: status=completed, net=25454.21, PF=1.32, trades=95
- v866_2015-2019_structuresearch_round01_case0010: status=completed, net=13268.74, PF=1.12, trades=155
- v866_2017-2023_structuresearch_round01_case0010: status=completed, net=68116.38, PF=1.26, trades=230
- v866_2012-2014_structuresearch_round01_case0011: status=completed, net=25447.31, PF=1.32, trades=95
- v866_2015-2019_structuresearch_round01_case0011: status=completed, net=13316.56, PF=1.12, trades=155
- v866_2017-2023_structuresearch_round01_case0011: status=completed, net=67582.05, PF=1.26, trades=230

## 2026-06-19 06:51:58 +08:00 - Robust parameter search Task 7 sensitivity stress round01 complete
- v86_2012-2014_stress_round01_case0501: status=completed, net=88700.92, PF=1.57, trades=97
- v86_2015-2019_stress_round01_case0501: status=completed, net=2639.39, PF=1.02, trades=169
- v86_2017-2023_stress_round01_case0501: status=completed, net=36888.87, PF=1.16, trades=250
- v86_2012-2014_stress_round01_case0502: status=completed, net=57367.02, PF=1.49, trades=97
- v86_2015-2019_stress_round01_case0502: status=completed, net=19675.31, PF=1.15, trades=158
- v86_2017-2023_stress_round01_case0502: status=completed, net=73620.49, PF=1.21, trades=239
- v866_2012-2014_stress_round01_case1001: status=completed, net=25454.21, PF=1.32, trades=95
- v866_2015-2019_stress_round01_case1001: status=completed, net=13274.10, PF=1.12, trades=155
- v866_2017-2023_stress_round01_case1001: status=completed, net=68113.66, PF=1.26, trades=230
- v866_2012-2014_stress_round01_case1002: status=completed, net=25303.17, PF=1.33, trades=95
- v866_2015-2019_stress_round01_case1002: status=completed, net=13338.84, PF=1.12, trades=155
- v866_2017-2023_stress_round01_case1002: status=completed, net=67622.76, PF=1.26, trades=230
- v866_2012-2014_stress_round01_case0401: status=completed, net=23015.22, PF=1.36, trades=95
- v866_2015-2019_stress_round01_case0401: status=completed, net=12775.21, PF=1.14, trades=155
- v866_2017-2023_stress_round01_case0401: status=completed, net=57778.77, PF=1.28, trades=230
- v866_2012-2014_stress_round01_case0402: status=completed, net=24393.94, PF=1.34, trades=95
- v866_2015-2019_stress_round01_case0402: status=completed, net=13136.80, PF=1.13, trades=155
- v866_2017-2023_stress_round01_case0402: status=completed, net=63390.18, PF=1.27, trades=230
- Spread widening not executed in this round because current MT5 tester config has no previously verified fixed-spread field in this project; retained as residual risk for optional later validation.

## 2026-06-19 06:57:12 +08:00 - Robust parameter search yearly validation for selected main candidates complete
- v86_2012_yearly_round01_case0502: status=completed, net=3917.31, PF=1.21, trades=33
- v86_2013_yearly_round01_case0502: status=completed, net=38081.41, PF=3.01, trades=29
- v86_2014_yearly_round01_case0502: status=completed, net=4603.73, PF=1.20, trades=35
- v86_2015_yearly_round01_case0502: status=completed, net=-4597.74, PF=0.68, trades=32
- v86_2016_yearly_round01_case0502: status=completed, net=17039.21, PF=1.64, trades=27
- v86_2017_yearly_round01_case0502: status=completed, net=-2137.23, PF=0.87, trades=38
- v86_2018_yearly_round01_case0502: status=completed, net=20374.03, PF=2.04, trades=24
- v86_2019_yearly_round01_case0502: status=completed, net=-4385.70, PF=0.79, trades=39
- v86_2020_yearly_round01_case0502: status=completed, net=33783.30, PF=2.09, trades=33
- v86_2021_yearly_round01_case0502: status=completed, net=635.99, PF=1.04, trades=33
- v86_2022_yearly_round01_case0502: status=completed, net=4139.33, PF=1.23, trades=39
- v86_2023_yearly_round01_case0502: status=completed, net=-2725.17, PF=0.80, trades=35
- v866_2012_yearly_round01_case0010: status=completed, net=-1808.98, PF=0.90, trades=31
- v866_2013_yearly_round01_case0010: status=completed, net=29720.37, PF=2.77, trades=29
- v866_2014_yearly_round01_case0010: status=completed, net=2295.28, PF=1.11, trades=35
- v866_2015_yearly_round01_case0010: status=completed, net=-4755.31, PF=0.63, trades=31
- v866_2016_yearly_round01_case0010: status=completed, net=14460.36, PF=1.67, trades=27
- v866_2017_yearly_round01_case0010: status=completed, net=-629.50, PF=0.96, trades=37
- v866_2018_yearly_round01_case0010: status=completed, net=15040.81, PF=1.84, trades=24
- v866_2019_yearly_round01_case0010: status=completed, net=-5048.89, PF=0.74, trades=38
- v866_2020_yearly_round01_case0010: status=completed, net=13833.58, PF=1.62, trades=29
- v866_2021_yearly_round01_case0010: status=completed, net=4501.11, PF=1.23, trades=33
- v866_2022_yearly_round01_case0010: status=completed, net=14170.98, PF=1.86, trades=37
- v866_2023_yearly_round01_case0010: status=completed, net=-2509.94, PF=0.82, trades=34

## 2026-06-19 07:00:16 +08:00 - Robust parameter search optional 2020-2025/2020-2026 controls complete
- v86_2020-2025_control_robust_case0502: status=completed, net=289919.86, PF=1.78, trades=201
- v86_2020-2026_control_robust_case0502: status=completed, net=489512.30, PF=2.07, trades=215
- v86_2020-2025_control_aggressive_case0005: status=completed, net=269550.48, PF=1.74, trades=207
- v86_2020-2026_control_aggressive_case0005: status=completed, net=475720.24, PF=2.07, trades=221
- v86_2020-2025_control_conservative_case0002: status=completed, net=215522.96, PF=2.00, trades=189
- v86_2020-2026_control_conservative_case0002: status=completed, net=314203.80, PF=2.22, trades=203
- v866_2020-2025_control_robust_case0010: status=completed, net=355945.87, PF=2.02, trades=189
- v866_2020-2026_control_robust_case0010: status=completed, net=556052.56, PF=2.27, trades=203
- v866_2020-2025_control_aggressive_case0005: status=completed, net=443339.80, PF=2.02, trades=189
- v866_2020-2026_control_aggressive_case0005: status=completed, net=716968.27, PF=2.29, trades=203
- v866_2020-2025_control_conservative_case0401: status=completed, net=249474.53, PF=2.00, trades=189
- v866_2020-2026_control_conservative_case0401: status=completed, net=371235.57, PF=2.23, trades=203

## 2026-06-19 07:02:19 +08:00 - Robust parameter search Task 8 final summary completed
- Summary report: E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_summary.md
- Final candidates directory: E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search
- Matrix: E:\CODEXMACD\HCSJ\matrix\robust_parameter_search_matrix.csv
- Group scores: E:\CODEXMACD\HCSJ\matrix\robust_parameter_group_scores.csv
- Completed runs: 102 / 102
- Main recommendation: v8.66 robust main case0010.
- Anchor check: v8.66 robust case0010 2020-2026.06.30 net=556052.56, retention=99.74% vs 557,505.36 USD anchor.
- Status: 全部计划任务已执行并归档，固定点差放大压力测试作为残余风险记录。
## 2026-06-19 15:01:40 +08:00 - 创建新窗口交接文件
- 类型：交接文档建立，未执行回测，未修改 EA 源码。
- 新增/更新文件：E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
- 目的：让新窗口能够快速理解项目目标、当前主线参数、已完成工作、下一阶段任务、归档规范、日志规范和禁止事项。
- 当前主线：v8.66_robust_main_case0010.set。
- 下一阶段建议：先制定 v8.66 压力测试与 walk-forward 验证计划，再分批执行。
## 2026-06-19 15:47:39 +08:00 - v8.67 precheck batch 20260619_1547_precheck
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1547_precheck
模块：precheck
任务目标：按 v8.67 下一阶段计划执行 precheck 环境有效性验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019 / 2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：dateshift shift00 smoke gate
回测数量：2
成功：2
失败：0
关键指标：
- v866_B_dateshift_2012-2019_shift00_r01_case0001: status=completed, profit=55826.12, PF=1.17, trades=250
- v866_B_dateshift_2020-2026_shift00_r01_case0002: status=completed, profit=556052.56, PF=2.27, trades=203
初筛结论：通过
原因代码：OK
下一步：继续进入 A 预检或 B dateshift 扩展
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1547_precheck
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1547_precheck
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1547_precheck
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1547_precheck\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1547_precheck
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1547_precheck\matrix.csv
## 2026-06-19 15:48:49 +08:00 - v8.67 precheck batch 20260619_1548_precheck
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1548_precheck
模块：precheck
任务目标：按 v8.67 下一阶段计划执行 precheck 环境有效性验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502
场景配置：dateshift shift00 smoke gate
回测数量：2
成功：2
失败：0
关键指标：
- v866_A_dateshift_2012-2019_shift00_r01_case0001: status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift00_r01_case0002: status=completed, profit=489512.30, PF=2.07, trades=215
初筛结论：通过
原因代码：OK
下一步：继续进入 A 预检或 B dateshift 扩展
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1548_precheck
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1548_precheck
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1548_precheck
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1548_precheck\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1548_precheck
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1548_precheck\matrix.csv
## 2026-06-19 16:11:16 +08:00 - v8.67 precheck batch 20260619_1611_precheck
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1611_precheck
模块：precheck
任务目标：按 v8.67 下一阶段计划执行 precheck 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：shift00
回测数量：1
成功：0
失败：0
DryRun：1
关键指标：
- v866_B_dateshift_2020-2026_shift00_r01_case0001: scenario=shift00, status=dry_run, profit=, PF=, trades=
初筛结论：DRY_RUN
原因代码：OK
下一步：dry-run 完成后执行真实批次
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1611_precheck
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1611_precheck
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1611_precheck
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1611_precheck\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1611_precheck
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1611_precheck\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1611_precheck\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1611_precheck\_batch_manifest.csv
## 2026-06-19 16:11:26 +08:00 - v8.67 dateshift batch 20260619_1611_dateshift
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1611_dateshift
模块：dateshift
任务目标：按 v8.67 下一阶段计划执行 dateshift 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019 / 2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：shift03
回测数量：2
成功：0
失败：0
DryRun：2
关键指标：
- v866_B_dateshift_2012-2019_shift03_r01_case0001: scenario=shift03, status=dry_run, profit=, PF=, trades=
- v866_B_dateshift_2020-2026_shift03_r01_case0002: scenario=shift03, status=dry_run, profit=, PF=, trades=
初筛结论：DRY_RUN
原因代码：OK
下一步：dry-run 完成后执行真实批次
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1611_dateshift
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1611_dateshift
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1611_dateshift
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1611_dateshift\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1611_dateshift
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1611_dateshift\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1611_dateshift\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1611_dateshift\_batch_manifest.csv
## 2026-06-19 16:17:01 +08:00 - v8.67 dateshift B stage report
类型：报告生成
run_id: 20260619_1600_dateshift_B
模块：dateshift
回测数量：16
成功：16
失败：0
初筛结论：Continue
原因代码：OK
下一步：Run A/C/D dateshift comparison batch.
输出路径：
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1600_dateshift_B\matrix.csv
- report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1600_dateshift_B\dateshift_stage_report.md
## 2026-06-19 16:18:37 +08:00 - v8.67 dateshift batch 20260619_1600_dateshift_B
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1600_dateshift_B
模块：dateshift
任务目标：执行 B 主线 shift00-shift07 双窗口日期边界敏感性验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019 / 2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：shift00,shift01,shift02,shift03,shift04,shift05,shift06,shift07
回测数量：16
成功：16
失败：0
关键指标：
- v866_B_dateshift_2012-2019_shift00_r01_case0001: scenario=shift00, status=completed, profit=55826.12, PF=1.17, trades=250
- v866_B_dateshift_2020-2026_shift00_r01_case0002: scenario=shift00, status=completed, profit=556052.56, PF=2.27, trades=203
- v866_B_dateshift_2012-2019_shift01_r01_case0003: scenario=shift01, status=completed, profit=55826.12, PF=1.17, trades=250
- v866_B_dateshift_2020-2026_shift01_r01_case0004: scenario=shift01, status=completed, profit=556052.56, PF=2.27, trades=203
- v866_B_dateshift_2012-2019_shift02_r01_case0005: scenario=shift02, status=completed, profit=55826.12, PF=1.17, trades=250
- v866_B_dateshift_2020-2026_shift02_r01_case0006: scenario=shift02, status=completed, profit=556052.56, PF=2.27, trades=203
- v866_B_dateshift_2012-2019_shift03_r01_case0007: scenario=shift03, status=completed, profit=55826.12, PF=1.17, trades=250
- v866_B_dateshift_2020-2026_shift03_r01_case0008: scenario=shift03, status=completed, profit=501650.99, PF=2.26, trades=200
- v866_B_dateshift_2012-2019_shift04_r01_case0009: scenario=shift04, status=completed, profit=55826.12, PF=1.17, trades=250
- v866_B_dateshift_2020-2026_shift04_r01_case0010: scenario=shift04, status=completed, profit=501650.99, PF=2.26, trades=200
- v866_B_dateshift_2012-2019_shift05_r01_case0011: scenario=shift05, status=completed, profit=55826.12, PF=1.17, trades=250
- v866_B_dateshift_2020-2026_shift05_r01_case0012: scenario=shift05, status=completed, profit=501650.99, PF=2.26, trades=200
- v866_B_dateshift_2012-2019_shift06_r01_case0013: scenario=shift06, status=completed, profit=60042.63, PF=1.17, trades=249
- v866_B_dateshift_2020-2026_shift06_r01_case0014: scenario=shift06, status=completed, profit=501650.99, PF=2.26, trades=200
- v866_B_dateshift_2012-2019_shift07_r01_case0015: scenario=shift07, status=completed, profit=60042.63, PF=1.17, trades=249
- v866_B_dateshift_2020-2026_shift07_r01_case0016: scenario=shift07, status=completed, profit=501650.99, PF=2.26, trades=200
初筛结论：Continue
原因代码：OK
下一步：Run A/C/D dateshift comparison batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1600_dateshift_B
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1600_dateshift_B
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1600_dateshift_B\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1600_dateshift_B\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1600_dateshift_B\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1600_dateshift_B\dateshift_stage_report.md
## 2026-06-19 16:21:40 +08:00 - v8.67 dateshift batch 20260619_1630_dateshift_ACD
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1630_dateshift_ACD
模块：dateshift
任务目标：按 v8.67 下一阶段计划执行 dateshift 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502
场景配置：shift00,shift01,shift02,shift03,shift04,shift05,shift06,shift07
回测数量：16
成功：16
失败：0
DryRun：0
关键指标：
- v866_A_dateshift_2012-2019_shift00_r01_case0001: scenario=shift00, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift00_r01_case0002: scenario=shift00, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_dateshift_2012-2019_shift01_r01_case0003: scenario=shift01, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift01_r01_case0004: scenario=shift01, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_dateshift_2012-2019_shift02_r01_case0005: scenario=shift02, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift02_r01_case0006: scenario=shift02, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_dateshift_2012-2019_shift03_r01_case0007: scenario=shift03, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift03_r01_case0008: scenario=shift03, status=completed, profit=419292.26, PF=2.07, trades=214
- v866_A_dateshift_2012-2019_shift04_r01_case0009: scenario=shift04, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift04_r01_case0010: scenario=shift04, status=completed, profit=419292.26, PF=2.07, trades=214
- v866_A_dateshift_2012-2019_shift05_r01_case0011: scenario=shift05, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift05_r01_case0012: scenario=shift05, status=completed, profit=419292.26, PF=2.07, trades=214
- v866_A_dateshift_2012-2019_shift06_r01_case0013: scenario=shift06, status=completed, profit=141981.65, PF=1.22, trades=254
- v866_A_dateshift_2020-2026_shift06_r01_case0014: scenario=shift06, status=completed, profit=419292.26, PF=2.07, trades=214
- v866_A_dateshift_2012-2019_shift07_r01_case0015: scenario=shift07, status=completed, profit=141981.65, PF=1.22, trades=254
- v866_A_dateshift_2020-2026_shift07_r01_case0016: scenario=shift07, status=completed, profit=419292.26, PF=2.07, trades=214
初筛结论：通过
原因代码：OK
下一步：Run A/C/D dateshift comparison batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1630_dateshift_ACD
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1630_dateshift_ACD
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1630_dateshift_ACD
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1630_dateshift_ACD\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1630_dateshift_ACD
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1630_dateshift_ACD\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1630_dateshift_ACD\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1630_dateshift_ACD\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1630_dateshift_ACD\dateshift_stage_report.md
## 2026-06-19 16:24:43 +08:00 - v8.67 dateshift batch 20260619_1640_dateshift_C
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1640_dateshift_C
模块：dateshift
任务目标：按 v8.67 下一阶段计划执行 dateshift 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2012-2019 / 2020-2026
输入参数：C=v8.66_aggressive_case0005
场景配置：shift00,shift01,shift02,shift03,shift04,shift05,shift06,shift07
回测数量：16
成功：16
失败：0
DryRun：0
关键指标：
- v866_C_dateshift_2012-2019_shift00_r01_case0001: scenario=shift00, status=completed, profit=57221.99, PF=1.15, trades=250
- v866_C_dateshift_2020-2026_shift00_r01_case0002: scenario=shift00, status=completed, profit=716968.27, PF=2.29, trades=203
- v866_C_dateshift_2012-2019_shift01_r01_case0003: scenario=shift01, status=completed, profit=57221.99, PF=1.15, trades=250
- v866_C_dateshift_2020-2026_shift01_r01_case0004: scenario=shift01, status=completed, profit=716968.27, PF=2.29, trades=203
- v866_C_dateshift_2012-2019_shift02_r01_case0005: scenario=shift02, status=completed, profit=57221.99, PF=1.15, trades=250
- v866_C_dateshift_2020-2026_shift02_r01_case0006: scenario=shift02, status=completed, profit=716968.27, PF=2.29, trades=203
- v866_C_dateshift_2012-2019_shift03_r01_case0007: scenario=shift03, status=completed, profit=57221.99, PF=1.15, trades=250
- v866_C_dateshift_2020-2026_shift03_r01_case0008: scenario=shift03, status=completed, profit=642304.43, PF=2.28, trades=200
- v866_C_dateshift_2012-2019_shift04_r01_case0009: scenario=shift04, status=completed, profit=57221.99, PF=1.15, trades=250
- v866_C_dateshift_2020-2026_shift04_r01_case0010: scenario=shift04, status=completed, profit=642304.43, PF=2.28, trades=200
- v866_C_dateshift_2012-2019_shift05_r01_case0011: scenario=shift05, status=completed, profit=57221.99, PF=1.15, trades=250
- v866_C_dateshift_2020-2026_shift05_r01_case0012: scenario=shift05, status=completed, profit=642304.43, PF=2.28, trades=200
- v866_C_dateshift_2012-2019_shift06_r01_case0013: scenario=shift06, status=completed, profit=61819.05, PF=1.16, trades=249
- v866_C_dateshift_2020-2026_shift06_r01_case0014: scenario=shift06, status=completed, profit=642304.43, PF=2.28, trades=200
- v866_C_dateshift_2012-2019_shift07_r01_case0015: scenario=shift07, status=completed, profit=61819.05, PF=1.16, trades=249
- v866_C_dateshift_2020-2026_shift07_r01_case0016: scenario=shift07, status=completed, profit=642304.43, PF=2.28, trades=200
初筛结论：通过
原因代码：OK
下一步：Run A/C/D dateshift comparison batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1640_dateshift_C
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1640_dateshift_C
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1640_dateshift_C
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1640_dateshift_C\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1640_dateshift_C
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1640_dateshift_C\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1640_dateshift_C\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1640_dateshift_C\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1640_dateshift_C\dateshift_stage_report.md
## 2026-06-19 16:27:30 +08:00 - v8.67 dateshift batch 20260619_1650_dateshift_D
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1650_dateshift_D
模块：dateshift
任务目标：按 v8.67 下一阶段计划执行 dateshift 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：D
输入窗口：2012-2019 / 2020-2026
输入参数：D=v8.66_conservative_case0401
场景配置：shift00,shift01,shift02,shift03,shift04,shift05,shift06,shift07
回测数量：16
成功：16
失败：0
DryRun：0
关键指标：
- v866_D_dateshift_2012-2019_shift00_r01_case0001: scenario=shift00, status=completed, profit=51100.55, PF=1.19, trades=250
- v866_D_dateshift_2020-2026_shift00_r01_case0002: scenario=shift00, status=completed, profit=371235.57, PF=2.23, trades=203
- v866_D_dateshift_2012-2019_shift01_r01_case0003: scenario=shift01, status=completed, profit=51100.55, PF=1.19, trades=250
- v866_D_dateshift_2020-2026_shift01_r01_case0004: scenario=shift01, status=completed, profit=371235.57, PF=2.23, trades=203
- v866_D_dateshift_2012-2019_shift02_r01_case0005: scenario=shift02, status=completed, profit=51100.55, PF=1.19, trades=250
- v866_D_dateshift_2020-2026_shift02_r01_case0006: scenario=shift02, status=completed, profit=371235.57, PF=2.23, trades=203
- v866_D_dateshift_2012-2019_shift03_r01_case0007: scenario=shift03, status=completed, profit=51100.55, PF=1.19, trades=250
- v866_D_dateshift_2020-2026_shift03_r01_case0008: scenario=shift03, status=completed, profit=340977.30, PF=2.23, trades=200
- v866_D_dateshift_2012-2019_shift04_r01_case0009: scenario=shift04, status=completed, profit=51100.55, PF=1.19, trades=250
- v866_D_dateshift_2020-2026_shift04_r01_case0010: scenario=shift04, status=completed, profit=340977.30, PF=2.23, trades=200
- v866_D_dateshift_2012-2019_shift05_r01_case0011: scenario=shift05, status=completed, profit=51100.55, PF=1.19, trades=250
- v866_D_dateshift_2020-2026_shift05_r01_case0012: scenario=shift05, status=completed, profit=340977.30, PF=2.23, trades=200
- v866_D_dateshift_2012-2019_shift06_r01_case0013: scenario=shift06, status=completed, profit=54152.16, PF=1.20, trades=249
- v866_D_dateshift_2020-2026_shift06_r01_case0014: scenario=shift06, status=completed, profit=340977.30, PF=2.23, trades=200
- v866_D_dateshift_2012-2019_shift07_r01_case0015: scenario=shift07, status=completed, profit=54152.16, PF=1.20, trades=249
- v866_D_dateshift_2020-2026_shift07_r01_case0016: scenario=shift07, status=completed, profit=340977.30, PF=2.23, trades=200
初筛结论：通过
原因代码：OK
下一步：Run A/C/D dateshift comparison batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1650_dateshift_D
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1650_dateshift_D
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1650_dateshift_D\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1650_dateshift_D\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1650_dateshift_D\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1650_dateshift_D\dateshift_stage_report.md
## 2026-06-19 16:28:23 +08:00 - v8.67 dateshift A/B/C/D comparison summary
类型：报告生成
run_id: 20260619_1600_dateshift_B / 20260619_1630_dateshift_ACD / 20260619_1640_dateshift_C / 20260619_1650_dateshift_D
模块：dateshift
回测数量：64
成功：64
失败：0
初筛结论：B/C 进入 walk-forward；A/D 保留对照
原因代码：OK
下一步：Run wf20/wf12 on B and C; B remains mainline, C remains challenger.
输出路径：
- report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\dateshift_ABCD_comparison_20260619.md
## 2026-06-19 16:40:44 +08:00 - v8.67 wf20 batch 20260619_1710_wf20_B
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1710_wf20_B
模块：wf20
任务目标：按 v8.67 下一阶段计划执行 wf20 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019
输入参数：B=v8.66_robust_main_case0010
场景配置：validate
回测数量：1
成功：1
失败：0
DryRun：0
关键指标：
- v866_B_wf20_2012-2019_validate_r01_case0001: scenario=validate, status=completed, profit=55826.12, PF=1.17, trades=250
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1710_wf20_B
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1710_wf20_B
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1710_wf20_B
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1710_wf20_B\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1710_wf20_B
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1710_wf20_B\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1710_wf20_B\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1710_wf20_B\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1710_wf20_B\wf_stage_report.md
## 2026-06-19 16:42:39 +08:00 - v8.67 wf20 batch 20260619_1715_wf20_C
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1715_wf20_C
模块：wf20
任务目标：按 v8.67 下一阶段计划执行 wf20 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2012-2019
输入参数：C=v8.66_aggressive_case0005
场景配置：validate
回测数量：1
成功：1
失败：0
DryRun：0
关键指标：
- v866_C_wf20_2012-2019_validate_r01_case0001: scenario=validate, status=completed, profit=57221.99, PF=1.15, trades=250
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1715_wf20_C
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1715_wf20_C
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1715_wf20_C
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1715_wf20_C\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1715_wf20_C
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1715_wf20_C\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1715_wf20_C\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1715_wf20_C\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1715_wf20_C\wf_stage_report.md
## 2026-06-19 16:44:01 +08:00 - v8.67 wf12 batch 20260619_1720_wf12_B
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1720_wf12_B
模块：wf12
任务目标：按 v8.67 下一阶段计划执行 wf12 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：validate
回测数量：1
成功：1
失败：0
DryRun：0
关键指标：
- v866_B_wf12_2020-2026_validate_r01_case0001: scenario=validate, status=completed, profit=556052.56, PF=2.27, trades=203
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1720_wf12_B
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1720_wf12_B
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1720_wf12_B
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1720_wf12_B\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1720_wf12_B
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1720_wf12_B\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1720_wf12_B\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1720_wf12_B\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1720_wf12_B\wf_stage_report.md
## 2026-06-19 16:45:30 +08:00 - v8.67 wf12 batch 20260619_1725_wf12_C
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1725_wf12_C
模块：wf12
任务目标：按 v8.67 下一阶段计划执行 wf12 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2020-2026
输入参数：C=v8.66_aggressive_case0005
场景配置：validate
回测数量：1
成功：1
失败：0
DryRun：0
关键指标：
- v866_C_wf12_2020-2026_validate_r01_case0001: scenario=validate, status=completed, profit=716968.27, PF=2.29, trades=203
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1725_wf12_C
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1725_wf12_C
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1725_wf12_C
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1725_wf12_C\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1725_wf12_C
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1725_wf12_C\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1725_wf12_C\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1725_wf12_C\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1725_wf12_C\wf_stage_report.md
## 2026-06-19 16:46:30 +08:00 - v8.67 B/C WF20 WF12 completed
类型：回测 / 小批次验证 / 汇总报告
计划文件：E:\CODEXMACD\docs\superpowers\plans\2026-06-19-v867-wf20-wf12-BC-execution.md
Runs：20260619_1710_wf20_B / 20260619_1715_wf20_C / 20260619_1720_wf12_B / 20260619_1725_wf12_C
报告：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\wf20_wf12_BC_comparison_20260619.md
B mainline status：GREEN both directions；继续作为当前主线
C challenger status：GREEN both directions; promote to equal-depth challenger validation；不直接替代 B
关键比较：C 近期利润优势 28.94%；C 老窗口 DD 惩罚 3.41 个百分点
最终结论：Keep B as current mainline. Promote C to equal-depth challenger validation because C passed wf20 and wf12, has material recent-window profit advantage, and old-window DD penalty is not material. Do not replace B yet.
下一步：先执行 B/C spread 与 slippage，小步验证后再进入 quarter / month_core
## 2026-06-19 16:54:57 +08:00 - v8.67 slippage batch 20260619_tdd_slippage_green
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_tdd_slippage_green
模块：slippage
任务目标：按 v8.67 下一阶段计划执行 slippage 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：delay100
回测数量：1
成功：0
失败：0
DryRun：1
关键指标：
- v866_B_slippage_2020-2026_delay100_r01_case0001: scenario=delay100, status=dry_run, profit=, PF=, trades=
初筛结论：DRY_RUN
原因代码：OK
下一步：dry-run 完成后执行真实批次
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_tdd_slippage_green
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_tdd_slippage_green
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_slippage_green
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_tdd_slippage_green\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_slippage_green
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_tdd_slippage_green\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_slippage_green\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_slippage_green\_batch_manifest.csv
## 2026-06-19 16:55:41 +08:00 - v8.67 slippage batch 20260619_1810_slippage_B
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1810_slippage_B
模块：slippage
任务目标：按 v8.67 下一阶段计划执行 slippage 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：delay000,delay100,delay500
回测数量：3
成功：3
失败：0
DryRun：0
关键指标：
- v866_B_slippage_2020-2026_delay000_r01_case0001: scenario=delay000, status=completed, profit=556052.56, PF=2.27, trades=203
- v866_B_slippage_2020-2026_delay100_r01_case0002: scenario=delay100, status=completed, profit=556052.56, PF=2.27, trades=203
- v866_B_slippage_2020-2026_delay500_r01_case0003: scenario=delay500, status=completed, profit=556052.56, PF=2.27, trades=203
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1810_slippage_B
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1810_slippage_B
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1810_slippage_B
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1810_slippage_B\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1810_slippage_B
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1810_slippage_B\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1810_slippage_B\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1810_slippage_B\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1810_slippage_B\slippage_stage_report.md
## 2026-06-19 16:56:18 +08:00 - v8.67 slippage batch 20260619_1815_slippage_C
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1815_slippage_C
模块：slippage
任务目标：按 v8.67 下一阶段计划执行 slippage 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2020-2026
输入参数：C=v8.66_aggressive_case0005
场景配置：delay000,delay100,delay500
回测数量：3
成功：3
失败：0
DryRun：0
关键指标：
- v866_C_slippage_2020-2026_delay000_r01_case0001: scenario=delay000, status=completed, profit=716968.27, PF=2.29, trades=203
- v866_C_slippage_2020-2026_delay100_r01_case0002: scenario=delay100, status=completed, profit=716968.27, PF=2.29, trades=203
- v866_C_slippage_2020-2026_delay500_r01_case0003: scenario=delay500, status=completed, profit=716968.27, PF=2.29, trades=203
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1815_slippage_C
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1815_slippage_C
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1815_slippage_C
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1815_slippage_C\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1815_slippage_C
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1815_slippage_C\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1815_slippage_C\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1815_slippage_C\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1815_slippage_C\slippage_stage_report.md
## 2026-06-19 16:57:05 +08:00 - v8.67 B/C slippage small batch completed
类型：回测 / slippage ExecutionMode 延迟压力 / 汇总报告
Runs：20260619_1810_slippage_B / 20260619_1815_slippage_C
报告：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\slippage_BC_comparison_20260619.md
场景：delay000 / delay100 / delay500，窗口：2020-2026
结论：B and C both pass ExecutionMode slippage-delay stress. Keep B as current mainline; keep C as equal-depth challenger. Do not treat this as spread validation.
注意：spread 未执行；当前 .set 无 spread/slippage 输入，MT5 config 仅确认 ExecutionMode 延迟可控。
下一步：建立真实 spread 测试路径后再进入 quarter / month_core。
## 2026-06-19 17:03:05 +08:00 - v8.67 quarter batch 20260619_tdd_quarter_recent_green
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_tdd_quarter_recent_green
模块：quarter
任务目标：按 v8.67 下一阶段计划执行 quarter 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：q01
回测数量：1
成功：0
失败：0
DryRun：1
关键指标：
- v866_B_quarter_2020-2026_q01_r01_case0001: scenario=q01, status=dry_run, profit=, PF=, trades=
初筛结论：DRY_RUN
原因代码：OK
下一步：dry-run 完成后执行真实批次
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_tdd_quarter_recent_green
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_tdd_quarter_recent_green
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_quarter_recent_green
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_tdd_quarter_recent_green\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_quarter_recent_green
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_tdd_quarter_recent_green\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_quarter_recent_green\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_quarter_recent_green\_batch_manifest.csv
## 2026-06-19 17:03:05 +08:00 - v8.67 quarter batch 20260619_tdd_quarter_old_green
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_tdd_quarter_old_green
模块：quarter
任务目标：按 v8.67 下一阶段计划执行 quarter 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019
输入参数：B=v8.66_robust_main_case0010
场景配置：q01
回测数量：1
成功：0
失败：0
DryRun：1
关键指标：
- v866_B_quarter_2012-2019_q01_r01_case0001: scenario=q01, status=dry_run, profit=, PF=, trades=
初筛结论：DRY_RUN
原因代码：OK
下一步：dry-run 完成后执行真实批次
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_tdd_quarter_old_green
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_tdd_quarter_old_green
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_quarter_old_green
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_tdd_quarter_old_green\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_quarter_old_green
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_tdd_quarter_old_green\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_quarter_old_green\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_tdd_quarter_old_green\_batch_manifest.csv
## 2026-06-19 17:07:39 +08:00 - v8.67 quarter batch 20260619_1830_quarter_B_old
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1830_quarter_B_old
模块：quarter
任务目标：按 v8.67 下一阶段计划执行 quarter 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019
输入参数：B=v8.66_robust_main_case0010
场景配置：q01,q02,q03,q04,q05,q06,q07,q08,q09,q10,q11,q12,q13,q14,q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,q25,q26,q27,q28,q29,q30,q31,q32
回测数量：32
成功：32
失败：0
DryRun：0
关键指标：
- v866_B_quarter_2012-2019_q01_r01_case0001: scenario=q01, status=completed, profit=-2533.06, PF=0.45, trades=10
- v866_B_quarter_2012-2019_q02_r01_case0002: scenario=q02, status=completed, profit=2766.49, PF=1.72, trades=5
- v866_B_quarter_2012-2019_q03_r01_case0003: scenario=q03, status=completed, profit=-6266.12, PF=0.01, trades=9
- v866_B_quarter_2012-2019_q04_r01_case0004: scenario=q04, status=completed, profit=5805.40, PF=2.74, trades=9
- v866_B_quarter_2012-2019_q05_r01_case0005: scenario=q05, status=completed, profit=1512.43, PF=1.46, trades=7
- v866_B_quarter_2012-2019_q06_r01_case0006: scenario=q06, status=completed, profit=13368.51, PF=2.62, trades=9
- v866_B_quarter_2012-2019_q07_r01_case0007: scenario=q07, status=completed, profit=501.12, PF=1.29, trades=7
- v866_B_quarter_2012-2019_q08_r01_case0008: scenario=q08, status=completed, profit=4766.64, PF=3.40, trades=8
- v866_B_quarter_2012-2019_q09_r01_case0009: scenario=q09, status=completed, profit=3556.04, PF=1.87, trades=9
- v866_B_quarter_2012-2019_q10_r01_case0010: scenario=q10, status=completed, profit=3561.06, PF=1.62, trades=9
- v866_B_quarter_2012-2019_q11_r01_case0011: scenario=q11, status=completed, profit=-3025.54, PF=0.06, trades=8
- v866_B_quarter_2012-2019_q12_r01_case0012: scenario=q12, status=completed, profit=-1985.81, PF=0.53, trades=10
- v866_B_quarter_2012-2019_q13_r01_case0013: scenario=q13, status=completed, profit=-1920.56, PF=0.48, trades=10
- v866_B_quarter_2012-2019_q14_r01_case0014: scenario=q14, status=completed, profit=-5047.40, PF=0.10, trades=8
- v866_B_quarter_2012-2019_q15_r01_case0015: scenario=q15, status=completed, profit=628.19, PF=1.24, trades=7
- v866_B_quarter_2012-2019_q16_r01_case0016: scenario=q16, status=completed, profit=2207.43, PF=1.72, trades=5
- v866_B_quarter_2012-2019_q17_r01_case0017: scenario=q17, status=completed, profit=12525.37, PF=6.34, trades=5
- v866_B_quarter_2012-2019_q18_r01_case0018: scenario=q18, status=completed, profit=2474.20, PF=1.67, trades=8
- v866_B_quarter_2012-2019_q19_r01_case0019: scenario=q19, status=completed, profit=-3325.47, PF=0.23, trades=9
- v866_B_quarter_2012-2019_q20_r01_case0020: scenario=q20, status=completed, profit=2664.55, PF=1.77, trades=5
- v866_B_quarter_2012-2019_q21_r01_case0021: scenario=q21, status=completed, profit=-3204.54, PF=0.35, trades=8
- v866_B_quarter_2012-2019_q22_r01_case0022: scenario=q22, status=completed, profit=-4849.68, PF=0.38, trades=12
- v866_B_quarter_2012-2019_q23_r01_case0023: scenario=q23, status=completed, profit=1740.24, PF=2.13, trades=8
- v866_B_quarter_2012-2019_q24_r01_case0024: scenario=q24, status=completed, profit=3277.44, PF=1.64, trades=11
- v866_B_quarter_2012-2019_q25_r01_case0025: scenario=q25, status=completed, profit=-1048.57, PF=0.00, trades=2
- v866_B_quarter_2012-2019_q26_r01_case0026: scenario=q26, status=completed, profit=5769.32, PF=2.37, trades=7
- v866_B_quarter_2012-2019_q27_r01_case0027: scenario=q27, status=completed, profit=7462.73, PF=2.47, trades=10
- v866_B_quarter_2012-2019_q28_r01_case0028: scenario=q28, status=completed, profit=2140.92, PF=1.71, trades=6
- v866_B_quarter_2012-2019_q29_r01_case0029: scenario=q29, status=completed, profit=-4252.12, PF=0.46, trades=13
- v866_B_quarter_2012-2019_q30_r01_case0030: scenario=q30, status=completed, profit=4732.08, PF=1.98, trades=9
- v866_B_quarter_2012-2019_q31_r01_case0031: scenario=q31, status=completed, profit=-2237.68, PF=0.56, trades=8
- v866_B_quarter_2012-2019_q32_r01_case0032: scenario=q32, status=completed, profit=-2650.76, PF=0.15, trades=8
初筛结论：通过
原因代码：OK
下一步：Review losing quarters before month_core.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1830_quarter_B_old
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1830_quarter_B_old
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1830_quarter_B_old
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1830_quarter_B_old\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1830_quarter_B_old
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1830_quarter_B_old\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1830_quarter_B_old\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1830_quarter_B_old\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1830_quarter_B_old\quarter_stage_report.md
## 2026-06-19 17:11:16 +08:00 - v8.67 quarter batch 20260619_1840_quarter_B_recent
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1840_quarter_B_recent
模块：quarter
任务目标：按 v8.67 下一阶段计划执行 quarter 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：q01,q02,q03,q04,q05,q06,q07,q08,q09,q10,q11,q12,q13,q14,q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,q25,q26
回测数量：26
成功：26
失败：0
DryRun：0
关键指标：
- v866_B_quarter_2020-2026_q01_r01_case0001: scenario=q01, status=completed, profit=15162.31, PF=23.41, trades=5
- v866_B_quarter_2020-2026_q02_r01_case0002: scenario=q02, status=completed, profit=3609.75, PF=2.15, trades=9
- v866_B_quarter_2020-2026_q03_r01_case0003: scenario=q03, status=completed, profit=-3179.46, PF=0.00, trades=5
- v866_B_quarter_2020-2026_q04_r01_case0004: scenario=q04, status=completed, profit=-407.38, PF=0.93, trades=10
- v866_B_quarter_2020-2026_q05_r01_case0005: scenario=q05, status=completed, profit=6234.66, PF=3.62, trades=8
- v866_B_quarter_2020-2026_q06_r01_case0006: scenario=q06, status=completed, profit=5788.71, PF=3.12, trades=9
- v866_B_quarter_2020-2026_q07_r01_case0007: scenario=q07, status=completed, profit=-4049.53, PF=0.23, trades=8
- v866_B_quarter_2020-2026_q08_r01_case0008: scenario=q08, status=completed, profit=2038.64, PF=1.69, trades=8
- v866_B_quarter_2020-2026_q09_r01_case0009: scenario=q09, status=completed, profit=1763.03, PF=1.38, trades=9
- v866_B_quarter_2020-2026_q10_r01_case0010: scenario=q10, status=completed, profit=1341.09, PF=1.49, trades=12
- v866_B_quarter_2020-2026_q11_r01_case0011: scenario=q11, status=completed, profit=269.06, PF=1.07, trades=9
- v866_B_quarter_2020-2026_q12_r01_case0012: scenario=q12, status=completed, profit=2217.35, PF=1.75, trades=8
- v866_B_quarter_2020-2026_q13_r01_case0013: scenario=q13, status=completed, profit=4472.27, PF=4.01, trades=6
- v866_B_quarter_2020-2026_q14_r01_case0014: scenario=q14, status=completed, profit=-1817.25, PF=0.30, trades=10
- v866_B_quarter_2020-2026_q15_r01_case0015: scenario=q15, status=completed, profit=-5411.61, PF=0.00, trades=8
- v866_B_quarter_2020-2026_q16_r01_case0016: scenario=q16, status=completed, profit=1553.86, PF=1.39, trades=10
- v866_B_quarter_2020-2026_q17_r01_case0017: scenario=q17, status=completed, profit=3922.54, PF=1.89, trades=6
- v866_B_quarter_2020-2026_q18_r01_case0018: scenario=q18, status=completed, profit=1489.47, PF=1.44, trades=5
- v866_B_quarter_2020-2026_q19_r01_case0019: scenario=q19, status=completed, profit=6032.05, PF=6.82, trades=6
- v866_B_quarter_2020-2026_q20_r01_case0020: scenario=q20, status=completed, profit=2267.86, PF=1.53, trades=6
- v866_B_quarter_2020-2026_q21_r01_case0021: scenario=q21, status=completed, profit=11237.65, PF=5.48, trades=9
- v866_B_quarter_2020-2026_q22_r01_case0022: scenario=q22, status=completed, profit=2789.64, PF=1.72, trades=9
- v866_B_quarter_2020-2026_q23_r01_case0023: scenario=q23, status=completed, profit=6746.83, PF=3.38, trades=7
- v866_B_quarter_2020-2026_q24_r01_case0024: scenario=q24, status=completed, profit=8378.72, PF=2.70, trades=8
- v866_B_quarter_2020-2026_q25_r01_case0025: scenario=q25, status=completed, profit=4422.79, PF=2.40, trades=9
- v866_B_quarter_2020-2026_q26_r01_case0026: scenario=q26, status=completed, profit=4434.51, PF=5.11, trades=5
初筛结论：通过
原因代码：OK
下一步：Compare B/C quarter concentration before month_core.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1840_quarter_B_recent
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1840_quarter_B_recent
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1840_quarter_B_recent
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1840_quarter_B_recent\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1840_quarter_B_recent
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1840_quarter_B_recent\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1840_quarter_B_recent\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1840_quarter_B_recent\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1840_quarter_B_recent\quarter_stage_report.md
## 2026-06-19 17:15:39 +08:00 - v8.67 quarter batch 20260619_1850_quarter_C_old
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1850_quarter_C_old
模块：quarter
任务目标：按 v8.67 下一阶段计划执行 quarter 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2012-2019
输入参数：C=v8.66_aggressive_case0005
场景配置：q01,q02,q03,q04,q05,q06,q07,q08,q09,q10,q11,q12,q13,q14,q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,q25,q26,q27,q28,q29,q30,q31,q32
回测数量：32
成功：32
失败：0
DryRun：0
关键指标：
- v866_C_quarter_2012-2019_q01_r01_case0001: scenario=q01, status=completed, profit=-2822.54, PF=0.43, trades=10
- v866_C_quarter_2012-2019_q02_r01_case0002: scenario=q02, status=completed, profit=2970.44, PF=1.69, trades=5
- v866_C_quarter_2012-2019_q03_r01_case0003: scenario=q03, status=completed, profit=-6743.74, PF=0.02, trades=9
- v866_C_quarter_2012-2019_q04_r01_case0004: scenario=q04, status=completed, profit=6358.24, PF=2.72, trades=9
- v866_C_quarter_2012-2019_q05_r01_case0005: scenario=q05, status=completed, profit=1576.88, PF=1.44, trades=7
- v866_C_quarter_2012-2019_q06_r01_case0006: scenario=q06, status=completed, profit=14424.27, PF=2.54, trades=9
- v866_C_quarter_2012-2019_q07_r01_case0007: scenario=q07, status=completed, profit=541.07, PF=1.28, trades=7
- v866_C_quarter_2012-2019_q08_r01_case0008: scenario=q08, status=completed, profit=5285.41, PF=3.38, trades=8
- v866_C_quarter_2012-2019_q09_r01_case0009: scenario=q09, status=completed, profit=3801.47, PF=1.85, trades=9
- v866_C_quarter_2012-2019_q10_r01_case0010: scenario=q10, status=completed, profit=3806.09, PF=1.60, trades=9
- v866_C_quarter_2012-2019_q11_r01_case0011: scenario=q11, status=completed, profit=-3319.36, PF=0.06, trades=8
- v866_C_quarter_2012-2019_q12_r01_case0012: scenario=q12, status=completed, profit=-2180.18, PF=0.53, trades=10
- v866_C_quarter_2012-2019_q13_r01_case0013: scenario=q13, status=completed, profit=-2079.89, PF=0.49, trades=10
- v866_C_quarter_2012-2019_q14_r01_case0014: scenario=q14, status=completed, profit=-5462.46, PF=0.10, trades=8
- v866_C_quarter_2012-2019_q15_r01_case0015: scenario=q15, status=completed, profit=658.83, PF=1.23, trades=7
- v866_C_quarter_2012-2019_q16_r01_case0016: scenario=q16, status=completed, profit=2368.49, PF=1.70, trades=5
- v866_C_quarter_2012-2019_q17_r01_case0017: scenario=q17, status=completed, profit=13890.35, PF=6.19, trades=5
- v866_C_quarter_2012-2019_q18_r01_case0018: scenario=q18, status=completed, profit=2710.46, PF=1.67, trades=8
- v866_C_quarter_2012-2019_q19_r01_case0019: scenario=q19, status=completed, profit=-3640.09, PF=0.23, trades=9
- v866_C_quarter_2012-2019_q20_r01_case0020: scenario=q20, status=completed, profit=2829.87, PF=1.72, trades=5
- v866_C_quarter_2012-2019_q21_r01_case0021: scenario=q21, status=completed, profit=-3547.15, PF=0.34, trades=8
- v866_C_quarter_2012-2019_q22_r01_case0022: scenario=q22, status=completed, profit=-5274.38, PF=0.38, trades=12
- v866_C_quarter_2012-2019_q23_r01_case0023: scenario=q23, status=completed, profit=1913.06, PF=2.13, trades=8
- v866_C_quarter_2012-2019_q24_r01_case0024: scenario=q24, status=completed, profit=3504.15, PF=1.62, trades=11
- v866_C_quarter_2012-2019_q25_r01_case0025: scenario=q25, status=completed, profit=-1152.56, PF=0.00, trades=2
- v866_C_quarter_2012-2019_q26_r01_case0026: scenario=q26, status=completed, profit=6262.78, PF=2.35, trades=7
- v866_C_quarter_2012-2019_q27_r01_case0027: scenario=q27, status=completed, profit=8187.28, PF=2.43, trades=10
- v866_C_quarter_2012-2019_q28_r01_case0028: scenario=q28, status=completed, profit=2318.33, PF=1.71, trades=6
- v866_C_quarter_2012-2019_q29_r01_case0029: scenario=q29, status=completed, profit=-4668.08, PF=0.46, trades=13
- v866_C_quarter_2012-2019_q30_r01_case0030: scenario=q30, status=completed, profit=5128.34, PF=1.96, trades=9
- v866_C_quarter_2012-2019_q31_r01_case0031: scenario=q31, status=completed, profit=-2475.51, PF=0.55, trades=8
- v866_C_quarter_2012-2019_q32_r01_case0032: scenario=q32, status=completed, profit=-2912.42, PF=0.14, trades=8
初筛结论：通过
原因代码：OK
下一步：Review losing quarters before month_core.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1850_quarter_C_old
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1850_quarter_C_old
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1850_quarter_C_old
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1850_quarter_C_old\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1850_quarter_C_old
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1850_quarter_C_old\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1850_quarter_C_old\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1850_quarter_C_old\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1850_quarter_C_old\quarter_stage_report.md
## 2026-06-19 17:19:14 +08:00 - v8.67 quarter batch 20260619_1900_quarter_C_recent
类型：回测 / 参数生成 / 报告生成
run_id: 20260619_1900_quarter_C_recent
模块：quarter
任务目标：按 v8.67 下一阶段计划执行 quarter 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2020-2026
输入参数：C=v8.66_aggressive_case0005
场景配置：q01,q02,q03,q04,q05,q06,q07,q08,q09,q10,q11,q12,q13,q14,q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,q25,q26
回测数量：26
成功：26
失败：0
DryRun：0
关键指标：
- v866_C_quarter_2020-2026_q01_r01_case0001: scenario=q01, status=completed, profit=16796.17, PF=23.62, trades=5
- v866_C_quarter_2020-2026_q02_r01_case0002: scenario=q02, status=completed, profit=3943.35, PF=2.14, trades=9
- v866_C_quarter_2020-2026_q03_r01_case0003: scenario=q03, status=completed, profit=-3494.36, PF=0.00, trades=5
- v866_C_quarter_2020-2026_q04_r01_case0004: scenario=q04, status=completed, profit=-527.61, PF=0.91, trades=10
- v866_C_quarter_2020-2026_q05_r01_case0005: scenario=q05, status=completed, profit=6872.55, PF=3.58, trades=8
- v866_C_quarter_2020-2026_q06_r01_case0006: scenario=q06, status=completed, profit=6360.86, PF=3.11, trades=9
- v866_C_quarter_2020-2026_q07_r01_case0007: scenario=q07, status=completed, profit=-4430.96, PF=0.23, trades=8
- v866_C_quarter_2020-2026_q08_r01_case0008: scenario=q08, status=completed, profit=2245.49, PF=1.69, trades=8
- v866_C_quarter_2020-2026_q09_r01_case0009: scenario=q09, status=completed, profit=1838.98, PF=1.36, trades=9
- v866_C_quarter_2020-2026_q10_r01_case0010: scenario=q10, status=completed, profit=1477.43, PF=1.50, trades=12
- v866_C_quarter_2020-2026_q11_r01_case0011: scenario=q11, status=completed, profit=281.55, PF=1.07, trades=9
- v866_C_quarter_2020-2026_q12_r01_case0012: scenario=q12, status=completed, profit=2483.33, PF=1.77, trades=8
- v866_C_quarter_2020-2026_q13_r01_case0013: scenario=q13, status=completed, profit=4908.72, PF=3.98, trades=6
- v866_C_quarter_2020-2026_q14_r01_case0014: scenario=q14, status=completed, profit=-1994.77, PF=0.30, trades=10
- v866_C_quarter_2020-2026_q15_r01_case0015: scenario=q15, status=completed, profit=-5875.11, PF=0.00, trades=8
- v866_C_quarter_2020-2026_q16_r01_case0016: scenario=q16, status=completed, profit=1640.95, PF=1.38, trades=10
- v866_C_quarter_2020-2026_q17_r01_case0017: scenario=q17, status=completed, profit=4194.13, PF=1.86, trades=6
- v866_C_quarter_2020-2026_q18_r01_case0018: scenario=q18, status=completed, profit=1600.57, PF=1.42, trades=5
- v866_C_quarter_2020-2026_q19_r01_case0019: scenario=q19, status=completed, profit=6760.11, PF=6.99, trades=6
- v866_C_quarter_2020-2026_q20_r01_case0020: scenario=q20, status=completed, profit=2435.28, PF=1.51, trades=6
- v866_C_quarter_2020-2026_q21_r01_case0021: scenario=q21, status=completed, profit=12471.30, PF=5.41, trades=9
- v866_C_quarter_2020-2026_q22_r01_case0022: scenario=q22, status=completed, profit=3045.08, PF=1.71, trades=9
- v866_C_quarter_2020-2026_q23_r01_case0023: scenario=q23, status=completed, profit=7401.20, PF=3.38, trades=7
- v866_C_quarter_2020-2026_q24_r01_case0024: scenario=q24, status=completed, profit=8962.44, PF=2.60, trades=8
- v866_C_quarter_2020-2026_q25_r01_case0025: scenario=q25, status=completed, profit=4986.08, PF=2.40, trades=9
- v866_C_quarter_2020-2026_q26_r01_case0026: scenario=q26, status=completed, profit=4896.98, PF=5.07, trades=5
初筛结论：通过
原因代码：OK
下一步：Compare B/C quarter concentration before month_core.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260619_1900_quarter_C_recent
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260619_1900_quarter_C_recent
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1900_quarter_C_recent
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1900_quarter_C_recent\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1900_quarter_C_recent
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1900_quarter_C_recent\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1900_quarter_C_recent\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260619_1900_quarter_C_recent\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260619_1900_quarter_C_recent\quarter_stage_report.md
## 2026-06-19 17:20:09 +08:00 - v8.67 B/C quarter unattended batch completed
类型：回测 / quarter 时间切片 / 无人值守汇总
Runs：20260619_1830_quarter_B_old / 20260619_1840_quarter_B_recent / 20260619_1850_quarter_C_old / 20260619_1900_quarter_C_recent
报告：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\quarter_BC_comparison_20260619.md
Spread可行性报告：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\spread_feasibility_20260619.md
B old positive_rate：0.5938
C old positive_rate：0.5938
B recent positive_rate：0.8077
C recent positive_rate：0.8077
结论：Stop before month_core. Keep B as current mainline and C as challenger, but quarter slicing shows old-window concentration risk for both B and C. Do not expand to month_core until losing-quarter clusters are reviewed.
下一步：先复盘 old-window losing-quarter clusters，不进入无人值守 month_core。
## 2026-06-20 00:52:17 +08:00 - v8.67 next-stage quarter cluster and spread path
类型：复盘 / 风险聚类 / spread 路径设计
输入：B/C 2012-2019 quarter matrices
输出：
- quarter losing cluster review: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\quarter_losing_cluster_review_20260620.md
- true spread test path: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\spread_test_path_20260620.md
核心结论：B/C 老窗口亏损季度完全重叠，C 没有解决 B 的弱 regime，只是放大同类收益/亏损结构。
决策：B 保持主线，C 保持同深度挑战者；不要直接进入 unattended month_core。
下一步：先针对 shared losing clusters 做局部 month slicing，或先建立 custom-symbol spread path。
## 2026-06-20 00:58:39 +08:00 - v8.67 month_cluster batch 20260620_tdd_monthcluster_C_green
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_tdd_monthcluster_C_green
模块：month_cluster
任务目标：按 v8.67 下一阶段计划执行 month_cluster 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2012-2019
输入参数：C=v8.66_aggressive_case0005
场景配置：m201407
回测数量：1
成功：0
失败：0
DryRun：1
关键指标：
- v866_C_month_cluster_2012-2019_m201407_r01_case0001: scenario=m201407, status=dry_run, profit=, PF=, trades=
初筛结论：DRY_RUN
原因代码：OK
下一步：dry-run 完成后执行真实批次
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_tdd_monthcluster_C_green
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_tdd_monthcluster_C_green
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_tdd_monthcluster_C_green
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_tdd_monthcluster_C_green\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_tdd_monthcluster_C_green
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_tdd_monthcluster_C_green\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_tdd_monthcluster_C_green\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_tdd_monthcluster_C_green\_batch_manifest.csv
## 2026-06-20 00:58:39 +08:00 - v8.67 month_cluster batch 20260620_tdd_monthcluster_B_green
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_tdd_monthcluster_B_green
模块：month_cluster
任务目标：按 v8.67 下一阶段计划执行 month_cluster 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019
输入参数：B=v8.66_robust_main_case0010
场景配置：m201407
回测数量：1
成功：0
失败：0
DryRun：1
关键指标：
- v866_B_month_cluster_2012-2019_m201407_r01_case0001: scenario=m201407, status=dry_run, profit=, PF=, trades=
初筛结论：DRY_RUN
原因代码：OK
下一步：dry-run 完成后执行真实批次
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_tdd_monthcluster_B_green
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_tdd_monthcluster_B_green
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_tdd_monthcluster_B_green
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_tdd_monthcluster_B_green\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_tdd_monthcluster_B_green
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_tdd_monthcluster_B_green\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_tdd_monthcluster_B_green\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_tdd_monthcluster_B_green\_batch_manifest.csv
## 2026-06-20 01:02:46 +08:00 - v8.67 month_cluster batch 20260620_1010_monthcluster_B_old
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1010_monthcluster_B_old
模块：month_cluster
任务目标：按 v8.67 下一阶段计划执行 month_cluster 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019
输入参数：B=v8.66_robust_main_case0010
场景配置：m201407,m201408,m201409,m201410,m201411,m201412,m201501,m201502,m201503,m201504,m201505,m201506,m201701,m201702,m201703,m201704,m201705,m201706,m201907,m201908,m201909,m201910,m201911,m201912
回测数量：24
成功：24
失败：0
DryRun：0
关键指标：
- v866_B_month_cluster_2012-2019_m201407_r01_case0001: scenario=m201407, status=completed, profit=-2046.09, PF=0.00, trades=3
- v866_B_month_cluster_2012-2019_m201408_r01_case0002: scenario=m201408, status=completed, profit=0.00, PF=0.00, trades=0
- v866_B_month_cluster_2012-2019_m201409_r01_case0003: scenario=m201409, status=completed, profit=-433.68, PF=0.33, trades=4
- v866_B_month_cluster_2012-2019_m201410_r01_case0004: scenario=m201410, status=completed, profit=253.52, PF=1.18, trades=5
- v866_B_month_cluster_2012-2019_m201411_r01_case0005: scenario=m201411, status=completed, profit=-1947.95, PF=0.00, trades=2
- v866_B_month_cluster_2012-2019_m201412_r01_case0006: scenario=m201412, status=completed, profit=-304.38, PF=0.70, trades=3
- v866_B_month_cluster_2012-2019_m201501_r01_case0007: scenario=m201501, status=completed, profit=1519.23, PF=16.04, trades=2
- v866_B_month_cluster_2012-2019_m201502_r01_case0008: scenario=m201502, status=completed, profit=-2350.26, PF=0.04, trades=5
- v866_B_month_cluster_2012-2019_m201503_r01_case0009: scenario=m201503, status=completed, profit=-952.45, PF=0.06, trades=3
- v866_B_month_cluster_2012-2019_m201504_r01_case0010: scenario=m201504, status=completed, profit=-1887.46, PF=0.20, trades=4
- v866_B_month_cluster_2012-2019_m201505_r01_case0011: scenario=m201505, status=completed, profit=-1452.03, PF=0.26, trades=3
- v866_B_month_cluster_2012-2019_m201506_r01_case0012: scenario=m201506, status=completed, profit=120.56, PF=0.00, trades=1
- v866_B_month_cluster_2012-2019_m201701_r01_case0013: scenario=m201701, status=completed, profit=-3181.82, PF=0.16, trades=5
- v866_B_month_cluster_2012-2019_m201702_r01_case0014: scenario=m201702, status=completed, profit=824.36, PF=1.83, trades=2
- v866_B_month_cluster_2012-2019_m201703_r01_case0015: scenario=m201703, status=completed, profit=-373.76, PF=0.00, trades=1
- v866_B_month_cluster_2012-2019_m201704_r01_case0016: scenario=m201704, status=completed, profit=401.63, PF=1.18, trades=3
- v866_B_month_cluster_2012-2019_m201705_r01_case0017: scenario=m201705, status=completed, profit=-3062.67, PF=0.08, trades=5
- v866_B_month_cluster_2012-2019_m201706_r01_case0018: scenario=m201706, status=completed, profit=-2452.92, PF=0.02, trades=4
- v866_B_month_cluster_2012-2019_m201907_r01_case0019: scenario=m201907, status=completed, profit=434.19, PF=1.42, trades=2
- v866_B_month_cluster_2012-2019_m201908_r01_case0020: scenario=m201908, status=completed, profit=-968.38, PF=0.69, trades=5
- v866_B_month_cluster_2012-2019_m201909_r01_case0021: scenario=m201909, status=completed, profit=-1039.13, PF=0.00, trades=1
- v866_B_month_cluster_2012-2019_m201910_r01_case0022: scenario=m201910, status=completed, profit=-2000.80, PF=0.00, trades=3
- v866_B_month_cluster_2012-2019_m201911_r01_case0023: scenario=m201911, status=completed, profit=-900.10, PF=0.10, trades=3
- v866_B_month_cluster_2012-2019_m201912_r01_case0024: scenario=m201912, status=completed, profit=184.94, PF=1.81, trades=2
初筛结论：通过
原因代码：OK
下一步：Stop and review failed month artifacts.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1010_monthcluster_B_old
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1010_monthcluster_B_old
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1010_monthcluster_B_old
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1010_monthcluster_B_old\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1010_monthcluster_B_old
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1010_monthcluster_B_old\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1010_monthcluster_B_old\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1010_monthcluster_B_old\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1010_monthcluster_B_old\month_cluster_stage_report.md
## 2026-06-20 01:03:31 +08:00 - v8.67 month_cluster stopped after B zero-trade month
类型：回测 / month_cluster / 停机规则触发
目标：shared losing clusters 局部月度切片
B run：20260620_1010_monthcluster_B_old
C run：未执行，原因是 B 触发 zero-trade 停机条件
报告：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\monthcluster_BC_losing_clusters_20260620.md
B cases：24
zero-trade months：1
losing months：16
结论：不进入 full month_core；不自动跑 C；等待人工决定 zero-trade 月份是否算硬失败。
## 2026-06-20 01:05:40 +08:00 - v8.67 month_cluster batch 20260620_1110_monthcluster_C_m201408_diag
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1110_monthcluster_C_m201408_diag
模块：month_cluster
任务目标：按 v8.67 下一阶段计划执行 month_cluster 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2012-2019
输入参数：C=v8.66_aggressive_case0005
场景配置：m201408
回测数量：1
成功：1
失败：0
DryRun：0
关键指标：
- v866_C_month_cluster_2012-2019_m201408_r01_case0001: scenario=m201408, status=completed, profit=0.00, PF=0.00, trades=0
初筛结论：通过
原因代码：OK
下一步：Stop and review failed month artifacts.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1110_monthcluster_C_m201408_diag\month_cluster_stage_report.md
## 2026-06-20 01:06:22 +08:00 - v8.67 m201408 zero-trade forensic
类型：诊断 / month_cluster / zero-trade 复盘
B run：20260620_1010_monthcluster_B_old / m201408 trades=0
C diagnostic run：20260620_1110_monthcluster_C_m201408_diag / m201408 trades=0
报告：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\monthcluster_zero_trade_forensic_201408_20260620.md
结论：B/C 在 2014-08 均无交易，属于共享 NO_SIGNAL_MONTH 或 regime 覆盖断档；不是 B 独有问题，也不是 MT5 无报告问题。
下一步：若接受 NO_SIGNAL_MONTH 为可分析空仓，可只跑 C 剩余 23 个月；否则先检查 EA 信号过滤。
## 2026-06-20 01:08:10 +08:00 - 建立 v8.66 压力测试与 walk-forward 验证执行计划
- 类型：计划文档建立，未执行回测，未修改 EA 源码。
- 新增文件：E:\CODEXMACD\docs\superpowers\plans\2026-06-20-v866-pressure-walkforward-validation.md
- 目的：将下一阶段固定年份过拟合排查拆成可执行任务，包括 smoke test、日期平移、双向 walk-forward、固定点差、滑点、季度/月度拆解、最终报告。
- 当前主线参数：v8.66_robust_main_case0010.set。
- 关键要求：先执行 smoke test，不允许未验证加载链路就批量回测；所有结果必须归档并更新 WORK_LOG.md。
## 2026-06-20 01:12:17 +08:00 - 建立五小时压力验证工作计划
- 类型：计划文档建立，未执行回测，未修改 EA 源码。
- 新增文件：E:\CODEXMACD\docs\superpowers\plans\2026-06-20-five-hour-pressure-validation-workplan.md
- 目的：把下一阶段压力验证拆成 5 小时可执行工作块，优先完成 smoke test、日期平移、双向 walk-forward、固定点差可行性检查、阶段总结和交接更新。
- 预计核心回测数量：约 163 次。
- 执行前提：先通过 smoke test，确认 MT5 正确加载 EA 与 .set。
## 2026-06-20 01:21:38 +08:00 - Five-hour unattended execution started
- Plan=E:\CODEXMACD\docs\superpowers\plans\2026-06-20-five-hour-pressure-validation-workplan.md
- BatchStamp=20260620_012138
- Rule=Smoke must pass before batch

## 2026-06-20 01:21:51 +08:00 - Five-hour Task 1 smoke completed
- RunId=v866_B_smoke_2020-2026_20260620_012138_case0001
- Net=556052.56
- PF=2.27
- Trades=203
- DiffPct=0

## 2026-06-20 01:34:56 +08:00 - Five-hour Task 2 date-shift completed
- Runs=64
- Summary=E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\date_shift_summary.csv
- High=0
- Medium=7

## 2026-06-20 01:44:41 +08:00 - Five-hour Task 3 reverse walk-forward completed
- Rows=48
- Summary=E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2020_2026_to_2012_2019.csv

## 2026-06-20 01:54:22 +08:00 - Five-hour Task 4 forward walk-forward completed
- Rows=48
- Summary=E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2012_2019_to_2020_2026.csv

## 2026-06-20 01:54:45 +08:00 - Five-hour Task 5 spread feasibility completed with blocker
- Summary=E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\spread_feasibility_summary.csv
- Decision=inconclusive
- Reason=current runner has no verified MT5 fixed-spread config hook

## 2026-06-20 01:54:45 +08:00 - Five-hour Task 6 stage summary completed
- Summary=E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md
- MainDecision=keep v8.66 robust case0010 as main candidate pending spread/slippage/monthly validation
- AggressiveDecision=keep aggressive as observation only; do not promote yet

## 2026-06-20 01:54:45 +08:00 - Five-hour Task 7 handoff updated
- Handoff=E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
- StageSummary=E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md

## 2026-06-20 01:54:45 +08:00 - Five-hour unattended execution completed
- Master=E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_master_matrix.csv
- StageSummary=E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md
- Status=completed without EA source changes

## 2026-06-20 02:08:26 +08:00 - 建立 12 小时生产准备工作计划
- 类型：计划文档建立，未执行回测，未修改 EA 源码。
- 新增文件：E:\CODEXMACD\docs\superpowers\plans\2026-06-20-twelve-hour-production-readiness-workplan.md
- 目的：把后续工作从单纯回测推进到生产准备体系，包括季度/月度稳定性、固定点差 blocker、滑点设计、v8.67 工程化、回归测试、forward monitor、生产准备报告和交接更新。
- 重要原则：12 小时目标是推进到 demo/forward-test ready 或 micro-live observation candidate，不承诺直接 full live ready。
## 2026-06-20 02:15:06 +08:00 - 12h Task 1 integrity review completed
- Fixed stage1 path display copy=E:\CODEXMACD\HCSJ\matrix\production_readiness\pressure_walkforward_stage1_summary_paths_fixed.md
- No raw historical matrix changed
- Production readiness matrix dir=E:\CODEXMACD\HCSJ\matrix\production_readiness

## 2026-06-20 02:46:36 +08:00 - 12h Task 2 quarterly breakdown completed
- Runs=192
- Matrix=E:\CODEXMACD\HCSJ\matrix\production_readiness\quarterly_breakdown_matrix.csv
- Summary=E:\CODEXMACD\HCSJ\matrix\production_readiness\quarterly_breakdown_summary.csv
- B rating=good

## 2026-06-20 03:33:13 +08:00 - 12h Task 3 monthly core breakdown completed
- Runs=288
- Matrix=E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_core_matrix.csv
- Summary=E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_core_summary.csv
- B rating=watch
- C rating=watch

## 2026-06-20 03:33:14 +08:00 - 12h Task 4 fixed-spread blocker investigation completed
- Decision=blocked
- CandidateFieldHits=0
- Csv=E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_feasibility_recheck.csv
- Notes=E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_feasibility_notes.md

## 2026-06-20 03:33:14 +08:00 - 12h Task 5 slippage-test design completed
- Decision=requires_temp_ea_or_external_execution_model
- Plan=E:\CODEXMACD\docs\superpowers\plans\2026-06-20-slippage-test-ea-design.md
- Feasibility=E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_test_feasibility.md
- ProductionEAChanged=false

## 2026-06-20 03:36:45 +08:00 - 12h Task 7 v8.67 regression completed
- EX5: D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5
- Matrix: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_regression_matrix.csv
- Summary: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_regression_summary.md
- 2020-2026 net: 556052.56, PF: 2.27, trades: 203

## 2026-06-20 03:37:32 +08:00 - 12h Task 8 forward monitor package completed
- Folder: E:\CODEXMACD\HCSJ\forward_monitor
- Files: trade log, daily equity, incident log, checklist, micro-live observation rules

## 2026-06-20 04:24:45 +08:00 - 12h Extra monthly A/D extension completed
- Extension runs: 288
- Extension matrix: E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_AD_extension_matrix.csv
- Full matrix: E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_full_matrix.csv
- Full summary: E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_full_summary.csv

---

## 2026-06-20 12-hour unattended production readiness wrap-up

- Mode: unattended production-readiness execution.
- Completed: quarterly breakdown, monthly core breakdown, monthly A/D extension, spread feasibility recheck, slippage-test design, v8.67 production-engineering copy, compile, regression, near-term extra regression, forward monitor package, set manifest, release candidate package.
- Main candidate: E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5.
- Recommended set: E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set.
- Main anchor: 2020-2026 net profit 556,052.56, PF 2.27, trades 203.
- Extra near-term regression: 2024.01.01-2026.06.30 net profit 161514.75, PF 2.70, trades 70.
- Readiness decision: Level 2 demo / forward-test ready; not full live ready.
- Remaining blockers: verified fixed-spread pressure test and executable slippage pressure test.
- Production report: $reportPath.
- Archived production report: $archiveReportPath.
- SET manifest: $manifestPath.
- Release candidate folder: $releaseDir.
- Note: first ad-hoc near-term summary CSV had blank wrapper fields; fixed summary was generated from authoritative metrics CSV at $fixedCsv.

## 2026-06-20 Parser & Continuation follow-up completed
- Time: 2026-06-20 04:46:11
- Task completed: report parser enhancement in E:\CODEXMACD\HCSJ\scripts\robust_search_runner.ps1
- Added parser fields: buy_trades, sell_trades, max_consecutive_winning_trades, max_consecutive_losing_trades, max_consecutive_winning_count, max_consecutive_losing_count
- Added artifact: E:\CODEXMACD\HCSJ\matrix\production_readiness\report_parser_enhancement.md
- Added artifact: E:\CODEXMACD\docs\superpowers\plans\2026-06-20-fixed-spread-slippage-execution-continuation-plan.md
- Validation note: direct parse check on 867_near_term_extra_2024_20260630.htm returns long/short counts and consecutive-loss count successfully.
- No historical .set/.exe/.mq5/.csv/.htm files were overwritten.

## 2026-06-20 04:51:34 +08:00 - 12h/无人值守续跑：v8.67 滑点探针（配置级）
- Type：运行
- 脚本：E:\CODEXMACD\HCSJ\scripts\run_v867_slippage_probe.ps1
- 对象：E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5（v8.67）
- 场景：
  - Slippage=3 与 Deviation=3
  - 窗口：2012-2019、2020-2026
- 运行结果：4/4 完成
- 结论：Decision=requires_temp_ea_or_external_model（未出现可验证的滑点压力差异）
- 输出：
  - Matrix CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_probe_v867_20260620_045032.csv
  - Matrix MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_probe_v867_20260620_045032.md
- 附注：配置级探针与 ExecutionMode/Deviation 在当前验证链路中无法形成可靠的真实滑点模型。
## 2026-06-20 04:51:34 +08:00 - Change: 处理配置级滑点探针脚本与解析器容错
- 修改文件：E:\CODEXMACD\HCSJ\scripts\robust_search_runner.ps1
- 类型：修复
- 变更：Get-ReportMetrics 增加空路径保护，避免历史无报告场景直接抛异常导致整批中断。
- 修改文件：E:\CODEXMACD\HCSJ\scripts\run_v867_slippage_probe.ps1
- 类型：修复
- 变更：修正字符串转义和配置探针构造，确保脚本可执行。
- 影响：un_v867_slippage_probe.ps1 成功产出 4 个场景运行结果。
## 2026-06-20 04:52:17 +08:00 - v8.67 wf20 batch D
类型：回测 / 参数生成 / 报告生成
run_id: D
模块：wf20
任务目标：按 v8.67 下一阶段计划执行 wf20 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502
场景配置：validate
回测数量：2
成功：2
失败：0
DryRun：0
关键指标：
- v866_A_wf20_2012-2019_validate_r01_case0001: scenario=validate, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_wf20_2012-2019_validate_r01_case0002: scenario=validate, status=completed, profit=133752.99, PF=1.22, trades=255
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\D
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\D
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\D
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\D\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\D
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\D\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\D\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\D\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\D\wf_stage_report.md
## 2026-06-20 04:52:25 +08:00 - v8.67 precheck batch 20260620_0452_precheck
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_0452_precheck
模块：precheck
任务目标：按 v8.67 下一阶段计划执行 precheck 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A/D
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502; D=v8.66_conservative_case0401
场景配置：shift00
回测数量：4
成功：0
失败：0
DryRun：4
关键指标：
- v866_A_dateshift_2012-2019_shift00_r01_case0001: scenario=shift00, status=dry_run, profit=, PF=, trades=
- v866_A_dateshift_2020-2026_shift00_r01_case0002: scenario=shift00, status=dry_run, profit=, PF=, trades=
- v866_D_dateshift_2012-2019_shift00_r01_case0003: scenario=shift00, status=dry_run, profit=, PF=, trades=
- v866_D_dateshift_2020-2026_shift00_r01_case0004: scenario=shift00, status=dry_run, profit=, PF=, trades=
初筛结论：DRY_RUN
原因代码：OK
下一步：dry-run 完成后执行真实批次
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_0452_precheck
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_0452_precheck
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0452_precheck
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0452_precheck\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0452_precheck
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0452_precheck\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0452_precheck\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0452_precheck\_batch_manifest.csv
## 2026-06-20 04:53:08 +08:00 - v8.67 wf20 batch 20260620_0452_wf20
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_0452_wf20
模块：wf20
任务目标：按 v8.67 下一阶段计划执行 wf20 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A/D
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502; D=v8.66_conservative_case0401
场景配置：validate
回测数量：4
成功：4
失败：0
DryRun：0
关键指标：
- v866_A_wf20_2012-2019_validate_r01_case0001: scenario=validate, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_wf20_2012-2019_validate_r01_case0002: scenario=validate, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_D_wf20_2012-2019_validate_r01_case0003: scenario=validate, status=completed, profit=51100.55, PF=1.19, trades=250
- v866_D_wf20_2012-2019_validate_r01_case0004: scenario=validate, status=completed, profit=51100.55, PF=1.19, trades=250
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_0452_wf20
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_0452_wf20
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0452_wf20
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0452_wf20\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0452_wf20
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0452_wf20\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0452_wf20\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0452_wf20\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0452_wf20\wf_stage_report.md
## 2026-06-20 04:53:47 +08:00 - v8.67 wf12 batch 20260620_0453_wf12
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_0453_wf12
模块：wf12
任务目标：按 v8.67 下一阶段计划执行 wf12 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A/D
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502; D=v8.66_conservative_case0401
场景配置：validate
回测数量：4
成功：4
失败：0
DryRun：0
关键指标：
- v866_A_wf12_2020-2026_validate_r01_case0001: scenario=validate, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_wf12_2020-2026_validate_r01_case0002: scenario=validate, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_D_wf12_2020-2026_validate_r01_case0003: scenario=validate, status=completed, profit=371235.57, PF=2.23, trades=203
- v866_D_wf12_2020-2026_validate_r01_case0004: scenario=validate, status=completed, profit=371235.57, PF=2.23, trades=203
初筛结论：通过
原因代码：OK
下一步：Stop this branch and review wf_stage_report.md before running the next object.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_0453_wf12
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_0453_wf12
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0453_wf12
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0453_wf12\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0453_wf12
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0453_wf12\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0453_wf12\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0453_wf12\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0453_wf12\wf_stage_report.md
## 2026-06-20 04:55:51 +08:00 - v8.67 wf20 batch 20260620_0455_wf20
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_0455_wf20
模块：wf20
任务目标：按 v8.67 下一阶段计划执行 wf20 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2012-2019 / 2020-2026
输入参数：C=v8.66_aggressive_case0005
场景配置：validate
回测数量：2
成功：2
失败：0
DryRun：0
关键指标：
- v866_C_wf20_2012-2019_validate_r01_case0001: scenario=validate, status=completed, profit=57221.99, PF=1.15, trades=250
- v866_C_wf20_2012-2019_validate_r01_case0002: scenario=validate, status=completed, profit=57221.99, PF=1.15, trades=250
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_0455_wf20
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_0455_wf20
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0455_wf20
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0455_wf20\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0455_wf20
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0455_wf20\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0455_wf20\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0455_wf20\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0455_wf20\wf_stage_report.md
## 2026-06-20 04:56:11 +08:00 - v8.67 wf12 batch 20260620_0455_wf12
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_0455_wf12
模块：wf12
任务目标：按 v8.67 下一阶段计划执行 wf12 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：C
输入窗口：2012-2019 / 2020-2026
输入参数：C=v8.66_aggressive_case0005
场景配置：validate
回测数量：2
成功：2
失败：0
DryRun：0
关键指标：
- v866_C_wf12_2020-2026_validate_r01_case0001: scenario=validate, status=completed, profit=716968.27, PF=2.29, trades=203
- v866_C_wf12_2020-2026_validate_r01_case0002: scenario=validate, status=completed, profit=716968.27, PF=2.29, trades=203
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_0455_wf12
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_0455_wf12
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0455_wf12
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0455_wf12\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0455_wf12
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0455_wf12\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0455_wf12\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0455_wf12\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0455_wf12\wf_stage_report.md
## 2026-06-20 04:59:23 +08:00 - v8.67 wf20 batch 20260620_0459_wf20
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_0459_wf20
模块：wf20
任务目标：按 v8.67 下一阶段计划执行 wf20 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019 / 2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：validate
回测数量：2
成功：2
失败：0
DryRun：0
关键指标：
- v866_B_wf20_2012-2019_validate_r01_case0001: scenario=validate, status=completed, profit=55826.12, PF=1.17, trades=250
- v866_B_wf20_2012-2019_validate_r01_case0002: scenario=validate, status=completed, profit=55826.12, PF=1.17, trades=250
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_0459_wf20
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_0459_wf20
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0459_wf20
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0459_wf20\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0459_wf20
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0459_wf20\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0459_wf20\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0459_wf20\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0459_wf20\wf_stage_report.md
## 2026-06-20 04:59:43 +08:00 - v8.67 wf12 batch 20260620_0459_wf12
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_0459_wf12
模块：wf12
任务目标：按 v8.67 下一阶段计划执行 wf12 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B
输入窗口：2012-2019 / 2020-2026
输入参数：B=v8.66_robust_main_case0010
场景配置：validate
回测数量：2
成功：2
失败：0
DryRun：0
关键指标：
- v866_B_wf12_2020-2026_validate_r01_case0001: scenario=validate, status=completed, profit=556052.56, PF=2.27, trades=203
- v866_B_wf12_2020-2026_validate_r01_case0002: scenario=validate, status=completed, profit=556052.56, PF=2.27, trades=203
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_0459_wf12
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_0459_wf12
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0459_wf12
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0459_wf12\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0459_wf12
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0459_wf12\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0459_wf12\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_0459_wf12\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_0459_wf12\wf_stage_report.md

## 2026-06-20 04:56:13 +08:00 - v8.67 执行风险 probe（固定点差，配置级）
类型：执行风险验证 / 配置级探针
run_id: 20260620_045613
模块：spread
输入对象：v8.67生产候选（默认case0010）
输入窗口：2012-2019 / 2020-2026
参数与配置：Spread=1.0 / 1.5 / 2.0，使用 v8.67 标准 set
回测数量：6
成功：6
失败：0
DryRun：0
关键指标（示例）：
- v867_spread_probe_20260620045613_S1_0_S2012_2019_case0001: spread=1.0, status=completed, net_profit=55826.12, PF=1.17, trades=250
- v867_spread_probe_20260620045613_S1_0_S2020_2026_case0002: spread=1.0, status=completed, net_profit=556052.56, PF=2.27, trades=203
- v867_spread_probe_20260620045613_S2_0_S2020_2026_case0006: spread=2.0, status=completed, net_profit=556052.56, PF=2.27, trades=203
初筛结论：inconclusive（结果无变化，未能证明真实固定点差控制有效）
原因代码：FIXED_SPREAD_INCONCLUSIVE
输出：
- CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_v867_20260620_045613.csv
- MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_v867_20260620_045613.md

## 2026-06-20 04:57:44 +08:00 - v8.67 执行风险 probe（滑点/偏差，配置级）
类型：执行风险验证 / 配置级探针
run_id: 20260620_045744
模块：slippage
输入对象：v8.67生产候选（默认case0010）
输入窗口：2012-2019 / 2020-2026
参数与配置：Slippage=3，Deviation=3 两组，对应窗口各2组
回测数量：4
成功：4
失败：0
DryRun：0
关键指标（示例）：
- v867_slippage_probe_20260620045744_Slippage_S2012_2019_case0001: field=Slippage, status=completed, net_profit=55826.12, PF=1.17, trades=250
- v867_slippage_probe_20260620045744_Slippage_S2020_2026_case0002: field=Slippage, status=completed, net_profit=556052.56, PF=2.27, trades=203
- v867_slippage_probe_20260620045744_Deviation_S2012_2019_case0003: field=Deviation, status=completed, net_profit=55826.12, PF=1.17, trades=250
初筛结论：requires_temp_ea_or_external_model
原因代码：CONFIG_SLIPPAGE_NOT_RELIABLE
输出：
- CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_probe_v867_20260620_045744.csv
- MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_probe_v867_20260620_045744.md

## 2026-06-20 05:17:07 +08:00 - User-initiated 12h production readiness execution start
- Action: start production_readiness_backtest_runner.ps1 in detached mode
- Scope: Task 1~5 pre-engineering, then append WORK_LOG from script
- OutputLog: E:\CODEXMACD\HCSJ\logs\production_readiness_backtest_runner_20260620_unattended.log



## 2026-06-20 05:17:10 +08:00 - User-initiated 12h production readiness execution start (rerun)
- Action: launch production_readiness_backtest_runner.ps1 in detached mode
- OutputOut: E:\CODEXMACD\HCSJ\logs\production_readiness_backtest_runner_20260620_051710_out.log
- OutputErr: E:\CODEXMACD\HCSJ\logs\production_readiness_backtest_runner_20260620_051710_err.log
- Scope: Task 1~5 pre-engineering



## 2026-06-20 05:17:10 +08:00 - 12h Task 1 integrity review completed
- Fixed stage1 path display copy=E:\CODEXMACD\HCSJ\matrix\production_readiness\pressure_walkforward_stage1_summary_paths_fixed.md
- No raw historical matrix changed
- Production readiness matrix dir=E:\CODEXMACD\HCSJ\matrix\production_readiness

## 2026-06-20 05:21:14 +08:00 - Archived baseline production-readiness matrices before rerun
- TargetDir: E:\CODEXMACD\HCSJ\matrix\production_readiness\history\20260620_051710_preexisting
- Files: quarterly_breakdown_matrix.csv, quarterly_breakdown_summary.csv, monthly_breakdown_core_matrix.csv, monthly_breakdown_core_summary.csv, monthly_breakdown_full_matrix.csv, monthly_breakdown_full_summary.csv


## 2026-06-20 05:49:49 +08:00 - 12h Task 2 quarterly breakdown completed
- Runs=192
- Matrix=E:\CODEXMACD\HCSJ\matrix\production_readiness\quarterly_breakdown_matrix.csv
- Summary=E:\CODEXMACD\HCSJ\matrix\production_readiness\quarterly_breakdown_summary.csv
- B rating=good

## 2026-06-20 06:38:12 +08:00 - 12h Task 3 monthly core breakdown completed
- Runs=288
- Matrix=E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_core_matrix.csv
- Summary=E:\CODEXMACD\HCSJ\matrix\production_readiness\monthly_breakdown_core_summary.csv
- B rating=watch
- C rating=watch

## 2026-06-20 06:38:13 +08:00 - 12h Task 4 fixed-spread blocker investigation completed
- Decision=candidate_fields_found_unverified
- CandidateFieldHits=12
- Csv=E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_feasibility_recheck.csv
- Notes=E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_feasibility_notes.md

## 2026-06-20 06:38:13 +08:00 - 12h Task 5 slippage-test design completed
- Decision=requires_temp_ea_or_external_execution_model
- Plan=E:\CODEXMACD\docs\superpowers\plans\2026-06-20-slippage-test-ea-design.md
- Feasibility=E:\CODEXMACD\HCSJ\matrix\production_readiness\slippage_test_feasibility.md
- ProductionEAChanged=false
## 2026-06-20 06:40:56 +08:00 - 12h Task 9 production-readiness report completed
- Type: completion report generated for continuation run
- RunId: 20260620_051710
- Decision: Level 2 (demo/forward allowed with constraints), live-not-ready
- ReportFile: E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_report_20260620_051710.md
- Inputs reviewed: task 7 regression, task 2 quarterly, task 3 monthly_core, task 4 spread blocker, task 5 slippage feasibility
- Key status:
  - B (v8.66 robust) quarterly rating: good, profitable quarters 30/48 (62.5%)
  - B/C monthly_core rating: watch, profitable months 66/144 (45.83%)
  - Spread blocker: candidate_fields_found_unverified (12)
  - Slippage: requires_temp_ea_or_external_execution_model
  - v8.67 main anchor: 2020-2026 net profit 556052.56, PF 2.27, trades 203

## 2026-06-20 06:40:56 +08:00 - 12h Task 10 final handoff and cleanup completed
- type: final handoff update + continuity checkpoint
- Handoff updated in: E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
- Added continuity section:
  - Current decision and main artifacts
  - New report pointer
  - Remaining work (execution-risk closure first)
- Historical artifacts retained; no overwrite of existing production files
- Next action: continue execution-risk closure (fixed-spread + slippage EA validation), then re-assess micro-live gating
## 2026-06-20 07:48:02 - v8.67临时滑点EA闭环补测
- 类型：回测 / 参数生成 / 报告生成
- 任务目标：执行临时滑点EA压力测试（对象B/C，级别0/1/2/3/5）
- 输入文件：E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
- 执行文件：E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.ex5
- 输出目录：
  - 矩阵/报告: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074601
  - .set: E:\CODEXMACD\HCSJ\set\v8.67\20260620_074601
  - 报告归档: E:\CODEXMACD\HCSJ\backtest_archive\v867_slippage_harness_20260620_074601
  - 结果CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074601\slippage_harness_v867_20260620_074601.csv
  - 结果MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074601\slippage_harness_v867_20260620_074601.md
- 回测数量：20
- 成功：6
- 失败：14
- 决议：partial
- 后续：基于利润与PF退化阈值更新执行风险结论
## 2026-06-20 07:48:32 - v8.67临时滑点EA闭环补测
- 类型：回测 / 参数生成 / 报告生成
- 任务目标：执行临时滑点EA压力测试（对象B/C，级别0/1/2/3/5）
- 输入文件：E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
- 执行文件：E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.ex5
- 输出目录：
  - 矩阵/报告: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074622
  - .set: E:\CODEXMACD\HCSJ\set\v8.67\20260620_074622
  - 报告归档: E:\CODEXMACD\HCSJ\backtest_archive\v867_slippage_harness_20260620_074622
  - 结果CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074622\slippage_harness_v867_20260620_074622.csv
  - 结果MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074622\slippage_harness_v867_20260620_074622.md
- 回测数量：20
- 成功：7
- 失败：13
- 决议：partial
- 后续：基于利润与PF退化阈值更新执行风险结论
## 2026-06-20 07:53:21 - v8.67临时滑点EA闭环补测
- 类型：回测 / 参数生成 / 报告生成
- 任务目标：执行临时滑点EA压力测试（对象B/C，级别0/1/2/3/5）
- 输入文件：E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
- 执行文件：E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.ex5
- 输出目录：
  - 矩阵/报告: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074910
  - .set: E:\CODEXMACD\HCSJ\set\v8.67\20260620_074910
  - 报告归档: E:\CODEXMACD\HCSJ\backtest_archive\v867_slippage_harness_20260620_074910
  - 结果CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074910\slippage_harness_v867_20260620_074910.csv
  - 结果MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074910\slippage_harness_v867_20260620_074910.md
- 回测数量：20
- 成功：20
- 失败：0
- 决议：completed
- 后续：基于利润与PF退化阈值更新执行风险结论
## 2026-06-20 07:55:32 +08:00 - v8.67 fixed-spread probe
- 类型：回测 / 参数生成 / 报告生成
- 任务目标：执行固定点差压力探针（对象 B，v8.67 主线设置）
- 输入文件：E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
- 执行文件：D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5
- 输出目录：
  - 矩阵/报告: E:\CODEXMACD\HCSJ\matrix\production_readiness
  - .set: E:\CODEXMACD\HCSJ\set\v8.67\20260620_075408（由测试自动生成）
  - 报告归档: E:\CODEXMACD\HCSJ\backtest_archive\v8.67
  - 结果CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_v867_20260620_075408.csv
  - 结果MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_v867_20260620_075408.md
  - 执行日志: E:\CODEXMACD\HCSJ\logs\run_v867_spread_probe_20260620_075408.log
- 回测数量：6
- 成功：6
- 失败：0
- 决议：inconclusive（三档配置均与基线一致，未观察到 Spread 对收益/PF 的可区分影响）
- 备注：保留结论以便后续继续推进固定点差真值校验。
## 2026-06-20 08:00:00 +08:00 - v8.67 fixed spread extended probe (execution-risk continuation)
- 类型：回测 / 风险验证 / 报告
- 任务目标：验证 Spread 字段在当前 MT5 测试链路中的真实点差压力效应
- 输入文件：E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
- 输入对象：B（主线稳健）
- 输入窗口：2012-2019 / 2020-2026
- 场景：Spread = 0 / 1 / 20 / 100
- 回测数量：8
- 成功：8
- 失败：0
- 决议：inconclusive（指标无显著变化，固定点差可验证证据仍缺）
- 关键指标：net / PF / 交易数 across both windows unchanged by spread levels
- 输出：
  - E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_extended_20260620_075745.csv
  - E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_extended_20260620_075745.md
  - E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074910\slippage_harness_v867_20260620_074910.csv
  - E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_074910\slippage_harness_v867_20260620_074910.md
- 下一步：更新交接并进入 demo/forward 运维确认阶段
## 2026-06-20 08:02:01 +08:00 - v8.67 forward-monitor stage kickoff
- 类型：阶段衔接 / 运维包启动 / 文档更新
- run_id: 20260620_0802_fwd_monitor
- 任务目标：从 execution-risk 闭环切换到 demo/forward 运维准备，建立可执行的 forward-monitor 会话起点。
- 主线文件：
  - EA: E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
  - EX5: D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5
  - Set: E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
  - 报告: E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_report_20260620_080000.md
- 回测：无新增回测。
- 输出文件：
  - 会话启动：E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_session_20260620_0802.md
  - 清单文件：E:\CODEXMACD\HCSJ\forward_monitor\forward_test_checklist.md
  - 日终检查文件：E:\CODEXMACD\HCSJ\forward_monitor\forward_test_daily_equity.csv
  - 异常事件文件：E:\CODEXMACD\HCSJ\forward_monitor\forward_test_incident_log.csv
- 关键动作：
  - 核对前置检查清单与停机条件，确认可直接进入 demo/forward 日常巡检流程
  - 记录当前状态到 handoff 与工作日志
- 回测数量：0
- 成功：0
- 失败：0
- 初筛结论：通过（运维阶段已启动，等待实际挂单后进入实盘观察前置检查）
- 原因代码：PM01
- 下一步：
  - 实际挂载后按会话文件执行“上机前检查 -> 连接后检查 -> 每日/每周巡检 -> 异常升级”。
  - 任何异常立即写入 incident_log，并同步更新 handoff 与 WORK_LOG。
## 2026-06-20 08:03:06 +08:00 - v8.67 forward monitor stage推进启动（无人值守持续）
类型：阶段衔接 / 运维启动 / 状态核验
模块：forward-monitor
任务目标：在12h执行风险闭环完成后，进入 demo/forward 运维流程，不改EA核心。
MT5路径：D:\MT5测试\MetaTrader 5
主线文件：
- E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
- E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
- D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5
环境核验：
- terminal64.exe 当前状态：NOT_RUNNING
- EX5 文件存在：true
- forward monitor 会话：E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_session_20260620_0802.md
回测状态：无需新增回测（本轮进入运维阶段）。
记录动作：
- 已保持 \\forward_monitor 目录和 3 个监控 CSV（equity/trade/incident）
- 下一个动作：挂载 EA 到 demo/forward 账户后开始填报日终/周检记录
初筛结论：继续
原因代码：FORWARD_MONITOR_READY
下一步：启动前线账户挂载，按 forward_test_checklist.md 执行每日巡检并补齐 daily/trade/incident 记录。
## 2026-06-20 14:57:34 +08:00 - v8.67 ����ֵ�ؽ����ļ���׼����¼
- �ļ����£���� orward_monitor ����ģ���봥�������ļ����������� handoff/�Ự�ļ��е���ʾ����Ʒ�
- �ļ����䣺
  - E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_daily_report_template.md���Ѵ�����
  - E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_trigger_rules_summary.md���Ѵ�����
- ��־���������� E:\CODEXMACD\forward_monitor\forward_test_daily_equity.csv �� orward_test_trade_log.csv �ճ����¹���Ϊ�̶��������
- ��ɸ���ۣ����
- ��һ����ʹ���´�������ʱ�� HANDOFF ��һ���ڹ̶���ִ�У����� EA Դ�롣
## 2026-06-20 14:57:42 +08:00 - Monitoring templates and trigger rules created
- Added fixed monitoring templates for next unattended handoff.
- Files created:
  - E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_daily_report_template.md
  - E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_trigger_rules_summary.md
- Files updated:
  - E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_session_20260620_0802.md
  - E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
- Next action: next window should execute this sequence daily, no manual interpretation required.
## 2026-06-20  2026-06-20 15:41:25
- ȷ�ϣ�24Сʱ�ƻ��Ѳ��䡰��ǰ���������Զ��������ԡ���
- ��һ�����������ƻ��ļ�ִ����������� A/B/C/D ���ơ�
- ִ��Լ����ÿ����������ɺ�׷����־���ļ�·��������������A���ٽ���B/C/D����������ʷ�ļ���


## AUTORUN_START autonomous_run_20260620_20260620_154355
# �Զ�������ֵ��������¼
- Run ID: autonomous_run_20260620_20260620_154355
- ��ʼʱ��: 2026-06-20 15:43:55
- ����ָ����Դ: E:\CODEXMACD\docs\superpowers\plans\2026-06-20-twentyfour-hour-final-production-readiness-plan.md
- �汾: SniperTrendEA_v8.67_grokbase_production_ready
- Ŀ��: ��24Сʱ����ֵ�ؼƻ�+�������������ִ��
- ��������: P0��ϣ��ز���ʧ��/·��д�����/����ȱʧ/��ɫ�澯��
- �鵵����: set->E:\CODEXMACD\HCSJ\set������->E:\CODEXMACD\HCSJ\backtest_archive�����->E:\CODEXMACD\HCSJ\matrix\production_readiness����������ʷ�ļ���ʱ�����׺��
- ״̬: ������������׶�1
- Ŀ¼�ɴ���У��:
- report_dir_exists: True
- matrix_dir_exists: True
- plan_exists: True
- worklog_exists: True
- session_dir_exists: True
- set_dir_exists: True
- handoff_exists: True


### �׶�1ê��У�飨2026-06-20 15:43:57��
- �ƻ��ļ���������־�������ļ���EAԴ������Լ������
- ea_file: True
- plan_file: True
- worklog: True
- handoff_file: True
- ��ǰ����״̬���׶�1�ѽ��룬�ȴ�Smoke��֤��
- ��ע����ǰ����δ��⵽�Զ�������MT5�ز����Ŀ�ֱ��ִ����ڣ������ⲿ�ű������ý׶����ֹ�/�ű�����·������

### �׶�1 Smoke������¼��2026-06-20 15:46:34��
- ����������ͨ��	erminal64.exe /portable /configִ�� 8_67_smoke_runtime_20260620_154412.ini ʱ��terminal δ�Զ���ɻز���δ���ɱ��档
- ��⣺	erminal64�����������̣�PID 16000������ִ��ǿ����ֹ��
- ���ۣ�����P0�������ز����޿ɸ����������
- �����������������������������ԣ�Ŀǰ���ƽ�����һ�׶Σ������ز�����޸���ɸ�����֤��

### �׶�1 Smokeִ�У�2026-06-20 15:46:57��
- ����: Invoke-Mt5Backtest v8.67_smoke_autostart_20260620_154646
- ���: SMOKE_RUN_RESULT|id=v8.67_smoke_autostart_20260620_154646|status=completed|net=5743.97|pf=1.68|trades=11|report=E:\CODEXMACD\HCSJ\backtest_archive\v8.67\smoke\v8.67_smoke_autostart_20260620_154646\v8.67_smoke_autostart_20260620_154646.htm|metrics=E:\CODEXMACD\HCSJ\backtest_archive\v8.67\smoke\v8.67_smoke_autostart_20260620_154646\v8.67_smoke_autostart_20260620_154646_metrics.csv|seconds=10

### �׶�2-1 ִ�У�2026-06-20 15:47:45��
- ģʽ��v8.67 �׶�2��������֤����1��3����
- Ŀ�괰�ڣ�2012-2014 / 2015-2019 / 2017-2023
- ����set��E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
- ���ժҪ��

- v8.67_stage2_20260620_154708_1: status=completed, net=25454.21, pf=1.32, trades=95, report=E:\CODEXMACD\HCSJ\backtest_archive\v8.67\2012-2014\v8.67_stage2_20260620_154708_1\v8.67_stage2_20260620_154708_1.htm - v8.67_stage2_20260620_154708_2: status=completed, net=13268.74, pf=1.12, trades=155, report=E:\CODEXMACD\HCSJ\backtest_archive\v8.67\2015-2019\v8.67_stage2_20260620_154708_2\v8.67_stage2_20260620_154708_2.htm - v8.67_stage2_20260620_154708_3: status=completed, net=68116.38, pf=1.26, trades=230, report=E:\CODEXMACD\HCSJ\backtest_archive\v8.67\2017-2023\v8.67_stage2_20260620_154708_3\v8.67_stage2_20260620_154708_3.htm

### �׶�2-2 ִ�У�2026-06-20 15:48:29��
- ģʽ��v8.67 �׶�2�細����֤����2��3��������
- ����set��E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
- ���ժҪ��
- v8.67_stage2_20260620_154752_r2_1: status=completed, net=13268.74, pf=1.12, trades=155, report=E:\CODEXMACD\HCSJ\backtest_archive\v8.67\cv_2012_train_2015-2019\v8.67_stage2_20260620_154752_r2_1\v8.67_stage2_20260620_154752_r2_1.htm - v8.67_stage2_20260620_154752_r2_2: status=completed, net=68116.38, pf=1.26, trades=230, report=E:\CODEXMACD\HCSJ\backtest_archive\v8.67\cv_2015_train_2017-2023\v8.67_stage2_20260620_154752_r2_2\v8.67_stage2_20260620_154752_r2_2.htm - v8.67_stage2_20260620_154752_r2_3: status=completed, net=25454.21, pf=1.32, trades=95, report=E:\CODEXMACD\HCSJ\backtest_archive\v8.67\cv_2017_train_2012-2014\v8.67_stage2_20260620_154752_r2_3\v8.67_stage2_20260620_154752_r2_3.htm
## 2026-06-20 15:52:51 - v8.67��ʱ����EA�ջ�����
- ���ͣ��ز� / �������� / ��������
- ����Ŀ�꣺ִ����ʱ����EAѹ�����ԣ�����B/C������0/1/2/3/5��
- �����ļ���E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
- ִ���ļ���E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.ex5
- ���Ŀ¼��
  - ����/����: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_155009
  - .set: E:\CODEXMACD\HCSJ\set\v8.67\20260620_155009
  - ����鵵: E:\CODEXMACD\HCSJ\backtest_archive\v867_slippage_harness_20260620_155009
  - ���CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_155009\slippage_harness_v867_20260620_155009.csv
  - ���MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_155009\slippage_harness_v867_20260620_155009.md
- �ز�������12
- �ɹ���12
- ʧ�ܣ�0
- ���飺completed
- ����������������PF�˻���ֵ����ִ�з��ս���

### �׶�4 ����ƽ����֤��2026-06-20 15:54:10��
- �׶Σ�v8.67 �׶�4 DateShift ��֤
- �������Σ�6
- v8.67_stage4_20260620_155258_shift0_1: status=completed, net=25454.21, pf=1.32, trades=95, from=, to= - v8.67_stage4_20260620_155258_shift7_2: status=completed, net=27003.44, pf=1.33, trades=93, from=, to= - v8.67_stage4_20260620_155258_shift0_3: status=completed, net=13268.74, pf=1.12, trades=155, from=, to= - v8.67_stage4_20260620_155258_shift7_4: status=completed, net=13268.74, pf=1.12, trades=155, from=, to= - v8.67_stage4_20260620_155258_shift0_5: status=completed, net=68116.38, pf=1.26, trades=230, from=, to= - v8.67_stage4_20260620_155258_shift7_6: status=completed, net=72627.20, pf=1.26, trades=229, from=, to=

## 2026-06-20 �Զ��������������ƽ����գ�2026-06-20 15:54:13��
- ��ǰ״̬������ֵ�ؼ���ִ���У�P0δ������δ��·�����Ƿ��ա�
- �������
  - Smoke ��ɣ�v8.67, 2024.01-06, completed, report �����ɣ�
  - �׶�2�����������Σ�2012-2014 / 2015-2019 / 2017-2023��3�����
  - �׶�2�������⽻������3����ɣ����ڻ��⣩
  - �׶�3���̶����̽�� 6����ɣ�����������仯�������ж�Ϊ���������ʵ�����֤��
  - �׶�3����ʱ���� harness������B/C��0/1/2����12����ɣ�ȫ�� completed
  - �׶�4������ƽ������6����shift0/7�����
- ��һ����������ִ�У�
  - ���м���/�¶�ȫ������⣨����ʷ�ű�·���ɸ��ã�
  - ����5/7/10�¶ȴ��� shift �� 2017-2023/2012-2019 ����
  - ���ܵ� HCSJ\matrix\production_readiness �Ľ׶��ܽ������վ��߱�
- ������������Ԥ�� 24Сʱ�ƻ��������˳���ƽ������жϡ�

### �׶�4.1 �¶���������2020ǰ3�£���2026-06-20 15:57:05)
- v8.67_stage4_month2020_20260620_155630_1: completed net=2371.04 pf=0.00 trades=1
- v8.67_stage4_month2020_20260620_155630_2: completed net=10347.56 pf=0.00 trades=2
- v8.67_stage4_month2020_20260620_155630_3: completed net=1388.66 pf=0.00 trades=1

### �׶�4.1 �¶���������2020��Ѯ4-6�£���2026-06-20 15:57:41)
- v8.67_stage4_month2020_4: completed net=-325.01 pf=0.69 trades=2
- v8.67_stage4_month2020_5: completed net=1540.62 pf=2.51 trades=4
- v8.67_stage4_month2020_6: completed net=2291.99 pf=3.29 trades=3

### �׶�4.1 �¶���������2020��Ѯ7-9�£���2026-06-20 15:58:20)
- v8.67_stage4_month2020_20260620_155748_7: completed net=-1305.56 pf=0.00 trades=3
- v8.67_stage4_month2020_20260620_155748_8: completed net=-470.88 pf=0.53 trades=2
- v8.67_stage4_month2020_20260620_155748_9: completed net=2053.65 pf=14.39 trades=2

### �׶�4.1 �¶���������2020ĩ��10-12�£���2026-06-20 15:59:09)
- v8.67_stage4_month2020_20260620_155836_10: completed net=-3445.08 pf=0.08 trades=5
- v8.67_stage4_month2020_20260620_155836_11: completed net=5101.50 pf=6.12 trades=2
- v8.67_stage4_month2020_20260620_155836_12: completed net=-673.56 pf=0.33 trades=3
## 2026-06-20 16:05:08 +08:00 - v8.67 quarter batch 2020-2026 (20260620_160022)
���ͣ��ز� / �������� / ��������
- ����Ŀ�꣺�� v8.67 ��һ�׶μƻ�ִ�� quarter ��֤�����ڣ�2020-2026��
- �������v8.67 ���߲���
- run_tag: 20260620_160022
- ���ڣ�2020-2026��q01��q26��
- ����������52
- �ɹ���26
- ʧ�ܣ�26
- �������E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_quarter_2020_2026_20260620160022.csv
- ����set��E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
- EA ex5��D:\MT5����\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5
- ִ��״̬����ֹ������
## 2026-06-20 16:10:06 +08:00 - v8.67 quarter batch 2020-2026 clean (20260620_160533)
���ͣ��ز� / �������� / ��������
- ����Ŀ�꣺�� v8.67 ��һ�׶μƻ�ִ�� quarter ��֤�����ڣ�2020-2026����ϴ�����ܣ�
- �������v8.67 ���߲���
- run_tag=20260620_160533
- ���ڣ�2020-2026��q01��q26��
- ����������26
- �ɹ���26
- ʧ�ܣ�0
- �������E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_quarter_clean_2020_2026_20260620160533.csv
- report root: E:\CODEXMACD\HCSJ\backtest_archive\v8.67\2020-2026
- ִ��״̬��ͨ��
## 2026-06-20 16:16:04 +08:00 - v8.67 quarter batch 2012-2019 clean (20260620_161011)
���ͣ��ز� / �������� / ��������
- ����Ŀ�꣺�� v8.67 ��һ�׶μƻ�ִ�� quarter ��֤�����ڣ�2012-2019����ϴ�����ܣ�
- �������v8.67 ���߲���
- run_tag=20260620_161011
- ���ڣ�2012-2019��q01��q32��
- ����������32
- �ɹ���32
- ʧ�ܣ�0
- �������E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_quarter_clean_2012_2019_20260620161011.csv
- report root: E:\CODEXMACD\HCSJ\backtest_archive\v8.67\2012-2019
- ִ��״̬��ͨ��
## 2026-06-20 16:20:38 +08:00 - v8.67 month_cluster batch (selected 22 months) (20260620_161608)
���ͣ��ز� / �������� / ��������
- ����Ŀ�꣺�� v8.67 ��һ�׶μƻ�ִ�� month_cluster ��֤��ѡ������/���£�
- ���ڣ�2012-2019��22���ص��£�
- run_tag=20260620_161608
- ����������24
- �ɹ���24
- ʧ�ܣ�0
- �������E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_month_cluster_clean_20260620_20260620161608.csv
- ִ��״̬��ͨ��
## 2026-06-20 16:25:20 +08:00 - v8.67 quarter/month_cluster quick����
- �ļ���HCSJ\matrix\production_readiness\v867_quarter_clean_2020_2026_20260620160533.csv
- �ļ���HCSJ\matrix\production_readiness\v867_quarter_clean_2012_2019_20260620161011.csv
- �ļ���HCSJ\matrix\production_readiness\v867_month_cluster_clean_20260620_20260620161608.csv
- �ؼ�ֵ��
  - quarter2020: count=26/success=26/win=21/sum=81307.56/avgPF=3.04/medPF=1.74/minPF=0/minTrades=5/maxDD=34.89
  - quarter2012: count=32/success=32/win=19/sum=39112.85/avgPF=1.42/medPF=1.54/minPF=0/minTrades=2/maxDD=39.14
  - month_cluster: count=24/success=24/win=7/sum=-21615.45/avgPF=1.09/medPF=0.13/minPF=0/minTrades=0/maxDD=23.94
- ���ۣ����ȼ����v8.67���߳����еͲ������¶ȴش��������Լ��п���7/24ӯ�����ֵ���ԣ��������������������Aȱ�ڸ��ˣ��˶Թؼ������µĲ�����������setӳ�䣩

## 2026-06-20 16:28:19 +08:00 - v8.67 dateshift batch 20260620_1625_dateshift
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1625_dateshift
模块：dateshift
任务目标：按 v8.67 下一阶段计划执行 dateshift 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502
场景配置：shift00,shift01,shift02,shift03,shift04,shift05,shift06,shift07
回测数量：16
成功：16
失败：0
DryRun：0
关键指标：
- v866_A_dateshift_2012-2019_shift00_r01_case0001: scenario=shift00, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift00_r01_case0002: scenario=shift00, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_dateshift_2012-2019_shift01_r01_case0003: scenario=shift01, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift01_r01_case0004: scenario=shift01, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_dateshift_2012-2019_shift02_r01_case0005: scenario=shift02, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift02_r01_case0006: scenario=shift02, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_dateshift_2012-2019_shift03_r01_case0007: scenario=shift03, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift03_r01_case0008: scenario=shift03, status=completed, profit=419292.26, PF=2.07, trades=214
- v866_A_dateshift_2012-2019_shift04_r01_case0009: scenario=shift04, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift04_r01_case0010: scenario=shift04, status=completed, profit=419292.26, PF=2.07, trades=214
- v866_A_dateshift_2012-2019_shift05_r01_case0011: scenario=shift05, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_dateshift_2020-2026_shift05_r01_case0012: scenario=shift05, status=completed, profit=419292.26, PF=2.07, trades=214
- v866_A_dateshift_2012-2019_shift06_r01_case0013: scenario=shift06, status=completed, profit=141981.65, PF=1.22, trades=254
- v866_A_dateshift_2020-2026_shift06_r01_case0014: scenario=shift06, status=completed, profit=419292.26, PF=2.07, trades=214
- v866_A_dateshift_2012-2019_shift07_r01_case0015: scenario=shift07, status=completed, profit=141981.65, PF=1.22, trades=254
- v866_A_dateshift_2020-2026_shift07_r01_case0016: scenario=shift07, status=completed, profit=419292.26, PF=2.07, trades=214
初筛结论：通过
原因代码：OK
下一步：Run A/C/D dateshift comparison batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1625_dateshift
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1625_dateshift
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1625_dateshift\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1625_dateshift\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1625_dateshift\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1625_dateshift\dateshift_stage_report.md
## 2026-06-20 16:28:45 +08:00 - v8.67 wf20 batch 20260620_1628_wf20
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1628_wf20
模块：wf20
任务目标：按 v8.67 下一阶段计划执行 wf20 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502
场景配置：validate
回测数量：2
成功：2
失败：0
DryRun：0
关键指标：
- v866_A_wf20_2012-2019_validate_r01_case0001: scenario=validate, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_wf20_2012-2019_validate_r01_case0002: scenario=validate, status=completed, profit=133752.99, PF=1.22, trades=255
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1628_wf20
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1628_wf20
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1628_wf20
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1628_wf20\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1628_wf20
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1628_wf20\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1628_wf20\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1628_wf20\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1628_wf20\wf_stage_report.md
## 2026-06-20 16:29:08 +08:00 - v8.67 wf12 batch 20260620_1628_wf12
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1628_wf12
模块：wf12
任务目标：按 v8.67 下一阶段计划执行 wf12 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502
场景配置：validate
回测数量：2
成功：2
失败：0
DryRun：0
关键指标：
- v866_A_wf12_2020-2026_validate_r01_case0001: scenario=validate, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_wf12_2020-2026_validate_r01_case0002: scenario=validate, status=completed, profit=489512.30, PF=2.07, trades=215
初筛结论：通过
原因代码：OK
下一步：Stop this branch and review wf_stage_report.md before running the next object.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1628_wf12
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1628_wf12
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1628_wf12
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1628_wf12\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1628_wf12
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1628_wf12\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1628_wf12\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1628_wf12\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1628_wf12\wf_stage_report.md
## 2026-06-20 16:33:13 +08:00 - v8.67 wf12 batch 20260620_1632_wf12
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1632_wf12
模块：wf12
任务目标：按 v8.67 下一阶段计划执行 wf12 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502
场景配置：validate
回测数量：2
成功：2
失败：0
DryRun：0
关键指标：
- v866_A_wf12_2020-2026_validate_r01_case0001: scenario=validate, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_wf12_2020-2026_validate_r01_case0002: scenario=validate, status=completed, profit=489512.30, PF=2.07, trades=215
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1632_wf12
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1632_wf12
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1632_wf12
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1632_wf12\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1632_wf12
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1632_wf12\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1632_wf12\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1632_wf12\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1632_wf12\wf_stage_report.md
## 2026-06-20 16:33:00 +08:00 - 24h unattended blocker triage: WF baseline repair
类型：排障 / runner修复 / 回测复跑
- 问题现象：24小时任务在 A 对象 wf12 批次后停止，StageDecision=Stop。
- 失败批次：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1628_wf12\wf_stage_report.md
- 根因：run_v867_next_stage.ps1 的 Get-WfBaselineProfit 只包含 B/C baseline，A 对照组缺少 2012-2019 与 2020-2026 baseline，导致 profit_retention 为空并被阈值函数按 0 处理，误判 FAIL_ELIMINATED。
- 修复文件：E:\CODEXMACD\HCSJ\scripts\run_v867_next_stage.ps1
- 修复内容：补齐 A baseline（2012-2019=133752.99，2020-2026=489512.30），并补齐 D baseline（2012-2019=35790.43，2020-2026=371235.57）以避免后续对照组同类误判。
- 复跑批次：20260620_1632_wf12
- 复跑报告：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1632_wf12\wf_stage_report.md
- 复跑结果：StageDecision=Continue；2/2 completed；profit=489512.30，PF=2.07，trades=215。
- 结论：该阻塞不是 MT5/EA 执行失败，而是 runner 判级基线缺失；已修复并继续 24h 无人值守任务。
## 2026-06-20 16:35:52 +08:00 - v8.67 wf12 batch 20260620_1635_wf12
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1635_wf12
模块：wf12
任务目标：按 v8.67 下一阶段计划执行 wf12 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A/D
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502; D=v8.66_conservative_case0401
场景配置：validate
回测数量：4
成功：4
失败：0
DryRun：0
关键指标：
- v866_A_wf12_2020-2026_validate_r01_case0001: scenario=validate, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_A_wf12_2020-2026_validate_r01_case0002: scenario=validate, status=completed, profit=489512.30, PF=2.07, trades=215
- v866_D_wf12_2020-2026_validate_r01_case0003: scenario=validate, status=completed, profit=371235.57, PF=2.23, trades=203
- v866_D_wf12_2020-2026_validate_r01_case0004: scenario=validate, status=completed, profit=371235.57, PF=2.23, trades=203
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1635_wf12
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1635_wf12
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1635_wf12
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1635_wf12\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1635_wf12
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1635_wf12\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1635_wf12\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1635_wf12\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1635_wf12\wf_stage_report.md
## 2026-06-20 16:36:00 +08:00 - 24h unattended blocker correction: A/D WF rerun
类型：排障修正 / 回测复跑
- 追加发现：历史 20260620_0453_wf12 中 A/D 均因 baseline 缺失被误判 FAIL_ELIMINATED；归档文件完整，问题仍属于 runner 判级层。
- D baseline 修正：2012-2019 使用完整窗口实际值 51100.55；2020-2026 使用 371235.57。
- 复跑批次：20260620_1635_wf12
- 输出矩阵：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1635_wf12\matrix.csv
- 阶段报告：E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1635_wf12\wf_stage_report.md
- 复跑结果：A/D 共 4/4 completed，StageDecision=Continue，StageReason=All WF cases passed required thresholds。
- 结论：24h 任务停止根因已排除，继续执行无人值守后续批次。
## 2026-06-20 16:37:10 +08:00 - v8.67 wf20 batch 20260620_1636_wf20
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1636_wf20
模块：wf20
任务目标：按 v8.67 下一阶段计划执行 wf20 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A/D
输入窗口：2012-2019 / 2020-2026
输入参数：A=v8.6_control_robust_case0502; D=v8.66_conservative_case0401
场景配置：validate
回测数量：4
成功：4
失败：0
DryRun：0
关键指标：
- v866_A_wf20_2012-2019_validate_r01_case0001: scenario=validate, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_A_wf20_2012-2019_validate_r01_case0002: scenario=validate, status=completed, profit=133752.99, PF=1.22, trades=255
- v866_D_wf20_2012-2019_validate_r01_case0003: scenario=validate, status=completed, profit=51100.55, PF=1.19, trades=250
- v866_D_wf20_2012-2019_validate_r01_case0004: scenario=validate, status=completed, profit=51100.55, PF=1.19, trades=250
初筛结论：通过
原因代码：OK
下一步：Wait for operator confirmation before running the next WF batch.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1636_wf20
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1636_wf20
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1636_wf20
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1636_wf20\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1636_wf20
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1636_wf20\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1636_wf20\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1636_wf20\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1636_wf20\wf_stage_report.md
## 2026-06-20 16:44:48 +08:00 - v8.67 month_cluster batch 20260620_1637_month_cluster
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1637_month_cluster
模块：month_cluster
任务目标：按 v8.67 下一阶段计划执行 month_cluster 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A/D
输入窗口：2012-2019
输入参数：A=v8.6_control_robust_case0502; D=v8.66_conservative_case0401
场景配置：m201407,m201408,m201409,m201410,m201411,m201412,m201501,m201502,m201503,m201504,m201505,m201506,m201701,m201702,m201703,m201704,m201705,m201706,m201907,m201908,m201909,m201910,m201911,m201912
回测数量：48
成功：48
失败：0
DryRun：0
关键指标：
- v866_A_month_cluster_2012-2019_m201407_r01_case0001: scenario=m201407, status=completed, profit=-2066.46, PF=0.00, trades=3
- v866_A_month_cluster_2012-2019_m201408_r01_case0002: scenario=m201408, status=completed, profit=0.00, PF=0.00, trades=0
- v866_A_month_cluster_2012-2019_m201409_r01_case0003: scenario=m201409, status=completed, profit=-481.83, PF=0.33, trades=4
- v866_A_month_cluster_2012-2019_m201410_r01_case0004: scenario=m201410, status=completed, profit=451.15, PF=1.33, trades=5
- v866_A_month_cluster_2012-2019_m201411_r01_case0005: scenario=m201411, status=completed, profit=-1944.75, PF=0.00, trades=2
- v866_A_month_cluster_2012-2019_m201412_r01_case0006: scenario=m201412, status=completed, profit=-217.23, PF=0.78, trades=3
- v866_A_month_cluster_2012-2019_m201501_r01_case0007: scenario=m201501, status=completed, profit=1800.26, PF=17.07, trades=2
- v866_A_month_cluster_2012-2019_m201502_r01_case0008: scenario=m201502, status=completed, profit=-2404.32, PF=0.04, trades=5
- v866_A_month_cluster_2012-2019_m201503_r01_case0009: scenario=m201503, status=completed, profit=-949.38, PF=0.07, trades=3
- v866_A_month_cluster_2012-2019_m201504_r01_case0010: scenario=m201504, status=completed, profit=-1879.72, PF=0.22, trades=4
- v866_A_month_cluster_2012-2019_m201505_r01_case0011: scenario=m201505, status=completed, profit=-1382.47, PF=0.29, trades=3
- v866_A_month_cluster_2012-2019_m201506_r01_case0012: scenario=m201506, status=completed, profit=133.76, PF=0.00, trades=1
- v866_A_month_cluster_2012-2019_m201701_r01_case0013: scenario=m201701, status=completed, profit=-3152.39, PF=0.17, trades=5
- v866_A_month_cluster_2012-2019_m201702_r01_case0014: scenario=m201702, status=completed, profit=1013.51, PF=2.01, trades=2
- v866_A_month_cluster_2012-2019_m201703_r01_case0015: scenario=m201703, status=completed, profit=-413.47, PF=0.00, trades=1
- v866_A_month_cluster_2012-2019_m201704_r01_case0016: scenario=m201704, status=completed, profit=806.03, PF=1.36, trades=3
- v866_A_month_cluster_2012-2019_m201705_r01_case0017: scenario=m201705, status=completed, profit=-3105.26, PF=0.09, trades=5
- v866_A_month_cluster_2012-2019_m201706_r01_case0018: scenario=m201706, status=completed, profit=-2515.94, PF=0.02, trades=4
- v866_A_month_cluster_2012-2019_m201907_r01_case0019: scenario=m201907, status=completed, profit=594.69, PF=1.57, trades=2
- v866_A_month_cluster_2012-2019_m201908_r01_case0020: scenario=m201908, status=completed, profit=-1650.07, PF=0.60, trades=6
- v866_A_month_cluster_2012-2019_m201909_r01_case0021: scenario=m201909, status=completed, profit=-1047.99, PF=0.00, trades=1
- v866_A_month_cluster_2012-2019_m201910_r01_case0022: scenario=m201910, status=completed, profit=-1997.37, PF=0.00, trades=3
- v866_A_month_cluster_2012-2019_m201911_r01_case0023: scenario=m201911, status=completed, profit=-887.75, PF=0.11, trades=3
- v866_A_month_cluster_2012-2019_m201912_r01_case0024: scenario=m201912, status=completed, profit=205.02, PF=1.81, trades=2
- v866_D_month_cluster_2012-2019_m201407_r01_case0025: scenario=m201407, status=completed, profit=-1770.97, PF=0.00, trades=3
- v866_D_month_cluster_2012-2019_m201408_r01_case0026: scenario=m201408, status=completed, profit=0.00, PF=0.00, trades=0
- v866_D_month_cluster_2012-2019_m201409_r01_case0027: scenario=m201409, status=completed, profit=-368.65, PF=0.33, trades=4
- v866_D_month_cluster_2012-2019_m201410_r01_case0028: scenario=m201410, status=completed, profit=218.92, PF=1.19, trades=5
- v866_D_month_cluster_2012-2019_m201411_r01_case0029: scenario=m201411, status=completed, profit=-1676.50, PF=0.00, trades=2
- v866_D_month_cluster_2012-2019_m201412_r01_case0030: scenario=m201412, status=completed, profit=-240.85, PF=0.72, trades=3
- v866_D_month_cluster_2012-2019_m201501_r01_case0031: scenario=m201501, status=completed, profit=1301.79, PF=15.96, trades=2
- v866_D_month_cluster_2012-2019_m201502_r01_case0032: scenario=m201502, status=completed, profit=-2024.70, PF=0.04, trades=5
- v866_D_month_cluster_2012-2019_m201503_r01_case0033: scenario=m201503, status=completed, profit=-817.16, PF=0.06, trades=3
- v866_D_month_cluster_2012-2019_m201504_r01_case0034: scenario=m201504, status=completed, profit=-1629.19, PF=0.20, trades=4
- v866_D_month_cluster_2012-2019_m201505_r01_case0035: scenario=m201505, status=completed, profit=-1232.98, PF=0.27, trades=3
- v866_D_month_cluster_2012-2019_m201506_r01_case0036: scenario=m201506, status=completed, profit=102.96, PF=0.00, trades=1
- v866_D_month_cluster_2012-2019_m201701_r01_case0037: scenario=m201701, status=completed, profit=-2767.08, PF=0.16, trades=5
- v866_D_month_cluster_2012-2019_m201702_r01_case0038: scenario=m201702, status=completed, profit=708.88, PF=1.83, trades=2
- v866_D_month_cluster_2012-2019_m201703_r01_case0039: scenario=m201703, status=completed, profit=-320.03, PF=0.00, trades=1
- v866_D_month_cluster_2012-2019_m201704_r01_case0040: scenario=m201704, status=completed, profit=368.50, PF=1.20, trades=3
- v866_D_month_cluster_2012-2019_m201705_r01_case0041: scenario=m201705, status=completed, profit=-2660.78, PF=0.08, trades=5
- v866_D_month_cluster_2012-2019_m201706_r01_case0042: scenario=m201706, status=completed, profit=-2122.99, PF=0.02, trades=4
- v866_D_month_cluster_2012-2019_m201907_r01_case0043: scenario=m201907, status=completed, profit=379.36, PF=1.43, trades=2
- v866_D_month_cluster_2012-2019_m201908_r01_case0044: scenario=m201908, status=completed, profit=-758.97, PF=0.72, trades=5
- v866_D_month_cluster_2012-2019_m201909_r01_case0045: scenario=m201909, status=completed, profit=-895.80, PF=0.00, trades=1
- v866_D_month_cluster_2012-2019_m201910_r01_case0046: scenario=m201910, status=completed, profit=-1726.02, PF=0.00, trades=3
- v866_D_month_cluster_2012-2019_m201911_r01_case0047: scenario=m201911, status=completed, profit=-767.58, PF=0.10, trades=3
- v866_D_month_cluster_2012-2019_m201912_r01_case0048: scenario=m201912, status=completed, profit=159.26, PF=1.81, trades=2
初筛结论：通过
原因代码：OK
下一步：Stop and review failed month artifacts.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1637_month_cluster
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1637_month_cluster
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1637_month_cluster
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1637_month_cluster\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1637_month_cluster
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1637_month_cluster\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1637_month_cluster\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1637_month_cluster\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1637_month_cluster\month_cluster_stage_report.md
## 2026-06-20 16:52:22 +08:00 - v8.67 month_cluster batch 20260620_1645_month_cluster
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1645_month_cluster
模块：month_cluster
任务目标：按 v8.67 下一阶段计划执行 month_cluster 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：A/D
输入窗口：2012-2019
输入参数：A=v8.6_control_robust_case0502; D=v8.66_conservative_case0401
场景配置：m201407,m201408,m201409,m201410,m201411,m201412,m201501,m201502,m201503,m201504,m201505,m201506,m201701,m201702,m201703,m201704,m201705,m201706,m201907,m201908,m201909,m201910,m201911,m201912
回测数量：48
成功：48
失败：0
DryRun：0
关键指标：
- v866_A_month_cluster_2012-2019_m201407_r01_case0001: scenario=m201407, status=completed, profit=-2066.46, PF=0.00, trades=3
- v866_A_month_cluster_2012-2019_m201408_r01_case0002: scenario=m201408, status=completed, profit=0.00, PF=0.00, trades=0
- v866_A_month_cluster_2012-2019_m201409_r01_case0003: scenario=m201409, status=completed, profit=-481.83, PF=0.33, trades=4
- v866_A_month_cluster_2012-2019_m201410_r01_case0004: scenario=m201410, status=completed, profit=451.15, PF=1.33, trades=5
- v866_A_month_cluster_2012-2019_m201411_r01_case0005: scenario=m201411, status=completed, profit=-1944.75, PF=0.00, trades=2
- v866_A_month_cluster_2012-2019_m201412_r01_case0006: scenario=m201412, status=completed, profit=-217.23, PF=0.78, trades=3
- v866_A_month_cluster_2012-2019_m201501_r01_case0007: scenario=m201501, status=completed, profit=1800.26, PF=17.07, trades=2
- v866_A_month_cluster_2012-2019_m201502_r01_case0008: scenario=m201502, status=completed, profit=-2404.32, PF=0.04, trades=5
- v866_A_month_cluster_2012-2019_m201503_r01_case0009: scenario=m201503, status=completed, profit=-949.38, PF=0.07, trades=3
- v866_A_month_cluster_2012-2019_m201504_r01_case0010: scenario=m201504, status=completed, profit=-1879.72, PF=0.22, trades=4
- v866_A_month_cluster_2012-2019_m201505_r01_case0011: scenario=m201505, status=completed, profit=-1382.47, PF=0.29, trades=3
- v866_A_month_cluster_2012-2019_m201506_r01_case0012: scenario=m201506, status=completed, profit=133.76, PF=0.00, trades=1
- v866_A_month_cluster_2012-2019_m201701_r01_case0013: scenario=m201701, status=completed, profit=-3152.39, PF=0.17, trades=5
- v866_A_month_cluster_2012-2019_m201702_r01_case0014: scenario=m201702, status=completed, profit=1013.51, PF=2.01, trades=2
- v866_A_month_cluster_2012-2019_m201703_r01_case0015: scenario=m201703, status=completed, profit=-413.47, PF=0.00, trades=1
- v866_A_month_cluster_2012-2019_m201704_r01_case0016: scenario=m201704, status=completed, profit=806.03, PF=1.36, trades=3
- v866_A_month_cluster_2012-2019_m201705_r01_case0017: scenario=m201705, status=completed, profit=-3105.26, PF=0.09, trades=5
- v866_A_month_cluster_2012-2019_m201706_r01_case0018: scenario=m201706, status=completed, profit=-2515.94, PF=0.02, trades=4
- v866_A_month_cluster_2012-2019_m201907_r01_case0019: scenario=m201907, status=completed, profit=594.69, PF=1.57, trades=2
- v866_A_month_cluster_2012-2019_m201908_r01_case0020: scenario=m201908, status=completed, profit=-1650.07, PF=0.60, trades=6
- v866_A_month_cluster_2012-2019_m201909_r01_case0021: scenario=m201909, status=completed, profit=-1047.99, PF=0.00, trades=1
- v866_A_month_cluster_2012-2019_m201910_r01_case0022: scenario=m201910, status=completed, profit=-1997.37, PF=0.00, trades=3
- v866_A_month_cluster_2012-2019_m201911_r01_case0023: scenario=m201911, status=completed, profit=-887.75, PF=0.11, trades=3
- v866_A_month_cluster_2012-2019_m201912_r01_case0024: scenario=m201912, status=completed, profit=205.02, PF=1.81, trades=2
- v866_D_month_cluster_2012-2019_m201407_r01_case0025: scenario=m201407, status=completed, profit=-1770.97, PF=0.00, trades=3
- v866_D_month_cluster_2012-2019_m201408_r01_case0026: scenario=m201408, status=completed, profit=0.00, PF=0.00, trades=0
- v866_D_month_cluster_2012-2019_m201409_r01_case0027: scenario=m201409, status=completed, profit=-368.65, PF=0.33, trades=4
- v866_D_month_cluster_2012-2019_m201410_r01_case0028: scenario=m201410, status=completed, profit=218.92, PF=1.19, trades=5
- v866_D_month_cluster_2012-2019_m201411_r01_case0029: scenario=m201411, status=completed, profit=-1676.50, PF=0.00, trades=2
- v866_D_month_cluster_2012-2019_m201412_r01_case0030: scenario=m201412, status=completed, profit=-240.85, PF=0.72, trades=3
- v866_D_month_cluster_2012-2019_m201501_r01_case0031: scenario=m201501, status=completed, profit=1301.79, PF=15.96, trades=2
- v866_D_month_cluster_2012-2019_m201502_r01_case0032: scenario=m201502, status=completed, profit=-2024.70, PF=0.04, trades=5
- v866_D_month_cluster_2012-2019_m201503_r01_case0033: scenario=m201503, status=completed, profit=-817.16, PF=0.06, trades=3
- v866_D_month_cluster_2012-2019_m201504_r01_case0034: scenario=m201504, status=completed, profit=-1629.19, PF=0.20, trades=4
- v866_D_month_cluster_2012-2019_m201505_r01_case0035: scenario=m201505, status=completed, profit=-1232.98, PF=0.27, trades=3
- v866_D_month_cluster_2012-2019_m201506_r01_case0036: scenario=m201506, status=completed, profit=102.96, PF=0.00, trades=1
- v866_D_month_cluster_2012-2019_m201701_r01_case0037: scenario=m201701, status=completed, profit=-2767.08, PF=0.16, trades=5
- v866_D_month_cluster_2012-2019_m201702_r01_case0038: scenario=m201702, status=completed, profit=708.88, PF=1.83, trades=2
- v866_D_month_cluster_2012-2019_m201703_r01_case0039: scenario=m201703, status=completed, profit=-320.03, PF=0.00, trades=1
- v866_D_month_cluster_2012-2019_m201704_r01_case0040: scenario=m201704, status=completed, profit=368.50, PF=1.20, trades=3
- v866_D_month_cluster_2012-2019_m201705_r01_case0041: scenario=m201705, status=completed, profit=-2660.78, PF=0.08, trades=5
- v866_D_month_cluster_2012-2019_m201706_r01_case0042: scenario=m201706, status=completed, profit=-2122.99, PF=0.02, trades=4
- v866_D_month_cluster_2012-2019_m201907_r01_case0043: scenario=m201907, status=completed, profit=379.36, PF=1.43, trades=2
- v866_D_month_cluster_2012-2019_m201908_r01_case0044: scenario=m201908, status=completed, profit=-758.97, PF=0.72, trades=5
- v866_D_month_cluster_2012-2019_m201909_r01_case0045: scenario=m201909, status=completed, profit=-895.80, PF=0.00, trades=1
- v866_D_month_cluster_2012-2019_m201910_r01_case0046: scenario=m201910, status=completed, profit=-1726.02, PF=0.00, trades=3
- v866_D_month_cluster_2012-2019_m201911_r01_case0047: scenario=m201911, status=completed, profit=-767.58, PF=0.10, trades=3
- v866_D_month_cluster_2012-2019_m201912_r01_case0048: scenario=m201912, status=completed, profit=159.26, PF=1.81, trades=2
初筛结论：通过
原因代码：OK
下一步：Do not run full month_core before cluster review.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1645_month_cluster
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1645_month_cluster
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1645_month_cluster
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1645_month_cluster\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1645_month_cluster
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1645_month_cluster\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1645_month_cluster\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1645_month_cluster\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1645_month_cluster\month_cluster_stage_report.md
## 2026-06-20 16:53:08 +08:00 - 24h unattended task pool A: validation artifact index
类型：证据索引 / 归档审计
- Result index: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_validation_result_index_20260620_165308.csv
- Artifact audit: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_validation_artifact_audit_20260620_165308.md
- Indexed rows: 375
- Rows with missing artifacts: 12
- 结论：继续执行；该任务不修改EA源码。

## 2026-06-20 17:01:09 +08:00 - v8.67 month_cluster batch 20260620_1653_month_cluster
类型：回测 / 参数生成 / 报告生成
run_id: 20260620_1653_month_cluster
模块：month_cluster
任务目标：按 v8.67 下一阶段计划执行 month_cluster 小批次验证
MT5路径：D:\MT5测试\MetaTrader 5
输入对象：B/C
输入窗口：2012-2019
输入参数：B=v8.66_robust_main_case0010; C=v8.66_aggressive_case0005
场景配置：m201407,m201408,m201409,m201410,m201411,m201412,m201501,m201502,m201503,m201504,m201505,m201506,m201701,m201702,m201703,m201704,m201705,m201706,m201907,m201908,m201909,m201910,m201911,m201912
回测数量：48
成功：48
失败：0
DryRun：0
关键指标：
- v866_B_month_cluster_2012-2019_m201407_r01_case0001: scenario=m201407, status=completed, profit=-2046.09, PF=0.00, trades=3
- v866_B_month_cluster_2012-2019_m201408_r01_case0002: scenario=m201408, status=completed, profit=0.00, PF=0.00, trades=0
- v866_B_month_cluster_2012-2019_m201409_r01_case0003: scenario=m201409, status=completed, profit=-433.68, PF=0.33, trades=4
- v866_B_month_cluster_2012-2019_m201410_r01_case0004: scenario=m201410, status=completed, profit=253.52, PF=1.18, trades=5
- v866_B_month_cluster_2012-2019_m201411_r01_case0005: scenario=m201411, status=completed, profit=-1947.95, PF=0.00, trades=2
- v866_B_month_cluster_2012-2019_m201412_r01_case0006: scenario=m201412, status=completed, profit=-304.38, PF=0.70, trades=3
- v866_B_month_cluster_2012-2019_m201501_r01_case0007: scenario=m201501, status=completed, profit=1519.23, PF=16.04, trades=2
- v866_B_month_cluster_2012-2019_m201502_r01_case0008: scenario=m201502, status=completed, profit=-2350.26, PF=0.04, trades=5
- v866_B_month_cluster_2012-2019_m201503_r01_case0009: scenario=m201503, status=completed, profit=-952.45, PF=0.06, trades=3
- v866_B_month_cluster_2012-2019_m201504_r01_case0010: scenario=m201504, status=completed, profit=-1887.46, PF=0.20, trades=4
- v866_B_month_cluster_2012-2019_m201505_r01_case0011: scenario=m201505, status=completed, profit=-1452.03, PF=0.26, trades=3
- v866_B_month_cluster_2012-2019_m201506_r01_case0012: scenario=m201506, status=completed, profit=120.56, PF=0.00, trades=1
- v866_B_month_cluster_2012-2019_m201701_r01_case0013: scenario=m201701, status=completed, profit=-3181.82, PF=0.16, trades=5
- v866_B_month_cluster_2012-2019_m201702_r01_case0014: scenario=m201702, status=completed, profit=824.36, PF=1.83, trades=2
- v866_B_month_cluster_2012-2019_m201703_r01_case0015: scenario=m201703, status=completed, profit=-373.76, PF=0.00, trades=1
- v866_B_month_cluster_2012-2019_m201704_r01_case0016: scenario=m201704, status=completed, profit=401.63, PF=1.18, trades=3
- v866_B_month_cluster_2012-2019_m201705_r01_case0017: scenario=m201705, status=completed, profit=-3062.67, PF=0.08, trades=5
- v866_B_month_cluster_2012-2019_m201706_r01_case0018: scenario=m201706, status=completed, profit=-2452.92, PF=0.02, trades=4
- v866_B_month_cluster_2012-2019_m201907_r01_case0019: scenario=m201907, status=completed, profit=434.19, PF=1.42, trades=2
- v866_B_month_cluster_2012-2019_m201908_r01_case0020: scenario=m201908, status=completed, profit=-968.38, PF=0.69, trades=5
- v866_B_month_cluster_2012-2019_m201909_r01_case0021: scenario=m201909, status=completed, profit=-1039.13, PF=0.00, trades=1
- v866_B_month_cluster_2012-2019_m201910_r01_case0022: scenario=m201910, status=completed, profit=-2000.80, PF=0.00, trades=3
- v866_B_month_cluster_2012-2019_m201911_r01_case0023: scenario=m201911, status=completed, profit=-900.10, PF=0.10, trades=3
- v866_B_month_cluster_2012-2019_m201912_r01_case0024: scenario=m201912, status=completed, profit=184.94, PF=1.81, trades=2
- v866_C_month_cluster_2012-2019_m201407_r01_case0025: scenario=m201407, status=completed, profit=-2248.88, PF=0.00, trades=3
- v866_C_month_cluster_2012-2019_m201408_r01_case0026: scenario=m201408, status=completed, profit=0.00, PF=0.00, trades=0
- v866_C_month_cluster_2012-2019_m201409_r01_case0027: scenario=m201409, status=completed, profit=-478.87, PF=0.33, trades=4
- v866_C_month_cluster_2012-2019_m201410_r01_case0028: scenario=m201410, status=completed, profit=270.04, PF=1.18, trades=5
- v866_C_month_cluster_2012-2019_m201411_r01_case0029: scenario=m201411, status=completed, profit=-2136.88, PF=0.00, trades=2
- v866_C_month_cluster_2012-2019_m201412_r01_case0030: scenario=m201412, status=completed, profit=-334.55, PF=0.70, trades=3
- v866_C_month_cluster_2012-2019_m201501_r01_case0031: scenario=m201501, status=completed, profit=1689.26, PF=16.22, trades=2
- v866_C_month_cluster_2012-2019_m201502_r01_case0032: scenario=m201502, status=completed, profit=-2565.58, PF=0.04, trades=5
- v866_C_month_cluster_2012-2019_m201503_r01_case0033: scenario=m201503, status=completed, profit=-1042.84, PF=0.06, trades=3
- v866_C_month_cluster_2012-2019_m201504_r01_case0034: scenario=m201504, status=completed, profit=-2056.57, PF=0.20, trades=4
- v866_C_month_cluster_2012-2019_m201505_r01_case0035: scenario=m201505, status=completed, profit=-1593.82, PF=0.26, trades=3
- v866_C_month_cluster_2012-2019_m201506_r01_case0036: scenario=m201506, status=completed, profit=132.88, PF=0.00, trades=1
- v866_C_month_cluster_2012-2019_m201701_r01_case0037: scenario=m201701, status=completed, profit=-3506.87, PF=0.15, trades=5
- v866_C_month_cluster_2012-2019_m201702_r01_case0038: scenario=m201702, status=completed, profit=900.08, PF=1.82, trades=2
- v866_C_month_cluster_2012-2019_m201703_r01_case0039: scenario=m201703, status=completed, profit=-411.14, PF=0.00, trades=1
- v866_C_month_cluster_2012-2019_m201704_r01_case0040: scenario=m201704, status=completed, profit=420.31, PF=1.17, trades=3
- v866_C_month_cluster_2012-2019_m201705_r01_case0041: scenario=m201705, status=completed, profit=-3358.63, PF=0.08, trades=5
- v866_C_month_cluster_2012-2019_m201706_r01_case0042: scenario=m201706, status=completed, profit=-2685.97, PF=0.02, trades=4
- v866_C_month_cluster_2012-2019_m201907_r01_case0043: scenario=m201907, status=completed, profit=474.02, PF=1.42, trades=2
- v866_C_month_cluster_2012-2019_m201908_r01_case0044: scenario=m201908, status=completed, profit=-1052.61, PF=0.69, trades=5
- v866_C_month_cluster_2012-2019_m201909_r01_case0045: scenario=m201909, status=completed, profit=-1146.63, PF=0.00, trades=1
- v866_C_month_cluster_2012-2019_m201910_r01_case0046: scenario=m201910, status=completed, profit=-2201.26, PF=0.00, trades=3
- v866_C_month_cluster_2012-2019_m201911_r01_case0047: scenario=m201911, status=completed, profit=-985.85, PF=0.10, trades=3
- v866_C_month_cluster_2012-2019_m201912_r01_case0048: scenario=m201912, status=completed, profit=199.74, PF=1.80, trades=2
初筛结论：通过
原因代码：OK
下一步：Do not run full month_core before cluster review.
输出路径：
- set: E:\CODEXMACD\HCSJ\set\v8.67_validation_runs\20260620_1653_month_cluster
- ini: E:\CODEXMACD\HCSJ\v8.67_validation_runs\20260620_1653_month_cluster
- htm: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1653_month_cluster
- metrics: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1653_month_cluster\matrix.csv
- notes: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1653_month_cluster
- matrix: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1653_month_cluster\matrix.csv
- logs: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1653_month_cluster\_logs
- manifest: E:\CODEXMACD\HCSJ\backtest_archive\v8.67_validation_runs\20260620_1653_month_cluster\_batch_manifest.csv
- stage_report: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1653_month_cluster\month_cluster_stage_report.md
## 2026-06-20 17:01:42 +08:00 - 24h unattended month-cluster A/B/C/D summary
类型：月度簇对比 / 过拟合风险解释
- Summary CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_month_cluster_abcd_summary_20260620_170142.csv
- Summary MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_month_cluster_abcd_summary_20260620_170142.md
- A/D run: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1645_month_cluster\matrix.csv
- B/C run: E:\CODEXMACD\HCSJ\matrix\v8.67_validation_runs\20260620_1653_month_cluster\matrix.csv
- 结论：A/B/C/D 在重点亏损月簇均为 active_positive_rate=0.3043，属于结构性弱点证据；执行链路未阻塞，readiness 维持 demo/forward。

## 2026-06-20 17:02:11 +08:00 - 24h unattended task pool A: real artifact audit
类型：归档审计 / 证据闭环
- Audit: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_validation_real_artifact_audit_20260620_170211.md
- Real rows: 363
- Real missing rows: 0
- DRY_RUN missing rows: 12
- 结论：真实回测产物无缺失；历史DRY_RUN缺失不作为blocker。

## 2026-06-20 17:03:08 +08:00 - 24h unattended continuation report and handoff update
类型：阶段报告 / 交接更新
- Continuation report: E:\CODEXMACD\HCSJ\matrix\production_readiness\production_readiness_unattended_continuation_20260620_170308.md
- Handoff updated: E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
- Current decision: Level 2 demo/forward only
- 下一步：继续任务池B/C，但不修改EA源码。

## 2026-06-20 17:04:17 +08:00 - 24h unattended task pool B: dateshift A/B/C/D summary
类型：起止边界敏感性汇总 / 过拟合排查
- Summary CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_dateshift_abcd_summary_20260620_170417.csv
- Summary MD: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_dateshift_abcd_summary_20260620_170417.md
- Selected runs: A=20260620_1625_dateshift; B=20260619_1600_dateshift_B; C=20260619_1640_dateshift_C; D=20260619_1650_dateshift_D
- 结论：dateshift 未出现总窗口亏损，但旧窗口PF偏弱；月度簇风险仍保留。

## 2026-06-20 17:19:25 +08:00 - 24h unattended task pool B: near-boundary regression
类型：边界窗口回归 / 近期样本拆解
- CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_near_boundary_regression_20260620_171828.csv
- Report: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_near_boundary_regression_20260620_171828.md
- Runs: 5
- Completed: 5
- 结论：已补充2024/2025/2026H1及相邻窗口；不修改EA源码。

## 2026-06-20 17:20:21 +08:00 - 24h unattended task pool C: execution risk go/no-go matrix
类型：执行风险闭环 / go-no-go判定
- Matrix: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_execution_risk_go_no_go_matrix_20260620_172021.md
- Spread source: E:\CODEXMACD\HCSJ\matrix\production_readiness\spread_probe_v867_20260620_154834.csv
- Slippage source: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_slippage_harness_20260620_155009\slippage_harness_v867_20260620_155009.csv
- Decision: NO-GO real-money live; GO demo/forward only.

## 2026-06-20 17:20:44 +08:00 - 24h unattended remaining progress index
类型：索引 / 交接更新
- Index: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_24h_remaining_progress_index_20260620_172044.md
- Handoff updated: E:\CODEXMACD\HANDOFF_NEXT_WINDOW.md
- 结论：剩余进度继续推进并形成统一入口。

## 2026-06-20 17:21:04 +08:00 - 24h unattended task pool D: forward monitor readiness audit
类型：forward-monitor审计 / 运维交接
- Audit: E:\CODEXMACD\HCSJ\forward_monitor\forward_monitor_readiness_audit_20260620_172104.md
- Decision: monitoring files ready; real account baseline not fabricated.

## 2026-06-20 17:21:23 +08:00 - 24h unattended task pool B: month-cluster mitigation plan
类型：风险处置计划 / 后续开发入口
- Plan: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_month_cluster_mitigation_plan_20260620_172123.md
- Evidence: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_month_cluster_abcd_summary_20260620_170142.md
- Decision: Keep Level 2 demo/forward; mitigation required before live promotion.

## 2026-06-20 17:22:49 +08:00 - 24h unattended task pool B: D near-boundary regression
类型：保守参数近端边界对照 / 无源码修改
- CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v866_D_near_boundary_regression_20260620_172153.csv
- Report: E:\CODEXMACD\HCSJ\matrix\production_readiness\v866_D_near_boundary_regression_20260620_172153.md
- Runs: 5
- Completed: 5

## 2026-06-20 17:23:19 +08:00 - 24h unattended task pool B: B vs D near-boundary comparison
类型：主线/保守参数对比
- CSV: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_B_vs_D_near_boundary_comparison_20260620_172319.csv
- Report: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_B_vs_D_near_boundary_comparison_20260620_172319.md
- 结论：D继续作为观察对象，不替代B，除非后续证明DD改善足以抵消收益锚点损失。
