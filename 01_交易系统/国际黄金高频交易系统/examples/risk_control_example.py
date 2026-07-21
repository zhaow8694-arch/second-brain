from loguru import logger
from src.risk_control.base_risk_controller import BaseRiskController, RiskLimit

def main():
    # 配置日志
    logger.add("logs/risk_control.log", rotation="500 MB")
    
    # 创建风险限制配置
    risk_limits = RiskLimit(
        max_position_size=10.0,    # 最大持仓量
        max_daily_loss=1000.0,     # 最大日亏损
        max_drawdown=0.1,          # 最大回撤
        max_leverage=5.0,          # 最大杠杆
        min_margin_ratio=0.1,      # 最小保证金率
        max_order_size=5.0,        # 最大单笔订单量
        max_orders_per_minute=10   # 每分钟最大订单数
    )
    
    # 创建风控控制器
    risk_controller = BaseRiskController(risk_limits)
    
    try:
        # 模拟交易场景
        logger.info("开始模拟交易场景...")
        
        # 1. 设置初始账户余额
        risk_controller.update_balance(10000.0)
        logger.info(f"初始账户余额: {risk_controller.current_balance}")
        
        # 2. 检查开仓风险
        symbol = "BTCUSDT"
        position_size = 5.0
        price = 50000.0
        
        logger.info(f"检查开仓风险: {symbol}, 数量: {position_size}, 价格: {price}")
        if risk_controller.check_position_risk(symbol, position_size):
            logger.info("持仓风险检查通过")
            if risk_controller.check_order_risk(symbol, position_size, price):
                logger.info("订单风险检查通过")
                # 更新持仓
                risk_controller.update_position(symbol, position_size)
                logger.info(f"持仓已更新: {risk_controller.positions}")
            else:
                logger.error("订单风险检查未通过")
        else:
            logger.error("持仓风险检查未通过")
            
        # 3. 模拟盈亏
        pnl = 500.0
        risk_controller.update_pnl(pnl)
        logger.info(f"更新盈亏: {pnl}, 当前日盈亏: {risk_controller.daily_pnl}")
        
        # 4. 检查账户风险
        if risk_controller.check_account_risk():
            logger.info("账户风险检查通过")
        else:
            logger.error("账户风险检查未通过")
            
        # 5. 查看风险预警
        alerts = risk_controller.get_alerts()
        if alerts:
            logger.info("发现风险预警:")
            for alert in alerts:
                logger.warning(f"级别: {alert.level}, 类型: {alert.type}, 消息: {alert.message}")
        else:
            logger.info("没有风险预警")
            
    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        logger.info("模拟交易场景结束")

if __name__ == "__main__":
    main() 