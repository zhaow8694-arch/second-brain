# 硅基远征军 · 工作日志

## 2026-04-27

### V2.7 升级内容

#### 1. 行情引擎全面升级
- **标的覆盖**: 从 3 个扩展到 15+ 个
  - 贵金属: XAU/USD (黄金), XAG/USD (白银)
  - 加密货币: BTC/USDT, ETH/USDT, SOL/USDT, DOGE/USDT
  - 美股: NVDA, AAPL, TSLA, MSFT, AMZN, GOOGL, META
  - ETF: SPY (标普500), QQQ (纳斯达克)
  - 指数: DJI (道琼斯), IXIC (纳斯达克综合)
- **数据源降级链**: OpenBB → Yahoo Finance → Binance API → gold-api.com
- **缓存机制**: 60 秒本地文件缓存 (`market_cache/` 目录)
- **配置驱动**: 新增品种只需在 `SYMBOL_LEGACY_CONFIG` 添加一行

#### 2. 系统容灾增强
- **全局异常保护**: `main.py` 所有任务包裹 try/except
- **输入容错**: EOFError/KeyboardInterrupt 自动降级到默认任务 (15-行情数据引擎)
- **CrewAI 保护**: `crew.kickoff()` 异常时保留行情+回测数据，不崩溃
- **总参谋长增强**: 支持 15+ 个标的的自然语言识别

#### 3. 文件变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `core/market_data_legacy.py` | 重写 | 15+ 标的配置 + 缓存机制 + 多源降级 |
| `core/market_data.py` | 更新 | 同步扩展 SYMBOL_CONFIG |
| `command/chief_of_staff.py` | 更新 | 新增 10+ 个标的映射 |
| `command/operations.py` | 更新 | 回测菜单动态加载标的列表 |
| `main.py` | 更新 | 全局异常保护 + 输入容错 |
| `WORK_LOG.md` | 新建 | 工作日志系统 |

### 问题记录
- **PET 崩溃**: VS Code Python Environment Tool 崩溃，不影响代码运行。重启 VS Code 可恢复。
- **PowerShell 嵌套引号**: 在 `py -3.13 -c "..."` 中嵌套双引号会导致 SyntaxError。解决方案：改用 `.py` 文件执行。
- **OpenBB 4.7.1 兼容性**: `OBBject_EquityInfo` 导入错误，双模引擎自动降级到 Legacy 模式。
- **CrewAI 1.14.3 变更**: `Tool` 从 `crewai` 移到 `crewai.tools`，且必须用 `@tool` 装饰器 + docstring。

### 修复记录
- `core/tools.py`: 适配 CrewAI 1.14.3 `@tool` 装饰器语法
- `core/tools.py`: 新增 `get_market_summary_for_agent` — 降维版 Agent 数据工具
- `core/market_data.py`: 添加 `get_price()`、`get_historical_data()` 等向后兼容函数
- `command/operations.py`: `run_financial_mission` 添加 try/except 异常保护
- `command/operations.py`: `run_financial_mission` Agent backstory 升级（Grok 建议采纳）
- `command/operations.py`: `run_financial_mission` Task description/expected_output 结构化升级
- `command/operations.py`: `run_financial_mission` WATCH_LIST 从 3 个硬编码改为动态 17 个标的
- `command/operations.py`: `run_financial_mission` intel_agent 新增 Market_History_Summary Tool
- `command/operations.py`: `run_financial_mission` 模拟开仓 + 组合摘要 + write_log 全部加 try/except
- `command/chief_of_staff.py`: 军情局注册表函数指向修正

### V2.7.1 全面代码审查修复 (2026-04-27)

#### 修复的 8 个问题
| # | 文件 | 问题 | 修复方式 |
|---|------|------|----------|
| 1 | `command/menu.py` | `get_choice()` 提示 "1-17" 但实际有 18 个选项 | 改为 "1-18" |
| 2 | `command/chief_of_staff.py` | "原油" 错误映射到 XAU/USD | 改为 USO (原油 ETF) |
| 3 | `core/market_data.py` | `change_24h` 硬编码为 0.0 | 从数据源获取真实涨跌幅 |
| 4 | `command/chief_of_staff.py` | `_call_department()` 调用 `get_market_data` 不带参数 | 自动传入 `target` |
| 5 | `command/operations.py` | `run_backtest_mission` 缺少 `import json` | 函数内添加 import |
| 6 | `_verify.py`, `_verify_v24.py` | 过时的测试文件 | 删除 |
| 7 | `core/tools.py` | 采集时间硬编码 | 改为 `datetime.now()` |
| 8 | `core/market_data_legacy.py` | gold-api 价格未做类型校验 | 添加 `float()` + `>0` 检查 |

#### 增强项
- `core/market_data_legacy.py`: 新增 USO (原油 ETF) 品种配置
- `core/market_data_legacy.py`: Binance/Yahoo/gold-api 三个数据源全部返回 `change_24h`
- `core/market_data.py`: OpenBB 路径也计算 `change_24h`

### V2.8 两阶段金融分析升级 (2026-04-27)

#### 新增内容
1. **宏观环境分析（两阶段流程）**
   - 新增 3 个宏观指标：VIX（波动率指数）、DXY（美元指数）、US10Y（10年期国债收益率）
   - 新增 `get_macro_data()` 函数统一获取宏观数据
   - 新增 `macro_agent`（宏观环境分析师）— 在个股分析前先判断 Risk-On/Off 模式

