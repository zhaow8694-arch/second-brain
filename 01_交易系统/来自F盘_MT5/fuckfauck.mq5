//+------------------------------------------------------------------+
//|                                         Guardian_Earth_V20.mq5   |
//|                          V20.8.0 [破晓机甲·全闭环完整版]          |
//|                          目标战区: XAUUSD, XAGUSD, SPX500, US30  |
//+------------------------------------------------------------------+
#property copyright "Guardian Protocol"
#property link      "Earth_Defense_System"
#property version   "20.80"
#property strict
#include <Trade\Trade.mqh>

// ==================================================================
// 🎛️ 指挥中枢
// ==================================================================
input group "--- 🛡️ 核心风控与安全 ---"
input double InpRiskPercent   = 1.0;      // 1. 每单最大风险 (% of balance)
input double InpDailyMaxLoss  = 5.0;      // 2. 日极寒熔断线 (%)
input int    InpStartHour     = 15;       // 3. 开火起始小时
input int    InpEndHour       = 23;       // 4. 开火结束小时
input bool   InpFridayExit    = true;     // 5. 周五22点强制清仓
input int    InpMagicNumber   = 208000;
input int    InpMaxLevels     = 4;        // 6. 最大加仓级数

input group "--- 💰 动态装甲 ---"
input double InpHWM_Activate  = 2.0;      // 7. 利润激活线 (%)
input double InpHWM_Retract   = 0.8;      // 8. 回撤对切线 (%)

input group "--- 🐺 狼群战术 ---"
input double InpLevelUpPct    = 0.4;      // 9. 升段加仓阈值 (%)
input double InpL3_BailoutPct = 0.2;      // 10. 重仓(>=3层)保本撤退线 (%)

input group "--- 📡 信号灵敏度 ---"
input double InpVolMultiplier = 0.8;      // 11. 量能系数
input double InpPullbackPct   = 0.6;      // 12. 回踩容忍度 (%)
input bool   InpUseMacroFilter= false;    // 13. H4宏观过滤

// ==================================================================
// 📡 内部状态机
// ==================================================================
CTrade trade;
int h_ema14, h_ema21, h_ema60, h_atr, h_macd, h_ema576;
double v_ema14[], v_ema21[], v_ema60[], v_atr[], v_macd_m[], v_macd_s[], v_ema576[];
double Dyn_SL_L, Dyn_SL_S;

datetime last_bar_time;
double HWM_Price=0;
bool IsHalfClosed=false;
bool IsSymbolHalted=false;
double DailyStartBalance=0;
datetime LastDailyReset=0;

// 🧮 2倍step物理防护：精准计算到物理SL的风险手数
double CalculateLotSize(double sl_distance)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = balance * InpRiskPercent / 100.0;
   if(risk_amount <= 0) return SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN) * 2.0;

   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick_size == 0) tick_size = _Point;

   double sl_points = sl_distance / tick_size;
   if(sl_points <= 0) sl_points = 10;

   double lot = risk_amount / (sl_points * tick_value);

   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN) * 2.0;
   double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   // 强制2倍step对切合法性
   lot = MathFloor(lot / (2.0 * step)) * (2.0 * step);
   lot = MathMax(min_lot, MathMin(max_lot, lot));

   return lot;
}

void AutoCalibrate()
{
   string s = _Symbol;
   if(StringFind(s,"XAUUSD")>=0 || StringFind(s,"GOLD")>=0){ Dyn_SL_L=3.5; Dyn_SL_S=3.5; }
   else if(StringFind(s,"SPX500")>=0 || StringFind(s,"US500")>=0){ Dyn_SL_L=3.0; Dyn_SL_S=2.0; }
   else if(StringFind(s,"US30")>=0 || StringFind(s,"DJI")>=0){ Dyn_SL_L=3.5; Dyn_SL_S=2.5; }
   else { Dyn_SL_L=3.0; Dyn_SL_S=3.0; }
}

