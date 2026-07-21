//+------------------------------------------------------------------+
//|                                         Guardian_Earth_V20.mq5   |
//|                          V20.7.1 [无懈可击·终极破甲 MT5 完整版]  |
//|                          目标战区: XAUUSD, XAGUSD, SPX500, US30  |
//+------------------------------------------------------------------+
#property copyright "Guardian Protocol"
#property link      "Earth_Defense_System"
#property version   "20.71"
#property strict

#include <Trade\Trade.mqh> 

// ==================================================================
// 🎛️ 模块一：指挥中枢 (全参数外部控制台)
// ==================================================================
input group "--- 🛡️ 核心风控与安全 ---"
input double   InpDailyMaxLoss      = 10.0;  // 1.单品种日极寒熔断线 (%)
input int      InpMagicNumber       = 207100;// 专属防伪编号
input int      InpStartHour         = 15;    // 允许开火起始小时 (服务器时间)
input int      InpEndHour           = 23;    // 允许开火结束小时 (服务器时间)
input bool     InpFridayExit        = true;  // 周五深夜是否强制清仓避险

input group "--- 💰 动态装甲 (高水位半仓防守) ---"
input double   InpHWM_Activate      = 2.5;   // 2.激活防守需达到的利润 (%)
input double   InpHWM_Retract       = 1.2;   // 3.高位回撤多少执行平仓 (%)

input group "--- 🐺 狼群战术 (顺势加仓追击) ---"
input double   InpLevelUpPct        = 0.5;   // 4.每段加仓阈值 (%)
input double   InpL3_BailoutPct     = 0.2;   // 5.L3满载保本撤退线 (%)

// ==================================================================
// 📡 模块二：雷达系统与全局变量
// ==================================================================
CTrade trade; 
int h_ema14, h_ema21, h_ema60, h_atr, h_macd, h_ema576;
double v_ema14[], v_ema21[], v_ema60[], v_atr[], v_macd_m[], v_macd_s[], v_ema576[];
double Dynamic_ATR_SL_Long, Dynamic_ATR_SL_Short;
datetime last_bar_time; 
double DailyStartBalance = 0; datetime LastDailyReset = 0; 
double HWM_Price = 0; bool IsHalfClosed = false; bool IsSymbolHalted = false;

// 战区自适应
void AutoCalibrate() {
   string s = _Symbol;
   if(StringFind(s,"XAUUSD")>=0 || StringFind(s,"GOLD")>=0) { Dynamic_ATR_SL_Long=3.5; Dynamic_ATR_SL_Short=3.5; }
   else if(StringFind(s,"SPX500")>=0 || StringFind(s,"US500")>=0) { Dynamic_ATR_SL_Long=3.0; Dynamic_ATR_SL_Short=2.0; }
   else if(StringFind(s,"US30")>=0 || StringFind(s,"DJI")>=0) { Dynamic_ATR_SL_Long=3.5; Dynamic_ATR_SL_Short=2.5; }
   else { Dynamic_ATR_SL_Long=3.0; Dynamic_ATR_SL_Short=3.0; }
}

int OnInit() {
   trade.SetExpertMagicNumber(InpMagicNumber); AutoCalibrate(); 
   h_ema14=iMA(_Symbol,PERIOD_M15,14,0,MODE_EMA,PRICE_CLOSE);
   h_ema21=iMA(_Symbol,PERIOD_M15,21,0,MODE_EMA,PRICE_CLOSE);
   h_ema60=iMA(_Symbol,PERIOD_M15,60,0,MODE_EMA,PRICE_CLOSE);
   h_atr=iATR(_Symbol,PERIOD_M15,14);
   h_macd=iMACD(_Symbol,PERIOD_H1,12,26,9,PRICE_CLOSE);
   h_ema576=iMA(_Symbol,PERIOD_H4,576,0,MODE_EMA,PRICE_CLOSE);
   ArraySetAsSeries(v_ema14,true); ArraySetAsSeries(v_ema21,true); ArraySetAsSeries(v_ema60,true);
   ArraySetAsSeries(v_atr,true); ArraySetAsSeries(v_macd_m,true); ArraySetAsSeries(v_macd_s,true);
   ArraySetAsSeries(v_ema576,true);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int r) {
   IndicatorRelease(h_ema14); IndicatorRelease(h_ema21); IndicatorRelease(h_ema60);
   IndicatorRelease(h_atr); IndicatorRelease(h_macd); IndicatorRelease(h_ema576);
}

