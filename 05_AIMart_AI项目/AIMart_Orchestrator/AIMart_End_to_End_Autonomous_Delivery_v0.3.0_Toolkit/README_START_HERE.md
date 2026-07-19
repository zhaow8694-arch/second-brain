# AIMart v0.3.0 End-to-End Autonomous Delivery Toolkit

目标：把 AIMart 从“单版本无人值守”推进到“从一次深度沟通到最终可交付版本的全程无人干预”。

本工具包不是放进项目源码的文件夹，而是外部启动器。建议解压到：

```text
E:\AIMart_Orchestrator\aimart_e2e_autonomous_delivery_v030
```

目标项目默认是：

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

启动方式：

```text
START_V0.3.0_END_TO_END_AUTONOMOUS_DELIVERY.cmd
```

这个 Runner 会在一个窗口中完成：

- 启动 Codex 无人值守执行
- 显示项目是否正在开展
- 显示 Git 分支、dirty 文件数量、日志更新时间、release 输出状态
- 显示最新 stdout/stderr 摘要
- 显示 Completion Gate 状态
- 结束后显示 release 目录、tag、git 状态、known issues

本阶段核心目标：

```text
v0.3.0：End-to-End Autonomous Delivery System + Agent Adapter Registry
```

它要让 AIMart 生成的执行包不只是某个小版本无人值守，而是能从 `v0.0.1` 规划、MVP、迭代、验收、冻结一直推进到最终交付版本。

重要原则：

- 不是让多个 AI 混合开发。
- 是一次深度沟通后，生成不同 AI 可独立执行的包。
- 用户选择一个 AI 执行，比如 Codex / Claude Code / Trae / Cursor。
- 该 AI 根据执行包持续执行、测试、修复、验收、冻结和进入下一阶段。
- 高风险动作不会默认执行，而是进入 APPROVAL_QUEUE，并继续其他不依赖该动作的任务。

运行前要求：

1. 项目工作区必须干净。
2. 当前 tag `v0.2.2` 必须存在并指向已完成提交。
3. 不要同时运行旧 Runner。
4. 不要修改 `releases/v0.1.0`、`releases/v0.1.1`、`releases/v0.2.1`、`releases/v0.2.2`。

如果 Runner 发现工作区不干净，会停止，避免版本混乱。
