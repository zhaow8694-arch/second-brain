# 测试工具使用指南

## 概述

本指南介绍了量化交易系统测试工具的使用方法。测试工具包括：

1. 测试数据生成器
2. 测试结果分析器
3. 测试报告生成器
4. 测试环境管理器

## 安装

```bash
# 克隆项目
git clone https://github.com/your-username/trading-system.git
cd trading-system

# 安装依赖
pip install -r requirements.txt

# 安装测试工具
pip install -e .
```

## 命令行工具

### 测试数据生成器

生成市场数据：
```bash
python -m src.tests.tools.cli data generate \
    --type market \
    --symbol BTC/USDT \
    --timeframe 1m \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --output market_data.csv
```

生成交易数据：
```bash
python -m src.tests.tools.cli data generate \
    --type trade \
    --symbol BTC/USDT \
    --count 1000 \
    --output trade_data.csv
```

生成系统数据：
```bash
python -m src.tests.tools.cli data generate \
    --type system \
    --count 1000 \
    --output system_data.csv
```

### 测试结果分析器

分析预测结果：
```bash
python -m src.tests.tools.cli analyze analyze-results \
    --type prediction \
    --input prediction_results.csv \
    --output analysis_results.json
```

分析性能数据：
```bash
python -m src.tests.tools.cli analyze analyze-results \
    --type performance \
    --input performance_data.csv \
    --output performance_analysis.json
```

分析错误数据：
```bash
python -m src.tests.tools.cli analyze analyze-results \
    --type error \
    --input error_logs.csv \
    --output error_analysis.json
```

### 测试报告生成器

生成HTML报告：
```bash
python -m src.tests.tools.cli report generate-report \
    --input analysis_results.json \
    --output report.html \
    --format html
```

生成PDF报告：
```bash
python -m src.tests.tools.cli report generate-report \
    --input analysis_results.json \
    --output report.pdf \
    --format pdf
```

### 测试环境管理器

创建测试环境：
```bash
python -m src.tests.tools.cli env create \
    --name test_env \
    --python-version 3.8 \
    --requirements pytest==7.4.0 \
    --requirements numpy==1.24.3 \
    --requirements pandas==2.0.3
```

获取环境信息：
```bash
python -m src.tests.tools.cli env info \
    --name test_env
```

导出环境配置：
```bash
python -m src.tests.tools.cli env export \
    --name test_env \
    --output env_config.yaml
```

导入环境配置：
```bash
python -m src.tests.tools.cli env import \
    --input env_config.yaml
```

## 示例

### 完整的测试流程

1. 创建测试环境：
```bash
python -m src.tests.tools.cli env create \
    --name test_env \
    --requirements pytest==7.4.0 \
    --requirements numpy==1.24.3 \
    --requirements pandas==2.0.3
```

2. 生成测试数据：
```bash
python -m src.tests.tools.cli data generate \
    --type market \
    --symbol BTC/USDT \
    --timeframe 1m \
    --count 1000 \
    --output market_data.csv
```

3. 运行测试：
```bash
python -m pytest src/tests/ -v
```

4. 分析测试结果：
```bash
python -m src.tests.tools.cli analyze analyze-results \
    --type prediction \
    --input prediction_results.csv \
    --output analysis_results.json
```

5. 生成测试报告：
```bash
python -m src.tests.tools.cli report generate-report \
    --input analysis_results.json \
    --output report.html \
    --format html
```

### 性能测试示例

1. 生成性能测试数据：
```bash
python -m src.tests.tools.cli data generate \
    --type performance \
    --count 1000 \
    --output performance_data.csv
```

2. 分析性能数据：
```bash
python -m src.tests.tools.cli analyze analyze-results \
    --type performance \
    --input performance_data.csv \
    --output performance_analysis.json
```

3. 生成性能报告：
```bash
python -m src.tests.tools.cli report generate-report \
    --input performance_analysis.json \
    --output performance_report.html \
    --format html
```

### 错误分析示例

1. 生成错误数据：
```bash
python -m src.tests.tools.cli data generate \
    --type error \
    --count 1000 \
    --output error_logs.csv
```

2. 分析错误数据：
```bash
python -m src.tests.tools.cli analyze analyze-results \
    --type error \
    --input error_logs.csv \
    --output error_analysis.json
```

3. 生成错误报告：
```bash
python -m src.tests.tools.cli report generate-report \
    --input error_analysis.json \
    --output error_report.html \
    --format html
```

## 注意事项

1. 环境管理
   - 建议为不同的测试场景创建独立的环境
   - 定期清理不需要的环境
   - 导出环境配置以便共享

2. 数据生成
   - 根据实际需求调整数据量
   - 注意数据的时间范围和频率
   - 保存生成的数据以供后续使用

3. 结果分析
   - 关注关键性能指标
   - 分析异常和错误模式
   - 定期生成分析报告

4. 报告生成
   - 选择合适的报告格式
   - 自定义报告模板
   - 定期更新报告内容

## 常见问题

1. 环境创建失败
   - 检查Python版本兼容性
   - 确保依赖包版本正确
   - 检查网络连接

2. 数据生成错误
   - 验证输入参数
   - 检查文件权限
   - 确保足够的磁盘空间

3. 分析结果异常
   - 检查数据格式
   - 验证分析参数
   - 查看错误日志

4. 报告生成失败
   - 检查输入数据格式
   - 验证模板文件
   - 确保输出目录存在 