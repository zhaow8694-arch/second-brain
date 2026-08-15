//+------------------------------------------------------------------+
//|                                             EA_2560_Strategy.mq5 |
//|                                          2560战法多空双向版 v1.0  |
//|                                                                   |
//|  策略逻辑：                                                        |
//|  核心指标：MA25（价格趋势线）+ VOL5/VOL60（均量线）               |
//|  多头：价格>MA25，VOL5上穿VOL60开多；回踩MA25缩量加仓             |
//|  空头：价格<MA25，VOL5上穿VOL60开空；反弹MA25缩量加仓             |
//|  离场：异常放量诱多/诱空 或 趋势破坏（价格穿越MA25）              |
//+------------------------------------------------------------------+
#property copyright   "2560 Strategy"
#property version     "1.00"
#property description "2560战法多空双向版 EA - 适用于黄金/原油/股指/加密货币"
#property strict

//+------------------------------------------------------------------+
//|                      外部输入参数                                  |
//+------------------------------------------------------------------+

// ---- 核心指标参数 ----
input group              "=== 核心指标参数 ==="
input int    Inp_MA_Period           = 25;      // MA25均线周期
input int    Inp_Vol5_Period         = 5;       // 短期均量线周期
input int    Inp_Vol60_Period        = 60;      // 长期均量线周期

// ---- 量化阈值参数 ----
input group              "=== 量化阈值参数 ==="
input double Inp_Vol_Sticky_Ratio    = 0.15;   // 均量线粘合阈值（两线差值占比，默认15%）
input double Inp_Price_Pullback_ATR  = 1.0;    // 回踩MA25的ATR距离阈值（默认1倍ATR）
input double Inp_Abnormal_Vol_Ratio  = 2.5;    // 异常放量倍数阈值（默认VOL60的2.5倍）
input double Inp_Candle_Body_Ratio   = 0.6;    // K线实体占比过滤阈值（默认60%）

// ---- 资金管理参数 ----
input group              "=== 资金管理参数 ==="
input double Inp_Risk_Percent        = 2.0;    // 单笔风险比例（占账户余额%，0=使用固定手数）
input double Inp_Lot_Size            = 0.1;    // 固定开仓手数（Risk_Percent=0时生效）
input int    Inp_Max_Orders          = 3;      // 同向最大持仓单数（含加仓）

// ---- 止损止盈参数 ----
input group              "=== 止损止盈参数 ==="
input double Inp_StopLoss_ATR        = 2.0;    // 初始止损ATR倍数
input double Inp_TakeProfit_ATR      = 4.0;    // 初始止盈ATR倍数
input double Inp_Trailing_Start_ATR  = 1.5;    // 启动移动止损的盈利ATR倍数
input double Inp_Trailing_Step_ATR   = 0.5;    // 移动止损步进ATR倍数

// ---- 过滤与风控参数 ----
input group              "=== 过滤与风控参数 ==="
input int    Inp_Magic_Number        = 2560001; // 订单魔术数字
input int    Inp_Trade_Start_Hour    = 8;       // 允许交易开始小时（服务器时间）
input int    Inp_Trade_End_Hour      = 22;      // 允许交易结束小时（服务器时间）
input bool   Inp_Friday_Close        = true;    // 是否开启周五强制平仓
input int    Inp_Friday_Close_Hour   = 21;      // 周五强制平仓触发小时
input int    Inp_Max_Spread          = 30;      // 最大允许点差（Points）
input double Inp_Max_Drawdown_Pct    = 15.0;    // 最大回撤熔断阈值（%）

//+------------------------------------------------------------------+
//|                      全局变量                                      |
//+------------------------------------------------------------------+
int      g_MA25_Handle  = INVALID_HANDLE;  // MA25指标句柄
int      g_ATR_Handle   = INVALID_HANDLE;  // ATR指标句柄
datetime g_LastBarTime  = 0;               // 上一根K线时间（OnBar机制）
double   g_MaxEquity    = 0;               // 账户历史最高净值
bool     g_EA_Stopped   = false;           // 熔断标志

