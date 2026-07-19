# Project Spec

```json
{
  "projectName": "Todo API MVP",
  "background": "用于测试 AIMart 编排器自动生成执行包功能",
  "rawDiscussion": "创建一个简单的 Todo API，实现任务的增删改查。",
  "mvpScope": [
    "只做后端 API",
    "不做前端界面"
  ],
  "forbiddenItems": [
    "只做后端 API",
    "不做前端界面"
  ],
  "techStackPreferences": [
    "Next.js",
    "TypeScript",
    "Zod",
    "Vitest",
    "pnpm"
  ],
  "targetAdapterType": "codex",
  "executionMode": "codex_only",
  "testingRequirements": [
    "核心模块必须有单元测试"
  ],
  "deliveryRequirements": [
    "ZIP delivery"
  ],
  "securityBoundaries": [
    "Do not read .env",
    "SSH keys",
    "or production credentials"
  ],
  "explicitRequirements": [
    "只做后端 API",
    "不做前端界面",
    "核心模块必须有单元测试",
    "ZIP delivery"
  ],
  "inferredAssumptions": [
    "Use Codex as the v0.1 target adapter.",
    "Use codex_only execution mode for v0.1."
  ],
  "openQuestions": [],
  "createdAt": "2026-06-10T05:36:58.325Z"
}
```