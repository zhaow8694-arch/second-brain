---
date: <% tp.date.now("YYYY-[W]ww") %>
tags:
  - weekly
  - review
---

# 📊 周报 <% tp.date.now("YYYY [Week] ww") %>

## 🎯 本周重点回顾
- 

## 📈 交易统计
| 指标 | 数值 |
|------|------|
| 总交易次数 | |
| 胜率 | |
| 总盈亏 | |
| 最大回撤 | |
| 最佳品种 | |

## 📂 项目进展
### 交易策略
- 

### AI 项目
- 

## 💡 本周关键洞察
- 

## ✅ 下周计划
- [ ] 

## 🔗 本周日记
```dataview
LIST 
FROM "Daily"
WHERE date >= date(<% tp.date.now("YYYY-MM-DD", -7) %>) AND date <= date(<% tp.date.now("YYYY-MM-DD") %>)
SORT file.name ASC
```
