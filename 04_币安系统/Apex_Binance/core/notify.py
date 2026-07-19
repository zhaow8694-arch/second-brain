"""
Telegram通知模块
替换原有的钉钉通知功能
"""
import os
import time
import logging
import threading
from typing import Optional
from datetime import datetime

import requests
from config import Config as config

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram通知器"""
    
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def _send_message_sync(self, message: str, parse_mode: str = "HTML") -> bool:
        """同步发送消息"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram配置不完整，跳过通知")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.debug(f"Telegram消息发送成功: {message[:50]}...")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram消息发送失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Telegram消息发送异常: {e}")
            return False
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """发送消息，自动处理超长消息分段"""
        if len(message) <= 4096:
            return self._send_message_sync(message, parse_mode)
        
        chunks = []
        while message:
            if len(message) <= 4096:
                chunks.append(message)
                break
            split_pos = message.rfind('\n', 0, 4096)
            if split_pos == -1:
                split_pos = 4096
            chunks.append(message[:split_pos])
            message = message[split_pos:].lstrip('\n')
        
        all_success = True
        for i, chunk in enumerate(chunks):
            if i > 0:
                time.sleep(0.5)
            success = self._send_message_sync(chunk, parse_mode)
            if not success:
                all_success = False
        return all_success
    
    def send_trade_alert(self, title: str, content: str) -> None:
        """发送交易提醒"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"<b>🚀 {title}</b>\n"
        message += f"<i>时间: {timestamp}</i>\n\n"
        message += content
        
        self.send_message(message)
    
    def send_error_alert(self, error_msg: str, context: str = "") -> bool:
        """发送错误提醒"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"<b>[ERROR] 系统错误</b>\n"
        message += f"<i>时间: {timestamp}</i>\n\n"
        
        if context:
            message += f"<b>上下文:</b> {self._escape_html(context)}\n"
        
        message += f"<b>错误信息:</b>\n<code>{self._escape_html(error_msg)}</code>"
        
        return self.send_message(message)
    
    def send_daily_report(self, report_data: dict) -> None:
        """发送日报"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"<b>📊 每日交易报告</b>\n"
        message += f"<i>生成时间: {timestamp}</i>\n\n"
        
        # 添加报告数据
        if 'total_pnl' in report_data:
            pnl = report_data['total_pnl']
            pnl_pct = report_data.get('total_pnl_pct', 0)
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            message += f"{pnl_emoji} <b>总盈亏:</b> {pnl:.2f} USDT ({pnl_pct:.2%})\n"
        
        if 'daily_pnl' in report_data:
            daily_pnl = report_data['daily_pnl']
            daily_pnl_pct = report_data.get('daily_pnl_pct', 0)
            daily_emoji = "🟢" if daily_pnl >= 0 else "🔴"
            message += f"{daily_emoji} <b>当日盈亏:</b> {daily_pnl:.2f} USDT ({daily_pnl_pct:.2%})\n"
        
        if 'positions_count' in report_data:
            message += f"📊 <b>持仓数量:</b> {report_data['positions_count']}\n"
        
        if 'win_rate' in report_data:
            win_rate = report_data['win_rate']
            win_emoji = "🎯" if win_rate >= 0.5 else "🎲"
            message += f"{win_emoji} <b>胜率:</b> {win_rate:.1%}\n"
        
        if 'risk_level' in report_data:
            risk = report_data['risk_level']
            risk_emoji = "🟢" if risk == "低" else "🟡" if risk == "中" else "🔴"
            message += f"{risk_emoji} <b>风险等级:</b> {risk}\n"
        
        self.send_message(message)
    
    def test_connection(self) -> bool:
        """测试Telegram连接"""
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram配置不完整")
            return False
        
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            bot_info = response.json()
            if bot_info.get("ok"):
                logger.info(f"Telegram连接测试成功 - 机器人: {bot_info['result']['username']}")
                
                # 测试发送消息
                test_msg = f"<b>✅ 连接测试成功</b>\n机器人: {bot_info['result']['username']}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                return self._send_message_sync(test_msg)
            
            return False
            
        except Exception as e:
            logger.error(f"Telegram连接测试失败: {e}")
            return False


# 创建全局通知器实例
telegram_notifier = TelegramNotifier()