# Apex_Binance v2.1 — 量化交易系统规格说明

> 更新日期：2026-06-19  
> 版本：v2.1（Z-Wei 策略增强版）

---

## 一、系统概述

Apex_Binance 是一个面向币安合约市场的**全自动量化交易系统**，采用多时间框架趋势跟踪策略，融合 Z-Wei 交易体系的核心方法论。系统具备完整的开仓→持仓管理→多路径平仓闭环，并通过 Telegram 实时推送交易通知。

**适用市场**：币安 USDT 永续合约（双向持仓模式）  
**运行模式**：模拟交易 / 实盘交易  
**交易标的**：25 个主流币种  
**循环周期**：约 30 秒/周期

---

## 二、项目结构

```
Apex_Binance/
├── app.py                      # 主应用程序（入口 + 主循环 + 协调器）
├── config.py                   # 配置管理（全部参数集中管理）
├── .env                        # 环境变量（API 密钥、交易参数）
├── .env.example                # 环境变量模板
├── requirements.txt            # 依赖清单
├── test_fixes.py               # 单元测试（35 个测试用例）
│
├── core/                       # 核心模块目录
│   ├── __init__.py
│   ├── exchange_client.py      # 交易所 API 封装
│   ├── strategy_engine.py      # 策略引擎（信号生成）
│   ├── risk_manager.py         # 风险管理器
│   ├── trade_executor.py       # 交易执行器
│   ├── notify.py               # Telegram 通知模块
│   └── state_store.py          # 状态持久化管理
│
├── trading_system.log          # 运行日志（轮转，5MB×3 备份）
└── guardian_earth_state_core.json  # 状态持久化文件
```

---

## 三、模块职责

### 3.1 [app.py](file:///e:/Apex_Binance/app.py) — 主应用程序

**角色**：系统总控制器，协调所有模块协作运行。

| 功能 | 说明 |
|------|------|
| 启动初始化 | 验证配置 → 测试 Telegram → 初始化交易所 → 恢复状态 → 同步持仓 |
| 主循环 | 每 ~30 秒执行一个 run_cycle，包含平仓检查链 + 信号扫描 |
| 平仓协调 | 按 P0→P5 优先级链依次检查各退出条件 |
| 状态报告 | 每 10 秒控制台显示 + 每 4 小时 Telegram 日报 |
| 优雅关闭 | SIGINT/SIGTERM 信号 → 保存状态 → Telegram 通知 |

### 3.2 [config.py](file:///e:/Apex_Binance/config.py) — 配置管理

**角色**：集中管理全部参数，支持 `.env` 环境变量覆盖。

**参数分类**：

| 类别 | 参数 | 默认值 | 说明 |
|------|------|--------|------|
| 风控 | `RISK_PCT` | 0.8% | 单笔风险金额占权益比例 |
| 风控 | `DAILY_MAX_LOSS` | 10% | 日亏损熔断阈值 |
| 风控 | `MAX_POSITIONS` | 6 | 最大总持仓数 |
| 风控 | `MAX_REGULAR_POSITIONS` | 4 | 普通币种最大持仓数 |
| 风控 | `COOLDOWN_TIME` | 3600s | 平仓后冷却时间 |
| 止损 | `ATR_SL_LONG` | 3.5 | 多头止损 ATR 倍数 |
| 止损 | `ATR_SL_SHORT` | 2.5 | 空头止损 ATR 倍数 |
| 移动止损 | `HWM_ACTIVATE_LONG` | 2.5% | 多头移动止损激活阈值 |
| 移动止损 | `HWM_ACTIVATE_SHORT` | 3.0% | 空头移动止损激活阈值 |
| 移动止损 | `HWM_RETRACT_LONG` | 1.2% | 多头移动止损回撤幅度 |
| 移动止损 | `HWM_RETRACT_SHORT` | 1.5% | 空头移动止损回撤幅度 |
| Z-Wei | `ADX_TRENDING_THRESHOLD` | 20 | ADX 趋势判断阈值 |
| Z-Wei | `ADX_STRONG_TREND` | 30 | ADX 强趋势阈值 |
| Z-Wei | `SIGNAL_EXPANSION_MAX` | 2.5 | K 线突兀放大上限 |
| Z-Wei | `DANGEROUS_BODY_MULTIPLIER` | 3.0 | 危险 K 线实体倍数 |
| Z-Wei | `MOMENTUM_RSI_OVERBOUGHT` | 70 | RSI 超买线 |
| Z-Wei | `MOMENTUM_RSI_OVERSOLD` | 30 | RSI 超卖线 |
| Z-Wei | `MOMENTUM_RSI_DELTA` | 5 | RSI 动量衰减阈值 |
| Z-Wei | `MAX_HOLD_HOURS` | 48 | 最大持仓时间 |
| 系统 | `REPORT_INTERVAL` | 14400s | 报告发送间隔 |

