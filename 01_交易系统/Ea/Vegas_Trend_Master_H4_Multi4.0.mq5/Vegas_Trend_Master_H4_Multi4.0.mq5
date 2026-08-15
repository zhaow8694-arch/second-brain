//+------------------------------------------------------------------+
//|                             Vegas_Trend_Master_H4_Multi.mq5      |
//|                                             Created by 编码助手 |
//+------------------------------------------------------------------+
#property copyright "编码助手"
#property version   "4.00" // 升级为4.0实盘版：固化圣杯参数 + 手机推送 + 每日简报

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade         trade;
CPositionInfo  posInfo;

//--- 开放的系统设置 ---
input string   InpSymbols = "XAUUSD,EURUSD,SP500,CHINA50"; // 交易品种(用英文逗号分隔)
input double   InpRiskPercent = 0.5;         // 单笔交易风险比例 (%)
input int      InpMagicNumber = 888888;      // EA魔术码
input bool     InpUseBreakEven = true;       // 是否启用保本止损

//--- 🔒 固化的“圣杯”参数 (不再显示在输入面板) ---
const double   OPTIMIZED_PARTIAL_CLOSE = 0.50; // 最佳平仓比例 50%
const int      OPTIMIZED_ADX_PERIOD = 14;      // 最佳ADX周期
const double   OPTIMIZED_ADX_THRESHOLD = 22.0; // 最佳ADX趋势阈值

//--- 均线参数 ---
input int      InpEma12  = 12;   
input int      InpEma144 = 144;  
input int      InpEma169 = 169;  
input int      InpEma288 = 288;  
input int      InpEma338 = 338;  
input int      InpEma576 = 576;  
input int      InpEma676 = 676;  

//--- 结构体与全局变量 ---
struct SymbolData
  {
   string   symbolName;
   int      h_ema12, h_ema144, h_ema169, h_ema288, h_ema338, h_ema576, h_ema676;
   int      h_adx; 
   datetime lastBarTime;
  };

SymbolData symbols[];
int lastReportDay = -1; // 用于记录上一次发送日报的日期

//+------------------------------------------------------------------+
//| EA初始化函数                                                      |
//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagicNumber);

   ushort separator = StringGetCharacter(",", 0);
   string result[];
   int count = StringSplit(InpSymbols, separator, result);
   
   if(count == 0) return(INIT_FAILED);

   ArrayResize(symbols, count);

   for(int i = 0; i < count; i++)
     {
      StringTrimLeft(result[i]);
      StringTrimRight(result[i]);
      symbols[i].symbolName = result[i];
      SymbolSelect(symbols[i].symbolName, true); 

      symbols[i].h_ema12  = iMA(symbols[i].symbolName, PERIOD_H4, InpEma12, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema144 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma144, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema169 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma169, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema288 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma288, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema338 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma338, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema576 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma576, 0, MODE_EMA, PRICE_CLOSE);
      symbols[i].h_ema676 = iMA(symbols[i].symbolName, PERIOD_H4, InpEma676, 0, MODE_EMA, PRICE_CLOSE);
      // 使用固化的最佳ADX参数
      symbols[i].h_adx    = iADX(symbols[i].symbolName, PERIOD_H4, OPTIMIZED_ADX_PERIOD);
      
      symbols[i].lastBarTime = 0;
     }
     
   Print("🚀 Vegas V4.0 实盘版启动完毕。圣杯参数已加载。");
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| 每次价格变动时触发的函数                                           |
//+------------------------------------------------------------------+
void OnTick()
  {
   // 1. 处理所有品种的交易逻辑
   for(int i = 0; i < ArraySize(symbols); i++)
     {
      ProcessSymbol(i);
     }
     
   // 2. 检查并发送每日11:00财报
   CheckAndSendDailyReport();
  }

