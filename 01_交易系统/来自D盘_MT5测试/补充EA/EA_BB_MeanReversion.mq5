//+------------------------------------------------------------------+
//|                                          EA_BB_MeanReversion.mq5 |
//|                                    布林带均值回归日内交易策略 v1.0 |
//|                                                                  |
//|  策略逻辑：                                                       |
//|  价格触碰布林带上轨 → 做空（预期回归中轨）                          |
//|  价格触碰布林带下轨 → 做多（预期回归中轨）                          |
//|  目标：中轨（MA20）或固定ATR倍数止盈                               |
//|                                                                  |
//|  适用品种：XAUUSD（黄金）                                         |
//|  推荐周期：M15                                                    |
//|  交易类型：日内短线，强制日内平仓，不隔夜                           |
//+------------------------------------------------------------------+
#property copyright "EA_BB_MeanReversion"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
CTrade trade;

//+------------------------------------------------------------------+
//| 输入参数定义                                                       |
//+------------------------------------------------------------------+

// === 布林带参数 ===
input group              "=== 布林带参数 ==="
input int                Inp_BB_Period        = 20;      // 布林带周期
input double             Inp_BB_Deviation     = 2.0;     // 标准差倍数（2.0=标准，2.5=保守）
input ENUM_APPLIED_PRICE Inp_BB_Price         = PRICE_CLOSE; // 应用价格

// === ATR参数 ===
input group              "=== ATR参数 ==="
input int                Inp_ATR_Period       = 14;      // ATR周期
input double             Inp_StopLoss_ATR     = 1.5;     // 止损ATR倍数
input double             Inp_TakeProfit_ATR   = 2.5;     // 止盈ATR倍数（也可用中轨止盈）
input bool               Inp_TP_Use_MidBand   = true;    // true=中轨止盈，false=ATR倍数止盈

// === 趋势过滤参数（ADX）===
input group              "=== 趋势过滤 ==="
input bool               Inp_Use_ADX_Filter   = true;    // 是否启用ADX过滤（震荡市才做均值回归）
input int                Inp_ADX_Period       = 14;      // ADX周期
input double             Inp_ADX_Max          = 30.0;    // ADX最大值（超过此值说明趋势太强，不做均值回归）

// === RSI辅助确认 ===
input group              "=== RSI辅助确认 ==="
input bool               Inp_Use_RSI_Filter   = true;    // 是否启用RSI过滤
input int                Inp_RSI_Period       = 14;      // RSI周期
input double             Inp_RSI_Oversold     = 35.0;    // RSI超卖阈值（低于此值才允许做多）
input double             Inp_RSI_Overbought   = 65.0;    // RSI超买阈值（高于此值才允许做空）

// === 资金管理参数 ===
input group              "=== 资金管理 ==="
input double             Inp_Risk_Percent     = 1.0;     // 固定风险比例（%账户余额，0=使用固定手数）
input double             Inp_Lot_Size         = 0.1;     // 固定手数（Risk_Percent=0时生效）
input int                Inp_Max_Orders       = 1;       // 最大同向持仓单数

// === 移动止损参数 ===
input group              "=== 移动止损 ==="
input bool               Inp_Use_Trailing     = true;    // 是否启用移动止损
input double             Inp_Trailing_Start_ATR = 1.0;  // 启动移动止损的盈利ATR倍数
input double             Inp_Trailing_Step_ATR  = 0.5;  // 移动止损步进ATR倍数

// === 日内强制平仓 ===
input group              "=== 日内强制平仓 ==="
input bool               Inp_Force_Close_EOD  = true;    // 是否启用日内强制平仓（不隔夜）
input int                Inp_Force_Close_Hour = 22;      // 强制平仓小时（服务器时间）
input int                Inp_Force_Close_Min  = 45;      // 强制平仓分钟

// === 交易时段过滤 ===
input group              "=== 交易时段过滤 ==="
input int                Inp_Trade_Start_Hour = 8;       // 允许开仓开始小时
input int                Inp_Trade_End_Hour   = 22;      // 允许开仓结束小时
input bool               Inp_Friday_Close     = true;    // 周五是否提前平仓
input int                Inp_Friday_Close_Hour= 21;      // 周五强制平仓小时