**交易对列表**（25 个）：BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, DOT, LINK, BCH, NEAR, UNI, LTC, APT, STX, ARB, OP, INJ, TIA, SUI, SEI, FET, TAO, WLD

**板块分类**：POW（BTC/BCH/LTC）、L1（ETH/SOL/BNB/SUI/NEAR/AVAX/APT/SEI/TIA/ADA）、L0（DOT）、INFRA（LINK/INJ）、L2（OP/ARB/STX）、MEME（DOGE/WLD）、PAYMENT（XRP）、DEFI（UNI）、AI（TAO/FET）

### 3.3 [core/exchange_client.py](file:///e:/Apex_Binance/core/exchange_client.py) — 交易所客户端

**角色**：封装 CCXT 库，提供统一的币安合约接口。

| 方法 | 功能 |
|------|------|
| `initialize(demo_mode)` | 连接币安、加载市场、设置双向持仓模式 |
| `get_balance()` | 返回 {total, free, used} USDT 余额 |
| `get_positions()` | 返回当前所有持仓字典 |
| `fetch_ohlcv(symbol, timeframe)` | 获取 K 线数据，返回 DataFrame |
| `fetch_ticker(symbol)` | 获取实时行情 |
| `create_market_order()` | 创建市价单（支持双向持仓参数） |
| `create_limit_order()` | 创建限价单 |
| `set_leverage(symbol, leverage)` | 设置杠杆倍数 |
| `fetch_funding_rate(symbol)` | 获取资金费率 |

### 3.4 [core/strategy_engine.py](file:///e:/Apex_Binance/core/strategy_engine.py) — 策略引擎

**角色**：信号生成的核心大脑，包含多时间框架分析、Z-Wei 过滤器和技术指标计算。

#### 信号生成流程

```
generate_signal(symbol)
├─ 获取 15m / 1h / 4h K线数据
├─ [Z-Wei 过滤] ADX震荡市检测 → 震荡则跳过
├─ [Z-Wei 过滤] 危险K线检测 → 实体突兀放大则跳过
├─ calculate_indicators() — 计算 EMA/ATR/RSI/MACD
├─ _check_trend() — 多时间框架 EMA60 趋势判断
├─ _check_momentum() — RSI + MACD 动量判断
├─ _check_volume() — 成交量确认
├─ _generate_trading_signal() — 趋势共振/动量/放量 综合决策
├─ [Z-Wei 过滤] _score_breakout_quality() — 突破质量评分（<0.4 丢弃）
└─ 返回 signal {direction, strength, atr, breakout_quality, market_regime, ...}
```

#### 技术指标

| 时间框架 | 指标 |
|---------|------|
| **4h** | EMA60, EMA576（长期趋势） |
| **1h** | EMA12, EMA26, EMA60, MACD, MACD Signal, MACD Hist（中期趋势+动量） |
| **15m** | EMA14, EMA21, EMA60, ATR(14), RSI(14), Vol SMA20（短期交易指标） |

#### 信号类型

| 类型 | 条件 | 强度 |
|------|------|------|
| **强趋势共振** | 4h+1h 同向趋势 + 动量确认 | strong |
| **趋势共振+放量** | 1h趋势 + 4h偏多/偏空 + 动量 + 成交量放大 | medium |

#### Z-Wei 新增过滤器

| 过滤器 | 方法 | 阈值 |
|--------|------|------|
| ADX 震荡市过滤 | `_is_trending()` | ADX ≥ 20 |
| 危险 K 线检测 | `_is_dangerous_candle()` | 实体 > 近 20 根均值 × 3 |
| 突破质量评分 | `_score_breakout_quality()` | 质量 < 0.4 丢弃 |

#### 市场状态分类

| 状态 | ADX 范围 | 策略行为 |
|------|---------|---------|
| `strong_trend` | ≥ 30 | 正常交易 |
| `weak_trend` | 20-30 | 正常交易 |
| `ranging` | < 20 | 不生成信号 |

