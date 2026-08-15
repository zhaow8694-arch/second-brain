# Strategy Pipeline Architecture (v0 - Phase 0 Design)

## 1. 任务背景与目标
用户要求构建端到端自动化策略流水线：
Strategy Factory → Auto Optimizer (参数搜索) → Backtest Engine → Strategy Scoring → Filter Engine (淘汰80%-95%) → Best Strategy EA 输出

本设计严格遵守：
- AGENTS.md 所有规则
- docs/AI_RULES.md（风控优先、模块边界、planning-only + compile-only 阶段）
- 当前项目处于 v0.5.x no-trade / compile-only / observability 边界（TASK-321 parser integration 等）
- 禁止任何 MT5 运行、Strategy Tester、真实交易、.ex5 直接落库

## 2. 总体架构原则（Phase 0 共识）
- **Python 主导生成与流程编排**（安全、易迭代）
- **MQL5 只提供可模板化、边界清晰的策略骨架**（复用现有 EaController + SignalEngine + RiskManager + ExecutionManager 架构）
- **所有输出必须走现有 compile-only / quarantine / validation 工具链**
- **每个阶段只改极小范围**，严禁一次性大重构
- **信号只算信号**，风控必须前置，执行必须唯一入口
- **利用现有资产**：tools/ 中的 parse_*、validate_*、run_mql5_compile_only_quarantined、backtest/sets、InputConfig 的 observability 机制

## 3. 流水线阶段定义（高层）
1. **Strategy Factory**：根据策略模板 + 参数定义，生成 MQL5 模块化策略代码（主要是 SignalEngine 变体 + InputConfig 片段）
2. **Auto Optimizer**：在参数空间内生成大量变体（网格 / 随机 / 进化），输出参数清单
3. **Backtest Engine**：利用现有 backtest/sets + tools/parse_strategy_tester_html_report.py 等，驱动“模拟回测流程”（compile-only 阶段仅生成 sets + manifest，不实际跑 MT5）
4. **Strategy Scoring**：按 AI_RULES 优先级打分（稳定性 > 回撤控制 > 风险收益比 > 净利润）
5. **Filter Engine**：硬过滤（风控底线）+ 软过滤（分数阈值），淘汰 80%-95%
6. **Best Strategy EA Output**：生成完整可编译的 TradingSystem + 对应模块 + 推荐 .set + manifest

## 4. MQL5 侧设计要点
- 保持现有 7 文件 inventory 不随意膨胀（通过生成到 `generated/` 或 `backtest/generated_sets/` 受控位置）
- 策略变体主要通过：
  - 不同的 SignalEngine 实现（或条件编译）
  - InputConfig 参数组合
  - 未来可扩展多 SignalEngine 注册机制
- 必须生成符合以下的代码：
  - SignalEngine 只返回 SignalResult（direction, confidence, reason）
  - RiskManager 的 CanExecuteSignal 必须被调用
  - ExecutionManager 是唯一执行入口
  - 大量 observability snapshot（GetReadOnly*Snapshot）
- 示例模板策略（Phase 1 起步）：
  - EMA Cross（当前已有骨架）
  - RSI Mean Reversion
  - ATR Breakout（带风控参数）
- MagicNumber 规则：策略ID + 变体ID + 版本

## 5. Python 侧设计要点
推荐目录（Phase 1 后逐步创建）：
python/strategy_pipeline/
  - factory/
  - optimizer/
  - backtest_driver/
  - scorer/
  - filter/
  - best_ea_generator/
  - templates/          # MQL5 代码模板
  - schemas/            # 参数空间定义 JSON Schema

参数空间定义示例（YAML/JSON）：
- strategy_type: ema_cross | rsi_reversion | atr_breakout
- fast_period: [10,20,50]
- slow_period: [50,100,200]
- atr_period, risk_pct, max_spread 等

## 6. 与现有基础设施集成
- backtest/sets/ ：Factory 可生成 observation mode 的 .set
- tools/：
  - run_mql5_compile_only_quarantined.py （生成代码必须通过）
  - inspect_mq5_strategy_inventory.py （验证 inventory）
  - parse_backtest_runtime_summary.py / validate_backtest_* （评分输入）
  - run_release_validation_bundle.py （最终集成检查点）
- docs/：使用 BACKTEST_REPORT_TEMPLATE 精神输出评分报告
- logger / RiskManager 的 observation snapshot 必须保留在生成的策略中

## 7. 风险点与缓解（Phase 0 识别）
- 风险1：生成代码破坏模块边界 → 缓解：代码生成模板必须通过静态检查 + 人工 review 模板
- 风险2：参数搜索爆炸导致太多无效变体 → 缓解：Filter 尽早介入 + 硬风控参数约束
- 风险3：超出 compile-only 边界 → 缓解：所有生成路径默认走 quarantine，manifest 记录
- 风险4：与当前 TASK-319 no-trade startup 冲突 → 缓解：本流水线完全独立于 MT5 启动，生成物不触发 terminal
- 风险5：一次性大改 → 缓解：本计划严格 Phase 化，每个 Phase 只改极小范围

## 8. 验证方式（贯穿所有 Phase）
- 静态：tools/ 中的 validate_mq5_static_* + inspect_mq5_strategy_inventory.py
- 编译：run_mql5_compile_only_quarantined.py
- 流程：run_release_validation_bundle.py + `validate_parser_manifest_integration.py` + `run_evidence_parser_pipeline.py`
- 文档：每次 Phase 用 DEV_LOG_TEMPLATE 汇报 + 更新本设计文档
- 边界：所有输出必须包含 "Inventory only; no MT5 run; no trading authorization." 声明

## 9. 推荐 Phase 划分（更新版）
- Phase 0（本阶段）：现状盘点 + 本设计文档（已完成）
- Phase 1：Strategy Factory 骨架 + 参数 Schema（Python 生成器，已完成骨架；MQL5 模板仍待授权）
- Phase 2：Auto Optimizer 基础实现（参数变异 + 清单输出）
- Phase 3：Backtest Driver 封装（集成现有 parse 工具 + sets 生成）
- Phase 4：Scorer + Filter 实现
- Phase 5：Best EA 生成器 + manifest 输出
- Phase 6：全流程编排脚本 + 集成到 release validation
- Phase 7+：实际策略模板扩展 + 真实参数空间定义 + 更多评分维度

## 10. 下一步
本 Phase 0 设计文档产出后，请求用户批准 Phase 1 计划后再执行任何代码修改。

---
**状态**：Phase 0 设计文档 v0 完成；Phase 1 Factory 骨架已落地（TASK-321）
**遵守**：planning-only + compile-only + AGENTS.md + AI_RULES.md

（后续实际实现时将严格按批准的范围执行）
