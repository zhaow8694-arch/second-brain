# AIMart v0.3.1 Recovery Finalize Toolkit

用途：接管当前 `feature/v0.3.1-auto-verified-customer-runtime` 分支上已经生成但未冻结的 v0.3.1 修改，在宿主 PowerShell 中自动完成：

- pnpm test / lint / build
- 生成 releases/v0.3.1/source ZIP
- 通过本地 Next API 生成 sample execution-pack ZIP
- 解压并验证 sample execution-pack 结构
- 校验 SHA256
- 写 RELEASE_MANIFEST.txt
- 检查历史 release 未被修改
- 提交本地 commit
- 创建/更新本地 tag v0.3.1
- 输出 PASS / FAIL

它不会修改 releases/v0.1.0、v0.1.1、v0.2.1、v0.2.2、v0.3.0。
它不会 git push。

## 使用

双击：

```text
START_V0.3.1_RECOVERY_FINALIZE.cmd
```

或在 PowerShell 中执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\Start_AIMart_v0.3.1_Recovery_Finalize.ps1
```

默认项目目录：

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

如需修改项目目录，编辑 ps1 顶部的 `$ProjectRoot`。
