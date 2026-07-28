//+------------------------------------------------------------------+
//|                                  Apex_Pyramid_Twin_Breakout.mq5 |
//|                     终极狂暴 V3：双子星掩护 + 零风险金字塔无限加仓 |
//|                     V3.2 猎杀逻辑地雷：根除嵌套循环焦点错乱        |
//+------------------------------------------------------------------+
#property copyright "Asymmetric System - Apex V3.2"
#property version   "3.20"

#include <Trade\Trade.mqh>
CTrade tradeA; // 掩护单 (打短线回血)
CTrade tradeB; // 趋势单基底 (摸奖单)
CTrade tradeP; // 金字塔加仓单 (利润再投资)

//--- 激进资金与基础参数
input string   _Config_         = "--- 资金与核心参数 ---";
input double   InpRiskPercent   = 2.0;       // 【指令二修改】单次总风险 2% (原5.0降级)
input int      InpAtrPeriod     = 14;        
input double   InpSlMultiplier  = 2.0;       // 【指令二修改】止损拓宽至2.0倍ATR (原0.8)
input int      InpBreakPeriod   = 10;        // 敏锐突破周期 (10根K线)

//--- 双子星参数
input string   _Twin_           = "--- 双子星订单管理 ---";
input double   InpTpMultiplierA = 1.5;       // 订单A：快速止盈回血
input double   InpBeMultiplierB = 0.8;       // 订单B：光速推平保触发距离
input double   InpTrailMultiplierB= 2.5;     // 趋势追踪止损距离 (稍收紧以保护加仓)

//--- 狂暴金字塔参数
input string   _Pyramid_        = "--- 金字塔加仓引擎 ---";
input bool     InpEnablePyramid = true;      // 是否开启狂暴加仓
input double   InpPyramidGap    = 1.5;       // 每隔多少倍 ATR 加仓一次
input int      InpMaxAddons     = 5;         // 最大允许加仓次数 (防保证金耗尽)

//--- 全局变量
int handle_atr;
double atr_buffer[];

// 【指令一新增】ADX 动能雷达句柄
int handle_adx;
double adx_buffer[];

int OnInit()
  {
   handle_atr = iATR(_Symbol, _Period, InpAtrPeriod);
   ArraySetAsSeries(atr_buffer, true);
   
   // 【指令一新增】ADX 指标初始化（参数固定为14）
   handle_adx = iADX(_Symbol, _Period, 14);
   ArraySetAsSeries(adx_buffer, true);
   
   tradeA.SetExpertMagicNumber(1001); // 掩护单
   tradeB.SetExpertMagicNumber(1002); // 摸奖底仓
   tradeP.SetExpertMagicNumber(1003); // 金字塔加仓单
   return(INIT_SUCCEEDED);
  }

void OnTick()
  {
   if(CopyBuffer(handle_atr, 0, 0, 2, atr_buffer) <= 0) return;
   double current_atr = atr_buffer[0];
   
   // 【指令一新增】实时获取 ADX 主线数值
   if(CopyBuffer(handle_adx, 0, 0, 1, adx_buffer) <= 0) return;
   double current_adx = adx_buffer[0];
   
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   double highest_high = 0, lowest_low = 0;
   double high_array[], low_array[];
   ArraySetAsSeries(high_array, true);
   ArraySetAsSeries(low_array, true);
   CopyHigh(_Symbol, _Period, 1, InpBreakPeriod, high_array);
   CopyLow(_Symbol, _Period, 1, InpBreakPeriod, low_array);
   highest_high = high_array[ArrayMaximum(high_array)];
   lowest_low = low_array[ArrayMinimum(low_array)];

   int total_positions = PositionsTotal();
   int my_positions = 0;
   
   // 统计当前品种属于本系统的单子
   for(int i = 0; i < total_positions; i++)
     {
      if(PositionGetSymbol(i) == _Symbol) my_positions++;
     }

   // 1. 发射双子星底仓 (无持仓时)
   if(my_positions == 0)
     {
      double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double sl_distance = current_atr * InpSlMultiplier; 
      
      double risk_money_per_trade = AccountInfoDouble(ACCOUNT_BALANCE) * (InpRiskPercent / 100.0) / 2.0;
      double base_lot_size = NormalizeDouble(risk_money_per_trade / (sl_distance / tick_size * tick_value), 2);
      double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      if(base_lot_size < min_lot) base_lot_size = min_lot; 

      // 【指令一修改】开仓条件增加 ADX > 24.0 动能过滤
      if(ask > highest_high && current_adx > 24.0)
        {
         double sl = bid - sl_distance;
         double tp_A = ask + (current_atr * InpTpMultiplierA);
         tradeA.Buy(base_lot_size, _Symbol, ask, sl, tp_A, "Twin A: Cover");
         tradeB.Buy(base_lot_size, _Symbol, ask, sl, 0, "Twin B: Base");
        }
      // 【指令一修改】开仓条件增加 ADX > 24.0 动能过滤
      else if(bid < lowest_low && current_adx > 24.0)
        {
         double sl = ask + sl_distance;
         double tp_A = bid - (current_atr * InpTpMultiplierA);
         tradeA.Sell(base_lot_size, _Symbol, bid, sl, tp_A, "Twin A: Cover");
         tradeB.Sell(base_lot_size, _Symbol, bid, sl, 0, "Twin B: Base");
        }
     }
   // 2. 趋势管理与金字塔加仓 (已有持仓时)
   else 
     {
      ManageApexSystem(current_atr, ask, bid);
     }
  }

