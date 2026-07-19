---
tags: [task, {{project}}]
date: <% tp.date.now("YYYY-MM-DD") >
status: todo
priority: medium
project: {{project}}
---

# {{title}}

## 任务信息
- **项目**: {{project}}
- **优先级**: 🟢 高 / 🟡 中 / 🔴 低
- **截止**: {{deadline}}
- **状态**: todo / doing / review / done

## 描述
{{description}}

## 检查清单
- [ ] 

## 关联
- 所属项目: [[]]
- 相关笔记: [[]]

---

## Dataview 汇总

在项目笔记中添加以下查询可自动汇总任务：

```dataview
TASK
FROM "01_交易系统" or "05_AIMart_AI项目"
WHERE !completed
SORT priority ASC
```
