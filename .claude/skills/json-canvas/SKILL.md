---
name: json-canvas
description: JSON Canvas (.canvas) — Obsidian 数字白板的底层格式
---

# JSON Canvas 技能

## 格式说明
.canvas 文件是 JSON 格式的数字白板，由 nodes 和 edges 组成。

## 基本结构
```json
{
  "nodes": [
    {
      "id": "uuid",
      "type": "text|file|link|group",
      "text": "节点内容",
      "x": 100,
      "y": 200,
      "width": 300,
      "height": 100,
      "color": "颜色名称"
    }
  ],
  "edges": [
    {
      "id": "uuid",
      "fromNode": "源节点ID",
      "fromSide": "left|right|top|bottom",
      "toNode": "目标节点ID",
      "toSide": "left|right|top|bottom",
      "label": "连线标签（可选）"
    }
  ]
}
```

## 节点类型
- **text**: 纯文本卡片
- **file**: 指向 vault 内文件的链接（用 path 属性）
- **link**: 外部 URL
- **group**: 分组容器（用 label 属性）

## 颜色选项
red, orange, yellow, green, cyan, blue, purple, pink

## 使用场景
- 思维导图式研究笔记组织
- 项目架构可视化
- 概念关系图谱
- 交易策略流程图