// ==================================================================
// 🛡️ 模块三 & 五：安全拦截与自动撤退
// ==================================================================
bool CheckSecurity() {
   datetime now = TimeCurrent(); MqlDateTime dt; TimeToStruct(now, dt);
   datetime today_s = now - (dt.hour*3600 + dt.min*60 + dt.sec);
   if(LastDailyReset != today_s) { DailyStartBalance=AccountInfoDouble(ACCOUNT_BALANCE); LastDailyReset=today_s; IsSymbolHalted=false; }
   if(IsSymbolHalted) return true;

   if(InpFridayExit && dt.day_of_week == FRIDAY && dt.hour >= 22) IsSymbolHalted = true;

   double pnl = 0;
   if(HistorySelect(today_s, now))
      for(int i=0; i<HistoryDealsTotal(); i++)
         if(HistoryDealGetString(HistoryDealGetTicket(i),DEAL_SYMBOL)==_Symbol && HistoryDealGetInteger(HistoryDealGetTicket(i),DEAL_MAGIC)==InpMagicNumber)
            pnl += HistoryDealGetDouble(HistoryDealGetTicket(i),DEAL_PROFIT);
   for(int i=PositionsTotal()-1; i>=0; i--)
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) pnl += PositionGetDouble(POSITION_PROFIT);

   if(pnl / (AccountInfoDouble(ACCOUNT_BALANCE)+1e-9) <= -(InpDailyMaxLoss/100.0) || IsSymbolHalted) {
      IsSymbolHalted = true;
      for(int i=PositionsTotal()-1; i>=0; i--)
         if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) trade.PositionClose(PositionGetTicket(i));
      return true;
   }
   return false;
}

// ==================================================================
// 🐺 模块四：火力交锋 (咬死利润逻辑)
// ==================================================================
int GetWolfLevel(long &type, double &avg_p, double &pm) {
   int lv=0; double vol=0, val=0, cur=0;
   for(int i=PositionsTotal()-1; i>=0; i--)
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) {
         lv++; type=PositionGetInteger(POSITION_TYPE); vol+=PositionGetDouble(POSITION_VOLUME);
         val+=(PositionGetDouble(POSITION_PRICE_OPEN)*PositionGetDouble(POSITION_VOLUME)); cur=PositionGetDouble(POSITION_PRICE_CURRENT);
      }
   if(lv>0) { avg_p = val/vol; pm = (type==POSITION_TYPE_BUY)?(cur-avg_p)/avg_p:(avg_p-cur)/avg_p; }
   return lv;
}

void ExecuteCombat(double ema14, double ema21, double ema60, double atr, double mh, double ema576) {
   long type; double avg_p, pm; int lv = GetWolfLevel(type, avg_p, pm);
   if(IsHalfClosed || IsSymbolHalted) return;
   double lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN) * 2.0;

   // 逆向信号离场
   if(lv > 0) {
      double c1 = iClose(_Symbol,PERIOD_M15,1);
      if((type==POSITION_TYPE_BUY && c1 < ema60) || (type==POSITION_TYPE_SELL && c1 > ema60)) {
         for(int i=PositionsTotal()-1; i>=0; i--) if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) trade.PositionClose(PositionGetTicket(i));
         return;
      }
   }

   if(lv == 0) { // L1 入场
      double c1=iClose(_Symbol,PERIOD_M15,1), l2=iLow(_Symbol,PERIOD_M15,2), h2=iHigh(_Symbol,PERIOD_M15,2);
      long v2=iVolume(_Symbol,PERIOD_M15,2), vs=0; for(int i=3;i<23;i++) vs+=iVolume(_Symbol,PERIOD_M15,i);
      if(ema14>ema21 && ema21>ema60 && c1>ema576 && l2<=ema14*1.002 && c1>ema14 && (v2>(vs/20.0)*1.2) && mh>0)
         if(trade.Buy(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_ASK),NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_ASK)-atr*Dynamic_ATR_SL_Long,_Digits),0,"L1")) HWM_Price=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      if(ema14<ema21 && ema21<ema60 && c1<ema576 && h2>=ema14*0.998 && c1<ema14 && (v2>(vs/20.0)*1.2) && mh<0)
         if(trade.Sell(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_BID),NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID)+atr*Dynamic_ATR_SL_Short,_Digits),0,"L1")) HWM_Price=SymbolInfoDouble(_Symbol,SYMBOL_BID);
   } 
   else if(lv < 3 && pm >= (InpLevelUpPct/100.0 * lv)) { // L2-L3 追击
      if(type==POSITION_TYPE_BUY) trade.Buy(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_ASK),0,0,"L"+(string)(lv+1));
      else trade.Sell(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_BID),0,0,"L"+(string)(lv+1));
   } 
   else if(lv >= 3 && pm <= (InpL3_BailoutPct/100.0)) { // L3 强制撤离
      for(int i=PositionsTotal()-1; i>=0; i--) if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) trade.PositionClose(PositionGetTicket(i));
   }
}

