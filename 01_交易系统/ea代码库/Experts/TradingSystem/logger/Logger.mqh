#ifndef LOGGER_MQH
#define LOGGER_MQH

#include "../config/InputConfig.mqh"

class Logger
{
private:
   bool initialized;

   string BuildMessage(const string moduleName,
                       const string level,
                       const string eventName,
                       const string detail)
   {
      string timeText = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
      return timeText + " [" + moduleName + "] [" + level + "] [" + _Symbol + "] " + eventName + " | " + detail;
   }

   void Write(const string moduleName,
              const string level,
              const string eventName,
              const string detail)
   {
      Print(BuildMessage(moduleName, level, eventName, detail));
   }

public:
   Logger()
   {
      initialized = false;
   }

   bool Init()
   {
      initialized = true;
      return initialized;
   }

   void Info(const string moduleName, const string eventName, const string detail)
   {
      Write(moduleName, "INFO", eventName, detail);
   }

   void Warning(const string moduleName, const string eventName, const string detail)
   {
      Write(moduleName, "WARNING", eventName, detail);
   }

   void Error(const string moduleName, const string eventName, const string detail)
   {
      Write(moduleName, "ERROR", eventName, detail);
   }

   void Debug(const string moduleName, const string eventName, const string detail)
   {
      if(!InpEnableDebugLog)
      {
         return;
      }

      Write(moduleName, "DEBUG", eventName, detail);
   }

   string BoolToText(const bool value)
   {
      if(value)
      {
         return "true";
      }

      return "false";
   }
};

#endif
