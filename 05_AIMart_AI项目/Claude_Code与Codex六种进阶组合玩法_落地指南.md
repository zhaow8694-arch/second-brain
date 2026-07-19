# Claude Code 与 Codex 六种进阶组合玩法 — 落地指南

> **来源**：抖音博主「阿森编程日记（AI自动化）」  
> **整理日期**：2026-07-07  
> **适用环境**：Windows · `codex.exe` · `claude` · Hooks · Git 已就绪  
> **核心结论**：不是两个 AI「心灵感应」，而是 **Claude Code 当调度层，Codex CLI 当执行层**，靠子代理 / MCP / Hook / Worktree 串成自动化流水线。

---

## 一、核心架构

```
Claude Code（调度层）  →  拆任务、验收、Code Review
        ↓ MCP / 子代理 / Hook
Codex CLI（执行层）    →  批量实现、跑测试、互审、过夜任务
        ↓
文件总线               →  BUILD_PROGRESS.md + HANDOFF.md + git commit
```

**信息传递不靠对话，靠文件与 Git。**

---

## 二、六种玩法可行性总览

| # | 玩法 | 能实现吗 | 难度 | 本机环境状态 |
|---|------|----------|------|--------------|
| 1 | Codex 当子代理 | ✅ 能 | ⭐⭐ | 缺自定义 agent 文件 |
| 2 | MCP 调 Codex | ✅ 能（**最推荐**） | ⭐⭐ | Codex 自带 `mcp-server` |
| 3 | Worktree 双开 | ✅ 能 | ⭐ | Git 已有 |
| 4 | Hook 触发 Codex | ✅ 能 | ⭐⭐⭐ | 已有 PostToolUse（claude-mem） |
| 5 | 双模型互审 | ✅ 能 | ⭐⭐ | 有 `codex review` |
| 6 | Full Auto 过夜 | ✅ 能 | ⭐⭐⭐ | `codex exec` + `approval_policy=never` |

---

## 三、玩法详解

### 1. Codex 当子代理

**原理**：Claude Code 拆任务 → 子代理里用 Bash 调 `codex exec` 干活，全程不用手动切换窗口。

**实现**：在项目建 `.claude/agents/codex-worker.md`：

```markdown
---
name: codex-worker
description: Use when bulk implementation, tests, or BUILD phase execution is needed.
tools: ["Bash", "Read", "Grep"]
---

你是 Codex 调度员。收到任务后：

1. 读 BUILD_PROGRESS.md 确认从哪继续
2. 执行：
   codex exec -C "{项目目录}" "读 BUILD.md，完成当前 phase，更新 BUILD_PROGRESS.md，跑 verify.ps1"
3. 把 Codex 输出摘要回报给主会话
```

**Claude 里用法**：

```text
用 codex-worker 子代理，从 BUILD_PROGRESS 当前 phase 继续实现 API 模块
```

**局限**：不是 Codex 嵌进 Claude 进程，而是子代理帮你调 CLI；够用，但不是原生一体。

---

### 2. MCP 调 Codex（优先试这个）

**原理**：Codex 官方提供 `codex mcp-server`（stdio），Claude Code 像调普通工具一样直接调 Codex，参数、上下文、返回值都走 MCP 协议。

**验证命令**：

```bash
codex mcp-server   # 把 Codex 包装成 MCP 服务
```

**Claude Code 配置**（项目或用户级 `.mcp.json` / `settings.json`）：

```json
{
  "mcpServers": {
    "codex": {
      "type": "stdio",
      "command": "C:\\Users\\Administrator\\AppData\\Local\\Programs\\OpenAI\\Codex\\bin\\codex.exe",
      "args": ["mcp-server"],
      "env": {}
    }
  }
}
```

配置好后**重启 Claude Code**，会出现 Codex 相关 MCP 工具，Claude 可直接调用，不用人工中转。

**局限**：

- 首次要信任 MCP
- Windows 路径要用完整路径
- 上下文大小仍受双方限制

---

### 3. Worktree 双开

**原理**：用 Git Worktree 同时打开两个工作区 — Claude Code 坐镇主分支做规划和验收，Codex 在另一个分支里闷头执行，物理隔离，合并时再对齐 diff。

**操作示例**（以 Korotko 为例）：