//+------------------------------------------------------------------+
//| 核心逻辑：处理单个品种的交易                                       |
//+------------------------------------------------------------------+
void ProcessSymbol(int index)
  {
   string sym = symbols[index].symbolName;
   datetime currentBarTime = iTime(sym, PERIOD_H4, 0);
   if(currentBarTime == 0 || currentBarTime == symbols[index].lastBarTime) return; 
   
   double ema12[], ema144[], ema169[], ema288[], ema338[], ema576[], ema676[], adx[];
   ArraySetAsSeries(ema12, true); ArraySetAsSeries(ema144, true); ArraySetAsSeries(ema169, true);
   ArraySetAsSeries(ema288, true); ArraySetAsSeries(ema338, true); ArraySetAsSeries(ema576, true); ArraySetAsSeries(ema676, true);
   ArraySetAsSeries(adx, true); 

   CopyBuffer(symbols[index].h_ema12, 0, 0, 3, ema12);
   CopyBuffer(symbols[index].h_ema144, 0, 0, 3, ema144);
   CopyBuffer(symbols[index].h_ema169, 0, 0, 3, ema169);
   CopyBuffer(symbols[index].h_ema288, 0, 0, 3, ema288);
   CopyBuffer(symbols[index].h_ema338, 0, 0, 3, ema338);
   CopyBuffer(symbols[index].h_ema576, 0, 0, 3, ema576);
   CopyBuffer(symbols[index].h_ema676, 0, 0, 3, ema676);
   CopyBuffer(symbols[index].h_adx, 0, 0, 3, adx); 

   double closePrice1 = iClose(sym, PERIOD_H4, 1);

   bool hasBuyPosition = false;
   bool hasSellPosition = false;
   ulong posTicket = 0;
   double currentVolume = 0.0;
   double openPrice = 0.0;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(posInfo.SelectByIndex(i))
        {
         if(posInfo.Symbol() == sym && posInfo.Magic() == InpMagicNumber)
           {
            posTicket = posInfo.Ticket();
            currentVolume = posInfo.Volume();
            openPrice = posInfo.PriceOpen();
            if(posInfo.PositionType() == POSITION_TYPE_BUY) hasBuyPosition = true;
            if(posInfo.PositionType() == POSITION_TYPE_SELL) hasSellPosition = true;
            break; 
           }
        }
     }

   // --- 平仓逻辑 ---
   if(hasBuyPosition)
     {
      bool isPartiallyClosed = HasPartiallyClosed(posTicket);

      if(closePrice1 < ema338[1])
        {
         trade.PositionClose(posTicket);
         NotifyTrade("📉 [" + sym + "] 多头全部清仓 (跌破防守底线 EMA338)");
        }
      else if(InpUseBreakEven && isPartiallyClosed && closePrice1 < openPrice)
        {
         trade.PositionClose(posTicket);
         NotifyTrade("🛡️ [" + sym + "] 多头触发保本止损，剩余仓位安全出局");
        }
      else if(!isPartiallyClosed && closePrice1 < ema288[1])
        {
         double closeVol = NormalizeVolume(sym, currentVolume * OPTIMIZED_PARTIAL_CLOSE);
         trade.PositionClosePartial(posTicket, closeVol);
         NotifyTrade("💰 [" + sym + "] 多头获利减仓 50% (跌破第一平仓线 EMA288)");
        }
     }
     
   if(hasSellPosition)
     {
      bool isPartiallyClosed = HasPartiallyClosed(posTicket);

      if(closePrice1 > ema338[1])
        {
         trade.PositionClose(posTicket);
         NotifyTrade("📈 [" + sym + "] 空头全部清仓 (突破防守底线 EMA338)");
        }
      else if(InpUseBreakEven && isPartiallyClosed && closePrice1 > openPrice)
        {
         trade.PositionClose(posTicket);
         NotifyTrade("🛡️ [" + sym + "] 空头触发保本止损，剩余仓位安全出局");
        }
      else if(!isPartiallyClosed && closePrice1 > ema288[1])
        {
         double closeVol = NormalizeVolume(sym, currentVolume * OPTIMIZED_PARTIAL_CLOSE);
         trade.PositionClosePartial(posTicket, closeVol);
         NotifyTrade("💰 [" + sym + "] 空头获利减仓 50% (突破第一平仓线 EMA288)");
        }
     }

   // --- 开仓逻辑 ---
   if(!hasBuyPosition && !hasSellPosition)
     {
      bool isTrending = (adx[1] > OPTIMIZED_ADX_THRESHOLD); // 使用最佳ADX阈值

      // 多头
      bool bullAlignment = (ema144[1] > ema169[1]) && (ema576[1] > ema676[1]);
      bool bullSlope = (ema169[0] > ema169[1]) && (ema676[0] > ema676[1]);
      bool bullCross = (ema12[1] > ema144[1] && ema12[1] > ema169[1]) && 
                       (ema12[2] <= ema144[2] || ema12[2] <= ema169[2]);

      if(bullAlignment && bullSlope && bullCross && isTrending)
        {
         double lotSize = CalculateLotSize(sym, ema338[1], POSITION_TYPE_BUY);
         if(lotSize > 0) 
           {
            trade.Buy(lotSize, sym, 0, 0, 0, "Vegas Bull");
            NotifyTrade("🟢 [" + sym + "] 多头信号确立！成功开多 " + DoubleToString(lotSize, 2) + " 手");
           }
        }

      // 空头
      bool bearAlignment = (ema144[1] < ema169[1]) && (ema576[1] < ema676[1]);
      bool bearSlope = (ema169[0] < ema169[1]) && (ema676[0] < ema676[1]);
      bool bearCross = (ema12[1] < ema144[1] && ema12[1] < ema169[1]) && 
                       (ema12[2] >= ema144[2] || ema12[2] >= ema169[2]);

      if(bearAlignment && bearSlope && bearCross && isTrending)
        {
         double lotSize = CalculateLotSize(sym, ema338[1], POSITION_TYPE_SELL);
         if(lotSize > 0) 
           {
            trade.Sell(lotSize, sym, 0, 0, 0, "Vegas Bear");
            NotifyTrade("🔴 [" + sym + "] 空头信号确立！成功开空 " + DoubleToString(lotSize, 2) + " 手");
           }
        }
     }

   symbols[index].lastBarTime = currentBarTime;
  }