//+------------------------------------------------------------------+
//| EA初始化                                                           |
//+------------------------------------------------------------------+
int OnInit()
  {
   // 创建MA25句柄
   g_MA25_Handle = iMA(_Symbol, PERIOD_CURRENT, Inp_MA_Period, 0, MODE_SMA, PRICE_CLOSE);
   if(g_MA25_Handle == INVALID_HANDLE)
     {
      Print("错误：创建MA25指标句柄失败，错误码=", GetLastError());
      return INIT_FAILED;
     }

   // 创建ATR(14)句柄
   g_ATR_Handle = iATR(_Symbol, PERIOD_CURRENT, 14);
   if(g_ATR_Handle == INVALID_HANDLE)
     {
      Print("错误：创建ATR指标句柄失败，错误码=", GetLastError());
      return INIT_FAILED;
     }

   // 初始化OnBar时间戳
   g_LastBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);

   // 初始化最高净值
   g_MaxEquity = AccountInfoDouble(ACCOUNT_EQUITY);

   Print("EA_2560_Strategy 初始化成功 | 品种=", _Symbol,
         " | 周期=", EnumToString(PERIOD_CURRENT),
         " | 魔术数字=", Inp_Magic_Number);
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
//| EA释放                                                             |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   if(g_MA25_Handle != INVALID_HANDLE) { IndicatorRelease(g_MA25_Handle); g_MA25_Handle = INVALID_HANDLE; }
   if(g_ATR_Handle  != INVALID_HANDLE) { IndicatorRelease(g_ATR_Handle);  g_ATR_Handle  = INVALID_HANDLE; }
   Print("EA_2560_Strategy 已卸载 | 原因=", reason);
  }

