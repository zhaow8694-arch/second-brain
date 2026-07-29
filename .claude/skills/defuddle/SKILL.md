---
name: defuddle
description: 网页内容降噪 — 将 HTML 转为纯净 Markdown，提取核心正文
---

# Defuddle 网页降噪技能

## 用途
从网页 HTML 中提取核心正文内容，剥离广告、侧边栏、评论区等噪音。

## 处理流程
1. 获取页面 HTML 源码（通过 WebFetch / curl）
2. 使用 Defuddle 算法提取正文
3. 清理无用元素（广告、导航、脚本等）
4. 将 MathJax/KaTeX 转为 MathML
5. 将 GitHub/Bootstrap 警告框转为 Obsidian Callouts
6. 提取 schema.org 元数据
7. 输出纯净 Markdown

## 输出规范
```markdown
---
tags: [web-clipping, source:域名]
date: 2026-06-26
source: https://原始URL
title: 页面标题
---

# 提取标题

> [!abstract] 摘要
> 内容摘要...

## 正文

[纯净 Markdown 内容]

---

> [!info] 元数据
> - 作者: ...
> - 发布日期: ...
> - 字数: ...
```
