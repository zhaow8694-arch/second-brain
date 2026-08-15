#ifndef NOTIFICATION_CENTER_MQH
#define NOTIFICATION_CENTER_MQH

class COmniNotificationCenter
{
private:
   bool pushEnabled;
   bool verbose;
   string prefix;
   datetime lastDailyPush;

   void Emit(const string level, const string text, const bool push)
   {
      string message = prefix + " [" + level + "] " + text;
      Print(message);
      if(pushEnabled && push)
         SendNotification(message);
   }

public:
   COmniNotificationCenter()
   {
      pushEnabled = false;
      verbose = true;
      prefix = "Omni";
      lastDailyPush = 0;
   }

   void Init(const bool enablePush, const string messagePrefix, const bool verboseLog)
   {
      pushEnabled = enablePush;
      prefix = messagePrefix;
      verbose = verboseLog;
   }

   void Info(const string text)
   {
      if(verbose)
         Emit("INFO", text, false);
   }

   void Warn(const string text)
   {
      Emit("WARN", text, true);
   }

   void Trade(const string text)
   {
      Emit("TRADE", text, true);
   }

   void Daily(const string text)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);
      datetime dayStamp = (datetime)(TimeCurrent() - (now.hour * 3600 + now.min * 60 + now.sec));
      if(dayStamp == lastDailyPush)
         return;

      lastDailyPush = dayStamp;
      Emit("DAILY", text, true);
   }
};

#endif
