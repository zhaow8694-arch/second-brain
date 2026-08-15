//+------------------------------------------------------------------+
//|                                  Apex_Rampage_V9_Origin.mq5      |
//|                     终极狂暴 V9.0-溯源版：100% 字节级复刻 12k 基因 |
//+------------------------------------------------------------------+
#property copyright "Asymmetric System - Apex V9 Origin"
#property version   "9.00"
#property strict

#include <Trade\Trade.mqh>
CTrade tradeA, tradeB, tradeP;

//--- 核心参数 (严格锁定 V3 的原始参数组合)
input string   _Config_         = "--- 资金与核心参数 ---";
input double   InpRiskPercent   = 5.0;       // 单次总风险 5%
input int      InpAtrPeriod     = 14;        
input double   InpSlMultiplier  = 0.8;       // 极窄初始止损
input int      InpBreakPeriod   = 10;        // 敏锐突破周期

input string   _Twin_           = "--- 双子星逻辑 ---";
input double   InpTpMultiplierA = 1.5;       // 订单A快速止盈
input double   InpBeMultiplierB = 0.8;       // 订单B平保触发
input double   InpTrailMultiplierB= 2.5;     // 原始 2.5 ATR 抗洗盘追踪

input string   _Pyramid_        = "--- 原始狂暴引擎 ---";
input bool     InpEnablePyramid = true;      // 开启加仓
input double   InpPyramidGap    = 1.5;       // 原始 1.5 ATR 间距
input int      InpMaxAddons     = 5;         // 最大加仓 5 次

//--- 全局变量
int handle_atr;
double atr_buffer[];
double base_lot_size = 0;

int OnInit() {
   handle_atr = iATR(_Symbol, _Period, InpAtrPeriod);
   ArraySetAsSeries(atr_buffer, true);
   tradeA.SetExpertMagicNumber(1001);
   tradeB.SetExpertMagicNumber(1002);
   tradeP.SetExpertMagicNumber(1003);
   return(INIT_SUCCEEDED);
}

void OnTick() {
   // 没有任何休市或点差拦截，全速裸奔！
   if(CopyBuffer(handle_atr, 0, 0, 2, atr_buffer) <= 0) return;
   
   double current_atr = atr_buffer[0];
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   double high_array[], low_array[];
   ArraySetAsSeries(high_array, true);
   ArraySetAsSeries(low_array, true);
   CopyHigh(_Symbol, _Period, 1, InpBreakPeriod, high_array);
   CopyLow(_Symbol, _Period, 1, InpBreakPeriod, low_array);
   double highest_high = high_array[ArrayMaximum(high_array)];
   double lowest_low = low_array[ArrayMinimum(low_array)];

   int my_positions = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--) {
      if(PositionGetSymbol(i) == _Symbol) my_positions++;
   }

   // 突破入场 (完全还原 V3 第一版逻辑)
   if(my_positions == 0) {
      double sl_distance = current_atr * InpSlMultiplier;
      double risk_money_per_trade = AccountInfoDouble(ACCOUNT_BALANCE) * (InpRiskPercent / 100.0) / 2.0;
      double tick_val = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tick_sz = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      
      base_lot_size = NormalizeDouble(risk_money_per_trade / (sl_distance / tick_sz * tick_val), 2);
      base_lot_size = MathMax(base_lot_size, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN));

      if(ask > highest_high) {
         double sl = bid - sl_distance;
         double tp_A = ask + (current_atr * InpTpMultiplierA);
         tradeA.Buy(base_lot_size, _Symbol, ask, sl, tp_A, "Twin A: Cover");
         tradeB.Buy(base_lot_size, _Symbol, ask, sl, 0, "Twin B: Base");
      } else if(bid < lowest_low) {
         double sl = ask + sl_distance;
         double tp_A = bid - (current_atr * InpTpMultiplierA);
         tradeA.Sell(base_lot_size, _Symbol, bid, sl, tp_A, "Twin A: Cover");
         tradeB.Sell(base_lot_size, _Symbol, bid, sl, 0, "Twin B: Base");
      }
   } else {
      ManageApexSystemOrigin(current_atr, ask, bid);
   }
}

