# AIMart v0.3.2 Autonomous Runner Hardening Toolkit

目标版本：v0.3.2

目标：把 v0.3.1 过程中暴露出来的 V1/V2/V3... 多次热修复问题，固化为一个稳定的单窗口无人值守 Runner。

本包是外部启动工具包，不要放进项目源码目录。

推荐解压位置：

```text
E:\AIMart_Orchestrator\aimart_v032_autonomous_runner_hardening
```

启动：

```text
START_V0.3.2_AUTONOMOUS_RUNNER_HARDENING.cmd
```

运行前必须满足：

- 当前项目目录存在。
- v0.3.1 tag 已存在并指向当前 HEAD。
- Git 工作区干净。
- releases/v0.3.1 中 source ZIP、sample ZIP、SHA256.txt、RELEASE_MANIFEST.txt、dogfood 证据存在。
- 不运行旧版 V1/V2/V3/V4/V5/V6/V7/V8/V9 hotfix runner。

v0.3.2 目标不是新增业务功能，而是增强 Runner 稳定性：

- 一个 Runner 自动识别失败阶段。
- 自动处理 stale sample ZIP。
- 自动区分 JSON zipBase64 与真实 ZIP。
- 自动标准化 ZIP entry 路径。
- 自动阻止旧 runner 误运行。
- 自动输出下一步动作。
- 自动 completion gate、commit、tag、freeze。

成功标准：窗口最终显示：

```text
Autonomous Runner Hardening: PASS
Completion Gate: PASS
Release artifacts: PASS
Sample pack: PASS
Git status: clean
Tag v0.3.2: points to final commit
```
