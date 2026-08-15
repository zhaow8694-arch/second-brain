#ifndef ENTRY_GUARD_MQH
#define ENTRY_GUARD_MQH

#include "OmniTypes.mqh"

class COmniEntryGuard
{
private:
   datetime lastInitialH1[OMNI_PRODUCT_COUNT];
   datetime lastExitTime[OMNI_PRODUCT_COUNT];

   bool TimeAtOrAfter(const int currentHour,
                      const int currentMinute,
                      const int limitHour,
                      const int limitMinute)
   {
      if(currentHour > limitHour) return true;
      if(currentHour == limitHour && currentMinute >= limitMinute) return true;
      return false;
   }

   string TimeText(const int hour, const int minute)
   {
      string hh = IntegerToString(hour);
      string mm = IntegerToString(minute);
      if(hour < 10) hh = "0" + hh;
      if(minute < 10) mm = "0" + mm;
      return hh + ":" + mm;
   }

public:
   void Reset()
   {
      ArrayInitialize(lastInitialH1, 0);
      ArrayInitialize(lastExitTime, 0);
   }

   bool ShouldBlockAllNewEntries(const bool closeOnFriday,
                                 const int fridayCloseHour,
                                 const int fridayCloseMinute,
                                 string &reason)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);

      if(now.day_of_week == 0 || now.day_of_week == 6)
      {
         reason = "weekend entry block";
         return true;
      }

      if(closeOnFriday &&
         now.day_of_week == 5 &&
         TimeAtOrAfter(now.hour, now.min, fridayCloseHour, fridayCloseMinute))
      {
         reason = "friday entry block after " + TimeText(fridayCloseHour, fridayCloseMinute);
         return true;
      }

      reason = "entry allowed";
      return false;
   }

   bool ShouldBlockRangeNewEntry(const int rangeCloseHour,
                                 const int rangeCloseMinute,
                                 string &reason)
   {
      MqlDateTime now;
      TimeToStruct(TimeCurrent(), now);

      if(TimeAtOrAfter(now.hour, now.min, rangeCloseHour, rangeCloseMinute))
      {
         reason = "range entry block after " + TimeText(rangeCloseHour, rangeCloseMinute);
         return true;
      }

      reason = "range entry allowed";
      return false;
   }

   bool AllowInitialEntry(const ENUM_OMNI_PRODUCT product,
                          const datetime h1BarTime,
                          string &reason)
   {
      int index = (int)product;
      if(index < 0 || index >= OMNI_PRODUCT_COUNT)
      {
         reason = "unknown product";
         return false;
      }

      if(h1BarTime > 0 && lastInitialH1[index] == h1BarTime)
      {
         reason = "initial entry already used on current H1 bar";
         return false;
      }

      reason = "initial entry allowed";
      return true;
   }

   bool AllowReentryAfterExit(const ENUM_OMNI_PRODUCT product,
                              const int cooldownMinutes,
                              string &reason)
   {
      int index = (int)product;
      if(index < 0 || index >= OMNI_PRODUCT_COUNT)
      {
         reason = "unknown product";
         return false;
      }

      if(cooldownMinutes <= 0 || lastExitTime[index] <= 0)
      {
         reason = "exit cooldown allowed";
         return true;
      }

      int elapsed = (int)(TimeCurrent() - lastExitTime[index]);
      int required = cooldownMinutes * 60;
      if(elapsed < required)
      {
         int remaining = (required - elapsed + 59) / 60;
         reason = "reentry cooldown after exit, remaining " + IntegerToString(remaining) + " minutes";
         return false;
      }

      reason = "exit cooldown allowed";
      return true;
   }

   void MarkInitialEntry(const ENUM_OMNI_PRODUCT product,
                         const datetime h1BarTime)
   {
      int index = (int)product;
      if(index < 0 || index >= OMNI_PRODUCT_COUNT) return;
      lastInitialH1[index] = h1BarTime;
   }

   void MarkExit(const ENUM_OMNI_PRODUCT product,
                 const datetime exitTime)
   {
      int index = (int)product;
      if(index < 0 || index >= OMNI_PRODUCT_COUNT) return;
      lastExitTime[index] = exitTime;
   }
};

#endif
