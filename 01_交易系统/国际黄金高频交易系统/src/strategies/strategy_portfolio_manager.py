from typing import Dict, Any, List, Optional, Type
import asyncio
import numpy as np
from datetime import datetime
from .base_strategy import BaseStrategy
from .trend_following_strategy import TrendFollowingStrategy
from .price_pressure_strategy import PricePressureStrategy

class StrategyPortfolioManager:
    """策略组合管理器"""
    
    def __init__(self,
                 symbols: List[str],
                 timeframe: str = '5m',
                 max_positions_per_strategy: int = 3,
                 max_total_positions: int = 5,
                 risk_allocation: Dict[str, float] = None,
                 correlation_threshold: float = 0.7,
                 rebalance_interval: int = 3600):  # 每小时重新平衡一次
        self.symbols = symbols
        self.timeframe = timeframe
        self.max_positions_per_strategy = max_positions_per_strategy
        self.max_total_positions = max_total_positions
        self.correlation_threshold = correlation_threshold
        self.rebalance_interval = rebalance_interval
        
        # 设置风险分配
        if risk_allocation is None:
            # 默认平均分配风险
            self.risk_allocation = {
                'trend_following': 0.5,
                'price_pressure': 0.5
            }
        else:
            self.risk_allocation = risk_allocation
            
        # 初始化策略实例
        self.strategies: Dict[str, List[BaseStrategy]] = {
            'trend_following': [],
            'price_pressure': []
        }
        
        # 初始化性能指标
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        
        # 初始化活跃信号
        self.active_signals: Dict[str, List[Dict[str, Any]]] = {}
        
        # 初始化相关性矩阵
        self.correlation_matrix: Optional[np.ndarray] = None
        
    async def initialize(self):
        """初始化策略组合"""
        # 为每个交易对创建策略实例
        for symbol in self.symbols:
            # 趋势跟踪策略
            trend_strategy = TrendFollowingStrategy(
                symbol=symbol,
                timeframe=self.timeframe,
                position_size_limit=self.risk_allocation['trend_following']
            )
            await trend_strategy.initialize()
            self.strategies['trend_following'].append(trend_strategy)
            
            # 价格压力策略
            pressure_strategy = PricePressureStrategy(
                symbol=symbol,
                timeframe=self.timeframe,
                position_size_limit=self.risk_allocation['price_pressure']
            )
            await pressure_strategy.initialize()
            self.strategies['price_pressure'].append(pressure_strategy)
            
            # 初始化活跃信号列表
            self.active_signals[symbol] = []
            
    async def update_market_data(self, market_data: Dict[str, Any]):
        """更新市场数据"""
        symbol = market_data['symbol']
        
        # 更新每个策略的市场数据
        for strategy_list in self.strategies.values():
            for strategy in strategy_list:
                if strategy.symbol == symbol:
                    await strategy.on_market_data(market_data)
                    
    async def generate_portfolio_signals(self) -> List[Dict[str, Any]]:
        """生成组合交易信号"""
        all_signals = []
        
        # 从每个策略获取信号
        for strategy_type, strategy_list in self.strategies.items():
            for strategy in strategy_list:
                signals = await strategy.generate_signals()
                for signal in signals:
                    signal['strategy_type'] = strategy_type
                    all_signals.append(signal)
                    
        # 过滤和优化信号
        filtered_signals = await self._filter_signals(all_signals)
        
        # 更新活跃信号
        for signal in filtered_signals:
            symbol = signal['symbol']
            self.active_signals[symbol].append(signal)
            
        return filtered_signals
        
    async def _filter_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤和优化信号"""
        if not signals:
            return []
            
        filtered_signals = []
        
        # 按信号强度排序
        sorted_signals = sorted(signals, key=lambda x: x['strength'], reverse=True)
        
        # 检查持仓限制和相关性
        for signal in sorted_signals:
            symbol = signal['symbol']
            strategy_type = signal['strategy_type']
            
            # 检查每个策略的最大持仓数
            strategy_positions = sum(1 for s in self.active_signals[symbol] 
                                  if s['strategy_type'] == strategy_type)
            if strategy_positions >= self.max_positions_per_strategy:
                continue
                
            # 检查总持仓数
            total_positions = sum(len(signals) for signals in self.active_signals.values())
            if total_positions >= self.max_total_positions:
                continue
                
            # 检查相关性
            if self._check_correlation(signal):
                filtered_signals.append(signal)
                
        return filtered_signals
        
    def _check_correlation(self, signal: Dict[str, Any]) -> bool:
        """检查相关性"""
        # 如果没有其他活跃信号，直接返回True
        active_symbols = set()
        for signals in self.active_signals.values():
            for s in signals:
                active_symbols.add(s['symbol'])
                
        if not active_symbols:
            return True
            
        # 如果相关性矩阵未初始化，返回True
        if self.correlation_matrix is None:
            return True
            
        # 获取信号对应的交易对索引
        symbol_index = self.symbols.index(signal['symbol'])
        
        # 检查与现有持仓的相关性
        for active_symbol in active_symbols:
            active_index = self.symbols.index(active_symbol)
            correlation = abs(self.correlation_matrix[symbol_index][active_index])
            if correlation > self.correlation_threshold:
                return False
                
        return True
        
    async def update_correlation_matrix(self, price_data: Dict[str, List[float]]):
        """更新相关性矩阵"""
        # 将价格数据转换为收益率
        returns = {}
        for symbol, prices in price_data.items():
            returns[symbol] = np.diff(np.log(prices))
            
        # 创建收益率矩阵
        returns_matrix = np.array([returns[symbol] for symbol in self.symbols])
        
        # 计算相关性矩阵
        self.correlation_matrix = np.corrcoef(returns_matrix)
        
    async def update_performance_metrics(self):
        """更新性能指标"""
        for strategy_type, strategy_list in self.strategies.items():
            for strategy in strategy_list:
                # 计算策略性能指标
                win_rate = self._calculate_win_rate(strategy)
                sharpe_ratio = self._calculate_sharpe_ratio(strategy)
                max_drawdown = self._calculate_max_drawdown(strategy)
                
                self.performance_metrics[f"{strategy_type}_{strategy.symbol}"] = {
                    'win_rate': win_rate,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown
                }
                
    def _calculate_win_rate(self, strategy: BaseStrategy) -> float:
        """计算胜率"""
        if not hasattr(strategy, 'trade_history') or not strategy.trade_history:
            return 0.0
            
        winning_trades = sum(1 for trade in strategy.trade_history if trade['pnl'] > 0)
        total_trades = len(strategy.trade_history)
        
        return winning_trades / total_trades if total_trades > 0 else 0.0
        
    def _calculate_sharpe_ratio(self, strategy: BaseStrategy) -> float:
        """计算夏普比率"""
        if not hasattr(strategy, 'trade_history') or not strategy.trade_history:
            return 0.0
            
        returns = [trade['pnl'] for trade in strategy.trade_history]
        if not returns:
            return 0.0
            
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        return mean_return / std_return if std_return > 0 else 0.0
        
    def _calculate_max_drawdown(self, strategy: BaseStrategy) -> float:
        """计算最大回撤"""
        if not hasattr(strategy, 'trade_history') or not strategy.trade_history:
            return 0.0
            
        cumulative_returns = np.cumsum([trade['pnl'] for trade in strategy.trade_history])
        if len(cumulative_returns) == 0:
            return 0.0
            
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (running_max - cumulative_returns) / running_max
        
        return np.max(drawdowns) if len(drawdowns) > 0 else 0.0
        
    async def rebalance_portfolio(self):
        """重新平衡投资组合"""
        # 更新性能指标
        await self.update_performance_metrics()
        
        # 根据性能调整风险分配
        total_sharpe = 0.0
        strategy_sharpes = {}
        
        for strategy_type in self.strategies.keys():
            strategy_sharpe = 0.0
            strategy_count = 0
            
            for symbol in self.symbols:
                metrics = self.performance_metrics.get(f"{strategy_type}_{symbol}")
                if metrics:
                    strategy_sharpe += metrics['sharpe_ratio']
                    strategy_count += 1
                    
            if strategy_count > 0:
                avg_sharpe = strategy_sharpe / strategy_count
                strategy_sharpes[strategy_type] = avg_sharpe
                total_sharpe += avg_sharpe
                
        # 如果有足够的性能数据，更新风险分配
        if total_sharpe > 0:
            for strategy_type, sharpe in strategy_sharpes.items():
                self.risk_allocation[strategy_type] = sharpe / total_sharpe
                
            # 更新每个策略的持仓限制
            for strategy_type, strategy_list in self.strategies.items():
                for strategy in strategy_list:
                    strategy.position_size_limit = self.risk_allocation[strategy_type]
                    
    async def run(self):
        """运行策略组合管理器"""
        while True:
            try:
                # 生成交易信号
                signals = await self.generate_portfolio_signals()
                
                # 定期重新平衡投资组合
                await self.rebalance_portfolio()
                
                # 等待下一个时间间隔
                await asyncio.sleep(self.rebalance_interval)
                
            except Exception as e:
                print(f"策略组合管理器运行错误: {e}")
                await asyncio.sleep(60)  # 发生错误时等待1分钟后重试 