int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber); 
   AutoCalibrate();
   
   h_ema14  = iMA(_Symbol,PERIOD_M15,14,0,MODE_EMA,PRICE_CLOSE);
   h_ema21  = iMA(_Symbol,PERIOD_M15,21,0,MODE_EMA,PRICE_CLOSE);
   h_ema60  = iMA(_Symbol,PERIOD_M15,60,0,MODE_EMA,PRICE_CLOSE);
   h_atr    = iATR(_Symbol,PERIOD_M15,14);
   h_macd   = iMACD(_Symbol,PERIOD_H1,12,26,9,PRICE_CLOSE);
   h_ema576 = iMA(_Symbol,PERIOD_H4,576,0,MODE_EMA,PRICE_CLOSE);

   ArraySetAsSeries(v_ema14,true); ArraySetAsSeries(v_ema21,true); ArraySetAsSeries(v_ema60,true);
   ArraySetAsSeries(v_atr,true); ArraySetAsSeries(v_macd_m,true); ArraySetAsSeries(v_macd_s,true);
   ArraySetAsSeries(v_ema576,true);

   // 【初始化修复】系统点火时立即锁定起始资金
   datetime now = TimeCurrent(); MqlDateTime dt; TimeToStruct(now,dt);
   LastDailyReset = now - (dt.hour*3600 + dt.min*60 + dt.sec);
   DailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);

   Print("🚀 V20.8.0 破晓终极版启动 | 初始基数锁定: ", DailyStartBalance, " | 风险: ", InpRiskPercent, "%");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int r)
{
   IndicatorRelease(h_ema14); IndicatorRelease(h_ema21); IndicatorRelease(h_ema60);
   IndicatorRelease(h_atr); IndicatorRelease(h_macd); IndicatorRelease(h_ema576);
}

// ==================================================================
// 🛡️ 熔断保护 (完美闭环)
// ==================================================================
bool IsSecurityBreached()
{
   datetime now=TimeCurrent(); MqlDateTime dt; TimeToStruct(now,dt);
   datetime today_s=now-(dt.hour*3600+dt.min*60+dt.sec);
   
   if(LastDailyReset!=today_s){ 
      DailyStartBalance=AccountInfoDouble(ACCOUNT_BALANCE); 
      LastDailyReset=today_s; 
      IsSymbolHalted=false; 
   }
   if(IsSymbolHalted) return true;
   
   if(InpFridayExit && dt.day_of_week==FRIDAY && dt.hour>=22){
      IsSymbolHalted=true; Print("🚩 周五深夜强制清仓离场");
   }
   
   double pnl=0;
   if(HistorySelect(today_s,now))
      for(int i=0;i<HistoryDealsTotal();i++)
         if(HistoryDealGetString(HistoryDealGetTicket(i),DEAL_SYMBOL)==_Symbol && HistoryDealGetInteger(HistoryDealGetTicket(i),DEAL_MAGIC)==InpMagicNumber)
            pnl+=HistoryDealGetDouble(HistoryDealGetTicket(i),DEAL_PROFIT) + HistoryDealGetDouble(HistoryDealGetTicket(i),DEAL_SWAP) + HistoryDealGetDouble(HistoryDealGetTicket(i),DEAL_COMMISSION);
            
   for(int i=PositionsTotal()-1;i>=0;i--)
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) 
         pnl+=PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP) + PositionGetDouble(POSITION_COMMISSION);
         
   if(DailyStartBalance > 0 && pnl/DailyStartBalance <= -(InpDailyMaxLoss/100.0)){
      IsSymbolHalted=true;
      for(int i=PositionsTotal()-1;i>=0;i--)
         if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) 
            trade.PositionClose(PositionGetTicket(i));
      Print("🛑 触发日极寒熔断！");
      return true;
   }
   return false;
}

// ==================================================================
// 🛡️ 动态装甲（舰队级物理对切）
// ==================================================================
void ManageArmor()
{
   int lv=0; long type=0; double val=0, vol=0, cur=0;
   for(int i=PositionsTotal()-1; i>=0; i--) 
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber){
         lv++; type = PositionGetInteger(POSITION_TYPE); 
         double p_vol = PositionGetDouble(POSITION_VOLUME);
         vol += p_vol; val += (PositionGetDouble(POSITION_PRICE_OPEN) * p_vol); 
         cur = PositionGetDouble(POSITION_PRICE_CURRENT);
      }
   if(lv == 0) { IsHalfClosed = false; HWM_Price = 0; return; }
   
   double avg_p = val / vol;
   if(HWM_Price == 0) HWM_Price = cur;
   if(type == POSITION_TYPE_BUY && cur > HWM_Price) HWM_Price = cur;
   if(type == POSITION_TYPE_SELL && cur < HWM_Price) HWM_Price = cur;
   
   if(!IsHalfClosed) {
      double pm = (type == POSITION_TYPE_BUY) ? (cur - avg_p) / avg_p : (avg_p - cur) / avg_p;
      double retract = (type == POSITION_TYPE_BUY) ? (HWM_Price - cur) / HWM_Price : (cur - HWM_Price) / HWM_Price;
      
      if(pm >= (InpHWM_Activate / 100.0) && retract >= (InpHWM_Retract / 100.0)) {
         for(int i=PositionsTotal()-1; i>=0; i--) 
            if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber){
               ulong ticket = PositionGetTicket(i); 
               double t_vol = PositionGetDouble(POSITION_VOLUME);
               double t_op = PositionGetDouble(POSITION_PRICE_OPEN);
               double stp = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
               double close_vol = MathFloor((t_vol / 2.0) / stp) * stp;
               if(close_vol >= SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN)){
                  if(trade.PositionClosePartial(ticket, close_vol)) {
                     trade.PositionModify(ticket, t_op, 0);
                     Print("🛡️ 舰队半仓成功！剩余仓位已移保本");
                  }else Print("❌ 半仓失败: ", trade.ResultRetcodeDescription());
               }
            }
         IsHalfClosed = true;
      }
   }
}

