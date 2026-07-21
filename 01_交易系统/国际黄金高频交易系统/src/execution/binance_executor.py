from typing import Dict, Any, Optional, List
import ccxt.async_support as ccxt
from datetime import datetime
from .base_executor import BaseExecutor

class BinanceExecutor(BaseExecutor):
    """Binance合约交易执行器"""
    
    def __init__(self, api_key: str, api_secret: str, test_mode: bool = True):
        super().__init__(api_key, api_secret, test_mode)
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True,
                'recvWindow': 60000
            }
        })
        
    async def _init_exchange(self):
        """初始化交易所连接"""
        if not self.exchange:
            self.exchange = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000
                }
            })
        await self.exchange.load_markets()
        
    async def open_position(self,
                          symbol: str,
                          direction: str,
                          volume: float,
                          price: Optional[float] = None,
                          stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None) -> Dict[str, Any]:
        """开仓"""
        try:
            await self._init_exchange()
            
            # 设置杠杆
            await self.exchange.fapiPrivate_post_leverage({
                'symbol': symbol.replace('/', ''),
                'leverage': 20  # 默认20倍杠杆
            })
            
            # 准备订单参数
            order_type = 'MARKET' if price is None else 'LIMIT'
            side = 'buy' if direction == 'long' else 'sell'
            
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': volume,
            }
            
            if price is not None:
                order_params['price'] = price
                
            # 发送订单
            order = await self.exchange.create_order(**order_params)
            
            # 如果设置了止损止盈
            if stop_loss or take_profit:
                position_side = 'LONG' if direction == 'long' else 'SHORT'
                if stop_loss:
                    await self.exchange.fapiPrivate_post_order({
                        'symbol': symbol.replace('/', ''),
                        'side': 'sell' if direction == 'long' else 'buy',
                        'type': 'STOP_MARKET',
                        'stopPrice': stop_loss,
                        'quantity': volume,
                        'positionSide': position_side,
                        'timeInForce': 'GTC'
                    })
                    
                if take_profit:
                    await self.exchange.fapiPrivate_post_order({
                        'symbol': symbol.replace('/', ''),
                        'side': 'sell' if direction == 'long' else 'buy',
                        'type': 'TAKE_PROFIT_MARKET',
                        'stopPrice': take_profit,
                        'quantity': volume,
                        'positionSide': position_side,
                        'timeInForce': 'GTC'
                    })
                    
            return order
            
        except Exception as e:
            raise Exception(f"开仓失败: {str(e)}")
            
    async def close_position(self,
                           position_id: str,
                           volume: Optional[float] = None) -> Dict[str, Any]:
        """平仓"""
        try:
            await self._init_exchange()
            
            # 获取持仓信息
            position = await self.exchange.fapiPrivate_get_position({'positionId': position_id})
            if not position:
                raise Exception("未找到持仓")
                
            # 准备平仓参数
            symbol = position['symbol']
            amount = volume if volume else float(position['positionAmt'])
            side = 'sell' if float(position['positionAmt']) > 0 else 'buy'
            
            # 发送平仓订单
            order = await self.exchange.create_order(
                symbol=symbol,
                type='MARKET',
                side=side,
                amount=abs(amount),
                params={'reduceOnly': True}
            )
            
            return order
            
        except Exception as e:
            raise Exception(f"平仓失败: {str(e)}")
            
    async def modify_position(self,
                            position_id: str,
                            stop_loss: Optional[float] = None,
                            take_profit: Optional[float] = None) -> Dict[str, Any]:
        """修改持仓"""
        try:
            await self._init_exchange()
            
            # 获取持仓信息
            position = await self.exchange.fapiPrivate_get_position({'positionId': position_id})
            if not position:
                raise Exception("未找到持仓")
                
            # 取消现有的止损止盈订单
            open_orders = await self.exchange.fapiPrivate_get_openOrders({
                'symbol': position['symbol']
            })
            
            for order in open_orders:
                if order['type'] in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']:
                    await self.exchange.cancel_order(order['orderId'], position['symbol'])
                    
            # 设置新的止损止盈
            position_side = 'LONG' if float(position['positionAmt']) > 0 else 'SHORT'
            if stop_loss:
                await self.exchange.fapiPrivate_post_order({
                    'symbol': position['symbol'],
                    'side': 'sell' if position_side == 'LONG' else 'buy',
                    'type': 'STOP_MARKET',
                    'stopPrice': stop_loss,
                    'quantity': abs(float(position['positionAmt'])),
                    'positionSide': position_side,
                    'timeInForce': 'GTC'
                })
                
            if take_profit:
                await self.exchange.fapiPrivate_post_order({
                    'symbol': position['symbol'],
                    'side': 'sell' if position_side == 'LONG' else 'buy',
                    'type': 'TAKE_PROFIT_MARKET',
                    'stopPrice': take_profit,
                    'quantity': abs(float(position['positionAmt'])),
                    'positionSide': position_side,
                    'timeInForce': 'GTC'
                })
                
            return {"status": "success", "message": "持仓修改成功"}
            
        except Exception as e:
            raise Exception(f"修改持仓失败: {str(e)}")
            
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取持仓"""
        try:
            await self._init_exchange()
            
            params = {}
            if symbol:
                params['symbol'] = symbol.replace('/', '')
                
            positions = await self.exchange.fapiPrivate_get_positionRisk(params)
            return [pos for pos in positions if float(pos['positionAmt']) != 0]
            
        except Exception as e:
            raise Exception(f"获取持仓失败: {str(e)}")
            
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            await self._init_exchange()
            account = await self.exchange.fapiPrivate_get_account()
            return {
                'total_balance': float(account['totalWalletBalance']),
                'unrealized_pnl': float(account['totalUnrealizedProfit']),
                'margin_balance': float(account['totalMarginBalance']),
                'available_balance': float(account['availableBalance']),
                'position_risk': float(account['totalPositionInitialMargin']),
                'update_time': datetime.fromtimestamp(account['updateTime'] / 1000)
            }
            
        except Exception as e:
            raise Exception(f"获取账户信息失败: {str(e)}")
            
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