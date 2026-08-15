---
tags: [交易系统, EA]
date: 2026-06-20
---

# AI模型优化说明

## 🎯 问题分析

### 原始问题
1. **极度自信**: AI模型输出95%+的置信度，预测过于极端
2. **预测偏差**: 总是预测"看跌"，很少预测"震荡"或"看涨"
3. **模型过拟合**: 复杂模型在有限数据上过度拟合

## 🔧 优化修改

### 1. 标签创建优化
**文件**: `trading_transformer_model.py` - `create_labels` 函数

**修改前**:
```python
# 使用33%和67%分位数作为动态阈值
lower_threshold = returns.quantile(0.33)
upper_threshold = returns.quantile(0.67)
# 结果: 看跌33%, 震荡34%, 看涨33%
```

**修改后**:
```python
# 使用40%和60%分位数，增加震荡类别比例
lower_threshold = returns.quantile(0.40)
upper_threshold = returns.quantile(0.60)
# 结果: 看跌40%, 震荡20%, 看涨40%
```

**效果**: 增加震荡类别的比例，减少极端预测

### 2. 类别权重平衡
**文件**: `trading_transformer_model.py` - `TradingModelTrainer.__init__`

**修改前**:
```python
self.criterion = nn.CrossEntropyLoss(weight=torch.tensor([3.0, 1.0, 3.0]).to(device))
# 看跌和看涨权重为3.0，震荡权重为1.0
```

**修改后**:
```python
self.criterion = nn.CrossEntropyLoss(weight=torch.tensor([1.2, 1.0, 1.2]).to(device))
# 平衡的权重，避免极端预测
```

**效果**: 减少对看跌和看涨的过度惩罚，让模型更愿意预测震荡

### 3. 模型架构简化
**文件**: `trading_transformer_model.py` - `TradingTransformer.__init__`

**修改前**:
```python
def __init__(self, input_dim, d_model=128, nhead=8, num_layers=6, 
             num_classes=3, dropout=0.1, max_len=100):
```

**修改后**:
```python
def __init__(self, input_dim, d_model=64, nhead=4, num_layers=3, 
             num_classes=3, dropout=0.2, max_len=100):
```

**效果**: 
- 减少模型复杂度，防止过拟合
- 增加dropout，提高泛化能力

### 4. 学习率优化
**文件**: `trading_transformer_model.py` - `TradingModelTrainer.__init__`

**修改前**:
```python
self.optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-5)
```

**修改后**:
```python
self.optimizer = optim.AdamW(model.parameters(), lr=5e-5, weight_decay=1e-4)
```

**效果**: 降低学习率，更稳定的训练过程

### 5. 温度缩放
**文件**: `trading_transformer_model.py` - `TradingModelTrainer.__init__`

**新增**:
```python
# 温度缩放参数 - 用于校准置信度
self.temperature = nn.Parameter(torch.ones(1) * 1.5)
```

**效果**: 校准模型置信度，减少过度自信

### 6. 数据文件修正
**文件**: `trading_transformer_model.py` - `main` 函数

**修改前**:
```python
df = load_data('XAUUSD15.csv')  # 错误的文件名
```

**修改后**:
```python
df = load_data('xinXAUUSD15.csv')  # 正确的文件名
```

## 📊 预期效果

### 训练数据分布
- **看跌**: 40% (之前33%)
- **震荡**: 20% (之前34%) 
- **看涨**: 40% (之前33%)

### 模型行为
1. **更平衡的预测**: 减少极端预测，增加震荡预测
2. **合理的置信度**: 避免95%+的过度自信
3. **更好的泛化**: 简化模型减少过拟合
4. **稳定训练**: 降低学习率提高训练稳定性

## 🚀 重新训练步骤

1. **停止当前AI系统**:
   ```bash
   # 结束所有Python进程
   taskkill /f /im python.exe
   ```

2. **重新训练模型**:
   ```bash
   py trading_transformer_model.py
   ```

3. **启动优化后的AI系统**:
   ```bash
   py continuous_ai_monitor.py mt4
   ```

## 📈 监控指标

训练过程中关注以下指标：
- **标签分布**: 确保三类标签相对平衡
- **分类准确率**: 看跌、震荡、看涨的准确率
- **置信度分布**: 避免过度自信的预测
- **验证损失**: 确保模型没有过拟合

## ⚠️ 注意事项

1. **数据质量**: 确保使用2019年后的高质量数据
2. **训练时间**: 简化模型后训练时间会减少
3. **模型保存**: 新模型会覆盖 `best_trading_model.pth`
4. **兼容性**: 需要同时更新 `continuous_ai_monitor.py` 中的模型参数

## 🔄 后续优化

如果问题仍然存在，可以考虑：
1. **数据增强**: 增加训练数据的多样性
2. **集成学习**: 使用多个模型投票
3. **置信度阈值**: 设置最低置信度阈值
4. **动态权重**: 根据预测历史调整权重 