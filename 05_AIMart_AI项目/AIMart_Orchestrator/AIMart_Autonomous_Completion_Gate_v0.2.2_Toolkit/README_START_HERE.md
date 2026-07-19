# AIMart v0.2.2 Autonomous Completion Gate Toolkit

这个工具包用于下一阶段开发：**v0.2.2 无人值守完成门禁与自验证系统**。

## 目标

v0.2.1 已经实现了“单窗口可视化无人值守 Runner”。  
v0.2.2 的目标是把我们手动做过的验收步骤固化为自动门禁：

- 自动运行 test / lint / build
- 自动检查 release 目录
- 自动校验 source ZIP 和 sample execution-pack ZIP
- 自动校验 SHA256
- 自动检查 sample execution-pack 中的关键文件
- 自动检查 source ZIP 不包含 node_modules / .next / .git / releases / codex_runs / .env
- 自动检查历史 release 没有被修改
- 自动生成最终交付文档
- 自动本地 commit
- 自动打当前版本 tag
- 不 push 远程
- 不改历史 tag
- 不改历史 release

## 放置位置

请把本工具包解压到项目目录外部，例如：

```text
E:\AIMart_Orchestrator\aimart_autonomous_completion_gate_v022
```

目标项目仍然是：

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

不要把这个工具包解压到目标项目根目录里。

## 启动方式

双击：

```text
START_V0.2.2_AUTONOMOUS_COMPLETION_GATE.cmd
```

启动后只保留这一个窗口即可。窗口会显示：

- 当前运行时间
- Codex 进程状态
- 当前 Git 分支
- dirty file 数量
- release 输出状态
- 最近 PROGRESS_LOG
- 最新 Codex 日志尾部
- known issues 状态
- 完成后的 release / tag / git status 汇总

## 重要限制

这个 Runner 不会 push 远程仓库。  
它会要求 Codex 只创建当前版本 `v0.2.2` 的本地 commit 和 tag，不允许修改历史 release 或历史 tag。

如果启动前发现目标项目工作区不是干净状态，Runner 默认会停止，避免把上一个任务的未提交修改混入 v0.2.2。