//+------------------------------------------------------------------+
//| 终极管理系统：推平保 -> 触发加仓 -> 统一追踪止损                      |
//+------------------------------------------------------------------+
void ManageApexSystem(double atr, double ask, double bid)
  {
   // 【V3.2重构】前置提取：在主循环开始前，先提取1002底仓手数
   double current_base_lot = 0;
   long base_position_type = -1; // 记录底仓方向：0=多, 1=空
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != 1002) continue;
      
      current_base_lot = PositionGetDouble(POSITION_VOLUME);
      base_position_type = PositionGetInteger(POSITION_TYPE);
      break; // 找到第一个1002底仓即可
     }
   
   int runner_count = 0;
   int addon_count = 0;
   double last_entry_buy = 0;
   double last_entry_sell = 999999;
   long current_trend_type = -1; // 0 for Buy, 1 for Sell

   // 扫描当前所有趋势单 (底仓 1002 和 加仓单 1003)
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      
      long magic = PositionGetInteger(POSITION_MAGIC);
      if(magic != 1002 && magic != 1003) continue; // 忽略打短线的 1001

      long type = PositionGetInteger(POSITION_TYPE);
      current_trend_type = type;
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      
      if(magic == 1002) runner_count++;
      if(magic == 1003) addon_count++;

      // 寻找最后一次开仓的价格 (用于计算加仓间距)
      if(type == POSITION_TYPE_BUY && open_price > last_entry_buy) last_entry_buy = open_price;
      if(type == POSITION_TYPE_SELL && open_price < last_entry_sell) last_entry_sell = open_price;
     }

   // 如果底仓已经阵亡，不执行任何金字塔操作
   if(runner_count == 0) return;

   double trail_distance = atr * InpTrailMultiplierB; 
   double pyramid_distance = atr * InpPyramidGap;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   // ================= 主管理循环：推平保 + 追踪止损 + 加仓 =================
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      long magic = PositionGetInteger(POSITION_MAGIC);
      if(magic != 1002 && magic != 1003) continue;

      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double current_sl = PositionGetDouble(POSITION_SL);
      double current_price = PositionGetDouble(POSITION_PRICE_CURRENT);
      long type = PositionGetInteger(POSITION_TYPE);

      // --- 多头逻辑 ---
      if(type == POSITION_TYPE_BUY)
        {
         // 1. 光速推平保 (只针对 1002 底仓)
         if(magic == 1002 && current_price - open_price > atr * InpBeMultiplierB && current_sl < open_price)
           {
            tradeB.PositionModify(ticket, open_price + 10 * point, 0);
            Print(">> 底仓已平保，子弹上膛！");
           }

         // 2. 统一追踪止损 (保护底仓和所有加仓单)
         if(current_sl >= open_price || magic == 1003) 
           {
            double new_sl = current_price - trail_distance;
            if(new_sl > current_sl) tradeB.PositionModify(ticket, new_sl, 0);
           }

         // 3. 狂暴金字塔加仓触发
         if(InpEnablePyramid && addon_count < InpMaxAddons && current_sl >= open_price)
           {
            // 如果当前价格 涨过了 [最后一单开仓价 + 设定的加仓间距]
            if(ask > last_entry_buy + pyramid_distance)
              {
               // 【V3.2重构】直接调用前置缓存的底仓手数，无嵌套循环
               if(current_base_lot > 0)
                 {
                  tradeP.Buy(current_base_lot, _Symbol, ask, ask - trail_distance, 0, "Pyramid Add Long");
                  Print(">> 狂暴加仓(多)！当前加仓层级: ", addon_count + 1, " 手数: ", current_base_lot);
                  last_entry_buy = ask; // 更新最后开仓价，防止同一价格反复加仓
                 }
              }
           }
        }

      // --- 空头逻辑 ---
      else if(type == POSITION_TYPE_SELL)
        {
         // 1. 光速推平保
         if(magic == 1002 && open_price - current_price > atr * InpBeMultiplierB && (current_sl > open_price || current_sl == 0))
           {
            tradeB.PositionModify(ticket, open_price - 10 * point, 0);
            Print(">> 底仓已平保，子弹上膛！");
           }

         // 2. 统一追踪止损
         if(current_sl <= open_price && current_sl != 0 || magic == 1003)
           {
            double new_sl = current_price + trail_distance;
            if(new_sl < current_sl || current_sl == 0) tradeB.PositionModify(ticket, new_sl, 0);
           }

         // 3. 狂暴金字塔加仓触发
         if(InpEnablePyramid && addon_count < InpMaxAddons && current_sl <= open_price && current_sl != 0)
           {
            if(bid < last_entry_sell - pyramid_distance)
              {
               // 【V3.2重构】直接调用前置缓存的底仓手数，无嵌套循环
               if(current_base_lot > 0)
                 {
                  tradeP.Sell(current_base_lot, _Symbol, bid, bid + trail_distance, 0, "Pyramid Add Short");
                  Print(">> 狂暴加仓(空)！当前加仓层级: ", addon_count + 1, " 手数: ", current_base_lot);
                  last_entry_sell = bid; 
                 }
              }
           }
        }
     }
  }
//+------------------------------------------------------------------+
