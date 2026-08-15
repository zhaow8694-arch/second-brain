# Backtest Reports

## 目录用途

本目录用于保存 MT5 Strategy Tester 的结构化回测报告。

每个报告应记录：

- 测试任务编号
- EA 版本
- 测试品种
- 测试周期
- 测试时间区间
- 使用的 .set 文件
- 关键输入参数
- Runtime summary 指标
- 风控状态
- 是否出现订单或持仓
- 最终结论
- 下一步建议

## 标准流程

1. 先生成或确认 .set 文件。
2. 在 MT5 Strategy Tester 中加载 .set。
3. 运行测试。
4. 从日志中复制关键 Runtime summary。
5. 填写结构化报告。
6. 报告和代码分开提交。

## 命名规范

建议格式：

TASK-XXX_version_description.md

例如：

TASK-010_v0.1.7_core_signal_log_throttle.md

## 禁止事项

- 不允许编造回测结果。
- 没有实际运行的测试不得写成“已通过”。
- 不允许把观察信号当成可实盘策略。
- 不允许在报告中声称当前系统可以真实交易。
- 当前阶段仍然是观察和工程稳定阶段。
