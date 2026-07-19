# AIMart Unified Autonomous Runner v0.2.1 Toolkit

这个包解决一个明确问题：

> 不再让用户为了无人值守任务打开 Runner 窗口、监控窗口、日志窗口等多个窗口。

## 重要说明

当前正在运行的 v0.2 任务不要中断，也不要为了这个包再开第三个窗口。

这个包用于 **当前任务完成后的下一轮开发**，目标是把 AIMart 的无人值守能力升级为：

- 一个入口
- 一个窗口
- 自动启动 Codex
- 自动保存日志
- 自动显示心跳状态
- 自动显示最近日志摘要
- 自动生成完成报告
- 失败时直接显示最后错误
- 不要求用户额外打开监控窗口

## 使用方式

当前 v0.2 任务结束并提交后，再双击：

```text
START_UNIFIED_AUTONOMOUS_RUNNER.cmd
```

默认项目目录：

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

默认任务提示：

```text
codex/NEXT_TASK_PROMPT_UNIFIED_RUNNER.md
```

## 这个包不会做什么

- 不会 push 远程仓库
- 不会修改 releases/v0.1.0
- 不会修改 releases/v0.1.1
- 不会读取 .env、SSH key、云凭据
- 不会执行生产部署
- 不会自动开多个窗口

## 成功后的目标

AIMart 自身应内置这种统一 Runner 模式，之后生成的 execution pack 也应包含：

```text
agent_adapters/codex/run-codex-unified-autonomous.ps1
agent_adapters/codex/run-codex-unified-autonomous.sh
agent_adapters/codex/CODEX_UNIFIED_AUTONOMOUS_RUNBOOK.md
runtime/AUTONOMOUS_RUN_STATUS.md
runtime/AUTONOMOUS_RUN_SUMMARY.md
```