### 3.5 [core/risk_manager.py](file:///e:/Apex_Binance/core/risk_manager.py) — 风险管理器

**角色**：资金管理、止损止盈计算、持仓限制、日亏损熔断。

| 方法 | 功能 |
|------|------|
| `initialize(equity)` | 设置初始权益和日起始权益 |
| `check_daily_loss_limit()` | 当日亏损 ≥ 10% 则熔断停交易 |
| `check_position_limit()` | 检查持仓数量+冷却期 |
| `calculate_position_size()` | 计算仓位 = 权益 × 0.8%（上限 10%） |
| `calculate_stop_loss()` | 止损 = 入场价 ± ATR × 倍数 |
| `calculate_take_profit()` | TP1 = 2×ATR, TP2 = 4×ATR |
| `should_take_profit_by_atr()` | 用 ATR 比例判断止盈 |
| `update_high_water_mark()` | HWM 移动止损计算 |
| `get_risk_report()` | 生成风险报告 |

**风控约束链**：
```
开仓前检查：日亏损熔断 → 持仓数量上限 → VIP/普通限制 → 冷却期
开仓参数：权益×0.8% 风险额 → ≤10% 保证金上限
开仓后保护：ATR 止损 → 盈利 2.5%/3% 激活移动止损 → TP1(部分平) → TP2(全平)
```

### 3.6 [core/trade_executor.py](file:///e:/Apex_Binance/core/trade_executor.py) — 交易执行器

**角色**：订单执行、持仓跟踪、平仓管理。

#### 持仓状态跟踪

所有持仓信息通过以下字典维护（以 symbol 简称作为 key）：

| 字典 | 含义 |
|------|------|
| `positions` | 持仓详情 {symbol, side, contracts, entry_price, mark_price, leverage} |
| `entry_prices` | 入场价 |
| `target_prices` | TP1 目标价 |
| `target_prices_tp2` | TP2 全平目标价 |
| `stop_losses` | 止损价 |
| `entry_atrs` | 入场时的 ATR 值 |
| `position_levels` | 仓位层级 |
| `base_sizes` | 基础仓位大小 |
| `partital_closes` | 部分平仓记录 |
| `position_history` | 完整交易历史（上限 200 条） |

#### 平仓体系（P0→P5 优先级链）

```
P0: check_dangerous_candle_exit()  危险K线反向 → 全平（最高优先级，保命级）
P1: check_stop_loss()              ATR止损触发 → 全平（强制实时价格，不使用缓存）
P2: check_momentum_exit()          动量衰减 → 全平（RSI 从超买/超卖区回落）
P3: check_time_exit()              时间止损 → 全平（持仓超过 48 小时）
P4: check_take_profit()            止盈：
    ├─ TP2 触发 → 全平（4×ATR）
    └─ TP1 触发 → 部分平 50%（ATR 比例判断）
P5: update_trailing_stop()         更新移动止损线（HWM 机制）
```

### 3.7 [core/notify.py](file:///e:/Apex_Binance/core/notify.py) — Telegram 通知

**通知类型**：

| 方法 | 触发场景 |
|------|---------|
| `send_trade_alert()` | 系统启动/关闭、开仓、平仓、部分平仓、持仓同步 |
| `send_error_alert()` | 系统异常、交易失败 |
| `send_daily_report()` | 每 4 小时定期报告 |
| `test_connection()` | 启动时验证连接 |

### 3.8 [core/state_store.py](file:///e:/Apex_Binance/core/state_store.py) — 状态管理

**功能**：系统状态的持久化和恢复。

- 保存风险管理和交易执行器的完整状态
- 支持多备份文件加载（主文件 + 3 个备用文件名）
- 每次保存前自动备份（保留最近 5 个）
- 版本兼容性校验（仅加载 v2.x）
- 跨日自动重置交易权限

---

## 四、核心交易流程

### 4.1 启动流程

```
1. 验证 .env 配置完整性
2. 测试 Telegram 连接
3. 初始化币安连接（默认模拟交易模式）
4. 获取账户余额
5. 初始化风险管理器
6. 加载上次状态（有则恢复持仓/风控信息）
7. 同步交易所持仓
8. 发送启动通知
9. 进入主循环
```

### 4.2 主循环流程（~30 秒/周期）

