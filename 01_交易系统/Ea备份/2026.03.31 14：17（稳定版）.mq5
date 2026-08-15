//+------------------------------------------------------------------+
//|                          Copyright 2026, Z.WeiV20.mq5            |
//|                        V20.8.4 [破晓机甲·时空锁定终极定稿版]     |
//|                          目标战区: XAUUSD, XAGUSD, SPX500, US30  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Z.Wei"
#property link      "Earth_Defense_System"
#property version   "20.84"
#property strict
#include <Trade\Trade.mqh>

// ==================================================================
// 🎛️ 指挥中枢 (彻底零硬编码)
// ==================================================================
input group "--- 🛡️ 核心风控与安全 ---"
input double InpRiskPercent   = 1.0;      // 1. 每单最大风险 (% of balance)
input double InpDailyMaxLoss  = 5.0;      // 2. 日极寒熔断线 (%)
input int    InpStartHour     = 15;       // 3. 开火起始小时
input int    InpEndHour       = 23;       // 4. 开火结束小时
input bool   InpFridayExit    = true;     // 5. 周五22点强制清仓
input int    InpMagicNumber   = 208400;
input int    InpMaxLevels     = 4;        // 6. 最大加仓级数

input group "--- 💰 动态装甲 ---"
input double InpHWM_Activate  = 2.0;      // 7. 利润激活线 (%)
input double InpHWM_Retract   = 0.8;      // 8. 回撤对切线 (%)

input group "--- 🐺 狼群战术 ---"
input double InpLevelUpPct    = 0.4;      // 9. 升段加仓阈值 (%)
input int    InpBailoutLevel  = 3;        // 10. 重仓保本激活层数
input double InpBailoutPct    = 0.2;      // 11. 重仓保本撤退线 (%)

input group "--- 📡 信号灵敏度 ---"
input double InpVolMultiplier = 0.8;      // 12. 量能系数
input double InpPullbackPct   = 0.6;      // 13. 回踩容忍度 (%)
input bool   InpUseMacroFilter= false;    // 14. H4宏观过滤

input group "--- 📡 Telegram推送 ---"
input string InpTelegramToken = "";       // Bot Token (BotFather获取)
input string InpTelegramChatID= "";       // Chat ID (多个用逗号分隔)

// ==================================================================
// 📡 内部状态机 + 通讯核心
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

   lot = MathFloor(lot / (2.0 * step)) * (2.0 * step);
   lot = MathMax(min_lot, MathMin(max_lot, lot));
   return lot;
}

bool SendTelegram(string message)
{
   if(InpTelegramToken=="" || InpTelegramChatID=="") return false;
   string url = "https://api.telegram.org/bot" + InpTelegramToken + "/sendMessage";
   
   // 替换换行符为JSON转义符
   StringReplace(message, "\n", "\\n");
   // 替换双引号为JSON转义符（防冲突）
   StringReplace(message, "\"", "\\\"");
   
   string json = "{\"chat_id\":\"" + InpTelegramChatID + "\",\"text\":\"" + message + "\",\"parse_mode\":\"HTML\"}";
   
   char post[], result[]; string res_headers;
   // 转换为 UTF-8 字节数组（减1是去掉末尾的隐藏结束符）
   int len = StringToCharArray(json, post, 0, WHOLE_ARRAY, CP_UTF8) - 1;
   ArrayResize(post, len);
   
   string headers = "Content-Type: application/json\r\n";
   int res = WebRequest("POST", url, headers, 3000, post, result, res_headers);
   
   if(res!=200) {
      // 终极排雷：直接打印出 Telegram 官方的报错原因！
      Print("❌ Telegram推送失败 Code: ", res, " | 官方拒收原因: ", CharArrayToString(result));
   } else {
      Print("✅ Telegram通讯链路连接成功！");
   }
   return (res==200);
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

   datetime now = TimeCurrent(); MqlDateTime dt; TimeToStruct(now,dt);
   LastDailyReset = now - (dt.hour*3600 + dt.min*60 + dt.sec);
   DailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);

   string msg = "🚀 <b>Guardian Earth V20.8.4 已启动</b>\n品种: " + _Symbol + "\n风险: " + DoubleToString(InpRiskPercent,1) + "%\n时间: " + TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES);
   SendTelegram(msg);

   Print("🚀 V20.8.4 终极定稿版启动 | 初始基数: ", DailyStartBalance);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int r)
{
   IndicatorRelease(h_ema14); IndicatorRelease(h_ema21); IndicatorRelease(h_ema60);
   IndicatorRelease(h_atr); IndicatorRelease(h_macd); IndicatorRelease(h_ema576);
   SendTelegram("💤 <b>Guardian Earth 战术系统已离线</b>\n战区: " + _Symbol);
}