//+------------------------------------------------------------------+
//| 主Tick函数                                                         |
//+------------------------------------------------------------------+
void OnTick()
  {
   // ---- 1. OnBar机制：只在新K线开盘时执行 ----
   if(!IsNewBar()) return;

   // ---- 2. 读取指标数据 ----
   double ma25_buf[3], atr_buf[3];
   if(CopyBuffer(g_MA25_Handle, 0, 0, 3, ma25_buf) < 3) return;
   if(CopyBuffer(g_ATR_Handle,  0, 0, 3, atr_buf)  < 3) return;
   ArraySetAsSeries(ma25_buf, true);
   ArraySetAsSeries(atr_buf,  true);

   double ma25_1  = ma25_buf[1];                                        // K1的MA25值
   double ma25_2  = ma25_buf[2];                                        // K2的MA25值
   double atr_1   = atr_buf[1];                                         // K1的ATR值
   if(atr_1 <= 0) return;

   double vol5_1  = GetVolMA(Inp_Vol5_Period,  1);                      // K1的5日均量
   double vol5_2  = GetVolMA(Inp_Vol5_Period,  2);                      // K2的5日均量
   double vol60_1 = GetVolMA(Inp_Vol60_Period, 1);                      // K1的60日均量
   double vol60_2 = GetVolMA(Inp_Vol60_Period, 2);                      // K2的60日均量
   double vol_k1  = (double)iVolume(_Symbol, PERIOD_CURRENT, 1);       // K1单根成交量
   if(vol60_1 <= 0) return;

   double close_1 = iClose(_Symbol, PERIOD_CURRENT, 1);
   double close_2 = iClose(_Symbol, PERIOD_CURRENT, 2);
   double open_1  = iOpen(_Symbol,  PERIOD_CURRENT, 1);
   double high_1  = iHigh(_Symbol,  PERIOD_CURRENT, 1);
   double low_1   = iLow(_Symbol,   PERIOD_CURRENT, 1);

   // ---- 3. 获取时间结构 ----
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   // ---- 4. 周五强制平仓（在时段过滤之前执行）----
   if(Inp_Friday_Close && dt.day_of_week == 5 && dt.hour >= Inp_Friday_Close_Hour)
     {
      CloseAllOrders();
      Comment("EA_2560 | 周五强制平仓已执行");
      return;
     }

   // ---- 5. 交易时段过滤 ----
   if(dt.hour < Inp_Trade_Start_Hour || dt.hour >= Inp_Trade_End_Hour)
      return;

   // ---- 6. 最大点差过滤 ----
   long cur_spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(cur_spread > Inp_Max_Spread) return;

   // ---- 7. 最大回撤熔断 ----
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
            Print("⚠️ 熔断触发！回撤=", DoubleToString(dd_pct, 2), "% 超过阈值=",
                  Inp_Max_Drawdown_Pct, "%，EA停止开仓");
           }
         Comment("EA_2560 ⚠️ 熔断停止 | 回撤=", DoubleToString(dd_pct, 2), "%");
         return;
        }
     }
   if(g_EA_Stopped) return;

   // ---- 8. K线实体占比过滤 ----
   double candle_range = high_1 - low_1;
   double candle_body  = MathAbs(close_1 - open_1);
   bool   body_ok      = (candle_range > 0) && (candle_body / candle_range >= Inp_Candle_Body_Ratio);

   // ---- 9. 预计算信号条件 ----
   // 均量线粘合（趋势确认/加仓信号）
   bool vol_sticky    = (MathAbs(vol5_1 - vol60_1) / vol60_1 < Inp_Vol_Sticky_Ratio);
   // 价格回踩MA25附近
   bool near_ma25     = (MathAbs(close_1 - ma25_1) <= Inp_Price_Pullback_ATR * atr_1);
   // 量能金叉（VOL5上穿VOL60）
   bool vol_cross_up  = (vol5_2 <= vol60_2) && (vol5_1 > vol60_1);
   // 异常放量（诱多/诱空信号）
   bool vol_abnormal  = (vol5_1 < vol60_1) && (vol_k1 > Inp_Abnormal_Vol_Ratio * vol60_1);
   // 加仓量能条件：均量粘合 或 VOL5>VOL60但单根缩量
   bool vol_add_ok    = vol_sticky || (vol5_1 > vol60_1 && vol_k1 < vol60_1);

   // ---- 10. 统计持仓 ----
   int buy_count  = CountOrders(POSITION_TYPE_BUY);
   int sell_count = CountOrders(POSITION_TYPE_SELL);
   int digits     = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   // ---- 11. 移动止损（每根K线更新）----
   UpdateTrailingStop(atr_1);

   // ============================================================
   //  多头逻辑（价格在MA25上方）
   // ============================================================
   if(close_1 > ma25_1)
     {
      // 多空切换：平掉所有空单
      if(sell_count > 0)
        {
         CloseOrdersByType(POSITION_TYPE_SELL);
         sell_count = 0;
        }

      // 放量离场：异常放量诱多，平掉所有多单
      if(vol_abnormal && buy_count > 0)
        {
         CloseOrdersByType(POSITION_TYPE_BUY);
         Print("多头放量离场：检测到诱多信号，平掉所有多单");
         return;
        }

      // 做多开仓：价格突破MA25 + 量能金叉 + 实体过滤 + 无持仓
      if(buy_count == 0 && vol_cross_up && body_ok &&
         close_2 < ma25_2 && close_1 > ma25_1)
        {
         double sl = NormalizeDouble(close_1 - Inp_StopLoss_ATR  * atr_1, digits);
         double tp = NormalizeDouble(close_1 + Inp_TakeProfit_ATR * atr_1, digits);
         if(OpenOrder(ORDER_TYPE_BUY, sl, tp))
            Print("做多开仓 | 价格突破MA25 + 量能金叉 | close=", close_1, " MA25=", ma25_1);
        }
      // 做多加仓：回踩MA25附近 + 量能条件满足 + 持仓未满
      else if(buy_count > 0 && buy_count < Inp_Max_Orders && near_ma25 && vol_add_ok)
        {
         double sl = NormalizeDouble(close_1 - Inp_StopLoss_ATR  * atr_1, digits);
         double tp = NormalizeDouble(close_1 + Inp_TakeProfit_ATR * atr_1, digits);
         if(OpenOrder(ORDER_TYPE_BUY, sl, tp))
            Print("做多加仓 | 回踩MA25缩量 | 当前持仓=", buy_count + 1, "/", Inp_Max_Orders);
        }
     }

   // ============================================================
   //  空头逻辑（价格在MA25下方）
   // ============================================================
   else if(close_1 < ma25_1)
     {
      // 多空切换：平掉所有多单
      if(buy_count > 0)
        {
         CloseOrdersByType(POSITION_TYPE_BUY);
         buy_count = 0;
        }

      // 放量离场：异常放量诱空，平掉所有空单
      if(vol_abnormal && sell_count > 0)
        {
         CloseOrdersByType(POSITION_TYPE_SELL);
         Print("空头放量离场：检测到诱空信号，平掉所有空单");
         return;
        }

      // 做空开仓：价格跌破MA25 + 量能金叉 + 实体过滤 + 无持仓
      if(sell_count == 0 && vol_cross_up && body_ok &&
         close_2 > ma25_2 && close_1 < ma25_1)
        {
         double sl = NormalizeDouble(close_1 + Inp_StopLoss_ATR  * atr_1, digits);
         double tp = NormalizeDouble(close_1 - Inp_TakeProfit_ATR * atr_1, digits);
         if(OpenOrder(ORDER_TYPE_SELL, sl, tp))
            Print("做空开仓 | 价格跌破MA25 + 量能金叉 | close=", close_1, " MA25=", ma25_1);
        }
      // 做空加仓：反弹至MA25附近 + 量能条件满足 + 持仓未满
      else if(sell_count > 0 && sell_count < Inp_Max_Orders && near_ma25 && vol_add_ok)
        {
         double sl = NormalizeDouble(close_1 + Inp_StopLoss_ATR  * atr_1, digits);
         double tp = NormalizeDouble(close_1 - Inp_TakeProfit_ATR * atr_1, digits);
         if(OpenOrder(ORDER_TYPE_SELL, sl, tp))
            Print("做空加仓 | 反弹MA25缩量 | 当前持仓=", sell_count + 1, "/", Inp_Max_Orders);
        }
     }

   // ---- 状态显示 ----
   Comment("EA_2560_Strategy 运行中",
           "\n品种: ", _Symbol,
           "\n时间: ", TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES),
           "\n多单: ", buy_count, "  空单: ", sell_count,
           "\nMA25: ", DoubleToString(ma25_1, digits),
           "\nATR:  ", DoubleToString(atr_1, digits),
           "\nVOL5: ", DoubleToString(vol5_1, 0), "  VOL60: ", DoubleToString(vol60_1, 0),
           "\n净值: ", DoubleToString(cur_equity, 2));
  }

