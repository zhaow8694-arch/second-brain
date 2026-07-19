---
date: <% tp.date.now("YYYY-MM") %>
tags:
  - monthly
  - review
---

# 🗓️ 月报 <% tp.date.now("YYYY-MM") %>

## 📈 月度交易统计
| 指标 | 数值 |
|------|------|
| 总交易次数 | |
| 胜率 | |
| 月盈亏 | |
| 最大回撤 | |
| 夏普比率 | |

## 🏗️ 项目里程碑
- 

## 🧠 知识增长
- 新学到的：
- 改变的看法：
- 需要深挖的：

## 📚 本月阅读/学习
```dataview
TABLE date, source, tags
FROM "06_学习收藏"
WHERE date >= date(<% tp.date.now("YYYY-MM-01") %>)
SORT date DESC
```

## ✅ 下月计划
- [ ] 

## 🔗 本月周报
```dataview
LIST
FROM "Periodic/周报"
WHERE file.name >= "<% tp.date.now("YYYY") %>" AND file.name <= "<% tp.date.now("YYYY") %>"
SORT file.name ASC
```
