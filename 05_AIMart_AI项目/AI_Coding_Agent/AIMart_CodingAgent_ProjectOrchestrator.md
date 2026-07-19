# AIMart AI Coding Agent 项目编排器总结

本文件总结了我们讨论的“AI Coding Agent 项目编排器”工具设计、功能、流程和多 Agent 支持。

## 核心目标
- 将讨论和需求自动生成边界文件、执行文件、自查文件、文档。
- 自动生成 Codex、Claude Code、Trae 执行包。
- 全程无人干预，实现自动开发、测试、自审、打包最终交付。

## 核心模块
1. 讨论管理模块：支持新增/修改/删除/快照讨论内容。
2. 讨论解析模块：将讨论转成结构化 ProjectSpec。
3. 文件生成模块：生成边界、执行、自查、文档、总控指令文件。
4. 自检模块：检测文件完整性和一致性。
5. 打包模块：生成 ZIP 或工作目录文件，可直接给 coding agent 使用。
6. Agent CLI 指令模块：生成 Codex/Claude/Trae 指令，直接在 CLI 执行。

## 支持多 Agent
- Codex：后端开发、规则引擎、API、测试、文档、打包交付。
- Claude Code：工程化工作流、多阶段无人干预、hooks、subagents。
- Trae：前端、管理后台、IDE 可视化开发、Builder 模式、轨迹记录。

## 输入
- Markdown/文本讨论内容
- MVP 范围
- 禁止项
- API 需求
- 数据模型
- 测试要求
- 交付标准
- 后续修改内容

## 输出
- 边界文件、约束文件、能力/数据模型文件
- 执行文件（AGENTS.md 等）
- 自查文件（SELF_REVIEW.md、FINAL_DELIVERY_CHECK.md）
- 文档（README.md、API_USAGE.md、IMPLEMENTATION_REPORT.md）
- Phase 总控指令 Markdown
- 多 agent 执行包
- 最终 ZIP 打包包

## 核心流程
1. 输入讨论
2. 生成 ProjectSpec
3. 生成各 agent 执行包
4. 选择 agent 执行（Codex / Claude / Trae）
5. 自动编码、测试、自审、修复
6. 打包最终交付
7. 输出 FINAL_DELIVERY_CHECK、RELEASE_NOTES、PHASE_DELIVERY_CHECK
8. 如果讨论修改，重新生成受影响文件

## 优点
- 全程无人干预
- 自动化生成所有项目文件
- 多 Agent 支持
- 可迭代更新讨论
- 可生成最终可交付项目

## 缺点与风险
- 依赖讨论质量
- 假设填充可能偏离真实需求
- 文件量大，维护成本高
- 不同 Agent 输出风格可能不一致
- 自动生成前端/管理后台 UI 可能不够精细
- 测试覆盖可能不足
- 安全边界仍需人工复核
- 多 Agent 支持增加适配成本

## 建议开发路线
1. v0.1：只支持 Codex 后端 MVP
2. v0.2：支持讨论动态修改
3. v0.3：支持 Claude Code 多阶段工程化
4. v0.4：支持 Trae 前端/管理后台 IDE 开发
5. v0.5：统一多 Agent 输出，增加最终验收和比对

