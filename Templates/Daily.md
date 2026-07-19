---
date: <% tp.date.now("YYYY-MM-DD") %>
tags:
  - daily
  - journal
mood: 
energy: 
focus: 
---

# 📅 <% tp.date.now("YYYY-MM-DD (dddd)") %>

[[<% tp.date.now("YYYY-MM-DD", -1) %>|← 昨天]] | [[<% tp.date.now("YYYY-MM-DD", 1) %>|明天 →]]

---

## 📥 Captures（原始捕获）

- 

---

## ✅ Tasks

- [ ] 

```tasks
not done
created after <% tp.date.now("YYYY-MM-DD", -7) %>
sort by priority
```

---

## 📊 交易记录

| 时间 | 品种 | 方向 | 手数 | 盈亏 | 备注 |
|------|------|------|------|------|------|
|      |      |      |      |      |      |

### 今日交易复盘
- 胜率： / 
- 最大盈利：
- 最大亏损：
- 教训：

## 🔄 每日复盘

### 今天什么事有推进？
- 

### 今天什么事卡住了？
- 

### 明天需要带走什么？
- 

---

## 💡 想法 & 灵感
- 

## 📝 今日创建的笔记
```dataview
LIST 
FROM "" 
WHERE file.cday = date("<% tp.date.now("YYYY-MM-DD") %>")
SORT file.ctime DESC
```