// === 风控参数 ===
input group              "=== 风控参数 ==="
input int                Inp_Magic_Number     = 8820001; // 魔术数字
input int                Inp_Max_Spread       = 35;      // 最大允许点差（Points）
input double             Inp_Max_Drawdown_Pct = 15.0;    // 最大回撤熔断阈值（%）
input double             Inp_Candle_Body_Ratio= 0.5;     // K线实体占比过滤（防止十字星开仓）

//+------------------------------------------------------------------+
//| 全局变量                                                          |
//+------------------------------------------------------------------+
int      g_BB_Handle     = INVALID_HANDLE;  // 布林带句柄
int      g_ATR_Handle    = INVALID_HANDLE;  // ATR句柄
int      g_ADX_Handle    = INVALID_HANDLE;  // ADX句柄
int      g_RSI_Handle    = INVALID_HANDLE;  // RSI句柄
datetime g_LastBarTime   = 0;               // 上一根K线时间（OnBar机制）
double   g_MaxEquity     = 0;               // 账户历史最高净值
bool     g_EA_Stopped    = false;           // 熔断标志

//+------------------------------------------------------------------+
//| 初始化                                                            |
//+------------------------------------------------------------------+
int OnInit()
  {
   // 创建布林带句柄
   g_BB_Handle = iBands(_Symbol, PERIOD_CURRENT, Inp_BB_Period, 0, Inp_BB_Deviation, Inp_BB_Price);
   if(g_BB_Handle == INVALID_HANDLE)
     {
      Print("布林带句柄创建失败，错误码：", GetLastError());
      return INIT_FAILED;
     }

   // 创建ATR句柄
   g_ATR_Handle = iATR(_Symbol, PERIOD_CURRENT, Inp_ATR_Period);
   if(g_ATR_Handle == INVALID_HANDLE)
     {
      Print("ATR句柄创建失败，错误码：", GetLastError());
      return INIT_FAILED;
     }

   // 创建ADX句柄（如启用）
   if(Inp_Use_ADX_Filter)
     {
      g_ADX_Handle = iADX(_Symbol, PERIOD_CURRENT, Inp_ADX_Period);
      if(g_ADX_Handle == INVALID_HANDLE)
        {
         Print("ADX句柄创建失败，错误码：", GetLastError());
         return INIT_FAILED;
        }
     }

   // 创建RSI句柄（如启用）
   if(Inp_Use_RSI_Filter)
     {
      g_RSI_Handle = iRSI(_Symbol, PERIOD_CURRENT, Inp_RSI_Period, Inp_BB_Price);
      if(g_RSI_Handle == INVALID_HANDLE)
        {
         Print("RSI句柄创建失败，错误码：", GetLastError());
         return INIT_FAILED;
        }
     }

   // 初始化最高净值
   g_MaxEquity = AccountInfoDouble(ACCOUNT_EQUITY);

   // 初始化K线时间
   g_LastBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);

   // 设置交易对象参数
   trade.SetExpertMagicNumber(Inp_Magic_Number);
   trade.SetDeviationInPoints(20);
   trade.SetTypeFilling(ORDER_FILLING_IOC);

   Print("EA_BB_MeanReversion v1.0 初始化成功 | 品种：", _Symbol, " | 周期：", EnumToString(PERIOD_CURRENT));
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
//| 反初始化                                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   if(g_BB_Handle  != INVALID_HANDLE) { IndicatorRelease(g_BB_Handle);  g_BB_Handle  = INVALID_HANDLE; }
   if(g_ATR_Handle != INVALID_HANDLE) { IndicatorRelease(g_ATR_Handle); g_ATR_Handle = INVALID_HANDLE; }
   if(g_ADX_Handle != INVALID_HANDLE) { IndicatorRelease(g_ADX_Handle); g_ADX_Handle = INVALID_HANDLE; }
   if(g_RSI_Handle != INVALID_HANDLE) { IndicatorRelease(g_RSI_Handle); g_RSI_Handle = INVALID_HANDLE; }
   Comment("");
  }

//+------------------------------------------------------------------+
//| 检测新K线                                                         |
//+------------------------------------------------------------------+
bool IsNewBar()
  {
   datetime cur_time = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(cur_time != g_LastBarTime)
     {
      g_LastBarTime = cur_time;
      return true;
     }
   return false;
  }

