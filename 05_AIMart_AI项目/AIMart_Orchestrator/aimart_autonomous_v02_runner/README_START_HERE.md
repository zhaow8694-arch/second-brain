# AIMart v0.2 Codex 无人值守运行包

这个包用于让 Codex 在 AIMart Orchestrator 项目中以无人值守方式执行下一阶段任务。

默认项目目录：

```text
E:\AIMart_Orchestrator\AIMart_Orchestrator_v0.1_CodexOnly_BuildPack
```

## 最简单用法

1. 下载并解压本 ZIP。
2. 双击 `START_AUTONOMOUS_V0.2.cmd`。
3. 脚本会自动：
   - 检查 Codex 是否可用
   - 写入 `codex/V0.2_AUTONOMOUS_PROMPT.md`
   - 创建 `codex_runs/autonomous_v0_2` 日志目录
   - 使用 `codex exec` 启动无人值守任务
   - 尽量使用 `workspace-write + approval never`

## 重要安全边界

脚本不会主动执行 `git push`。
任务提示中明确禁止：

- 修改 `releases/v0.1.0`
- 修改 `releases/v0.1.1`
- 删除历史 release
- 强制覆盖历史 tag
- 读取 `.env`、SSH key、系统密钥
- 生产部署
- 真实数据库迁移
- 云资源创建或删除

## 输出位置

日志会写入：

```text
codex_runs/autonomous_v0_2/
```

v0.2 产物应由 Codex 生成到：

```text
releases/v0.2.0/
```

## 如果 Codex CLI 不支持 approval never

脚本会自动检测 `codex exec --help`。如果当前 Codex 版本不支持显式 approval 参数，脚本会继续运行，并在日志中提示。

