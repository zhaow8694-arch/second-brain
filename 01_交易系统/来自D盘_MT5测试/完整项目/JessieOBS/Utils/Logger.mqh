#ifndef _LOGGER_MQH_
#define _LOGGER_MQH_

#include "../Includes/Defines.mqh"

class CLogger
{
private:
   bool   m_enabled;
   int    m_level;
   bool   m_alert;
   bool   m_push;

public:
   CLogger()
   {
      m_enabled = true;
      m_level   = LOG_INFO;
      m_alert   = false;
      m_push    = false;
   }

   void Init(bool enabled, int level, bool alert, bool push)
   {
      m_enabled = enabled;
      m_level   = level;
      m_alert   = alert;
      m_push    = push;
   }

   string GetTimestamp()
   {
      return TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   }

   string LevelToString(int level)
   {
      switch(level)
      {
         case LOG_INFO:  return "INFO";
         case LOG_WARN:  return "WARN";
         case LOG_ERROR: return "ERROR";
      }
      return "UNKN";
   }

   void Log(int level, string message)
   {
      if(!m_enabled || level < m_level) return;

      string entry = GetTimestamp() + " [" + LevelToString(level) + "] " + message;
      Print(entry);

      if(level == LOG_ERROR)
      {
         if(m_alert) Alert("JessieOBS ERROR: ", message);
         if(m_push)  SendNotification("JessieOBS ERROR: " + message);
      }
      else if(level == LOG_WARN)
      {
         if(m_alert) Alert("JessieOBS WARN: ", message);
      }
   }

   void Info(string message)  { Log(LOG_INFO, message); }
   void Warn(string message)  { Log(LOG_WARN, message); }
   void Error(string message) { Log(LOG_ERROR, message); }
};

#endif