```
每个周期执行：
┌─ 获取账户余额
├─ 检查日亏损熔断（触发则休眠至次日）
├─ 同步交易所持仓
├─ [P0] 危险K线反向 → 紧急全平
├─ [P1] 实时价格止损 → 全平
├─ [P2] RSI 动量衰减 → 全平
├─ [P3] 持仓超时 48h → 全平
├─ [P4] 止盈：
│     TP2(4×ATR) → 全平
│     TP1(ATR比例) → 部分平 50%
├─ [P5] 更新 HWM 移动止损线
├─ 扫描市场信号（每次 10 个币种，滚动）
│     ├─ ADX 震荡过滤
│     ├─ 危险K线过滤
│     ├─ 信号生成
│     ├─ 突破质量过滤
│     └─ 执行交易
├─ 定期报告（每 4 小时 Telegram 日报）
├─ 状态显示（每 10 秒控制台）
└─ 保存状态到文件
```

### 4.3 信号生成决策树

```
信号条件                          方向      强度
─────────────────────────────────────────────────
4h看多 + 1h看多 + RSI动量多     → long    strong
4h看空 + 1h看空 + RSI动量空     → short   strong
4h偏多 + 1h看多 + 动量 + 放量   → long    medium
4h偏空 + 1h看空 + 动量 + 放量   → short   medium
其他组合                         → 无信号
```

---

## 五、关键设计决策

### 5.1 为什么用 EMA60 而非其他均线

EMA60 在 4h 图约等于 10 日均线，在 1h 图约等于 2.5 日均线。它处于中期和长期之间，既能过滤短期噪音，又比 MA200 更及时反应趋势变化。±2% 的缓冲区避免了在均线附近反复穿越。

### 5.2 为什么多头止损 3.5×ATR，空头 2.5×ATR

加密货币市场中多头趋势通常比空头更持久但回撤更深，因此多头需要更宽的止损空间；空头趋势往往更快更急，用较窄的止损保护利润。

### 5.3 为什么止盈分 TP1 和 TP2

基于 Z-Wei 的"不追求完整行情"哲学：TP1（2×ATR）先锁定 50% 利润，剩余 50% 持仓让利润继续奔跑到 TP2（4×ATR）。这是一个经典的 1:1 → 1:2 风险收益比递进策略。

### 5.4 为什么 ADX 阈值设为 20

ADX < 20 被广泛认为是无趋势/震荡市的通用标准。在此状态下，趋势跟踪策略的胜率急剧下降。Z-Wei 体系明确要求"震荡市不交易"。

### 5.5 为什么移动止损空头从 4% 降到 3%

历史回测发现 4% 的移动止损激活阈值在空头方向保护过慢，价格可能已经大幅回撤。统一为与多头接近的阈值（3%）提供了更及时的保护。

---

## 六、已知局限与注意事项

| # | 局限 | 影响 | 缓解措施 |
|---|------|------|---------|
| 1 | 策略未经过严格 walk-forward 回测 | 参数可能非最优 | 建议先在模拟盘运行至少 2 周 |
| 2 | 全局单例模式 | 不支持多账户 | 当前设计仅单账户 |
| 3 | K 线数据无重试 | 网络波动时跳过信号 | exchange_client 依赖 CCXT 自带限速 |
| 4 | 资金费率已获取但未用于信号 | 信息浪费 | 可后续加入费率方向过滤 |
| 5 | 同板块不限制持仓数量 | 可能过度集中风险 | 通过 4 个普通持仓上限间接限制 |
| 6 | 1h 图 MACD 未在动量判断中生效 | 动量偏重 RSI | RSI 足以提供动量信号 |

---

## 七、运行与维护

### 启动

```bash
cd e:\Apex_Binance
.\venv\Scripts\python.exe app.py
```

### 停止

按 `Ctrl+C` 触发优雅关闭（保存状态 + 发送通知）。

### 日志

- 文件：`trading_system.log`（5MB 轮转，保留 3 个备份）
- 控制台：实时显示每 10 秒状态摘要
- Telegram：交易通知 + 定期报告 + 错误警报

### 测试

```bash
.\venv\Scripts\python.exe -m unittest test_fixes -v
# 35 个测试用例，覆盖所有模块
```

---

## 八、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2026-Q1 | 初始重构：模块化架构、Telegram 通知、风险管理 |
| v2.1 | 2026-06-19 | Z-Wei 策略增强：ADX 震荡过滤、危险 K 线检测、突破质量评分、TP2 全平、动量/时间退出、实时价格止损 |