//+------------------------------------------------------------------+
//| 检测新K线（OnBar机制）                                             |
//+------------------------------------------------------------------+
bool IsNewBar()
  {
   datetime cur_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(cur_bar == 0) return false;
   if(cur_bar != g_LastBarTime)
     {
      g_LastBarTime = cur_bar;
      return true;
     }
   return false;
  }

//+------------------------------------------------------------------+
//| 手动计算成交量简单移动平均                                          |
//+------------------------------------------------------------------+
double GetVolMA(int period, int shift)
  {
   if(period <= 0) return 0;
   double sum = 0;
   for(int i = shift; i < shift + period; i++)
      sum += (double)iVolume(_Symbol, PERIOD_CURRENT, i);
   return sum / period;
  }

//+------------------------------------------------------------------+
//| 统计本EA指定方向的持仓数量                                          |
//+------------------------------------------------------------------+
int CountOrders(ENUM_POSITION_TYPE pos_type)
  {
   int count = 0;
   for(int i = 0; i < PositionsTotal(); i++)
     {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != Inp_Magic_Number) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) == pos_type) count++;
     }
   return count;
  }

//+------------------------------------------------------------------+
//| 计算开仓手数（固定风险比例）                                        |
//+------------------------------------------------------------------+
double CalcLotSize(double sl_distance)
  {
   // 若未启用风险比例，使用固定手数
   if(Inp_Risk_Percent <= 0 || sl_distance <= 0) return Inp_Lot_Size;

   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick_value <= 0 || tick_size <= 0) return Inp_Lot_Size;

   double balance    = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_money = balance * Inp_Risk_Percent / 100.0;
   double lot        = risk_money / (sl_distance / tick_size * tick_value);

   double min_lot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lot = MathFloor(lot / lot_step) * lot_step;
   lot = MathMax(lot, min_lot);
   lot = MathMin(lot, max_lot);
   return lot;
  }