```powershell
cd E:\korotko-platfor
git worktree add ../korotko-codex-work -b codex/auto-phase3

# 窗口 A：Claude Code 坐主目录
cd E:\korotko-platfor

# 窗口 B：Codex 在 worktree
codex exec -C E:\korotko-platfor-codex-work "读 BUILD.md Phase 3，实现并 commit"
```

**早上合并**：

```powershell
git diff main..codex/auto-phase3
git merge codex/auto-phase3   # 或让 Claude review 后再 merge
```

**价值**：最稳的物理隔离方案；Korotko 曾有的 D/E 双目录分叉问题，用 Worktree 可正规解决。

---

### 4. Hook 触发 Codex

**原理**：写 PostToolUse 钩子，Claude 改完代码后自动触发 Codex 跑测试、补单测、生成 fixture，验证流程自动闭环。

**配置示意**（与 claude-mem 的 PostToolUse 可并存）：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "powershell -File D:\\Grok\\hooks-helper\\trigger-codex-verify.ps1"
        }]
      }
    ]
  }
}
```

**`trigger-codex-verify.ps1` 核心逻辑**：

```powershell
# 仅当改的是 apps/ 下代码时触发
codex exec -C $env:CLAUDE_PROJECT_DIR `
  "对刚才的改动跑相关测试，失败则修复，输出 TEST_RESULT.json"
```

**注意**：

- 别对所有 Write 都触发，会又慢又贵
- 建议只匹配 `apps/api/**`、`apps/mobile/**` 等
- Hook 和 claude-mem 的 PostToolUse 可以并存

---

### 5. 双模型互审

**原理**：让 Claude 和 Codex 两个不同模型互相审核代码 — Claude 写完丢给 Codex 审，Codex 改完再丢回 Claude 审，利用训练数据与偏好差异，抓单模型看不到的盲点。

**已有命令**：

```bash
codex exec review    # Codex 非交互审查
codex review         # 独立 review 子命令
```

**闭环脚本示意**：

```powershell
# Step 1: Codex 审 Claude 的改动
codex exec review --json > .orchestra/codex-review.json

# Step 2: Claude 读 review 结果决定修 or 过
claude -p "读 .orchestra/codex-review.json，修复 blocking issues"

# Step 3: Claude 审 Codex 改动（可用 /review skill 或 pr-review-toolkit agent）
```

**Claude 里也可直接说**：

```text
用 codex MCP 审查当前 git diff，修完后再用 code-reviewer 子代理复审
```

---

### 6. Full Auto 过夜

**原理**：睡前把需求拆成可验证的子任务，交给 Codex 以 Full Auto 模式串行执行，每个子任务自动提交；第二天早上用 Claude Code 看所有 diff，跑 CI 决定保留或回滚。

**本机条件**：`~/.codex/config.toml` 中已有 `approval_policy = "never"`，适合无人值守。

**睡前准备 `OVERNIGHT_TASKS.md`**：

```markdown
| ID | 任务 | 验收命令 | 状态 |
|----|------|----------|------|
| T1 | API 用户模块 | pnpm test api | pending |
| T2 | Admin 设置页 | pnpm build admin | pending |
```

**过夜脚本 `scripts/overnight-codex.ps1`**：

```powershell
foreach ($task in $tasks) {
  codex exec -C $ProjectDir --json `
    "完成 $($task.id): $($task.desc)。验收: $($task.verify)。通过后 git commit -m 'auto: $($task.id)'"
}
```

**早上 Claude**：

```text
读昨晚 git log 和 diff，跑 verify.ps1，列出要保留/回滚的 commit
```

> 视频里的「Full Auto」≈ `codex exec` + 任务清单 + 自动 commit + 早上人工/Claude 验收，**不是真·无人监督上线**。

---

## 四、推荐落地顺序（从易到难）

| 顺序 | 玩法 | 说明 |
|------|------|------|
| 第 1 步 | MCP 调 Codex | 约 10 分钟，收益最大 |
| 第 2 步 | Worktree 双开 | 避免分支冲突 |
| 第 3 步 | Codex 子代理 | 日常流水线 |
| 第 4 步 | 双模型互审 | 提升代码质量 |
| 第 5 步 | Hook 自动验证 | 需调频率，防烧钱 |
| 第 6 步 | 过夜 Full Auto | 流程成熟后再上 |

---

## 五、与 Grok / Claude / Codex 三件套搭配

```
         ┌─────────────┐
         │    Grok     │  总指挥：写 BUILD / TASK_QUEUE / 验收
         └──────┬──────┘
                │ 文件总线
    ┌───────────┼───────────┐
    ▼                       ▼
