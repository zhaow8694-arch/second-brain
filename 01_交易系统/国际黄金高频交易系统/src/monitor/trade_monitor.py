from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from execution.execution_manager import ExecutionManager
from risk.advanced_risk_controller import AdvancedRiskController

class TradeMonitor:
    """交易监控器"""
    
    def __init__(self,
                 execution_manager: ExecutionManager,
                 risk_controller: AdvancedRiskController,
                 check_interval: float = 1.0):
        self.execution_manager = execution_manager
        self.risk_controller = risk_controller
        self.check_interval = check_interval
        self.running = False
        self.position_updates: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        
    async def start(self):
        """启动监控"""
        self.running = True
        await asyncio.gather(
            self._monitor_positions(),
            self._monitor_risk_metrics(),
            self._generate_reports()
        )
        
    async def stop(self):
        """停止监控"""
        self.running = False
        
    async def _monitor_positions(self):
        """监控持仓状态"""
        while self.running:
            try:
                # 获取所有持仓
                all_positions = await self.execution_manager.get_all_positions()
                
                for executor_name, positions in all_positions.items():
                    executor = self.execution_manager.get_executor(executor_name)
                    if not executor:
                        continue
                        
                    for position in positions:
                        # 获取当前市场数据
                        symbol = position['symbol']
                        current_price = await self._get_current_price(executor, symbol)
                        atr_value = await self.risk_controller._get_atr(symbol)
                        
                        # 检查是否需要调整止损
                        new_stop_loss = await self.risk_controller.should_adjust_stop_loss(
                            position, current_price, atr_value
                        )
                        
                        if new_stop_loss:
                            # 更新止损位置
                            await self.execution_manager.modify_positions(
                                symbol=symbol,
                                executor_name=executor_name,
                                stop_loss=new_stop_loss,
                                position_id=position['id']
                            )
                            
                        # 记录持仓更新
                        self.position_updates.append({
                            'timestamp': datetime.now(),
                            'executor': executor_name,
                            'symbol': symbol,
                            'position_id': position['id'],
                            'current_price': current_price,
                            'stop_loss': new_stop_loss if new_stop_loss else position['stop_loss'],
                            'profit': position['profit'] if 'profit' in position else None
                        })
                        
            except Exception as e:
                print(f"持仓监控错误: {str(e)}")
                
            await asyncio.sleep(self.check_interval)
            
    async def _monitor_risk_metrics(self):
        """监控风险指标"""
        while self.running:
            try:
                # 获取所有账户信息
                account_info = await self.execution_manager.get_all_account_info()
                
                # 计算风险指标
                risk_metrics = await self.risk_controller.calculate_risk_metrics()
                
                # 更新性能指标
                self.performance_metrics = {
                    'timestamp': datetime.now(),
                    'risk_metrics': risk_metrics,
                    'account_info': account_info
                }
                
                # 检查风险限制
                for executor_name, info in account_info.items():
                    positions = await self.execution_manager.get_executor(executor_name).get_positions()
                    for position in positions:
                        if not await self.risk_controller.check_risk_limits(info, position):
                            # 如果超过风险限制，平掉该持仓
                            await self.execution_manager.close_positions(
                                symbol=position['symbol'],
                                executor_name=executor_name,
                                position_id=position['id']
                            )
                            print(f"风险限制触发，平仓: {position['symbol']}")
                            
            except Exception as e:
                print(f"风险监控错误: {str(e)}")
                
            await asyncio.sleep(self.check_interval * 5)  # 风险指标检查间隔可以长一些
            
    async def _generate_reports(self):
        """生成交易报告"""
        while self.running:
            try:
                # 等待积累足够的数据
                await asyncio.sleep(60)  # 每分钟生成一次报告
                
                # 生成持仓报告
                position_df = pd.DataFrame(self.position_updates)
                if not position_df.empty:
                    position_df['timestamp'] = pd.to_datetime(position_df['timestamp'])
                    position_report = self._generate_position_report(position_df)
                    
                    # 保存报告
                    await self._save_report('positions', position_report)
                    
                # 生成性能报告
                if self.performance_metrics:
                    performance_report = self._generate_performance_report()
                    
                    # 保存报告
                    await self._save_report('performance', performance_report)
                    
                # 清理旧数据
                self._cleanup_old_data()
                
            except Exception as e:
                print(f"报告生成错误: {str(e)}")
                
    def _generate_position_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成持仓报告"""
        # 按交易对分组统计
        by_symbol = df.groupby('symbol').agg({
            'current_price': ['last', 'mean', 'std'],
            'profit': ['sum', 'mean', 'count']
        }).round(4)
        
        # 计算持仓时间分布
        position_durations = df.groupby('position_id')['timestamp'].agg(['min', 'max'])
        position_durations['duration'] = position_durations['max'] - position_durations['min']
        
        return {
            'timestamp': datetime.now(),
            'symbol_stats': by_symbol.to_dict(),
            'position_durations': position_durations['duration'].describe().to_dict(),
            'total_positions': len(df['position_id'].unique()),
            'active_symbols': len(df['symbol'].unique())
        }
        
    def _generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        metrics = self.performance_metrics
        
        # 计算关键指标
        risk_metrics = metrics['risk_metrics']
        account_info = metrics['account_info']
        
        # 汇总所有账户的表现
        total_equity = sum(info['equity'] for info in account_info.values())
        total_balance = sum(info['balance'] for info in account_info.values())
        
        return {
            'timestamp': metrics['timestamp'],
            'total_equity': total_equity,
            'total_balance': total_balance,
            'total_profit': total_equity - total_balance,
            'win_rate': risk_metrics['win_rate'],
            'profit_factor': risk_metrics['profit_factor'],
            'sharpe_ratio': risk_metrics['sharpe_ratio'],
            'max_drawdown': risk_metrics['largest_drawdown'],
            'trade_count': risk_metrics['total_trades']
        }
        
    async def _save_report(self, report_type: str, report_data: Dict[str, Any]):
        """保存报告"""
        # TODO: 实现报告保存逻辑（数据库或文件）
        print(f"\n{report_type.upper()} 报告 - {datetime.now()}")
        print(report_data)
        
    def _cleanup_old_data(self):
        """清理旧数据"""
        # 保留最近24小时的数据
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.position_updates = [
            update for update in self.position_updates
            if update['timestamp'] > cutoff_time
        ]
        
    async def _get_current_price(self, executor: Any, symbol: str) -> float:
        """获取当前价格"""
        # TODO: 实现从交易所获取实时价格
        return 0.0  # 临时返回 