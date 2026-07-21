import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import asyncio
import random
import uuid

class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, config: Dict):
        """初始化测试数据生成器
        
        Args:
            config: 配置字典，包含各种数据生成的参数
        """
        self.config = config
        
    async def generate_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """生成市场数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            包含市场数据的DataFrame
        """
        # 验证参数
        if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
            raise ValueError('开始日期不能晚于结束日期')
            
        # 生成时间索引
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 根据时间周期生成时间点
        if timeframe == '1m':
            freq = '1min'
        elif timeframe == '5m':
            freq = '5min'
        elif timeframe == '15m':
            freq = '15min'
        elif timeframe == '1h':
            freq = '1H'
        elif timeframe == '4h':
            freq = '4H'
        elif timeframe == '1d':
            freq = 'D'
        else:
            raise ValueError(f'不支持的时间周期: {timeframe}')
            
        dates = pd.date_range(start=start, end=end, freq=freq)
        
        # 生成随机数据
        data = pd.DataFrame(index=dates)
        data['open'] = np.random.normal(500, 50, len(dates))
        data['high'] = data['open'] + np.random.uniform(0, 10, len(dates))
        data['low'] = data['open'] - np.random.uniform(0, 10, len(dates))
        data['close'] = np.random.uniform(data['low'], data['high'], len(dates))
        data['volume'] = np.random.uniform(100, 1000, len(dates))
        data['trades'] = np.random.randint(100, 1000, len(dates))
        
        return data
        
    async def generate_trade_data(
        self,
        symbol: str,
        num_trades: int
    ) -> pd.DataFrame:
        """生成交易数据
        
        Args:
            symbol: 交易对符号
            num_trades: 交易数量
            
        Returns:
            包含交易数据的DataFrame
        """
        if num_trades <= 0:
            raise ValueError('交易数量必须大于0')
            
        # 生成随机数据
        data = pd.DataFrame()
        data['order_id'] = [str(uuid.uuid4()) for _ in range(num_trades)]
        data['type'] = np.random.choice(
            self.config['trade_data']['order_types'],
            num_trades
        )
        data['side'] = np.random.choice(
            self.config['trade_data']['side_types'],
            num_trades
        )
        data['price'] = np.random.uniform(
            self.config['trade_data']['price_range']['min'],
            self.config['trade_data']['price_range']['max'],
            num_trades
        )
        data['volume'] = np.random.uniform(
            self.config['trade_data']['volume_range']['min'],
            self.config['trade_data']['volume_range']['max'],
            num_trades
        )
        data['status'] = np.random.choice(
            self.config['trade_data']['status_types'],
            num_trades
        )
        
        return data
        
    async def generate_system_data(
        self,
        duration_hours: int,
        interval_minutes: int
    ) -> pd.DataFrame:
        """生成系统数据
        
        Args:
            duration_hours: 持续时间（小时）
            interval_minutes: 采样间隔（分钟）
            
        Returns:
            包含系统数据的DataFrame
        """
        # 生成时间索引
        end = datetime.now()
        start = end - timedelta(hours=duration_hours)
        dates = pd.date_range(start=start, end=end, freq=f'{interval_minutes}min')
        
        # 生成数据
        data = []
        for date in dates:
            for component in self.config['system_data']['components']:
                for metric in self.config['system_data']['metrics']:
                    value = np.random.uniform(0, 100)
                    status = 'normal'
                    if value > 80:
                        status = 'critical'
                    elif value > 60:
                        status = 'warning'
                    elif value > 40:
                        status = 'error'
                        
                    data.append({
                        'timestamp': date,
                        'component': component,
                        'metric': metric,
                        'value': value,
                        'status': status
                    })
                    
        return pd.DataFrame(data)
        
    async def generate_orderbook(
        self,
        symbol: str,
        depth: int
    ) -> Dict:
        """生成订单簿数据
        
        Args:
            symbol: 交易对符号
            depth: 深度
            
        Returns:
            包含订单簿数据的字典
        """
        if depth <= 0:
            raise ValueError('深度必须大于0')
            
        # 生成随机数据
        base_price = np.random.uniform(
            self.config['trade_data']['price_range']['min'],
            self.config['trade_data']['price_range']['max']
        )
        
        bids = []
        asks = []
        
        # 生成买单
        for i in range(depth):
            price = base_price * (1 - i * 0.001)
            volume = np.random.uniform(
                self.config['trade_data']['volume_range']['min'],
                self.config['trade_data']['volume_range']['max']
            )
            bids.append([price, volume])
            
        # 生成卖单
        for i in range(depth):
            price = base_price * (1 + i * 0.001)
            volume = np.random.uniform(
                self.config['trade_data']['volume_range']['min'],
                self.config['trade_data']['volume_range']['max']
            )
            asks.append([price, volume])
            
        return {
            'bids': sorted(bids, key=lambda x: x[0], reverse=True),
            'asks': sorted(asks, key=lambda x: x[0])
        }
        
    async def generate_trade_history(
        self,
        symbol: str,
        num_trades: int
    ) -> pd.DataFrame:
        """生成交易历史数据
        
        Args:
            symbol: 交易对符号
            num_trades: 交易数量
            
        Returns:
            包含交易历史数据的DataFrame
        """
        if num_trades <= 0:
            raise ValueError('交易数量必须大于0')
            
        # 生成随机数据
        end = datetime.now()
        start = end - timedelta(hours=24)
        dates = pd.date_range(start=start, end=end, periods=num_trades)
        
        data = pd.DataFrame()
        data['timestamp'] = dates
        data['price'] = np.random.uniform(
            self.config['trade_data']['price_range']['min'],
            self.config['trade_data']['price_range']['max'],
            num_trades
        )
        data['volume'] = np.random.uniform(
            self.config['trade_data']['volume_range']['min'],
            self.config['trade_data']['volume_range']['max'],
            num_trades
        )
        data['side'] = np.random.choice(
            self.config['trade_data']['side_types'],
            num_trades
        )
        
        return data
        
    async def generate_performance_data(
        self,
        duration_hours: int,
        interval_minutes: int
    ) -> pd.DataFrame:
        """生成性能数据
        
        Args:
            duration_hours: 持续时间（小时）
            interval_minutes: 采样间隔（分钟）
            
        Returns:
            包含性能数据的DataFrame
        """
        # 生成时间索引
        end = datetime.now()
        start = end - timedelta(hours=duration_hours)
        dates = pd.date_range(start=start, end=end, freq=f'{interval_minutes}min')
        
        # 生成数据
        data = []
        for date in dates:
            for metric in self.config['system_data']['metrics']:
                value = np.random.uniform(0, 100)
                threshold = 80
                
                data.append({
                    'timestamp': date,
                    'metric': metric,
                    'value': value,
                    'threshold': threshold
                })
                
        return pd.DataFrame(data)
        
    async def generate_error_data(
        self,
        num_errors: int
    ) -> pd.DataFrame:
        """生成错误数据
        
        Args:
            num_errors: 错误数量
            
        Returns:
            包含错误数据的DataFrame
        """
        if num_errors <= 0:
            raise ValueError('错误数量必须大于0')
            
        # 生成随机数据
        end = datetime.now()
        start = end - timedelta(hours=24)
        dates = pd.date_range(start=start, end=end, periods=num_errors)
        
        error_types = [
            'connection_error',
            'timeout_error',
            'validation_error',
            'processing_error',
            'system_error'
        ]
        
        data = pd.DataFrame()
        data['timestamp'] = dates
        data['component'] = np.random.choice(
            self.config['system_data']['components'],
            num_errors
        )
        data['error_type'] = np.random.choice(error_types, num_errors)
        data['message'] = [f'Test error message {i}' for i in range(num_errors)]
        data['severity'] = np.random.choice(
            ['low', 'medium', 'high', 'critical'],
            num_errors
        )
        
        return data
        
    async def generate_test_scenarios(
        self,
        num_scenarios: int
    ) -> List[Dict]:
        """生成测试场景
        
        Args:
            num_scenarios: 场景数量
            
        Returns:
            包含测试场景的列表
        """
        if num_scenarios <= 0:
            raise ValueError('场景数量必须大于0')
            
        # 生成随机场景
        scenarios = []
        for i in range(num_scenarios):
            scenario = {
                'id': str(uuid.uuid4()),
                'description': f'Test scenario {i}',
                'data': {
                    'market_data': await self.generate_market_data(
                        'BTC/USDT',
                        '1h',
                        '2024-01-01',
                        '2024-01-31'
                    ),
                    'trade_data': await self.generate_trade_data(
                        'BTC/USDT',
                        100
                    ),
                    'system_data': await self.generate_system_data(
                        24,
                        5
                    )
                }
            }
            scenarios.append(scenario)
            
        return scenarios 