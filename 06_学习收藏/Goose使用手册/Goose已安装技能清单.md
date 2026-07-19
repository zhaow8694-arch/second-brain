# 🦆 Goose 已安装技能清单 — v3.1
> 生成日期：2026-07-06 | **技能总数：50个**
> 安装来源：DeerFlow (22) + Agent-Loop-Skills (7) + Claude Code (12) + Codex (8) + 自建 (1)
> 技能位置：`~/.agents/skills/`

---

## 一、技能速查表（按类别）

### 🎨 内容创作（10个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `frontend-design` | 92 | DeerFlow | 创建前端UI/页面/组件 |
| `image-generation` | 208 | DeerFlow | AI图片生成 |
| `video-generation` | 151 | DeerFlow | AI视频生成 |
| `music-generation` | 76 | DeerFlow | 音乐/歌曲生成 |
| `podcast-generation` | 203 | DeerFlow | 文本→播客音频 |
| `ppt-generation` | 463 | DeerFlow | 生成PPT演示文稿 |
| `newsletter-generation` | 343 | DeerFlow | 撰写新闻通讯/简报 |
| `web-design-guidelines` | 39 | DeerFlow | UI代码可访问性/UX审查 |
| `algorithmic-art` | ~95 | Claude Code | p5.js 算法艺术生成（粒子/流场/数学美）|
| `canvas-design` | ~120 | Claude Code | 设计哲学→画布视觉输出（PDF/PNG）|

### 📊 数据分析（4个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `data-analysis` | 248 | DeerFlow | Excel/CSV数据分析（多sheet、SQL查询、统计）|
| `tabular-cleanup` | 222 | Loop | 自动清洗脏数据（推断约束、修正问题）|
| `chart-visualization` | 72 | DeerFlow | 数据可视化（26种图表）|
| `consulting-analysis` | 631 | DeerFlow | 专业咨询报告生成（市场/品牌/金融分析）|

### 🔬 调研与研究（5个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `deep-research` | 198 | DeerFlow | 多角度深度调研 |
| `github-deep-research` | 166 | DeerFlow | GitHub仓库深度分析 |
| `systematic-literature-review` | 235 | DeerFlow | 学术文献综述/系统评价 |
| `academic-paper-review` | 289 | DeerFlow | 论文审阅/评论 |
| `literature-search` | 83 | Loop | 学术论文搜索（arXiv/Semantic Scholar）|

### 💻 开发与工程（6个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `code-documentation` | 415 | DeerFlow | 代码文档/README/API文档生成 |
| `optimize-loop` | 140 | Loop | 代码重构优化（保持行为不变降低复杂度）|
| `plan-loop` | 158 | Loop | 模糊需求→细化成可执行任务计划 |
| `swe-loop` | 183 | Loop | 自动实现功能（规划→编码→测试→提PR）|
| `mcp-builder` | 236 | Claude Code | MCP服务器构建指南（FastMCP/MCP SDK）|
| `webapp-testing` | 95 | Claude Code | Playwright Web测试工具包 |

### 🔒 安全审计（3个）— Codex 市场

| 技能名 | 行数 | 用途 |
|:-------|:----:|:------|
| `security-best-practices` | 86 | 语言/框架安全最佳实践审查（Python/JS/Go）|
| `security-threat-model` | 81 | 仓库级威胁建模：资产/攻击者/攻击路径/缓解措施 |
| `security-ownership-map` | 206 | Git仓库安全所有权拓扑（人员↔文件，bus factor分析）|

### 🚀 部署配置（7个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `vercel-deploy-claimable` | 112 | DeerFlow | 一键部署到Vercel |
| `netlify-deploy` | 247 | Codex | Netlify CLI 部署 |
| `cloudflare-deploy` | 224 | Codex | Cloudflare Workers/Pages 部署 |
| `render-deploy` | 479 | Codex | Render 部署（render.yaml Blueprint）|
| `bootstrap` | 94 | DeerFlow | 生成个性化SOUL.md |
| `skill-creator` | 534 | DeerFlow | 创建/修改/评估技能 |
| `claude-to-deerflow` | 217 | DeerFlow | 与DeerFlow Agent平台交互 |

### 🎤 语音合成（1个）🆕 免费替代

| 技能名 | 行数 | 来源 | 用途 | 说明 |
|:-------|:----:|:----|:------|:------|
| `edge-tts-skill` 🆕 | 117 | 自建 | **免费TTS语音合成**，中文13种+英文400+语音 | ✅ **零费用**，无需API Key |

