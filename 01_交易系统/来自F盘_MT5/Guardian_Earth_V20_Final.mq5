//+------------------------------------------------------------------+
//|                                         Guardian_Earth_V20.mq5   |
//|                          V20.7.1 [全参数控制台·终极破甲版]        |
//|                          目标战区: XAUUSD, XAGUSD, SPX500, US30  |
//+------------------------------------------------------------------+
#property copyright "Guardian Protocol"
#property link      "Earth_Defense_System"
#property version   "20.71"
#property strict

#include <Trade\Trade.mqh> 

// ==================================================================
// 🎛️ 模块一：指挥中枢 (全参数控制台)
// ==================================================================
input group "--- 🛡️ 核心风控与安全 ---"
input double   InpDailyMaxLoss      = 10.0;  // 1.单品种日极寒熔断线 (%)
input int      InpMagicNumber       = 207100;// 专属防伪编号
input int      InpStartHour         = 15;    // 允许开火起始小时 (服务器时间)
input int      InpEndHour           = 23;    // 允许开火结束小时 (服务器时间)
input bool     InpFridayExit        = true;  // 周五深夜强制清仓避险

input group "--- 💰 动态装甲 (舰队级半仓防守) ---"
input double   InpHWM_Activate      = 2.5;   // 2.全军平均利润激活线 (%)
input double   InpHWM_Retract       = 1.2;   // 3.全军最高水位回撤平仓线 (%)

input group "--- 🐺 狼群战术 (顺势追击) ---"
input double   InpLevelUpPct        = 0.5;   // 4.升段加仓阈值 (%)
input double   InpL3_BailoutPct     = 0.2;   // 5.L3满载保本撤退线 (%)

input group "--- 📡 信号灵敏度 (进场门槛调节) ---"
input double   InpVolMultiplier     = 1.0;   // 6.量能爆发系数 (调低易进场,如1.0)
input double   InpPullbackPct       = 0.5;   // 7.回踩容忍度 (%) (调高易进场,如0.8)
input bool     InpUseMacroFilter    = false; // 8.开启H4宏观过滤 (false为关闭大趋势限制)
input int      InpLotMultiplier     = 2;     // 9.初始弹药基数 (默认2倍MinLot，保证完美对切)

// ==================================================================
// 📡 模块二：内部雷达与状态机
// ==================================================================
CTrade trade; 
int h_ema14, h_ema21, h_ema60, h_atr, h_macd, h_ema576;
double v_ema14[], v_ema21[], v_ema60[], v_atr[], v_macd_m[], v_macd_s[], v_ema576[];
double Dyn_SL_L, Dyn_SL_S;
datetime last_bar_time; 
double DailyStartBalance=0; datetime LastDailyReset=0; 
double HWM_Price=0; bool IsHalfClosed=false; bool IsSymbolHalted=false;

void AutoCalibrate() {
   string s=_Symbol;
   if(StringFind(s,"XAUUSD")>=0||StringFind(s,"GOLD")>=0){Dyn_SL_L=3.5;Dyn_SL_S=3.5;}
   else if(StringFind(s,"SPX500")>=0||StringFind(s,"US500")>=0){Dyn_SL_L=3.0;Dyn_SL_S=2.0;}
   else if(StringFind(s,"US30")>=0||StringFind(s,"DJI")>=0){Dyn_SL_L=3.5;Dyn_SL_S=2.5;}
   else {Dyn_SL_L=3.0;Dyn_SL_S=3.0;}
}

int OnInit() {
   trade.SetExpertMagicNumber(InpMagicNumber); AutoCalibrate(); 
   h_ema14=iMA(_Symbol,PERIOD_M15,14,0,MODE_EMA,PRICE_CLOSE);
   h_ema21=iMA(_Symbol,PERIOD_M15,21,0,MODE_EMA,PRICE_CLOSE);
   h_ema60=iMA(_Symbol,PERIOD_M15,60,0,MODE_EMA,PRICE_CLOSE);
   h_atr=iATR(_Symbol,PERIOD_M15,14);
   h_macd=iMACD(_Symbol,PERIOD_H1,12,26,9,PRICE_CLOSE);
   h_ema576=iMA(_Symbol,PERIOD_H4,576,0,MODE_EMA,PRICE_CLOSE);
   ArraySetAsSeries(v_ema14,true);ArraySetAsSeries(v_ema21,true);ArraySetAsSeries(v_ema60,true);
   ArraySetAsSeries(v_atr,true);ArraySetAsSeries(v_macd_m,true);ArraySetAsSeries(v_macd_s,true);
   ArraySetAsSeries(v_ema576,true);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int r) {
   IndicatorRelease(h_ema14); IndicatorRelease(h_ema21); IndicatorRelease(h_ema60);
   IndicatorRelease(h_atr); IndicatorRelease(h_macd); IndicatorRelease(h_ema576);
}

