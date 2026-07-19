---
tags: [Loop Engineering, Agnes AI, 免费API, 智能体, 自动化]
date: 2026-06-20
source: "资本V现场/抖音"
category: "AI综合/AI编程"
---
# Loop Engineering循环工程 + Agnes免费API搭建AI自动化

## 核心要点
- Loop Engineering：设计一个循环让AI Agent自己定提示词、发现任务、处理任务、记录结果，再自己写下一条提示词继续跑
- 实践案例：AI每日自动扫描GitHub Trending，自动clone项目、打分、安装运行、微信推送结果
- 使用Agnes AI 2.0 Flash免费模型（全模态免费，文本模型调用量已超1.9万亿token）

## 关键洞察
- 架构设计核心：代码做稳定工具（去重、抓取、通知），Markdown保存状态，AI做判断和执行
- 子Agent处理单个项目的详细分析（clone、安装、测试），主Agent保持上下文清爽
- 免费模型最适合跑长期重复、人工做又很反感的自动化任务
- 类似思路可用于论文雷达、竞品监控等场景