### 📄 文档处理（4个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `pdf-skill` | 314 | Claude Code | PDF读写/OCR/合并/拆分/水印/加密/解密 |
| `docx-skill` | 590 | Claude Code | Word文档创建/编辑 |
| `pptx-skill` | 232 | Claude Code | PowerPoint幻灯片创建/编辑/提取 |
| `xlsx-skill` | 291 | Claude Code | Excel读写/公式/格式/图表 |

### ✍️ 写作与沟通（4个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `doc-coauthoring` | ~120 | Claude Code | 结构化文档共创 |
| `internal-comms` | ~60 | Claude Code | 企业内部通讯 |
| `brand-guidelines` | ~50 | Claude Code | Anthropic 品牌配色/字体风格 |
| `theme-factory` | ~80 | Claude Code | 10种预制主题美化文档/PPT/HTML |

### ✅ 质量/安全/测试（3个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `claim-verify` | 143 | Loop | 逐条验证数据报告中的结论 |
| `red-team` | 135 | Loop | 对抗性测试系统/提示词漏洞 |
| `find-skills` | 138 | DeerFlow | 搜索/安装新技能 |

### 🚀 Git/工作流（2个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `yeet` | 132 | Codex | 一键 stage→commit→push→开 PR（需 `gh auth login`）|
| `define-goal` | 99 | Codex | 帮助定义可测量目标/验收标准 |

### 🎲 趣味工具（2个）

| 技能名 | 行数 | 来源 | 用途 |
|:-------|:----:|:----|:------|
| `surprise-me` | 53 | DeerFlow | 随机组合技能创造惊喜体验 |
| `slack-gif-creator` | ~80 | Claude Code | 创建 Slack 优化动画 GIF |

---

## 二、技能来源分布

| 来源 | 数量 | 说明 |
|:----|:----:|:------|
| 🦌 DeerFlow | 22 | 核心内容创作+数据分析+调研 |
| 🔄 Agent-Loop-Skills | 7 | 验证门控迭代循环（优化/计划/测试）|
| 🔷 Claude Code | 12 | 文档处理+创意+写作+主题 |
| 🔴 Codex (OpenAI) | 8 | 安全+部署+Git+目标管理 |
| 🟢 **自建** 🆕 | **1** | **edge-tts-skill（免费TTS替代）** |

---

## 三、技能版本变更历史

| 版本 | 日期 | 技能数 | 变更 |
|:----|:----:|:------:|:------|
| v1.0 | 07-05 | 29 | 初始清单 |
| v2.0 | 07-06 | 35 | 补全Claude Code 6个技能 |
| v2.1 | 07-06 | 41 | 新增Claude Code 6个（创意/写作/品牌）|
| v3.0 | 07-06 | 51 | +10个Codex技能（安全3+部署3+语音2+Git2）|
| **v3.1** | **07-06** | **50** | **-2（speech/transcribe需付费）+1（edge-tts-skill免费替代）** |

---

## 四、已测试技能（17个）

| 技能                        | 测试结果 | 备注                          |
| :------------------------ | :--: | :-------------------------- |
| `pdf-skill`               |  ✅   | 8页真实PDF完整读写                 |
| `docx-skill`              |  ✅   | Word双向验证                    |
| `pptx-skill`              |  ✅   | 4页PPT深色主题                   |
| `xlsx-skill`              |  ✅   | 6月销售表+公式验证                  |
| `mcp-builder`             |  ✅   | MCP天气服务器完整创建                |
| `webapp-testing`          |  ✅   | Playwright截图+交互             |
| `deep-research`           |  ✅   | 中亚短剧报告                      |
| `security-best-practices` |  ✅   | 检出10个安全问题                   |
| `security-threat-model`   |  ✅   | Flask app 威胁建模7个威胁          |
| `security-ownership-map`  |  ✅   | networkx就绪                  |
| `netlify-deploy`          |  ✅   | npx netlify v26.1.0         |
| `cloudflare-deploy`       |  ✅   | 完整产品索引                      |
| `render-deploy`           |  ✅   | Blueprint双流程                |
| `edge-tts-skill` ✅ 新      |  ✅   | 16KB MP3生成成功                |
| `yeet`                    |  ✅   | gh v2.46.0已登录zhaow8694-arch |
| `define-goal`             |  ✅   | 纯指令零依赖                      |
| `music-generation`        |  ✅   | MiniMax API                 |

---

## 五、API Key 配置

| Key | 状态 | 用途 |
|:----|:----:|:------|
| `OPENAI_API_KEY` | ✅ 已配置 | edge-tts（不需要）、image-generation（备用）|
| `ANTHROPIC_API_KEY` | ✅ 已配置 | 所有DeerFlow技能 |
| `gh auth login` | ✅ 已登录 | `zhaow8694-arch`，yeet可用 |

---

*下次更新：安装/删除新技能后记得更新本文件*