void ManageApexSystemOrigin(double atr, double ask, double bid) {
   int runner_count = 0;
   int addon_count = 0;
   double last_entry_buy = 0;
   double last_entry_sell = 999999;
   long current_trend_type = -1;

   // 第一次扫描：统计状态 (100% 还原 V3 寻找边界的逻辑)
   for(int i = PositionsTotal() - 1; i >= 0; i--) {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      long magic = PositionGetInteger(POSITION_MAGIC);
      if(magic != 1002 && magic != 1003) continue;

      long type = PositionGetInteger(POSITION_TYPE);
      current_trend_type = type;
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      
      if(magic == 1002) runner_count++;
      if(magic == 1003) addon_count++;

      if(type == POSITION_TYPE_BUY && open_price > last_entry_buy) last_entry_buy = open_price;
      if(type == POSITION_TYPE_SELL && open_price < last_entry_sell) last_entry_sell = open_price;
   }

   // ！！！V3 独有的神级断路器：底仓没了直接不管加仓单 ！！！
   if(runner_count == 0) return;

   double trail_distance = atr * InpTrailMultiplierB; 
   double pyramid_distance = atr * InpPyramidGap;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   // 第二次扫描：遍历执行保护与加仓 (重现嵌套 BUG 链式反应)
   for(int i = PositionsTotal() - 1; i >= 0; i--) {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      long magic = PositionGetInteger(POSITION_MAGIC);
      if(magic != 1002 && magic != 1003) continue;

      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double current_sl = PositionGetDouble(POSITION_SL);
      double current_price = PositionGetDouble(POSITION_PRICE_CURRENT);
      long type = PositionGetInteger(POSITION_TYPE);

      if(type == POSITION_TYPE_BUY) {
         // 1. 光速推平保
         if(magic == 1002 && current_price - open_price > atr * InpBeMultiplierB && current_sl < open_price) {
            tradeB.PositionModify(ticket, open_price + 10 * point, 0);
         }

         // 2. 统一追踪止损
         if(current_sl >= open_price || magic == 1003) {
            double new_sl = current_price - trail_distance;
            if(new_sl > current_sl) tradeB.PositionModify(ticket, new_sl, 0);
         }

         // 3. 狂暴加仓 (写在循环内，重现毫秒级同 Tick 爆发)
         if(InpEnablePyramid && addon_count < InpMaxAddons && current_sl >= open_price) {
            if(ask > last_entry_buy + pyramid_distance) {
               tradeP.Buy(base_lot_size, _Symbol, ask, ask - trail_distance, 0, "Pyramid Add Long");
               last_entry_buy = ask; 
            }
         }
      }
      else if(type == POSITION_TYPE_SELL) {
         // 1. 推平保
         if(magic == 1002 && open_price - current_price > atr * InpBeMultiplierB && (current_sl > open_price || current_sl == 0)) {
            tradeB.PositionModify(ticket, open_price - 10 * point, 0);
         }

         // 2. 追踪止损
         if((current_sl <= open_price && current_sl != 0) || magic == 1003) {
            double new_sl = current_price + trail_distance;
            if(new_sl < current_sl || current_sl == 0) tradeB.PositionModify(ticket, new_sl, 0);
         }

         // 3. 狂暴加仓
         if(InpEnablePyramid && addon_count < InpMaxAddons && current_sl <= open_price && current_sl != 0) {
            if(bid < last_entry_sell - pyramid_distance) {
               tradeP.Sell(base_lot_size, _Symbol, bid, bid + trail_distance, 0, "Pyramid Add Short");
               last_entry_sell = bid; 
            }
         }
      }
   }
}