2. **总作战长合成 Agent**
   - 新增 `synthesis_agent`（总作战长）— 汇总所有 20+ 个标的的分析结果
   - 输出统一作战方案：资金分配、优先级排序、"开火/观望/撤退"总命令

3. **Agent 架构升级**
   - 从 3 个 Agent 扩展到 5 个 Agent：宏观分析师 → 情报特工 → 量化师 → 宪兵局长 → 总作战长
   - 执行流程：宏观环境 → 个股分析（情报→量化→风控）× N → 合成汇总

#### 修复的问题
- `core/market_data.py`: 修复 pandas FutureWarning（`float(row["Open"])` → `float(row["Open"].iloc[0])`）
- `core/market_data.py`: 历史数据获取从 30 天改为 60 天，确保回测有足够数据
- `command/operations.py`: 回测数据从 30 天改为 60 天，增加数据不足提示

#### 文件变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `core/market_data_legacy.py` | 更新 | 新增 VIX/DXY/US10Y 宏观指标配置 |
| `core/market_data.py` | 更新 | 新增 `get_macro_data()` 函数 + FutureWarning 修复 |
| `command/operations.py` | 重写 | 两阶段流程 + 5 Agent 架构 + 合成 Task |

### V2.8.1 智能标的选择 + Bug 修复 (2026-04-27)

#### 新增功能
1. **智能标的选择**
   - `run_financial_mission(session_id, symbols=None)` — 新增可选 `symbols` 参数
   - 当 `symbols=None` 时：显示交互菜单，用户输入编号选择要分析的标的
   - 当 `symbols` 提供时：只分析指定的标的，跳过其余
   - 总参谋长集成：`_call_department()` 传递 `all_targets` 给支持 `accepts_targets` 的部门

2. **总参谋长增强**
   - `DEPARTMENT_REGISTRY` 新增 `accepts_targets` 标记
   - `_call_department(department, session_id, target, all_targets)` — 新增 `all_targets` 参数
   - `execute_command` 传递 `all_targets` 给 `_call_department`

#### 修复的问题
- `command/operations.py`: 修复格式错误 `{price:<10s}` → `{price:<10.2f}`（float 类型不能用 s 格式）
- `command/operations.py`: 修复 CrewAI 返回值处理（`crew.kickoff()` 返回 CrewOutput 对象，需取 `.raw` 属性）
- `command/operations.py`: 增加 `traceback.print_exc()` 详细错误输出便于调试

#### 文件变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `command/operations.py` | 更新 | 智能标的选择 + 格式修复 + CrewAI 返回值处理 |
| `command/chief_of_staff.py` | 更新 | 新增 `accepts_targets` 机制 + `all_targets` 传递 |

### V2.9 Financial Gateway (财务主权网关) — 2026-04-28

#### 新增内容
1. **Financial Gateway (`core/financial_gateway.py`)**
   - V2.6 规划中的财务主权网关第一版实现
   - 统一封装交易所 API (ccxt)，支持多交易所切换
   - 双模运行：虚拟模式 (virtual) / 实盘模式 (live)
   - 自动检测 `IS_TESTNET` 环境变量，测试网自动切换端点
   - 统一订单接口：查询余额 → 下单 → 查询持仓 → 撤单
   - 所有操作记录流水到 `portfolio_log/`

2. **核心函数**
   - `get_mode()` — 获取当前运行模式 (virtual/live)
   - `check_connection()` — 测试交易所连接状态
   - `fetch_balance()` — 获取账户余额（虚拟/实盘双模）
   - `create_order(symbol, side, type, quantity, price)` — 统一下单接口
   - `get_positions()` — 获取当前持仓
   - `cancel_order(order_id, symbol)` — 撤销订单
   - `get_gateway_status()` — 网关状态摘要

3. **Auto-execute 升级**
   - `operations.py` 自动执行部分改为通过 `financial_gateway.create_order()` 下单
   - 虚拟模式走本地 `portfolio.json`，实盘模式走交易所 API
   - 下单结果明确显示当前模式 (virtual/live)

4. **Tools 模块重构 (`core/tools.py`)**
   - 移除模块级别 `from crewai.tools import tool`，改为延迟加载
   - 新增 `get_openbb_tool()`, `get_market_history_tool()`, `get_macro_tool()`, `get_available_symbols_tool()` 工厂函数
   - 所有 22 个模块可独立加载，不依赖 crewai

#### 环境变量新增
| 变量 | 说明 |
|------|------|
| `BINANCE_TESTNET_API_KEY` | 币安现货测试网 API Key |
| `BINANCE_TESTNET_SECRET_KEY` | 币安现货测试网 Secret Key |
| `IS_TESTNET=True` | 标注为测试环境，防止逻辑跑偏 |
| `GATEWAY_MODE=virtual` | 网关模式: virtual(虚拟) / live(实盘) |

#### 文件变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `core/financial_gateway.py` | **新建** | 财务主权网关第一版 |
| `core/tools.py` | 重构 | 延迟加载 CrewAI Tool，模块级不依赖 crewai |
| `command/operations.py` | 更新 | Auto-execute 通过网关下单 + Agent tools 使用工厂函数 |
| `.env` | 更新 | 新增测试网 Key + 网关配置 |