// ==================================================================
// 🛡️ 模块三：军需物流与熔断保护
// ==================================================================
bool IsSecurityBreached() {
   datetime now=TimeCurrent(); MqlDateTime dt; TimeToStruct(now,dt);
   datetime today_s=now-(dt.hour*3600+dt.min*60+dt.sec);
   
   if(LastDailyReset!=today_s){DailyStartBalance=AccountInfoDouble(ACCOUNT_BALANCE);LastDailyReset=today_s;IsSymbolHalted=false;}
   if(IsSymbolHalted) return true;
   
   // 周五深夜强制撤离
   if(InpFridayExit && dt.day_of_week==FRIDAY && dt.hour>=22) IsSymbolHalted=true;
   
   double pnl=0;
   if(HistorySelect(today_s,now))
      for(int i=0;i<HistoryDealsTotal();i++)
         if(HistoryDealGetString(HistoryDealGetTicket(i),DEAL_SYMBOL)==_Symbol && HistoryDealGetInteger(HistoryDealGetTicket(i),DEAL_MAGIC)==InpMagicNumber)
            pnl+=HistoryDealGetDouble(HistoryDealGetTicket(i),DEAL_PROFIT);
            
   for(int i=PositionsTotal()-1;i>=0;i--)
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) pnl+=PositionGetDouble(POSITION_PROFIT);
      
   if(pnl/(AccountInfoDouble(ACCOUNT_BALANCE)+1e-9)<=-(InpDailyMaxLoss/100.0) || IsSymbolHalted){
      IsSymbolHalted=true;
      for(int i=PositionsTotal()-1;i>=0;i--) 
         if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) trade.PositionClose(PositionGetTicket(i));
      return true;
   }
   return false;
}

// ==================================================================
// ⚔️ 模块四：火力交锋 (狼群战术与灵敏度旋钮)
// ==================================================================
void BattleLoop(double ema14, double ema21, double ema60, double atr, double mh, double ema576) {
   int lv=0; long t=0; double ap=0, pm=0, vol=0, val=0, cur=0;
   
   // 统计当前狼群兵力
   for(int i=PositionsTotal()-1;i>=0;i--) {
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber){
         lv++; t=PositionGetInteger(POSITION_TYPE); 
         double p_vol = PositionGetDouble(POSITION_VOLUME);
         vol+=p_vol;
         val+=(PositionGetDouble(POSITION_PRICE_OPEN)*p_vol); 
         cur=PositionGetDouble(POSITION_PRICE_CURRENT);
      }
   }
   if(lv>0){ap=val/vol;pm=(t==POSITION_TYPE_BUY)?(cur-ap)/ap:(ap-cur)/ap;}
   
   if(IsHalfClosed || IsSymbolHalted) return;
   
   double lot = SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN) * InpLotMultiplier;

   // 逆向信号拦截 (趋势破位，全军撤退)
   if(lv>0){
      double c1=iClose(_Symbol,PERIOD_M15,1);
      if((t==POSITION_TYPE_BUY && c1<ema60) || (t==POSITION_TYPE_SELL && c1>ema60)){
         for(int i=PositionsTotal()-1;i>=0;i--) 
            if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) trade.PositionClose(PositionGetTicket(i));
         return;
      }
   }

   // L1 侦察兵入场
   if(lv==0){ 
      double c1=iClose(_Symbol,PERIOD_M15,1), l2=iLow(_Symbol,PERIOD_M15,2), h2=iHigh(_Symbol,PERIOD_M15,2);
      long v2=iVolume(_Symbol,PERIOD_M15,2), vs=0; for(int i=3;i<23;i++) vs+=iVolume(_Symbol,PERIOD_M15,i);
      
      bool vol_ok = (v2 > (vs/20.0)*InpVolMultiplier);
      bool macro_ok = (!InpUseMacroFilter || (c1 > ema576)); 
      bool macro_ok_s = (!InpUseMacroFilter || (c1 < ema576)); 
      double pb_tolerance = InpPullbackPct / 100.0;

      if(ema14>ema21 && ema21>ema60 && macro_ok && l2<=ema14*(1.0+pb_tolerance) && c1>ema14 && vol_ok && mh>0)
         if(trade.Buy(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_ASK),NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_ASK)-atr*Dyn_SL_L,_Digits),0,"L1")) HWM_Price=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      
      if(ema14<ema21 && ema21<ema60 && macro_ok_s && h2>=ema14*(1.0-pb_tolerance) && c1<ema14 && vol_ok && mh<0)
         if(trade.Sell(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_BID),NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID)+atr*Dyn_SL_S,_Digits),0,"L1")) HWM_Price=SymbolInfoDouble(_Symbol,SYMBOL_BID);
   } 
   // L2/L3 乘胜追击
   else if(lv<3 && pm >= (InpLevelUpPct/100.0 * lv)){
      if(t==POSITION_TYPE_BUY) trade.Buy(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_ASK),0,0,"L"+(string)(lv+1));
      else trade.Sell(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_BID),0,0,"L"+(string)(lv+1));
   } 
   // L3 满载保本撤离
   else if(lv>=3 && pm <= (InpL3_BailoutPct/100.0)){
      for(int i=PositionsTotal()-1;i>=0;i--) 
         if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) trade.PositionClose(PositionGetTicket(i));
   }
}

