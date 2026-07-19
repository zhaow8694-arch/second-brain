---
tags: [second-brain, obsidian, claude-code, architecture]
date: 2026-06-26
source: 历史记忆 + 配置文件 + Gemini总结Obsidian与ClaudeCode
---

# Claude 升级 Obsidian 的第二大脑 — 全景报告

> 生成于 2026-06-26，基于知识库配置审计 + 历史记忆

---

## 📐 物理规模

| 指标 | 数值 |
|------|------|
| 知识库路径 | `E:\知识库\` |
| 总笔记数 | ~73,600 |
| 总大小 | ~14.4 GB |
| 数据库 | 5 个 SQLite（`07_数据库/`） |

---

## 🎨 界面与外观

- **主题**: Obsidian Nord（暗色系）
- **默认笔记位置**: `99_收件箱/`（新笔记自动落入收件箱，待分拣）
- **附件目录**: `附件/`

---

## 🧩 核心插件（17个开启）

| 插件                              | 用途                    |
| ------------------------------- | --------------------- |
| 🔗 双向链接 + 图谱                    | 知识网状结构的基础             |
| 🎨 Canvas 白板                    | 视觉化知识图谱（Excalidraw）   |
| 📅 Daily Notes + Periodic Notes | 日记/周记/月记自动化           |
| 🧮 Dataview                     | 用 SQL 式查询动态汇总笔记       |
| 📋 Templater                    | 模板引擎，自动注入 frontmatter |
| ⚡ QuickAdd                      | 快速捕获 + 宏命令            |
| 🔄 Obsidian Sync                | 多设备同步                 |
| 🎤 音频录制                         | 语音笔记                  |

---

## 🔌 社区插件（10个）

| 插件 | 功能 | 角色 |
|------|------|------|
| **Obsidian Local REST API** | 在 `localhost:27123` 暴露 HTTP API | 🔴 **核心桥接** — Claude Code 通过它操作笔记 |
| **RealClaudian** | Obsidian 内嵌 Claude Code 侧边栏 | 🟡 沉浸式 AI 交互 |
| **Excalidraw** | 手绘风格白板 | 知识可视化 |
| **Dataview** | 动态表格/列表查询 | 数据库视图 |
| **Templater** | 高级模板 | 统一笔记格式 |
| **Periodic Notes** | 日记/周记自动创建 | 时间线管理 |
| **QuickAdd** | 快捷指令 | 零摩擦捕获 |
| **Terminal** | Obsidian 内嵌终端 | 运行 CLI 命令 |
| **笔记同步助手** (bijitongbu) | 企业微信 → Obsidian 同步 | 外部信息摄入 |

---

## 🤖 Claude Code 集成架构

```
┌─────────────────────────────────────────────┐
│                  Claude Code CLI             │
│  (运行于 E:\知识库\ 根目录, effort=max)       │
│                                              │
│  ┌──────────┐  ┌─────────┐  ┌───────────┐  │
│  │  4 Hooks │  │ 7 Skills│  │  2 MCP    │  │
│  │ 生命周期  │  │  技能包  │  │  连接器   │  │
│  └────┬─────┘  └────┬────┘  └─────┬─────┘  │
│       │             │             │         │
└───────┼─────────────┼─────────────┼─────────┘
        │             │             │
        ▼             ▼             ▼
   PowerShell    .claude/     ┌──────────────┐
   脚本拦截     skills/       │ obsidian-mcp │──▶ localhost:27123
                              │ claude-mem   │──▶ SQLite 记忆库
                              └──────────────┘
        │
        ▼
   Obsidian Vault (E:\知识库\)
   ├── 01_交易系统/    ← EA 源码
   ├── 02_市场分析/    ← MACD 分析
   ├── 03_回测数据/
   ├── 04_币安系统/
   ├── 05_AIMart_AI项目/
   ├── 06_学习收藏/
   ├── 07_数据库/       ← 5 个 SQLite
   ├── 99_收件箱/       ← 默认新笔记落点
   ├── 附件/
   └── Excalidraw/
```

### 🔗 三层缓存架构

| 层级 | 文件 | 大小 | 角色 |
|------|------|------|------|
| 🔥 L1 热缓存 | `hot.md` | ~500词 | 会话启动自动加载，活跃上下文 |
| 📋 L2 总索引 | `📖 知识库索引总表.md` | 全库单行描述 | 全局导航，快速定位 |
| 📝 L3 原子笔记 | 各目录 `.md` 文件 | 按需下钻 3-5 页 | 知识本体 |

### 🪝 生命周期钩子（4个）

| 钩子 | 触发时机 | 功能 |
|------|----------|------|
| **SessionStart** | 会话启动 | 自动加载 hot.md + 检查收件箱 |
| **PreToolUse** | 工具调用前 | 阻断高危操作 + 保护 EA 源码 |
| **PostToolUse** | Write/Edit 后 | 自动检测 frontmatter 完整性 |
| **Stop** | 会话结束 | 提醒更新工作记录和索引 |

### 🛠️ 技能包（7个）

| 技能 | 功能 |
|------|------|
| `obsidian-markdown` | OFM 语法规范（Callouts、Wikilinks、Frontmatter） |
| `defuddle` | 网页内容降噪 → 纯净 Markdown |
| `json-canvas` | Canvas 白板格式操作 |
| `vault-maintenance` | 晨间启动/日终复盘/Vault 体检 |
| `vault-morning` | 晨间启动：读日记 → 迁移任务 → 生成今日日记 |
| `vault-eod` | 日终复盘：复盘交易 → 整理收件箱 → 更新索引 |
| `vault-lint` | 健康体检：孤立笔记/死链/缺失 frontmatter → 自动修复 |

### 📡 MCP 连接（2个）

| MCP | 类型 | 状态 |
|-----|------|------|
| **obsidian-local-rest-api-mcp** | stdio (cmd /c npx) → `localhost:27123` | ⚠️ 已配置，待实测连通 |
| **claude-mem** | worker 模式 | ✅ 运行中，本地文件记忆 |

---

## ⚠️ 当前待完成

| 事项                                   | 状态           |
| ------------------------------------ | ------------ |
| **Obsidian Local REST API MCP 实测连通** | 已配置但未验证      |
| Obsidian Sync 多设备                    | 已开启，待苹果笔记本验证 |
| 收件箱分拣自动化                             | 已配置技能，待日终触发  |
| SniperTrendEA v8.5 第6层成交量确认          | 待开发          |

---

## 🧠 设计哲学

1. **File over app** — 纯 Markdown，无供应商锁定，Claude 原生理解
2. **三层缓存** — hot.md（~500词）→ 索引总表 → 原子笔记，每次只下钻 3-5 页
3. **循环工程（Loop Engineering）** — 人不微操，而是设定规则+Hooks，让 AI 在边界内自迭代
4. **AI 原生 MCP** — Local REST API 暴露的不是 CRUD，而是 `create_or_update_note` 之类的高阶语义工具，消除 LLM 冗余决策树
5. **Obisidian 是持久层，Claude Code 是执行引擎** — 一个存储，一个思考+行动

---

## 📖 参考来源

- [[Gemini总结Obsidian与Claude Code]] — 升级蓝图
- [[CLAUDE.md]] — 第二大脑宪法
- [[hot.md]] — 活跃上下文
- [[MEMORY.md]] — 持久记忆索引
- `.claude/settings.json` — Hooks + MCP 配置
- `.obsidian/` — 插件与外观配置
