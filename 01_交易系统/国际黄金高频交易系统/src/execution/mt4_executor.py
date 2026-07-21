from typing import Dict, Any, Optional, List
import asyncio
import json
import websockets
from datetime import datetime
from .base_executor import BaseExecutor

class MT4Executor(BaseExecutor):
    """MT4交易执行器"""
    
    def __init__(self, api_key: str, api_secret: str, test_mode: bool = True):
        super().__init__(api_key, api_secret, test_mode)
        self.ws_url = "ws://localhost:8080"  # MT4 WebSocket服务器地址
        self.ws = None
        
    async def _connect(self):
        """连接到MT4 WebSocket服务器"""
        if not self.ws:
            self.ws = await websockets.connect(self.ws_url)
            
    async def _send_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发送命令到MT4"""
        try:
            await self._connect()
            
            message = {
                "command": command,
                "params": params,
                "api_key": self.api_key,
                "timestamp": datetime.now().timestamp()
            }
            
            await self.ws.send(json.dumps(message))
            response = await self.ws.recv()
            return json.loads(response)
            
        except Exception as e:
            raise Exception(f"MT4命令执行失败: {str(e)}")
            
    async def open_position(self,
                          symbol: str,
                          direction: str,
                          volume: float,
                          price: Optional[float] = None,
                          stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None) -> Dict[str, Any]:
        """开仓"""
        params = {
            "symbol": symbol,
            "cmd": 0 if direction == "buy" else 1,  # 0=BUY, 1=SELL
            "volume": volume,
            "price": price if price else 0,  # 0表示市价
            "slippage": 3,
            "stop_loss": stop_loss if stop_loss else 0,
            "take_profit": take_profit if take_profit else 0,
            "comment": "AI Trading System",
            "magic": 123456  # 魔术数字，用于标识订单来源
        }
        
        response = await self._send_command("OrderSend", params)
        if response.get("error"):
            raise Exception(f"开仓失败: {response['error']}")
            
        return response
        
    async def close_position(self,
                           position_id: str,
                           volume: Optional[float] = None) -> Dict[str, Any]:
        """平仓"""
        # 首先获取订单信息
        order_info = await self._send_command("OrderSelect", {
            "ticket": int(position_id),
            "select_by": 0  # 0=SELECT_BY_TICKET
        })
        
        if order_info.get("error"):
            raise Exception(f"获取订单信息失败: {order_info['error']}")
            
        # 准备平仓参数
        close_volume = volume if volume else order_info["volume"]
        params = {
            "ticket": int(position_id),
            "volume": close_volume,
            "price": 0,  # 市价
            "slippage": 3
        }
        
        response = await self._send_command("OrderClose", params)
        if response.get("error"):
            raise Exception(f"平仓失败: {response['error']}")
            
        return response
        
    async def modify_position(self,
                            position_id: str,
                            stop_loss: Optional[float] = None,
                            take_profit: Optional[float] = None) -> Dict[str, Any]:
        """修改持仓"""
        # 首先获取订单信息
        order_info = await self._send_command("OrderSelect", {
            "ticket": int(position_id),
            "select_by": 0
        })
        
        if order_info.get("error"):
            raise Exception(f"获取订单信息失败: {order_info['error']}")
            
        # 准备修改参数
        params = {
            "ticket": int(position_id),
            "price": order_info["open_price"],
            "stop_loss": stop_loss if stop_loss is not None else order_info["stop_loss"],
            "take_profit": take_profit if take_profit is not None else order_info["take_profit"]
        }
        
        response = await self._send_command("OrderModify", params)
        if response.get("error"):
            raise Exception(f"修改持仓失败: {response['error']}")
            
        return response
        
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取持仓"""
        positions = []
        total_orders = await self._send_command("OrdersTotal", {})
        
        for i in range(total_orders):
            order = await self._send_command("OrderSelect", {
                "index": i,
                "select_by": 1  # 1=SELECT_BY_POS
            })
            
            if order.get("error"):
                continue
                
            if order["type"] <= 1:  # 0=BUY, 1=SELL
                if not symbol or order["symbol"] == symbol:
                    positions.append({
                        "ticket": order["ticket"],
                        "symbol": order["symbol"],
                        "type": "buy" if order["type"] == 0 else "sell",
                        "volume": order["volume"],
                        "open_price": order["open_price"],
                        "stop_loss": order["stop_loss"],
                        "take_profit": order["take_profit"],
                        "profit": order["profit"],
                        "comment": order["comment"],
                        "open_time": order["open_time"]
                    })
                    
        return positions
        
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        account = await self._send_command("AccountInfo", {})
        
        return {
            "balance": account["balance"],
            "equity": account["equity"],
            "margin": account["margin"],
            "free_margin": account["free_margin"],
            "profit": account["profit"],
            "leverage": account["leverage"],
            "currency": account["currency"]
        }
        
    async def execute_batch_orders(self,
                                 orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量执行订单"""
        results = []
        for order in orders:
            try:
                if order['type'] == 'open':
                    result = await self.open_position(
                        symbol=order['symbol'],
                        direction=order['direction'],
                        volume=order['volume'],
                        price=order.get('price'),
                        stop_loss=order.get('stop_loss'),
                        take_profit=order.get('take_profit')
                    )
                elif order['type'] == 'close':
                    result = await self.close_position(
                        position_id=order['position_id'],
                        volume=order.get('volume')
                    )
                elif order['type'] == 'modify':
                    result = await self.modify_position(
                        position_id=order['position_id'],
                        stop_loss=order.get('stop_loss'),
                        take_profit=order.get('take_profit')
                    )
                else:
                    result = {'status': 'error', 'message': f"未知的订单类型: {order['type']}"}
                    
                results.append({
                    'order': order,
                    'result': result,
                    'status': 'success'
                })
                
            except Exception as e:
                results.append({
                    'order': order,
                    'error': str(e),
                    'status': 'error'
                })
                
        return results
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.ws:
            await self.ws.close() 