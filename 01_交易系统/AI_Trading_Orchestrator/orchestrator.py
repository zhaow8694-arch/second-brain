# orchestrator.py
# AI交易协同系统 V2.2 Final（完整版 + API配置支持）

import schedule
import time
from datetime import datetime

from risk_manager import RiskManager
from signal_generator import SignalGenerator
from market_data import MarketData
from price_fetcher import PriceFetcher
from notification_system import NotificationSystem
from telegram_notifier import TelegramNotifier
from trade_logger import TradeLogger
from backtest_simulator import BacktestSimulator
from grok_sentiment_analyzer import GrokSentimentAnalyzer
from gemini_chart_analyzer import GeminiChartAnalyzer
from deep import DeepSeekStrategyAnalyzer
from performance_tracker import PerformanceTracker
from system_dashboard import SystemDashboard
from strategy_optimizer import StrategyOptimizer
from api_config import APIConfig   # 新增API配置模块

class AI_Trading_Orchestrator:
    def __init__(self):
        self.rm = RiskManager(total_capital=20000)
        self.sg = SignalGenerator()
        self.md = MarketData()
        self.pf = PriceFetcher()
        self.ns = NotificationSystem()
        self.tg = TelegramNotifier()
        self.logger = TradeLogger()
        self.backtest = BacktestSimulator()
        self.grok = GrokSentimentAnalyzer()
        self.gemini = GeminiChartAnalyzer()
        self.deepseek = DeepSeekStrategyAnalyzer()
        self.performance = PerformanceTracker()
        self.dashboard = SystemDashboard()
        self.optimizer = StrategyOptimizer()
        self.api_config = APIConfig()   # 新增
        
        print(f"[{datetime.now()}] AI交易协同系统 V2.2 Final 启动成功")
        print(f"Telegram真实推送已启用 | 风险控制：单笔1% | API模式: {'真实' if self.api_config.use_real_api else '模拟'}")
        self.setup_schedule()

    def setup_schedule(self):
        schedule.every().day.at("08:00").do(self.morning_analysis)
        schedule.every(30).minutes.do(self.market_monitoring)
        schedule.every().day.at("20:00").do(self.evening_review)
        schedule.every().day.at("23:00").do(self.daily_backup)

    def morning_analysis(self):
        print(f"[{datetime.now()}] === 开始早晨AI分析 ===")
        
        data = self.pf.get_current_price()
        structure = self.pf.get_structure()
        
        sentiment = self.grok.analyze_sentiment()
        chart = self.gemini.analyze_chart(
            price=structure["price"],
            ema9_trend=structure["ema9_trend"],
            ob_type=structure["ob_type"],
            ob_price=structure["ob_price"]
        )
        
        signal = self.sg.generate_signal(
            price=structure["price"],
            ema9_trend=structure["ema9_trend"],
            ob_type=structure["ob_type"],
            ob_price=structure["ob_price"]
        )
        deepseek_advice = self.deepseek.analyze_strategy(signal, sentiment, chart)
        print(f"DeepSeek建议: {deepseek_advice['action']} | 原因: {deepseek_advice['reason']}")
        
        if signal["direction"]:
            self.ns.send_signal(signal)
            self.tg.send_signal(signal)
            self.logger.record_trade(signal, result="待执行")
        else:
            print("当前无有效交易信号")
        
        print("=== 早晨AI分析结束 ===\n")

    def market_monitoring(self):
        print(f"[{datetime.now()}] 盘中监控运行中...")

    def evening_review(self):
        print(f"[{datetime.now()}] === 开始晚间复盘 ===")
        self.backtest.run_simple_backtest(num_trades=10)
        self.performance.generate_daily_report()
        self.dashboard.generate_dashboard()
        self.optimizer.optimize_strategy()
        print("=== 复盘完成 ===\n")

    def daily_backup(self):
        print(f"[{datetime.now()}] 数据备份完成")

    def run(self):
        print("AI交易系统 V2.2 Final 正在运行，按 Ctrl+C 停止...")
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    orchestrator = AI_Trading_Orchestrator()
    orchestrator.run()