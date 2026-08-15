#property copyright "MT5tools"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>

input int    InpBtnX              = 20;   // Button start X
input int    InpBtnY              = 20;   // Button start Y
input int    InpBtnWidth          = 170;  // Button width
input int    InpBtnHeight         = 28;   // Button height
input int    InpBtnGap            = 8;    // Gap between buttons
input color  InpBtnColorAll       = clrTomato;
input color  InpBtnColorProfit    = clrSeaGreen;
input color  InpBtnColorLoss      = clrOrangeRed;
input bool   InpNeedConfirm       = true; // Need popup confirm
input bool   InpUseAsyncClose     = true; // Send close requests asynchronously
input int    InpRetryRounds       = 2;    // Retry rounds for remaining positions
input int    InpRoundDelayMs      = 150;  // Delay between rounds (ms)

enum CloseMode
{
   CLOSE_ALL = 0,
   CLOSE_PROFIT_ONLY = 1,
   CLOSE_LOSS_ONLY = 2
};

string BTN_ALL    = "EA_BTN_CLOSE_ALL";
string BTN_PROFIT = "EA_BTN_CLOSE_PROFIT";
string BTN_LOSS   = "EA_BTN_CLOSE_LOSS";

CTrade g_trade;

int OnInit()
{
   g_trade.SetAsyncMode(InpUseAsyncClose);

   if(!CreateButton(BTN_ALL,    "一键平全部持仓",       0, InpBtnColorAll))
      return(INIT_FAILED);

   if(!CreateButton(BTN_PROFIT, "一键平所有盈利持仓",   1, InpBtnColorProfit))
      return(INIT_FAILED);

   if(!CreateButton(BTN_LOSS,   "一键平所有亏损持仓",   2, InpBtnColorLoss))
      return(INIT_FAILED);

   Print("PositionBatchCloser EA loaded.");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   ObjectDelete(0, BTN_ALL);
   ObjectDelete(0, BTN_PROFIT);
   ObjectDelete(0, BTN_LOSS);
}

void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id != CHARTEVENT_OBJECT_CLICK)
      return;

   if(sparam == BTN_ALL)
      ClosePositions(CLOSE_ALL);
   else if(sparam == BTN_PROFIT)
      ClosePositions(CLOSE_PROFIT_ONLY);
   else if(sparam == BTN_LOSS)
      ClosePositions(CLOSE_LOSS_ONLY);
}

bool CreateButton(const string name, const string text, const int row, const color btn_color)
{
   int x = InpBtnX;
   int y = InpBtnY + row * (InpBtnHeight + InpBtnGap);

   if(!ObjectCreate(0, name, OBJ_BUTTON, 0, 0, 0))
   {
      Print("Failed to create button: ", name);
      return(false);
   }

   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE, InpBtnWidth);
   ObjectSetInteger(0, name, OBJPROP_YSIZE, InpBtnHeight);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, btn_color);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 10);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, clrBlack);
   ObjectSetString(0, name, OBJPROP_TEXT, text);

   return(true);
}

void ClosePositions(const CloseMode mode)
{
   int total = PositionsTotal();
   if(total <= 0)
   {
      Alert("当前没有持仓。");
      return;
   }

   string action_text = ModeToText(mode);
   if(InpNeedConfirm)
   {
      int answer = MessageBox("确认执行：" + action_text + " ?", "EA 批量平仓确认", MB_YESNO | MB_ICONQUESTION);
      if(answer != IDYES)
         return;
   }

   ulong tickets[];
   CollectMatchedTickets(mode, tickets);
   int matched = ArraySize(tickets);
   if(matched <= 0)
   {
      Alert("没有符合条件的持仓。");
      return;
   }

   int send_success = 0;
   int rounds = MathMax(1, InpRetryRounds);
   for(int r = 0; r < rounds; r++)
   {
      for(int i = 0; i < matched; i++)
      {
         ulong ticket = tickets[i];
         if(ticket == 0)
            continue;

         // Already closed in a previous round.
         if(!PositionSelectByTicket(ticket))
            continue;

         if(g_trade.PositionClose(ticket))
            send_success++;
         else
            PrintFormat("Close request failed. Ticket=%I64u, err=%d", ticket, GetLastError());
      }

      if(r < rounds - 1 && InpRoundDelayMs > 0)
         Sleep(InpRoundDelayMs);
   }

   int final_closed = 0;
   for(int i = 0; i < matched; i++)
   {
      if(!PositionSelectByTicket(tickets[i]))
         final_closed++;
   }

   string msg = StringFormat("%s 完成。符合条件: %d, 已平仓: %d, 未平: %d, 已发送请求: %d",
                             action_text, matched, final_closed, matched - final_closed, send_success);
   Alert(msg);
   Print(msg);
}

void CollectMatchedTickets(const CloseMode mode, ulong &tickets[])
{
   ArrayResize(tickets, 0);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;

      double profit = PositionGetDouble(POSITION_PROFIT);
      if(!ShouldClose(mode, profit))
         continue;

      int n = ArraySize(tickets);
      ArrayResize(tickets, n + 1);
      tickets[n] = ticket;
   }
}

bool ShouldClose(const CloseMode mode, const double profit)
{
   if(mode == CLOSE_ALL)
      return(true);

   if(mode == CLOSE_PROFIT_ONLY)
      return(profit > 0.0);

   if(mode == CLOSE_LOSS_ONLY)
      return(profit < 0.0);

   return(false);
}

string ModeToText(const CloseMode mode)
{
   if(mode == CLOSE_ALL)
      return("一键平全部持仓");

   if(mode == CLOSE_PROFIT_ONLY)
      return("一键平所有盈利持仓");

   if(mode == CLOSE_LOSS_ONLY)
      return("一键平所有亏损持仓");

   return("未知操作");
}