// ==================================================================
// 🛡️ 熔断保护 (完美闭环，去除弃用警告)
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
      IsSymbolHalted=true; 
      SendTelegram("🚩 <b>周末避险协议激活</b>\n战区: " + _Symbol + "\n状态: 强制清仓离场");
      for(int i=PositionsTotal()-1;i>=0;i--)
         if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) 
            trade.PositionClose(PositionGetTicket(i));
      return true;
   }
   
   double pnl=0;
   // 历史交易中提取手续费是合法的（DEAL_COMMISSION）
   if(HistorySelect(today_s,now))
      for(int i=0;i<HistoryDealsTotal();i++)
         if(HistoryDealGetString(HistoryDealGetTicket(i),DEAL_SYMBOL)==_Symbol && HistoryDealGetInteger(HistoryDealGetTicket(i),DEAL_MAGIC)==InpMagicNumber)
            pnl+=HistoryDealGetDouble(HistoryDealGetTicket(i),DEAL_PROFIT) + HistoryDealGetDouble(HistoryDealGetTicket(i),DEAL_SWAP) + HistoryDealGetDouble(HistoryDealGetTicket(i),DEAL_COMMISSION);
            
   // 实时持仓：已移除被官方弃用的 POSITION_COMMISSION
   for(int i=PositionsTotal()-1;i>=0;i--)
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) 
         pnl+=PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
         
   if(DailyStartBalance > 0 && pnl/DailyStartBalance <= -(InpDailyMaxLoss/100.0)){
      IsSymbolHalted=true;
      for(int i=PositionsTotal()-1;i>=0;i--)
         if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) 
            trade.PositionClose(PositionGetTicket(i));
      SendTelegram("🛑 <b>极寒熔断警报！</b>\n战区: " + _Symbol + "\n状态: 触及日亏损底线，全军物理隔离！");
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
                  }
               }
            }
         IsHalfClosed = true;
         SendTelegram("🛡️ <b>舰队装甲激活</b>\n战区: " + _Symbol + "\n战报: 利润回撤触发，成功落袋50%并焊死保本线！");
      }
   }
}

// ==================================================================
// ⚔️ 战术引擎（绝对时间锁定 + 倒金字塔防线）
// ==================================================================
void BattleLoop(double ema14, double ema21, double ema60, double atr, double mh, double ema576)
{
   int lv=0; long t=0; double ap=0, pm=0, vol=0, val=0, cur=0;
   double first_sl = 0; 
   datetime oldest_time = 0;
   bool first_found = false;
   
   // 【绝对时间防线】通过真实开仓时间，100%精准抓取 L1 的物理止损
   for(int i=PositionsTotal()-1; i>=0; i--){ 
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber){
         lv++; t=PositionGetInteger(POSITION_TYPE); 
         double p_vol = PositionGetDouble(POSITION_VOLUME);
         vol+=p_vol; val+=(PositionGetDouble(POSITION_PRICE_OPEN)*p_vol); 
         cur=PositionGetDouble(POSITION_PRICE_CURRENT);
         
         datetime open_time = (datetime)PositionGetInteger(POSITION_TIME);
         if(!first_found || open_time < oldest_time){
             oldest_time = open_time;
             first_sl = PositionGetDouble(POSITION_SL); 
             first_found = true;
         }
      }
   }
   if(lv>0){ap=val/vol;pm=(t==POSITION_TYPE_BUY)?(cur-ap)/ap:(ap-cur)/ap;}
   
   // 【防御前置】
   if(lv>0){
      double c1=iClose(_Symbol,PERIOD_M15,1);
      if((t==POSITION_TYPE_BUY && c1<ema60) || (t==POSITION_TYPE_SELL && c1>ema60)){
         SendTelegram("🔴 <b>趋势逆转警报</b>\n战区: " + _Symbol + "\n战报: K线跌破防守均线，全军已强制撤离！");
         for(int i=PositionsTotal()-1;i>=0;i--)
            if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) 
               trade.PositionClose(PositionGetTicket(i));
         return;
      }
      
      // 零硬编码保本层数
      if(lv >= InpBailoutLevel && pm <= (InpBailoutPct/100.0)){
         SendTelegram("💰 <b>重仓防守触发</b>\n战区: " + _Symbol + "\n战报: 利润回落至警戒线，全体安全平仓！");
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
            SendTelegram("🟢 <b>L1 侦察兵入场 (做多)</b>\n战区: " + _Symbol + "\n手数: " + DoubleToString(lot,2) + "\n止损: " + DoubleToString(sl,_Digits));
         }
      }
      
      if(ema14<ema21 && ema21<ema60 && (!InpUseMacroFilter || c1<ema576) && h2>=ema14*(1.0-pb_tol) && c1<ema14 && vol_ok && mh<0){
         double sl_d = atr * Dyn_SL_S; 
         double lot = CalculateLotSize(sl_d); 
         double sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID)+sl_d,_Digits);
         if(trade.Sell(lot,_Symbol,SymbolInfoDouble(_Symbol,SYMBOL_BID),sl,0,"L1")) {
            HWM_Price=SymbolInfoDouble(_Symbol,SYMBOL_BID);
            SendTelegram("🟢 <b>L1 侦察兵入场 (做空)</b>\n战区: " + _Symbol + "\n手数: " + DoubleToString(lot,2) + "\n止损: " + DoubleToString(sl,_Digits));
         }
      }
   }
   // 2. 狼群加仓 (倒金字塔：基于真实距离精算)
   else if(lv < InpMaxLevels && pm >= (InpLevelUpPct/100.0 * lv)){
      double current_price = (t==POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol,SYMBOL_ASK) : SymbolInfoDouble(_Symbol,SYMBOL_BID);
      double cloned_sl = (first_sl > 0) ? first_sl : 0;
      
      double actual_sl_dist = 0;
      if(cloned_sl > 0) actual_sl_dist = MathAbs(current_price - cloned_sl);
      else actual_sl_dist = atr * (t==POSITION_TYPE_BUY ? Dyn_SL_L : Dyn_SL_S); 
      
      double lot = CalculateLotSize(actual_sl_dist); 
      string cmt = "L"+(string)(lv+1);
      
      if(t==POSITION_TYPE_BUY){
         if(trade.Buy(lot,_Symbol,current_price,cloned_sl,0,cmt)){
            SendTelegram("🐺 <b>狼群加仓 (做多)</b>\n战区: " + _Symbol + "\n队列: " + cmt + "\n手数: " + DoubleToString(lot,2));
         }
      }else{
         if(trade.Sell(lot,_Symbol,current_price,cloned_sl,0,cmt)){
            SendTelegram("🐺 <b>狼群加仓 (做空)</b>\n战区: " + _Symbol + "\n队列: " + cmt + "\n手数: " + DoubleToString(lot,2));
         }
      }
   }
}

