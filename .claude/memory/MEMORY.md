# Memory Index

> 自动维护的持久记忆索引 — 每次会话启动时加载
> 记录不能在代码库/知识库中直接推断出的隐性知识
> 最大 200 行，超过时自动裁剪最旧条目

## 活跃记忆

- [第二大脑架构升级](C:\Users\Administrator\.claude\projects\E-----\memory\second-brain-upgrade.md) — hooks + skills + MCP + 三层缓存
- [SessionStart hook 编码修复](C:\Users\Administrator\.claude\projects\E-----\memory\hook-encoding-fix.md) — PowerShell UTF-8 乱码
- [Grok CLI 缓存膨胀](C:\Users\Administrator\.claude\projects\E-----\memory\grok-cache-bloat.md) — ~200GB 清理
- [SniperTrendEA v8.6 STOPLEVEL 修复](C:\Users\Administrator\.claude\projects\E-----\memory\snipertrendea-stoplevel-fix.md) — 2026-07-29 修复 CFD 品种错误 4756

## 数据库状态（2026-07-29）

| 数据库 | 记录数 |
|:-------|:------:|
| backtest_results.db | 6,307 |
| strategy_versions.db | 51（23个策略） |
| knowledge_index.db | 120 |
| learning_notes.db | 6 |
| parameter_optimization.db | 0（空）|

## 知识库规模
- 总文件：61,018（E 盘主库）+ 61,018（F 盘备份）
- EA 源码：3,184（MQ5 2,148 + MQ4 1,036）
- Git 提交：23 次

## SniperTrendEA 版本总结
- v8.6 merge (r35probe)：平均 +$74,715，18次测试，推荐版本
- v8.65 grokbase_risk：平均 +$57,494，风控优化版
- v8.69 fix2b：胜率 77.8%，但样本仅18次
- 当前实盘：v8.6 积极模式，XAUUSD.c H4

## 非对称交易理论（V3/V9）
- 核心：以极小试错成本博取肥尾单边利润（双子星掩护→光速平保→狂暴金字塔）
- V9 溯源版已修复"逻辑 Bug"但回测仅 +$251
- 原始 12k 参数在 EA8.28 纯技术原始版本.mq4 中
- 开发文档：01_交易系统/赵威MT4/终极非对称量化系统开发与排错全纪录.txt

## 数据库存储
- 数据文件：E:\知识库\07_数据库\（SSD 读写）
- 备份位置：F:\知识库\07_数据库\（HDD 冷备）

## 已知问题和规避方案

- Windows PowerShell 5.1 中文编码 → hook 脚本第一行有效代码写入 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`（2026-07-07 实际修复）
- 修改文件前必须先备份 → CLAUDE.md 已写入规则（2026-07-29）
- XAUUSD.c CFD 品种 STOPLEVEL 限制 → v8.6 已加入自适应修复

## 项目决策记录

- 2026-06-26 采用 worker-mode claude-mem（非 server-beta），手动维护本地记忆文件
- 2026-07-29 MEMORY.md 全面更新，新增数据库状态/EA分析/修复记录

## 操作记录指引
详细操作记录见 `操作日志.md`（根目录）
工作摘要见 `工作记录.md`（根目录）
