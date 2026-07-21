from typing import Dict, Any, Optional, List
from datetime import datetime
from .base_executor import BaseExecutor
from .binance_executor import BinanceExecutor
from .mt4_executor import MT4Executor

class ExecutionManager:
    """交易执行管理器"""
    
    def __init__(self):
        self.executors: Dict[str, BaseExecutor] = {}
        self.active_positions: Dict[str, List[Dict[str, Any]]] = {}
        
    def add_executor(self, name: str, executor: BaseExecutor):
        """添加执行器"""
        self.executors[name] = executor
        
    def get_executor(self, name: str) -> Optional[BaseExecutor]:
        """获取执行器"""
        return self.executors.get(name)
        
    async def execute_signal(self, signal: Dict[str, Any], executor_name: str) -> Dict[str, Any]:
        """执行交易信号"""
        executor = self.get_executor(executor_name)
        if not executor:
            raise ValueError(f"未找到执行器: {executor_name}")
            
        try:
            # 获取账户信息
            account_info = await executor.get_account_info()
            
            # 检查是否有足够的可用保证金
            if signal['position_size'] * signal['metadata']['market_data']['close'] > account_info['available_balance']:
                raise ValueError("可用保证金不足")
                
            # 如果需要锁仓
            if signal['should_lock']:
                orders = []
                # 添加锁仓订单
                if signal['lock_size']:
                    lock_direction = 'sell' if signal['direction'] == 'buy' else 'buy'
                    orders.append({
                        'type': 'open',
                        'symbol': signal['symbol'],
                        'direction': lock_direction,
                        'volume': signal['lock_size']
                    })
                    
            # 处理交易建议
            suggestions = signal['trading_suggestions']
            if suggestions['action'] == 'open':
                orders = []
                # 添加分批开仓订单
                for sub_pos in suggestions['sub_positions']:
                    price = signal['metadata']['market_data']['close']
                    if sub_pos['price_offset']:
                        price += price * sub_pos['price_offset']
                        
                    orders.append({
                        'type': 'open',
                        'symbol': signal['symbol'],
                        'direction': signal['direction'],
                        'volume': sub_pos['size'],
                        'price': price,
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit']
                    })
                    
                # 执行批量订单
                results = await executor.execute_batch_orders(orders)
                
                # 更新活跃持仓
                if signal['symbol'] not in self.active_positions:
                    self.active_positions[signal['symbol']] = []
                    
                for result in results:
                    if result['status'] == 'success':
                        position = {
                            'id': result['result']['id'],
                            'symbol': signal['symbol'],
                            'direction': signal['direction'],
                            'volume': result['order']['volume'],
                            'open_price': result['result']['price'],
                            'open_time': datetime.now(),
                            'stop_loss': signal['stop_loss'],
                            'take_profit': signal['take_profit'],
                            'signal_id': signal['id']
                        }
                        self.active_positions[signal['symbol']].append(position)
                        
                return {
                    'status': 'success',
                    'message': '交易信号执行成功',
                    'orders': results
                }
                
            elif suggestions['action'] == 'lock':
                # 执行锁仓订单
                results = await executor.execute_batch_orders(orders)
                return {
                    'status': 'success',
                    'message': '锁仓执行成功',
                    'orders': results
                }
                
            else:
                return {
                    'status': 'error',
                    'message': f"未知的交易建议动作: {suggestions['action']}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def close_positions(self,
                            symbol: str,
                            executor_name: str,
                            direction: Optional[str] = None) -> Dict[str, Any]:
        """平仓"""
        executor = self.get_executor(executor_name)
        if not executor:
            raise ValueError(f"未找到执行器: {executor_name}")
            
        try:
            positions = await executor.get_positions(symbol)
            if direction:
                positions = [p for p in positions if p['type'] == direction]
                
            if not positions:
                return {
                    'status': 'warning',
                    'message': '没有需要平仓的持仓'
                }
                
            orders = []
            for position in positions:
                orders.append({
                    'type': 'close',
                    'position_id': position['ticket'],
                    'volume': position['volume']
                })
                
            results = await executor.execute_batch_orders(orders)
            
            # 更新活跃持仓
            if symbol in self.active_positions:
                closed_ids = [order['position_id'] for order in orders]
                self.active_positions[symbol] = [
                    pos for pos in self.active_positions[symbol]
                    if pos['id'] not in closed_ids
                ]
                
            return {
                'status': 'success',
                'message': '平仓执行成功',
                'orders': results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def modify_positions(self,
                             symbol: str,
                             executor_name: str,
                             stop_loss: Optional[float] = None,
                             take_profit: Optional[float] = None,
                             direction: Optional[str] = None) -> Dict[str, Any]:
        """修改持仓"""
        executor = self.get_executor(executor_name)
        if not executor:
            raise ValueError(f"未找到执行器: {executor_name}")
            
        try:
            positions = await executor.get_positions(symbol)
            if direction:
                positions = [p for p in positions if p['type'] == direction]
                
            if not positions:
                return {
                    'status': 'warning',
                    'message': '没有需要修改的持仓'
                }
                
            orders = []
            for position in positions:
                orders.append({
                    'type': 'modify',
                    'position_id': position['ticket'],
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                })
                
            results = await executor.execute_batch_orders(orders)
            
            # 更新活跃持仓
            if symbol in self.active_positions:
                modified_ids = [order['position_id'] for order in orders]
                for pos in self.active_positions[symbol]:
                    if pos['id'] in modified_ids:
                        if stop_loss is not None:
                            pos['stop_loss'] = stop_loss
                        if take_profit is not None:
                            pos['take_profit'] = take_profit
                            
            return {
                'status': 'success',
                'message': '持仓修改成功',
                'orders': results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def get_all_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有持仓"""
        all_positions = {}
        for name, executor in self.executors.items():
            try:
                positions = await executor.get_positions()
                all_positions[name] = positions
            except Exception as e:
                print(f"获取{name}持仓失败: {str(e)}")
                all_positions[name] = []
                
        return all_positions
        
    async def get_all_account_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有账户信息"""
        all_info = {}
        for name, executor in self.executors.items():
            try:
                info = await executor.get_account_info()
                all_info[name] = info
            except Exception as e:
                print(f"获取{name}账户信息失败: {str(e)}")
                all_info[name] = {}
                
        return all_info 