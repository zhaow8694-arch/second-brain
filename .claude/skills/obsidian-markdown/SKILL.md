---
name: obsidian-markdown
description: Obsidian Flavored Markdown (OFM) — 知识库笔记的标准语法规范
---

# Obsidian Flavored Markdown (OFM) 技能

## 核心语法规则

### 1. Wikilinks（双向链接）
- 用 `[[笔记名]]` 而非相对路径链接
- 带别名：`[[笔记名|显示文本]]`
- 链接到标题：`[[笔记名#标题]]`
- 链接到块：`[[笔记名#^块ID]]`
- 只在真正有概念关联时使用，不滥加

### 2. Callouts（强调框）
```markdown
> [!note] 标题
> 内容

> [!info] 信息
> 一般信息

> [!warning] 警告
> 需要注意的内容

> [!danger] 危险
> 严重警告

> [!tip] 提示
> 小技巧

> [!question] 问题
> 疑问或待确认

> [!contradiction] 冲突
> 表示观点冲突或数据矛盾
```

### 3. YAML Frontmatter
```yaml
---
tags: [tag1, tag2]
date: 2026-06-26
source: URL或来源
aliases: [别名1, 别名2]
---
```

### 4. 任务列表
```markdown
- [ ] 未完成
- [/] 进行中
- [x] 已完成
- [-] 已取消
- [>] 已迁移
```

### 5. 注释
- `%%这是注释，仅在编辑模式可见%%`

### 6. 代码块标题
```markdown
```python:文件名.py
print("hello")
```
```

## 写作规范
- 一笔记一核心想法（原子化）
- 使用标题层级：`#` → `##` → `###`，不超过 4 级
- 段落间空一行
- 代码块指定语言
- 表格使用 GFM 对齐语法