// ==================================================================
// ⚔️ 战术引擎（倒金字塔加仓 + 真实止损锁定）
// ==================================================================
void BattleLoop(double ema14, double ema21, double ema60, double atr, double mh, double ema576)
{
   int lv=0; long t=0; double ap=0, pm=0, vol=0, val=0, cur=0;
   double first_sl = 0; 
   
   // 【循环修正】严格逆向遍历寻找首笔止损线
   for(int i=PositionsTotal()-1; i>=0; i--){ 
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber){
         lv++; t=PositionGetInteger(POSITION_TYPE); 
         double p_vol = PositionGetDouble(POSITION_VOLUME);
         vol+=p_vol; val+=(PositionGetDouble(POSITION_PRICE_OPEN)*p_vol); 
         cur=PositionGetDouble(POSITION_PRICE_CURRENT);
         // 获取最近发现的一笔（即最早期开出的那笔L1的SL）
         first_sl = PositionGetDouble(POSITION_SL); 
      }
   }
   if(lv>0){ap=val/vol;pm=(t==POSITION_TYPE_BUY)?(cur-ap)/ap:(ap-cur)/ap;}
   
   // 【防御前置】无视半仓状态，执行危机撤退
   if(lv>0){
      double c1=iClose(_Symbol,PERIOD_M15,1);
      if((t==POSITION_TYPE_BUY && c1<ema60) || (t==POSITION_TYPE_SELL && c1>ema60)){
         Print("🔴 趋势反转破位，全军强制撤离！");
         for(int i=PositionsTotal()-1;i>=0;i--)
            if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) 
               trade.PositionClose(PositionGetTicket(i));
         return;
      }
      
      // 只要重仓(>=3层)就激活保本撤离
      if(lv >= 3 && pm <= (InpL3_BailoutPct/100.0)){
         Print("💰 阵型重仓保本保险触发，全平离场");
         for(int i=PositionsTotal()-1;i>=0;i--)
            if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) 
               trade.PositionClose(PositionGetTicket(i));
         return;
      }
   }
   
   if(IsHalfClosed || IsSymbolHalted || lv >= InpMaxLevels) return;
   
   // 1. L1 入场
   if(lv==0){
      double c1=iClose(_Symbol,PERIOD_M15,1), l2=iLow(_Symbol,PERIOD_M15,2), h2=iHigh(_Symbol,PERIOD_M15,2);
      long v2=iVolume(_Symbol,PERIOD_M15,2), vs=0; 
      for(int i=3;i<23;i++) vs+=iVolume(_Symbol,PERIOD_M15,i);
      bool vol_ok = (v2 > (vs/20.0)*InpVolMultiplier);
      double pb_tol = InpPullbackPct / 100.0;
      
      if(ema14>ema21 && ema21>ema60 && (!InpUseMacroFilter || c1>ema576) && l2<=ema14*(1.0+pb_tol) && c1>ema14 && vol_ok && mh>0){
         double sl_d = atr * Dyn_SL_L; 
         double lot = CalculateLotSize(sl_d); 
         double sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_ASK)-sl_d,_Digits);
         if(trade.Buy(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_ASK),sl,0,"L1")) {
            HWM_Price=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
            Print("🟢 L1 多单开仓 | 手数:",lot," | 初始SL:",sl);
         }else Print("❌ L1(多)失败: ",trade.ResultRetcodeDescription());
      }
      
      if(ema14<ema21 && ema21<ema60 && (!InpUseMacroFilter || c1<ema576) && h2>=ema14*(1.0-pb_tol) && c1<ema14 && vol_ok && mh<0){
         double sl_d = atr * Dyn_SL_S; 
         double lot = CalculateLotSize(sl_d); 
         double sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID)+sl_d,_Digits);
         if(trade.Sell(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_BID),sl,0,"L1")) {
            HWM_Price=SymbolInfoDouble(_Symbol,SYMBOL_BID);
            Print("🟢 L1 空单开仓 | 手数:",lot," | 初始SL:",sl);
         }else Print("❌ L1(空)失败: ",trade.ResultRetcodeDescription());
      }
   }
   // 2. 狼群加仓 (【核心修复】绝对安全的动态手数与物理克隆SL)
   else if(lv < InpMaxLevels && pm >= (InpLevelUpPct/100.0 * lv)){
      double current_price = (t==POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol,SYMBOL_ASK) : SymbolInfoDouble(_Symbol,SYMBOL_BID);
      double cloned_sl = (first_sl > 0) ? first_sl : 0;
      
      // 精确计算当前价格到物理止损的真实距离，防止风险暴增
      double actual_sl_dist = 0;
      if(cloned_sl > 0) actual_sl_dist = MathAbs(current_price - cloned_sl);
      else actual_sl_dist = atr * (t==POSITION_TYPE_BUY ? Dyn_SL_L : Dyn_SL_S); 
      
      double lot = CalculateLotSize(actual_sl_dist); // 这里算出的就是真正控制住1%风险的递减手数
      string cmt = "L"+(string)(lv+1);
      
      if(t==POSITION_TYPE_BUY){
         if(trade.Buy(lot,_Symbol,current_price,cloned_sl,0,cmt))
            Print("🟢 加仓 ",cmt," 多单 | 倒金字塔手数:",lot," | 克隆SL:",cloned_sl);
         else Print("❌ 加仓失败: ",trade.ResultRetcodeDescription());
      }else{
         if(trade.Sell(lot,_Symbol,current_price,cloned_sl,0,cmt))
            Print("🟢 加仓 ",cmt," 空单 | 倒金字塔手数:",lot," | 克隆SL:",cloned_sl);
         else Print("❌ 加仓失败: ",trade.ResultRetcodeDescription());
      }
   }
}

