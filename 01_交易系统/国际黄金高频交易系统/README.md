# 国际黄金期货与数字货币高频交易系统

## 项目简介
本系统是一个集成了币安交易所和MT4平台的高频交易系统，结合DeepSeek AI模型进行市场分析和交易决策。

## 功能特点
- 多平台交易支持（币安、MT4）
- 实时行情数据采集
- AI辅助决策
- 风险控制系统
- 高频交易执行
- 实时监控告警

## 技术栈
- Python 3.10+
- FastAPI
- TimescaleDB
- Redis
- Kafka
- React/Vue.js

## 安装说明

### 环境要求
- Python 3.10+
- PostgreSQL 13+ with TimescaleDB
- Redis
- Kafka

### 安装步骤
1. 克隆项目
```bash
git clone [项目地址]
cd trading_system
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入实际配置
```

5. 初始化数据库
```bash
# 待补充数据库初始化命令
```

## 使用说明
1. 启动系统
```bash
# 待补充启动命令
```

2. 配置交易参数
- 在config目录下修改相关配置

3. 运行测试
```bash
pytest
```

## 项目结构
```
trading_system/
├── src/
│   ├── data_collectors/    # 数据采集模块
│   ├── strategies/         # 交易策略
│   ├── risk_management/    # 风控模块
│   ├── execution/          # 交易执行
│   └── utils/             # 工具函数
├── tests/                  # 测试代码
├── config/                 # 配置文件
├── docs/                   # 文档
└── requirements.txt        # 依赖包
```

## 开发计划
- [x] 基础环境搭建
- [ ] 数据采集模块
- [ ] 策略引擎开发
- [ ] 风控系统实现
- [ ] AI模型集成
- [ ] 交易执行系统
- [ ] 监控告警系统
- [ ] UI开发

## 注意事项
- 实盘交易前请确保充分测试
- 请严格遵守风控规则
- 定期检查系统状态
- 保管好API密钥

## 贡献指南
欢迎提交Issue和Pull Request

## 许可证
[待定] 