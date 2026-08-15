#property strict

#include "core/EaController.mqh"

EaController controller;

int OnInit()
{
   return controller.OnInit();
}

void OnTick()
{
   controller.OnTick();
}

void OnDeinit(const int reason)
{
   controller.OnDeinit(reason);
}