// ==================================================================
// 📡 驱动引擎 (UI精确核算机制)
// ==================================================================
void OnTick()
{
   if(IsSecurityBreached()){Comment("🌍 V20.8.0 | 熔断或周末休市中"); return;}
   
   ManageArmor();
   
   int lv=0; double total_vol=0, total_pnl=0;
   for(int i=PositionsTotal()-1;i>=0;i--){
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber){
         lv++; 
         total_vol += PositionGetDouble(POSITION_VOLUME);
         // 【UI精度修复】包含隔夜利息和手续费的真实净浮盈
         total_pnl += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP) + PositionGetDouble(POSITION_COMMISSION);
      }
   }
   double pnl_pct = (AccountInfoDouble(ACCOUNT_BALANCE)>0) ? total_pnl/AccountInfoDouble(ACCOUNT_BALANCE)*100 : 0;
   
   string status = IsHalfClosed ? "[🛡️半仓保本]" : (HWM_Price>0 ? "[🔥追踪中]" : "[📡扫描中]");
   Comment("🌍 Guardian Earth V20.8.0\n风险:",InpRiskPercent,"% | 总仓:",DoubleToString(total_vol,2),"手 | 净浮盈:",DoubleToString(pnl_pct,2),"%\n状态:",status);
   
   datetime cb=iTime(_Symbol,PERIOD_M15,0); 
   if(cb==last_bar_time) return;
   
   MqlDateTime dt; TimeCurrent(dt);
   if(dt.hour<InpStartHour || dt.hour>=InpEndHour) return;
   
   if(CopyBuffer(h_ema14,0,0,3,v_ema14)<=0 || CopyBuffer(h_ema21,0,0,3,v_ema21)<=0 ||
      CopyBuffer(h_ema60,0,0,3,v_ema60)<=0 || CopyBuffer(h_atr,0,0,3,v_atr)<=0 ||
      CopyBuffer(h_macd,0,0,3,v_macd_m)<=0 || CopyBuffer(h_macd,1,0,3,v_macd_s)<=0 ||
      CopyBuffer(h_ema576,0,0,3,v_ema576)<=0){
      Print("⚠️ 指标数据流中断");
      return;
   }
   
   BattleLoop(v_ema14[1],v_ema21[1],v_ema60[1],v_atr[1],v_macd_m[1]-v_macd_s[1],v_ema576[1]);
   last_bar_time=cb;
}
//+------------------------------------------------------------------+