// ==================================================================
// 🛡️ 模块五：舰队级动态装甲 (全军高水位追踪与物理对切)
// ==================================================================
void ManageArmor() {
   int lv=0; long type=0; double val=0, vol=0, cur=0;
   
   for(int i=PositionsTotal()-1; i>=0; i--) {
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) {
         lv++; type = PositionGetInteger(POSITION_TYPE);
         double p_vol = PositionGetDouble(POSITION_VOLUME);
         vol += p_vol;
         val += (PositionGetDouble(POSITION_PRICE_OPEN) * p_vol);
         cur = PositionGetDouble(POSITION_PRICE_CURRENT);
      }
   }

   if(lv == 0) { IsHalfClosed = false; HWM_Price = 0; return; }

   double avg_price = val / vol;
   if(HWM_Price == 0) HWM_Price = cur;

   if(type == POSITION_TYPE_BUY && cur > HWM_Price) HWM_Price = cur;
   if(type == POSITION_TYPE_SELL && cur < HWM_Price) HWM_Price = cur;

   if(!IsHalfClosed) {
      double pm = (type == POSITION_TYPE_BUY) ? (cur - avg_price) / avg_price : (avg_price - cur) / avg_price;
      double retract = (type == POSITION_TYPE_BUY) ? (HWM_Price - cur) / HWM_Price : (cur - HWM_Price) / HWM_Price;

      if(pm >= (InpHWM_Activate / 100.0) && retract >= (InpHWM_Retract / 100.0)) {
         for(int i=PositionsTotal()-1; i>=0; i--) {
            if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) {
               ulong ticket = PositionGetTicket(i);
               double t_vol = PositionGetDouble(POSITION_VOLUME);
               double t_op  = PositionGetDouble(POSITION_PRICE_OPEN);
               double stp   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
               double min_v = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
               
               double close_vol = MathFloor((t_vol / 2.0) / stp) * stp;
               
               if(close_vol >= min_v) {
                  if(trade.PositionClosePartial(ticket, close_vol)) {
                     trade.PositionModify(ticket, t_op, 0); 
                  }
               }
            }
         }
         IsHalfClosed = true;
      }
   }
}

// ==================================================================
// 🛰️ 模块六：全息通讯与主循环
// ==================================================================
void OnTick() {
   if(IsSecurityBreached()){Comment("🌍 V20.7.1 | 战区封锁中 (触及红线或周末)"); return;}
   ManageArmor();
   
   string ui = "🌍 Guardian Earth V20.7.1\n战区: "+_Symbol+"\n状态: "+((IsHalfClosed)?"[🛡️全军半仓保本]":((HWM_Price>0)?"[🔥追踪舰队水位]":"[📡雷达扫描中]"));
   Comment(ui);
   
   datetime cb=iTime(_Symbol,PERIOD_M15,0); if(cb==last_bar_time) return; 
   MqlDateTime dt; TimeCurrent(dt); if(dt.hour<InpStartHour||dt.hour>=InpEndHour) return; 
   
   if(CopyBuffer(h_ema14,0,0,3,v_ema14)<=0||CopyBuffer(h_ema21,0,0,3,v_ema21)<=0||CopyBuffer(h_ema60,0,0,3,v_ema60)<=0||
      CopyBuffer(h_atr,0,0,3,v_atr)<=0||CopyBuffer(h_macd,0,0,3,v_macd_m)<=0||CopyBuffer(h_macd,1,0,3,v_macd_s)<=0||
      CopyBuffer(h_ema576,0,0,3,v_ema576)<=0) return;
      
   BattleLoop(v_ema14[1],v_ema21[1],v_ema60[1],v_atr[1],v_macd_m[1]-v_macd_s[1],v_ema576[1]);
   last_bar_time=cb; 
}
//+------------------------------------------------------------------+