//+------------------------------------------------------------------+
//| 发送开仓订单                                                       |
//+------------------------------------------------------------------+
bool OpenOrder(ENUM_ORDER_TYPE order_type, double sl_price, double tp_price)
  {
   double price  = (order_type == ORDER_TYPE_BUY)
                   ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                   : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double sl_dist = MathAbs(price - sl_price);
   double lot    = CalcLotSize(sl_dist);

   MqlTradeRequest req = {};
   MqlTradeResult  res = {};
   req.action    = TRADE_ACTION_DEAL;
   req.symbol    = _Symbol;
   req.volume    = lot;
   req.type      = order_type;
   req.price     = NormalizeDouble(price, digits);
   req.sl        = NormalizeDouble(sl_price, digits);
   req.tp        = NormalizeDouble(tp_price, digits);
   req.deviation = 10;
   req.magic     = Inp_Magic_Number;
   req.comment   = "EA_2560";
   req.type_filling = ORDER_FILLING_IOC;

   bool ok = OrderSend(req, res);
   if(!ok || res.retcode != TRADE_RETCODE_DONE)
      Print("开仓失败 | 类型=", EnumToString(order_type),
            " | 手数=", lot,
            " | 返回码=", res.retcode,
            " | 说明=", res.comment);
   return (ok && res.retcode == TRADE_RETCODE_DONE);
  }

//+------------------------------------------------------------------+
//| 平掉指定方向的所有本EA订单                                          |
//+------------------------------------------------------------------+
void CloseOrdersByType(ENUM_POSITION_TYPE pos_type)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != Inp_Magic_Number) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) != pos_type) continue;

      MqlTradeRequest req = {};
      MqlTradeResult  res = {};
      req.action    = TRADE_ACTION_DEAL;
      req.position  = ticket;
      req.symbol    = _Symbol;
      req.volume    = PositionGetDouble(POSITION_VOLUME);
      req.type      = (pos_type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
      req.price     = (req.type == ORDER_TYPE_SELL)
                      ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                      : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      req.deviation = 10;
      req.magic     = Inp_Magic_Number;
      req.type_filling = ORDER_FILLING_IOC;
      OrderSend(req, res);
     }
  }

//+------------------------------------------------------------------+
//| 平掉所有本EA订单（周五平仓/熔断用）                                 |
//+------------------------------------------------------------------+
void CloseAllOrders()
  {
   CloseOrdersByType(POSITION_TYPE_BUY);
   CloseOrdersByType(POSITION_TYPE_SELL);
  }

//+------------------------------------------------------------------+
//| 移动止损（每根新K线更新所有持仓的止损）                             |
//+------------------------------------------------------------------+
void UpdateTrailingStop(double atr_val)
  {
   if(Inp_Trailing_Start_ATR <= 0 || atr_val <= 0) return;
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   for(int i = 0; i < PositionsTotal(); i++)
     {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != Inp_Magic_Number) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      ENUM_POSITION_TYPE pos_type  = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double cur_sl     = PositionGetDouble(POSITION_SL);
      double cur_tp     = PositionGetDouble(POSITION_TP);
      double cur_price  = (pos_type == POSITION_TYPE_BUY)
                          ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                          : SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      double profit_dist = (pos_type == POSITION_TYPE_BUY)
                           ? cur_price - open_price
                           : open_price - cur_price;

      // 盈利未达到启动阈值，不移动
      if(profit_dist < Inp_Trailing_Start_ATR * atr_val) continue;

      double new_sl = 0;
      if(pos_type == POSITION_TYPE_BUY)
        {
         new_sl = NormalizeDouble(cur_price - Inp_Trailing_Step_ATR * atr_val, digits);
         if(new_sl <= cur_sl) continue; // 新止损不优于旧止损，跳过
        }
      else
        {
         new_sl = NormalizeDouble(cur_price + Inp_Trailing_Step_ATR * atr_val, digits);
         if(new_sl >= cur_sl && cur_sl > 0) continue; // 新止损不优于旧止损，跳过
        }

      // 修改止损
      MqlTradeRequest req = {};
      MqlTradeResult  res = {};
      req.action   = TRADE_ACTION_SLTP;
      req.position = ticket;
      req.symbol   = _Symbol;
      req.sl       = new_sl;
      req.tp       = cur_tp;
      req.magic    = Inp_Magic_Number;
      OrderSend(req, res);
     }
  }
//+------------------------------------------------------------------+