//+------------------------------------------------------------------+
//| 计算开仓手数（固定风险比例）                                        |
//+------------------------------------------------------------------+
double CalcLotSize(double sl_points)
  {
   if(Inp_Risk_Percent <= 0 || sl_points <= 0)
      return NormalizeLot(Inp_Lot_Size);

   double balance      = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount  = balance * Inp_Risk_Percent / 100.0;
   double tick_value   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size    = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double lot_step     = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double min_lot      = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot      = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   if(tick_value <= 0 || tick_size <= 0) return NormalizeLot(Inp_Lot_Size);

   double lot = risk_amount / (sl_points / tick_size * tick_value);
   lot = MathFloor(lot / lot_step) * lot_step;
   lot = MathMax(min_lot, MathMin(max_lot, lot));
   return NormalizeLot(lot);
  }

//+------------------------------------------------------------------+
//| 手数规范化                                                        |
//+------------------------------------------------------------------+
double NormalizeLot(double lot)
  {
   double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double min_lot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   lot = MathFloor(lot / lot_step) * lot_step;
   return MathMax(min_lot, MathMin(max_lot, lot));
  }

//+------------------------------------------------------------------+
//| 统计本EA当前持仓数量                                               |
//+------------------------------------------------------------------+
int CountOrders(ENUM_POSITION_TYPE pos_type)
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
        {
         if(PositionGetInteger(POSITION_MAGIC) == Inp_Magic_Number &&
            PositionGetString(POSITION_SYMBOL) == _Symbol &&
            (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) == pos_type)
            count++;
        }
     }
   return count;
  }

