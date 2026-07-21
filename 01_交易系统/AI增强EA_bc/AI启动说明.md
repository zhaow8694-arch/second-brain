# AI增强风险管理EA - 启动说明

## 🚀 快速启动

### 方法一：一键启动（推荐）
```bash
py start_ai_services.py
```

### 方法二：手动启动
```bash
# 1. 启动AI监控服务
py continuous_ai_monitor.py

# 2. 启动状态监控（可选）
py ai_status_monitor.py
```

## 📋 系统要求

### 必需文件
- ✅ `continuous_ai_monitor.py` - AI监控服务
- ✅ `trading_transformer_model.py` - AI模型定义
- ✅ `trading_data_processor.pkl` - 数据处理器
- ✅ `best_trading_model.pth` - 训练好的模型（可选）

### Python环境
- Python 3.7+
- 必需包：torch, pandas, numpy, joblib, ta

## 🔧 服务状态检查

### 检查AI服务状态
```bash
py test_ai_service.py
```

### 实时监控状态
```bash
py ai_status_monitor.py
```

## 📊 监控文件

### 输入文件
- `market_data.csv` - MT4写入的市场数据

### 输出文件
- `ai_prediction.txt` - AI预测结果
  - 格式：`预测方向,置信度,时间戳`
  - 预测方向：1=买入, 2=卖出, 0=持有

## 🎯 当前AI预测状态

**预测方向**: 卖出 📉  
**置信度**: 0.890 (高 ⭐)  
**更新时间**: 2025-08-08 22:45  

## 💡 MT4 EA配置

1. 在MT4中加载 `AI_Enhanced_Risk_EA.mq4`
2. 确保以下参数设置：
   - `EnableAI = true` - 启用AI预测
   - `DataFileName = "market_data.csv"` - 数据文件名
   - `PredictionFileName = "ai_prediction.txt"` - 预测文件名
   - `MinAIConfidence = 0.6` - 最小AI置信度

## 🔍 故障排除

### AI服务未启动
```bash
# 检查Python进程
tasklist | findstr python

# 检查依赖项
py test_ai_service.py
```

### 预测文件未生成
1. 检查 `market_data.csv` 是否存在
2. 检查Python AI服务是否运行
3. 查看错误日志

### EA无法读取预测
1. 确认 `ai_prediction.txt` 文件格式正确
2. 检查文件权限
3. 确认EA参数设置正确

## 📞 技术支持

如果遇到问题，请检查：
1. Python环境是否正确安装
2. 所有必需文件是否存在
3. 文件权限是否正确
4. MT4 EA参数设置

## 🎉 启动成功标志

✅ Python AI服务正在运行  
✅ AI预测文件已生成  
✅ 预测置信度 > 0.6  
✅ MT4 EA可以正常读取预测  

---

**注意**: 确保在启动MT4 EA之前，Python AI服务已经正常运行并生成预测文件。 