// ==================================================================
// 🛡️ 模块五：动态装甲 (高水位追踪)
// ==================================================================
void ManageArmor() {
   bool has_pos = false;
   for(int i=PositionsTotal()-1; i>=0; i--) {
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) {
         has_pos = true;
         double cur=PositionGetDouble(POSITION_PRICE_CURRENT), op=PositionGetDouble(POSITION_PRICE_OPEN), vol=PositionGetDouble(POSITION_VOLUME);
         if(HWM_Price == 0) HWM_Price = cur;
         if(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY) {
            if(cur>HWM_Price) HWM_Price=cur;
            if(!IsHalfClosed && (cur-op)/op >= (InpHWM_Activate/100.0) && (HWM_Price-cur)/HWM_Price >= (InpHWM_Retract/100.0)) {
               double lot_step = SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
               if(trade.PositionClosePartial(PositionGetTicket(i),MathFloor((vol/2.0)/lot_step)*lot_step)) { IsHalfClosed=true; trade.PositionModify(PositionGetTicket(i),op,0); }
            }
         } else {
            if(cur<HWM_Price) HWM_Price=cur;
            if(!IsHalfClosed && (op-cur)/op >= (InpHWM_Activate/100.0) && (cur-HWM_Price)/HWM_Price >= (InpHWM_Retract/100.0)) {
               double lot_step = SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
               if(trade.PositionClosePartial(PositionGetTicket(i),MathFloor((vol/2.0)/lot_step)*lot_step)) { IsHalfClosed=true; trade.PositionModify(PositionGetTicket(i),op,0); }
            }
         }
      }
   }
   if(!has_pos) { IsHalfClosed = false; HWM_Price = 0; } // 核心修复：空仓后重置状态
}

// ==================================================================
// 🛰️ 模块六：主循环与全息 UI
// ==================================================================
void OnTick() {
   if(CheckSecurity()) { Comment("🌍 V20.7.1 | 战区封锁中 (已达红线或休息日)"); return; }
   ManageArmor();
   string ui = "🌍 V20.7.1 守护地球\n战区: "+_Symbol+"\n状态: "+((IsHalfClosed)?"[🛡️半仓保本]":((HWM_Price>0)?"[🔥追踪水位]":"[📡扫描中]"));
   Comment(ui);

   datetime cb=iTime(_Symbol,PERIOD_M15,0); if(cb==last_bar_time) return; 
   MqlDateTime dt; TimeCurrent(dt); if(dt.hour<InpStartHour || dt.hour>=InpEndHour) return; 

   if(CopyBuffer(h_ema14,0,0,3,v_ema14)<=0 || CopyBuffer(h_ema21,0,0,3,v_ema21)<=0 || 
      CopyBuffer(h_ema60,0,0,3,v_ema60)<=0 || CopyBuffer(h_atr,0,0,3,v_atr)<=0 ||
      CopyBuffer(h_macd,0,0,3,v_macd_m)<=0 || CopyBuffer(h_macd,1,0,3,v_macd_s)<=0 ||
      CopyBuffer(h_ema576,0,0,3,v_ema576)<=0) return;

   ExecuteCombat(v_ema14[1], v_ema21[1], v_ema60[1], v_atr[1], v_macd_m[1]-v_macd_s[1], v_ema576[1]);
   last_bar_time = cb; 
}