//+------------------------------------------------------------------+
//| 辅助函数：发送带打印的推送通知                                       |
//+------------------------------------------------------------------+
void NotifyTrade(string message)
  {
   Print(message);
   SendNotification(message); // 调用MT5底层手机推送功能
  }

//+------------------------------------------------------------------+
//| 辅助函数：生成并发送每日报告 (北京时间上午11:00)                       |
//+------------------------------------------------------------------+
void CheckAndSendDailyReport()
  {
   // 将格林威治时间(GMT)转换为北京时间(UTC+8)
   datetime gmtTime = TimeGMT();
   datetime beijingTime = gmtTime + 8 * 3600; 
   
   MqlDateTime dt;
   TimeToStruct(beijingTime, dt);
   
   // 检查是否到了北京时间上午11点，且今天还没有发送过
   if(dt.hour == 11 && dt.day != lastReportDay)
     {
      // 1. 获取基础资金信息
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      int posCount = PositionsTotal();
      
      // 2. 计算昨天一整天的利润 (需要计算服务器时间的昨天0点到24点)
      datetime serverTime = TimeCurrent();
      MqlDateTime sdt;
      TimeToStruct(serverTime, sdt);
      
      // 计算今天服务器0点的时间戳
      datetime startOfTodayServer = serverTime - (sdt.hour * 3600 + sdt.min * 60 + sdt.sec);
      datetime startOfYesterdayServer = startOfTodayServer - 86400; // 昨天0点
      datetime endOfYesterdayServer = startOfTodayServer - 1;       // 昨天23:59:59
      
      HistorySelect(startOfYesterdayServer, endOfYesterdayServer);
      int deals = HistoryDealsTotal();
      double yesterdayProfit = 0.0;
      
      for(int i = 0; i < deals; i++)
        {
         ulong ticket = HistoryDealGetTicket(i);
         // 累计单笔利润、隔夜利息、手续费
         yesterdayProfit += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         yesterdayProfit += HistoryDealGetDouble(ticket, DEAL_SWAP);
         yesterdayProfit += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
        }
        
      // 3. 组装财报文本
      string report = "📊【Vegas系统每日简报】\n";
      report += "时间：北京时间 11:00\n";
      report += "--------------------\n";
      report += "💰 账户余额：$" + DoubleToString(balance, 2) + "\n";
      report += "⚖️ 动态净值：$" + DoubleToString(equity, 2) + "\n";
      report += "📦 当前持仓单数：" + IntegerToString(posCount) + " 单\n";
      report += "--------------------\n";
      
      if(yesterdayProfit > 0)
         report += "🎉 昨日盈亏：+$" + DoubleToString(yesterdayProfit, 2);
      else if(yesterdayProfit < 0)
         report += "📉 昨日盈亏：-$" + DoubleToString(MathAbs(yesterdayProfit), 2);
      else
         report += "⏸️ 昨日盈亏：$0.00 (无平仓交易)";

      // 发送通知
      NotifyTrade(report);
      
      // 更新记录，防止今天重复发送
      lastReportDay = dt.day;
     }
  }

//+------------------------------------------------------------------+
//| 查询历史记录判断部分平仓                                           |
//+------------------------------------------------------------------+
bool HasPartiallyClosed(ulong position_ticket)
  {
   if(HistorySelectByPosition(position_ticket))
     {
      int deals = HistoryDealsTotal();
      int out_deals = 0;
      for(int i = 0; i < deals; i++)
        {
         ulong deal_ticket = HistoryDealGetTicket(i);
         if(HistoryDealGetInteger(deal_ticket, DEAL_ENTRY) == DEAL_ENTRY_OUT) out_deals++;
        }
      if(out_deals > 0) return true;
     }
   return false;
  }

//+------------------------------------------------------------------+
//| 手数计算与规范化 (逻辑保持不变)                                     |
//+------------------------------------------------------------------+
double CalculateLotSize(string sym, double slPrice, ENUM_POSITION_TYPE type)
  {
   double currentPrice = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_ASK) : SymbolInfoDouble(sym, SYMBOL_BID);
   double riskAmount = AccountInfoDouble(ACCOUNT_BALANCE) * (InpRiskPercent / 100.0);
   double tickSize = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);
   if(tickSize == 0 || tickValue == 0) return 0; 
   double slDistanceTicks = MathAbs(currentPrice - slPrice) / tickSize;
   if(slDistanceTicks <= 0) slDistanceTicks = 1; 
   double calcLot = riskAmount / (slDistanceTicks * tickValue);
   return NormalizeVolume(sym, calcLot);
  }

double NormalizeVolume(string sym, double vol)
  {
   double minLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
   double lot = MathFloor(vol / stepLot) * stepLot;
   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;
   return lot;
  }