//+------------------------------------------------------------------+
//| 平掉本EA所有持仓                                                   |
//+------------------------------------------------------------------+
void CloseAllOrders()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
        {
         if(PositionGetInteger(POSITION_MAGIC) == Inp_Magic_Number &&
            PositionGetString(POSITION_SYMBOL) == _Symbol)
           {
            trade.PositionClose(ticket);
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| 开仓函数                                                          |
//+------------------------------------------------------------------+
void OpenOrder(ENUM_ORDER_TYPE order_type, double sl, double tp, double lot)
  {
   double price = (order_type == ORDER_TYPE_BUY)
                  ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                  : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);

   if(order_type == ORDER_TYPE_BUY)
      trade.Buy(lot, _Symbol, price, sl, tp, "BB_MR_Buy");
   else
      trade.Sell(lot, _Symbol, price, sl, tp, "BB_MR_Sell");
  }

//+------------------------------------------------------------------+
//| 移动止损处理                                                       |
//+------------------------------------------------------------------+
void ManageTrailingStop(double atr_1)
  {
   if(!Inp_Use_Trailing) return;

   double trail_start = Inp_Trailing_Start_ATR * atr_1;
   double trail_step  = Inp_Trailing_Step_ATR  * atr_1;
   int    digits      = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != Inp_Magic_Number) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      ENUM_POSITION_TYPE pos_type  = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double             open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double             cur_sl     = PositionGetDouble(POSITION_SL);
      double             cur_tp     = PositionGetDouble(POSITION_TP);
      double             bid        = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double             ask        = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      if(pos_type == POSITION_TYPE_BUY)
        {
         double profit_dist = bid - open_price;
         if(profit_dist >= trail_start)
           {
            double new_sl = NormalizeDouble(bid - trail_step, digits);
            if(new_sl > cur_sl + trail_step * 0.5)
              {
               MqlTradeRequest req = {};
               MqlTradeResult  res = {};
               req.action   = TRADE_ACTION_SLTP;
               req.position = ticket;
               req.symbol   = _Symbol;
               req.sl       = new_sl;
               req.tp       = cur_tp;
               req.magic    = Inp_Magic_Number;
               if(!OrderSend(req, res))
                  Print("移动止损修改失败（Buy）错误码：", GetLastError());
              }
           }
        }
      else if(pos_type == POSITION_TYPE_SELL)
        {
         double profit_dist = open_price - ask;
         if(profit_dist >= trail_start)
           {
            double new_sl = NormalizeDouble(ask + trail_step, digits);
            if(cur_sl == 0 || new_sl < cur_sl - trail_step * 0.5)
              {
               MqlTradeRequest req = {};
               MqlTradeResult  res = {};
               req.action   = TRADE_ACTION_SLTP;
               req.position = ticket;
               req.symbol   = _Symbol;
               req.sl       = new_sl;
               req.tp       = cur_tp;
               req.magic    = Inp_Magic_Number;
               if(!OrderSend(req, res))
                  Print("移动止损修改失败（Sell）错误码：", GetLastError());
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| 主逻辑入口                                                        |
//+------------------------------------------------------------------+
void OnTick()
  {
   // --- 移动止损：每个Tick都执行（不依赖新K线）---
   double atr_buf[];
   ArraySetAsSeries(atr_buf, true);
   if(CopyBuffer(g_ATR_Handle, 0, 0, 3, atr_buf) >= 3)
      ManageTrailingStop(atr_buf[1]);

   // --- 以下逻辑只在新K线开盘时执行 ---
   if(!IsNewBar()) return;

   // ============================================================
   // 1. 读取指标数据
   // ============================================================
   double bb_upper[], bb_mid[], bb_lower[];
   double atr_data[];
   ArraySetAsSeries(bb_upper, true);
   ArraySetAsSeries(bb_mid,   true);
   ArraySetAsSeries(bb_lower, true);
   ArraySetAsSeries(atr_data, true);

   if(CopyBuffer(g_BB_Handle,  1, 0, 3, bb_upper) < 3) return; // 上轨
   if(CopyBuffer(g_BB_Handle,  0, 0, 3, bb_mid)   < 3) return; // 中轨（MA20）
   if(CopyBuffer(g_BB_Handle,  2, 0, 3, bb_lower) < 3) return; // 下轨
   if(CopyBuffer(g_ATR_Handle, 0, 0, 3, atr_data) < 3) return;

   double upper_1 = bb_upper[1];
   double mid_1   = bb_mid[1];
   double lower_1 = bb_lower[1];
   double atr_1   = atr_data[1];

   // 读取K1价格数据
   double close_1 = iClose(_Symbol, PERIOD_CURRENT, 1);
   double open_1  = iOpen(_Symbol,  PERIOD_CURRENT, 1);
   double high_1  = iHigh(_Symbol,  PERIOD_CURRENT, 1);
   double low_1   = iLow(_Symbol,   PERIOD_CURRENT, 1);

   // ============================================================
   // 2. ADX过滤（震荡市才做均值回归）
   // ============================================================
   if(Inp_Use_ADX_Filter)
     {
      double adx_buf[];
      ArraySetAsSeries(adx_buf, true);
      if(CopyBuffer(g_ADX_Handle, 0, 0, 3, adx_buf) < 3) return;
      double adx_1 = adx_buf[1];
      // ADX过高说明趋势太强，均值回归容易被打穿，跳过
      if(adx_1 > Inp_ADX_Max) return;
     }

   // ============================================================
   // 3. RSI辅助确认
   // ============================================================
   double rsi_1 = 50.0; // 默认中性值
   if(Inp_Use_RSI_Filter)
     {
      double rsi_buf[];
      ArraySetAsSeries(rsi_buf, true);
      if(CopyBuffer(g_RSI_Handle, 0, 0, 3, rsi_buf) < 3) return;
      rsi_1 = rsi_buf[1];
     }

   // ============================================================
   // 4. 时间过滤
   // ============================================================
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   // 周五提前平仓
   if(Inp_Friday_Close && dt.day_of_week == 5 && dt.hour >= Inp_Friday_Close_Hour)
     {
      CloseAllOrders();
      return;
     }

   // 日内强制平仓（不隔夜）
   if(Inp_Force_Close_EOD && dt.hour == Inp_Force_Close_Hour && dt.min >= Inp_Force_Close_Min)
     {
      CloseAllOrders();
      return;
     }

   // 交易时段过滤
   if(dt.hour < Inp_Trade_Start_Hour || dt.hour >= Inp_Trade_End_Hour) return;

   // ============================================================
   // 5. 点差过滤
   // ============================================================
   long cur_spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(cur_spread > Inp_Max_Spread) return;

   // ============================================================
   // 6. 最大回撤熔断
   // ============================================================
   double cur_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(cur_equity > g_MaxEquity) g_MaxEquity = cur_equity;
   if(g_MaxEquity > 0)
     {
      double dd_pct = (g_MaxEquity - cur_equity) / g_MaxEquity * 100.0;
      if(dd_pct >= Inp_Max_Drawdown_Pct)
        {
         if(!g_EA_Stopped)
           {
            g_EA_Stopped = true;
            Print("【熔断触发】账户回撤 ", DoubleToString(dd_pct, 2), "% 超过阈值 ", Inp_Max_Drawdown_Pct, "%，EA停止开仓");
           }
        }
      else
         g_EA_Stopped = false;
     }
   if(g_EA_Stopped) return;

   // ============================================================
   // 7. K线实体过滤（防止十字星和长影线开仓）
   // ============================================================
   double candle_range = high_1 - low_1;
   double candle_body  = MathAbs(close_1 - open_1);
   bool   body_ok      = (candle_range > 0) && (candle_body / candle_range >= Inp_Candle_Body_Ratio);

   // ============================================================
   // 8. 布林带均值回归信号判断
   // ============================================================

   // --- 做多信号：K1收盘价触碰或跌破布林带下轨 ---
   // 条件1：K1收盘价 <= 布林带下轨（价格已到达超卖区域）
   // 条件2：RSI处于超卖区域（可选）
   // 条件3：K线实体饱满（非十字星）
   // 条件4：当前无多头持仓（不重复开仓）
   bool buy_signal = (close_1 <= lower_1)
                     && (!Inp_Use_RSI_Filter || rsi_1 <= Inp_RSI_Oversold)
                     && body_ok
                     && (CountOrders(POSITION_TYPE_BUY) < Inp_Max_Orders);

   // --- 做空信号：K1收盘价触碰或突破布林带上轨 ---
   // 条件1：K1收盘价 >= 布林带上轨（价格已到达超买区域）
   // 条件2：RSI处于超买区域（可选）
   // 条件3：K线实体饱满（非十字星）
   // 条件4：当前无空头持仓（不重复开仓）
   bool sell_signal = (close_1 >= upper_1)
                      && (!Inp_Use_RSI_Filter || rsi_1 >= Inp_RSI_Overbought)
                      && body_ok
                      && (CountOrders(POSITION_TYPE_SELL) < Inp_Max_Orders);

   // ============================================================
   // 9. 执行开仓
   // ============================================================
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   // --- 执行做多 ---
   if(buy_signal)
     {
      double ask    = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl     = NormalizeDouble(ask - Inp_StopLoss_ATR * atr_1, digits);
      double tp;
      if(Inp_TP_Use_MidBand)
         tp = NormalizeDouble(mid_1, digits);   // 中轨止盈
      else
         tp = NormalizeDouble(ask + Inp_TakeProfit_ATR * atr_1, digits); // ATR止盈

      double sl_points = ask - sl;
      double lot = CalcLotSize(sl_points);
      OpenOrder(ORDER_TYPE_BUY, sl, tp, lot);
     }

   // --- 执行做空 ---
   if(sell_signal)
     {
      double bid    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double sl     = NormalizeDouble(bid + Inp_StopLoss_ATR * atr_1, digits);
      double tp;
      if(Inp_TP_Use_MidBand)
         tp = NormalizeDouble(mid_1, digits);   // 中轨止盈
      else
         tp = NormalizeDouble(bid - Inp_TakeProfit_ATR * atr_1, digits); // ATR止盈

      double sl_points = sl - bid;
      double lot = CalcLotSize(sl_points);
      OpenOrder(ORDER_TYPE_SELL, sl, tp, lot);
     }

   // ============================================================
   // 10. 图表状态显示
   // ============================================================
   string status = g_EA_Stopped ? "【熔断停止】" : "【运行中】";
   Comment("EA_BB_MeanReversion v1.0 ", status, "\n",
           "时间：", TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), "\n",
           "BB上轨：", DoubleToString(upper_1, digits),
           "  中轨：", DoubleToString(mid_1,   digits),
           "  下轨：", DoubleToString(lower_1, digits), "\n",
           "ATR：",    DoubleToString(atr_1,   digits),
           "  ADX过滤：", Inp_Use_ADX_Filter ? "开" : "关",
           "  RSI：",  DoubleToString(rsi_1, 1), "\n",
           "多头持仓：", CountOrders(POSITION_TYPE_BUY),
           "  空头持仓：", CountOrders(POSITION_TYPE_SELL),
           "  点差：", (string)cur_spread);
  }
//+------------------------------------------------------------------+
