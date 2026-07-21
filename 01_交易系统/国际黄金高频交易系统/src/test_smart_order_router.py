import asyncio
import pytest
from datetime import datetime
from execution.smart_order_router import SmartOrderRouter, VenueMetrics, OrderRouteResult

async def test_venue_metrics_update():
    """测试交易所指标更新"""
    router = SmartOrderRouter()
    
    # 添加测试数据
    binance_metrics = VenueMetrics(
        liquidity_score=0.9,
        execution_speed=50,
        historical_slippage=0.0005,
        trading_cost=0.001,
        success_rate=0.99
    )
    
    huobi_metrics = VenueMetrics(
        liquidity_score=0.8,
        execution_speed=80,
        historical_slippage=0.0008,
        trading_cost=0.002,
        success_rate=0.98
    )
    
    okex_metrics = VenueMetrics(
        liquidity_score=0.85,
        execution_speed=60,
        historical_slippage=0.0006,
        trading_cost=0.0015,
        success_rate=0.985
    )
    
    # 更新指标
    await router.update_venue_metrics("binance", binance_metrics)
    await router.update_venue_metrics("huobi", huobi_metrics)
    await router.update_venue_metrics("okex", okex_metrics)
    
    # 验证权重计算
    weights = await router.get_venue_weights()
    assert len(weights) == 3
    assert weights["binance"] > weights["okex"] > weights["huobi"]
    
    # 验证指标获取
    metrics = await router.get_venue_metrics("binance")
    assert metrics == binance_metrics
    
async def test_order_routing():
    """测试订单路由"""
    router = SmartOrderRouter(
        min_venue_count=2,
        max_venue_count=3,
        slippage_threshold=0.001,
        cost_threshold=0.002
    )
    
    # 添加测试数据
    venues = {
        "binance": VenueMetrics(0.9, 50, 0.0005, 0.001, 0.99),
        "huobi": VenueMetrics(0.8, 80, 0.0008, 0.002, 0.98),
        "okex": VenueMetrics(0.85, 60, 0.0006, 0.0015, 0.985),
        "ftx": VenueMetrics(0.75, 90, 0.001, 0.0025, 0.97),
        "kucoin": VenueMetrics(0.7, 100, 0.0012, 0.003, 0.96)
    }
    
    for venue, metrics in venues.items():
        await router.update_venue_metrics(venue, metrics)
    
    # 测试订单路由
    result = await router.route_order(
        symbol="BTC/USDT",
        side="buy",
        size=1.0,
        max_slippage=0.001
    )
    
    # 验证结果
    assert isinstance(result, OrderRouteResult)
    assert len(result.venue_allocations) <= 3  # 最大交易所数量
    assert len(result.venue_allocations) >= 2  # 最小交易所数量
    assert abs(sum(result.venue_allocations.values()) - 1.0) < 1e-6  # 总和应约等于1
    assert "binance" in result.venue_allocations  # 最优交易所应该被选中
    
    # 验证预估指标
    assert result.estimated_cost > 0
    assert result.estimated_slippage > 0
    assert result.execution_time > 0
    
async def test_dynamic_update():
    """测试动态更新"""
    router = SmartOrderRouter(update_interval=1)
    
    # 初始指标
    initial_metrics = VenueMetrics(0.9, 50, 0.0005, 0.001, 0.99)
    await router.update_venue_metrics("binance", initial_metrics)
    
    # 获取初始权重
    initial_weight = (await router.get_venue_weights())["binance"]
    
    # 更新指标
    updated_metrics = VenueMetrics(0.8, 60, 0.0006, 0.0012, 0.98)
    await router.update_venue_metrics("binance", updated_metrics)
    
    # 获取更新后的权重
    updated_weight = (await router.get_venue_weights())["binance"]
    
    # 验证权重变化
    assert initial_weight != updated_weight
    
async def main():
    """运行所有测试"""
    print("开始测试智能订单路由器...")
    
    try:
        print("\n测试交易所指标更新...")
        await test_venue_metrics_update()
        print("✓ 交易所指标更新测试通过")
        
        print("\n测试订单路由...")
        await test_order_routing()
        print("✓ 订单路由测试通过")
        
        print("\n测试动态更新...")
        await test_dynamic_update()
        print("✓ 动态更新测试通过")
        
        print("\n所有测试通过！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 