// ==================================================================
// 📡 驱动引擎 (UI精确核算机制)
// ==================================================================
void OnTick()
{
   if(IsSecurityBreached()){Comment("🌍 V20.8.4 | 熔断或周末休市中"); return;}
   
   ManageArmor();
   
   int lv=0; double total_vol=0, total_pnl=0;
   for(int i=PositionsTotal()-1;i>=0;i--){
      if(PositionGetSymbol(i)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber){
         lv++; 
         total_vol += PositionGetDouble(POSITION_VOLUME);
         total_pnl += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
      }
   }
   double pnl_pct = (AccountInfoDouble(ACCOUNT_BALANCE)>0) ? total_pnl/AccountInfoDouble(ACCOUNT_BALANCE)*100 : 0;
   
   string status = IsHalfClosed ? "[🛡️半仓保本]" : (HWM_Price>0 ? "[🔥追踪中]" : "[📡扫描中]");
   Comment("🌍 Guardian Earth V20.8.4\n风险:",InpRiskPercent,"% | 总仓:",DoubleToString(total_vol,2),"手 | 净浮盈:",DoubleToString(pnl_pct,2),"%\n状态:",status);
   
   datetime cb=iTime(_Symbol,PERIOD_M15,0); 
   if(cb==last_bar_time) return;
   
   MqlDateTime dt; TimeCurrent(dt);
   if(dt.hour<InpStartHour || dt.hour>=InpEndHour) return;
   
   if(CopyBuffer(h_ema14,0,0,3,v_ema14)<=0 || CopyBuffer(h_ema21,0,0,3,v_ema21)<=0 ||
      CopyBuffer(h_ema60,0,0,3,v_ema60)<=0 || CopyBuffer(h_atr,0,0,3,v_atr)<=0 ||
      CopyBuffer(h_macd,0,0,3,v_macd_m)<=0 || CopyBuffer(h_macd,1,0,3,v_macd_s)<=0 ||
      CopyBuffer(h_ema576,0,0,3,v_ema576)<=0){
      return;
   }
   
   BattleLoop(v_ema14[1],v_ema21[1],v_ema60[1],v_atr[1],v_macd_m[1]-v_macd_s[1],v_ema576[1]);
   last_bar_time=cb;
}
//+------------------------------------------------------------------+