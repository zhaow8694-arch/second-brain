import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any
from models.deepseek_interface import MarketFeatures

def generate_market_data(n_points: int = 100,
                        base_price: float = 50000.0,
                        base_volatility: float = 0.02) -> Tuple[List[MarketFeatures], List[float]]:
    """生成测试用的市场数据和波动率标签"""
    features_list = []
    volatility_labels = []
    
    # 生成价格序列
    prices = [base_price]
    returns = []
    for _ in range(n_points - 1):
        current_volatility = base_volatility * (1 + np.random.normal(0, 0.2))
        volatility_labels.append(current_volatility)
        price = prices[-1] * (1 + np.random.normal(0, current_volatility))
        prices.append(price)
        returns.append(np.log(price / prices[-1]))
    
    # 计算实现波动率
    window_size = 10
    for i in range(n_points):
        price = prices[i]
        if i >= window_size:
            realized_vol = np.std(returns[i-window_size:i]) * np.sqrt(252)
        else:
            realized_vol = base_volatility
            
        volume = np.random.lognormal(4, 0.5)
        spread = price * 0.0004
        
        features = MarketFeatures(
            timestamp=datetime.now() + timedelta(minutes=i),
            price=price,
            volume=volume,
            bid_price=price - spread/2,
            ask_price=price + spread/2,
            bid_volume=volume/2,
            ask_volume=volume/2,
            volatility=realized_vol,
            trend_strength=np.random.random(),
            momentum=np.random.normal(0, 1),
            order_imbalance=np.random.normal(0, 0.2),
            spread=spread,
            market_depth={'level_1': volume, 'level_2': volume*1.5},
            custom_indicators={
                'rsi': np.random.uniform(30, 70),
                'macd': np.random.normal(0, 1),
                'bb_width': realized_vol * 2
            }
        )
        features_list.append(features)
    
    return features_list, volatility_labels

def generate_order_book_data(
    base_price: float = 50000.0,
    depth: int = 5,
    spread_bps: float = 2.0
) -> Dict[str, Any]:
    """生成订单簿测试数据"""
    spread = base_price * (spread_bps / 10000)
    bid_prices = [base_price - spread/2]
    ask_prices = [base_price + spread/2]
    
    # 生成各档位价格
    for i in range(1, depth):
        bid_prices.append(bid_prices[0] * (1 - i * 0.0001))
        ask_prices.append(ask_prices[0] * (1 + i * 0.0001))
    
    # 生成各档位数量
    volumes = [np.random.lognormal(4, 0.5) for _ in range(depth)]
    bid_volumes = volumes
    ask_volumes = [v * np.random.uniform(0.8, 1.2) for v in volumes]
    
    return {
        'bid_prices': bid_prices,
        'ask_prices': ask_prices,
        'bid_volumes': bid_volumes,
        'ask_volumes': ask_volumes,
        'timestamp': datetime.now()
    }

def generate_execution_data(
    order_size: float,
    base_price: float = 50000.0,
    slippage_bps: float = 1.0
) -> Dict[str, Any]:
    """生成执行数据"""
    execution_price = base_price * (1 + slippage_bps/10000)
    execution_time = datetime.now()
    market_impact = execution_price - base_price
    
    return {
        'execution_price': execution_price,
        'executed_quantity': order_size,
        'execution_time': execution_time,
        'market_impact': market_impact,
        'transaction_cost': market_impact * order_size,
        'execution_delay': timedelta(milliseconds=np.random.randint(10, 100))
    }

def generate_strategy_signals(
    n_points: int = 100,
    signal_type: str = 'mean_reversion'
) -> List[Dict[str, Any]]:
    """生成策略信号数据"""
    signals = []
    base_price = 50000.0
    
    if signal_type == 'mean_reversion':
        # 生成均值回归信号
        price = base_price
        for i in range(n_points):
            deviation = np.random.normal(0, 100)
            price = base_price + deviation
            signal_strength = -deviation / 100  # 偏离越大，回归信号越强
            
            signals.append({
                'timestamp': datetime.now() + timedelta(minutes=i),
                'price': price,
                'signal_strength': signal_strength,
                'signal_type': 'mean_reversion',
                'confidence': np.abs(signal_strength) / 2
            })
    
    elif signal_type == 'momentum':
        # 生成动量信号
        price = base_price
        returns = []
        for i in range(n_points):
            return_val = np.random.normal(0, 0.001)
            returns.append(return_val)
            price *= (1 + return_val)
            
            if i >= 10:
                momentum = np.mean(returns[-10:])
                signal_strength = momentum * 100
            else:
                signal_strength = 0
                
            signals.append({
                'timestamp': datetime.now() + timedelta(minutes=i),
                'price': price,
                'signal_strength': signal_strength,
                'signal_type': 'momentum',
                'confidence': np.abs(signal_strength) / 2
            })
    
    return signals

def generate_risk_metrics(
    portfolio_value: float = 1000000.0,
    n_positions: int = 5
) -> Dict[str, Any]:
    """生成风险指标数据"""
    positions = []
    total_exposure = 0
    
    for _ in range(n_positions):
        position_size = np.random.uniform(0.1, 0.3) * portfolio_value
        total_exposure += position_size
        positions.append({
            'size': position_size,
            'unrealized_pnl': position_size * np.random.normal(0, 0.02),
            'var_95': position_size * 0.02,
            'max_drawdown': position_size * np.random.uniform(0.01, 0.05)
        })
    
    return {
        'total_exposure': total_exposure,
        'portfolio_var': np.sqrt(sum(p['var_95']**2 for p in positions)),
        'portfolio_sharpe': np.random.uniform(1.5, 2.5),
        'max_drawdown': max(p['max_drawdown'] for p in positions),
        'positions': positions,
        'timestamp': datetime.now()
    } 