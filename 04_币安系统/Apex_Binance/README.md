# Apex Binance 交易系统 v2.0

## 🚀 概述

这是一个完全重构的加密货币量化交易系统，专门用于币安(Binance)交易所的期货合约交易。系统采用模块化设计，具有完善的风险管理和Telegram通知功能。

## ✨ 主要改进

### 安全性提升
- ✅ 移除硬编码的API密钥
- ✅ 使用环境变量管理敏感信息
- ✅ 添加`.gitignore`保护敏感文件
- ✅ 创建`.env.example`模板文件
- ✅ 替换钉钉为Telegram通知

### 代码质量
- ✅ 模块化架构设计
- ✅ 清晰的职责分离
- ✅ 类型注解支持
- ✅ 完善的错误处理
- ✅ 详细的日志记录

### 功能增强
- ✅ 完整的风险管理模块
- ✅ 多时间框架策略引擎
- ✅ 智能仓位管理
- ✅ 移动止损止盈
- ✅ 自动状态恢复
- ✅ 定期报告生成

## 📁 项目结构

```
Apex_Binance/
├── .env                    # 环境变量配置文件
├── .env.example           # 环境变量模板
├── .gitignore            # Git忽略文件
├── requirements.txt      # Python依赖
├── config.py            # 配置管理
├── app.py              # 主应用程序
├── core/               # 核心模块
│   ├── __init__.py
│   ├── exchange_client.py  # 交易所客户端
│   ├── strategy_engine.py  # 策略引擎
│   ├── risk_manager.py     # 风险管理
│   ├── trade_executor.py   # 交易执行
│   ├── notify.py          # Telegram通知
│   └── state_store.py     # 状态管理
└── README.md           # 本文档
```

## 🚦 快速开始

### 1. 环境设置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的配置
# BINANCE_API_KEY=your_api_key
# BINANCE_SECRET=your_secret
# TELEGRAM_BOT_TOKEN=your_bot_token
# TELEGRAM_CHAT_ID=your_chat_id
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动系统
```bash
python app.py
```

## 🔧 配置说明

### 必需配置
- `BINANCE_API_KEY`: 币安API密钥
- `BINANCE_SECRET`: 币安API密钥
- `TELEGRAM_BOT_TOKEN`: Telegram机器人令牌
- `TELEGRAM_CHAT_ID`: Telegram聊天ID

### 交易配置
- `RISK_PCT`: 单笔风险比例 (默认: 0.8%)
- `DAILY_MAX_LOSS`: 日最大亏损比例 (默认: 10%)
- `MAX_POSITIONS`: 最大持仓数量 (默认: 6)
- `HIGH_LEV_COINS`: 高杠杆币种 (默认: BTC,ETH,SOL,DOGE)

### 策略参数
- `ATR_SL_LONG`: 多头止损ATR倍数 (默认: 3.5)
- `ATR_SL_SHORT`: 空头止损ATR倍数 (默认: 2.5)
- `HWM_ACTIVATE_LONG`: 多头移动止损激活阈值 (默认: 2.5%)
- `HWM_ACTIVATE_SHORT`: 空头移动止损激活阈值 (默认: 4.0%)

## 📊 系统特性

### 风险管理
- 日亏损熔断机制
- 仓位数量限制
- 单笔风险控制
- 冷却期机制
- 动态止损止盈

### 交易策略
- 多时间框架分析 (15m, 1h, 4h)
- 趋势跟踪策略
- 动量确认机制
- 成交量验证
- ATR波动率调整

### 监控通知
- Telegram实时通知
- 定期状态报告
- 错误警报
- 交易确认
- 系统状态

## 🛠️ 模块说明

### 1. 配置管理 (`config.py`)
- 统一管理所有配置参数
- 环境变量验证
- 类型安全访问

### 2. 交易所客户端 (`core/exchange_client.py`)
- 封装CCXT接口
- 统一的交易接口
- 错误处理和重试

### 3. 策略引擎 (`core/strategy_engine.py`)
- 多时间框架分析
- 技术指标计算
- 交易信号生成
- 数据缓存机制

### 4. 风险管理 (`core/risk_manager.py`)
- 仓位大小计算
- 止损止盈管理
- 风险限制检查
- 资金管理

### 5. 交易执行 (`core/trade_executor.py`)
- 订单执行管理
- 持仓状态跟踪
- 部分平仓功能
- 交易历史记录

### 6. 通知系统 (`core/notify.py`)
- Telegram消息发送
- 格式化通知内容
- 异步消息处理
- 连接测试

### 7. 状态管理 (`core/state_store.py`)
- 自动状态保存
- 状态恢复功能
- 备份机制
- 版本兼容性

## 📈 交易流程

1. **初始化**: 加载配置，连接交易所，恢复状态
2. **风险检查**: 检查日亏损限制，仓位限制
3. **持仓管理**: 同步实际持仓，检查止损止盈
4. **信号生成**: 扫描市场，生成交易信号
5. **交易执行**: 执行符合条件的交易
6. **状态更新**: 更新持仓状态，保存系统状态
7. **报告生成**: 定期发送状态报告

## 🔍 测试系统

运行完整的系统测试：
```bash
python -m pytest
```

测试内容包括：
- 配置验证
- Telegram连接
- 交易所连接
- 状态管理
- 策略引擎
- 风险管理

## ⚠️ 注意事项

1. **模拟交易**: 默认启用模拟交易模式
2. **风险控制**: 确保理解所有风险参数
3. **资金安全**: 使用独立的交易账户
4. **监控系统**: 定期检查系统状态
5. **备份重要**: 定期备份状态文件

## 🆘 故障排除

### 常见问题

1. **API连接失败**
   - 检查API密钥权限
   - 验证网络连接
   - 检查防火墙设置

2. **Telegram通知失败**
   - 验证机器人令牌
   - 检查Chat ID
   - 确认机器人已添加到群组

3. **状态恢复失败**
   - 检查状态文件权限
   - 验证JSON格式
   - 检查版本兼容性

### 日志文件
- 主日志: `trading_system.log`
- 交易日志: 控制台输出
- 错误日志: Telegram通知

## 📄 许可证

本项目仅供学习和研究使用。使用本系统进行实盘交易需要自行承担风险。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📞 支持

如有问题，请通过以下方式联系：
1. 查看日志文件
2. 检查配置设置
3. 运行系统测试
4. 提交GitHub Issue

---

**重要提示**: 加密货币交易具有高风险。在使用本系统进行实盘交易前，请确保：
- 充分理解交易策略
- 测试系统功能
- 设置适当的风险参数
- 使用可承受损失的资金