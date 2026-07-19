# AIMart v0.3.1 Auto-Verified Customer Runtime Toolkit

这个工具包用于开发 AIMart Orchestrator v0.3.1。

## 目标

把你刚才人工做过的所有验证步骤，全部放进自动执行链路里。以后 Runner 完成后不能只说“完成”，必须自动执行并显示：

- Git 状态检查
- Tag 指向检查
- Release 目录检查
- Source ZIP 检查
- SHA256 校验
- Sample execution-pack ZIP 解压检查
- 多 AI adapter 检查
- START_HERE / START_CODEX_AUTONOMOUS 客户入口检查
- pnpm test / lint / build
- Completion Gate PASS / FAIL
- 自动冻结、自动本地 commit、自动 tag

## 使用方式

1. 解压到项目外部，例如：

```text
E:\AIMart_Orchestrator\aimart_auto_verified_customer_runtime_v031
```

2. 确认 AIMart 项目已经完成并冻结 v0.3.0，工作区干净。

3. 双击：

```text
START_V0.3.1_AUTO_VERIFIED_CUSTOMER_RUNTIME.cmd
```

## 重要原则

- 不需要用户再手动执行验收命令。
- Runner 结束后必须显示 PASS / FAIL。
- 如果失败，必须告诉失败在哪个 gate，并写入 V0.3.1_KNOWN_ISSUES.md 或 BLOCKERS.md。
- 不允许修改历史 release：v0.1.0 / v0.1.1 / v0.2.1 / v0.2.2 / v0.3.0。
- 不允许 git push。