┌─────────┐           ┌─────────┐
│ Claude  │ ◄─ MCP ─► │  Codex  │
│ 拆任务   │           │ 执行/审查 │
│ 验收diff │           │ 过夜批量 │
└─────────┘           └─────────┘
```

| 工具 | 角色 |
|------|------|
| **Grok** | 写规格、拆任务、真机联调、更新 `D:\Grok\` 记忆 |
| **Claude Code** | MCP 调 Codex、子代理编排、早上审 diff |
| **Codex** | `exec` 批量实现、`review` 互审、过夜跑任务 |

**传递媒介**：`BUILD_PROGRESS.md` + `HANDOFF.md` + `git commit`（不是脑电波）。

---

## 六、心智模型：把 AI 想成一家公司

把多个 AI 和自动化脚本想成一家软件公司的岗位分工，最容易理解闭环逻辑：

| 角色                    | 岗位            | 职责（以 Korotko 为例）        |
| --------------------- | ------------- | ----------------------- |
| **你**                 | 产品负责人         | 提需求，如「福利页要接真 API」       |
| **Grok**              | 项目经理 + QA     | 写工单、/、记进度、真机联调          |
| **Claude Code**       | 技术主管          | 拆任务、调 Codex、Code Review |
| **Codex**             | 外包工程队         | 按 BUILD 大批量实现、跑测试       |
| **verify.ps1**        | CI 机器人        | 只说 PASS / FAIL          |
| **BUILD.md**          | 需求文档          | 不变的事实标准                 |
| **HANDOFF.md**        | 当期 Sprint 任务卡 | 当前这一迭代的具体活              |
| **BUILD_PROGRESS.md** | 进度指针          | 做到哪了、下一步干啥              |
| **git**               | 代码仓库          | 所有改动的物理记录               |

**三条铁律**：

1. **BUILD.md 不轻易改** — 改规格需产品负责人（你）确认  
2. **HANDOFF.md 覆盖写** — 只保留当前活跃任务  
3. **verify.ps1 是裁判** — 不说「我觉得做完了」，只看 0 FAIL  

**闭环本质**：

> 闭环 ≠ 三个 AI 互相聊天  
> 闭环 = 同一项目、同一套文件、同一条 git 历史、同一个机械裁判

---

## 七、本机环境的两个现实差异

1. **Claude 走 DeepSeek 代理**，不是视频里默认的 Anthropic 模型 — 编排思路一样，但规划和审查质量可能不同。
2. **Grok 进不了 Claude↔Codex 原生链路** — 适合当「写任务包 + 早上验收」的第三指挥，不适合硬塞进 MCP 里。

---

## 八、结论

**6 种都能实现**；本机 Codex、Claude、Git、Hook 均已就绪。

最快见效组合：**第 2 种 MCP 调 Codex** + **第 3 种 Worktree 双开**，几乎可复刻视频效果。

---

## 九、待落地配置清单（可选）

在指定项目（如 `E:\korotko-platfor`）可生成开箱配置：

| # | 文件 | 作用 |
|---|------|------|
| 1 | `.mcp.json` | 挂 Codex MCP |
| 2 | `.claude/agents/codex-worker.md` | Codex 子代理 |
| 3 | `scripts/overnight-codex.ps1` | 过夜脚本 |
| 4 | `D:\Grok\hooks-helper\trigger-codex-verify.ps1` | Hook 自动验证（可选） |

---

## 十、相关文档

| 文档 | 路径 |
|------|------|
| Korotko BUILD 规格 | `E:\korotko-platfor\BUILD.md` |
| AIMart Codex 总控指令 | `Downloads\AIMart_Codex_使用说明与总控指令.md` |
| Grok 记忆规则 | `D:\Grok\rules\MEMORY-RULES.md` |
| Claude Code 子代理文档 | `~/.claude/plugins/.../plugin-dev/agents/agent-creator.md` |

---

*整理：Grok · 基于 2026-07-07 会话内容*