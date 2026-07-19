"""
状态管理模块
负责保存和恢复系统状态
"""
import json
import os
import glob
import time
import shutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date

from config import Config as config
from core.risk_manager import risk_manager
from core.trade_executor import trade_executor

logger = logging.getLogger(__name__)


class StateManager:
    """状态管理器"""
    
    def __init__(self):
        self.state_file = config.STATE_FILE
        self.backup_files = [
            'guardian_earth_state_core.json',
            'guardian_earth_state.json',
            'eternal_guardian_state.json'
        ]
    
    def load_state(self) -> bool:
        """加载状态"""
        try:
            state_data = self._load_state_file()
            
            if not state_data:
                logger.info("没有找到状态文件，使用初始状态")
                return True
            
            # 加载风险管理器状态
            if 'risk_manager' in state_data:
                risk_data = state_data['risk_manager']
                risk_manager.daily_start_equity = risk_data.get('daily_start_equity')
                risk_manager.daily_date = risk_data.get('daily_date')
                risk_manager.initial_equity = risk_data.get('initial_equity')
                risk_manager.can_trade_today = risk_data.get('can_trade_today', True)
                risk_manager.cooldown_log = risk_data.get('cooldown_log', {})
                risk_manager.position_timers = risk_data.get('position_timers', {})
                risk_manager.high_water_marks = risk_data.get('high_water_marks', {})
                
                # 如果是旧日期，自动重置交易权限
                saved_date = risk_manager.daily_date
                if saved_date and saved_date != date.today().isoformat():
                    risk_manager.can_trade_today = True
                    logger.info(f"检测到日期变更 ({saved_date} -> {date.today().isoformat()})，已重置交易权限")
            
            # 加载交易执行器状态
            if 'trade_executor' in state_data:
                trade_data = state_data['trade_executor']
                
                trade_executor.positions = trade_data.get('positions', {})
                # 规范化持仓symbol: 清理历史脏数据中的非标准格式
                for key in list(trade_executor.positions.keys()):
                    pos = trade_executor.positions[key]
                    raw_sym = pos.get('symbol', key)
                    if '/' in str(raw_sym) or ':' in str(raw_sym):
                        normalized = str(raw_sym).split('/')[0].replace(':', '')
                        pos['symbol'] = normalized
                trade_executor.entry_prices = trade_data.get('entry_prices', {})
                trade_executor.target_prices = trade_data.get('target_prices', {})
                trade_executor.stop_losses = trade_data.get('stop_losses', {})
                trade_executor.position_levels = trade_data.get('position_levels', {})
                trade_executor.base_sizes = trade_data.get('base_sizes', {})
                trade_executor.entry_atrs = trade_data.get('entry_atrs', {})
                trade_executor.partial_closes = trade_data.get('partial_closes', {})
                trade_executor.synced_positions = set(trade_data.get('synced_positions', []))
                
                # 加载交易历史
                trade_executor.position_history = trade_data.get('position_history', [])
            
            logger.info("状态加载成功")
            return True
            
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            return False
    
    def save_state(self) -> bool:
        """保存状态"""
        try:
            state_data = {
                'timestamp': time.time(),
                'timestamp_human': datetime.now().isoformat(),
                'version': '2.0.0',
                
                'risk_manager': {
                    'daily_start_equity': risk_manager.daily_start_equity,
                    'daily_date': risk_manager.daily_date,
                    'initial_equity': risk_manager.initial_equity,
                    'can_trade_today': risk_manager.can_trade_today,
                    'cooldown_log': risk_manager.cooldown_log,
                    'position_timers': risk_manager.position_timers,
                    'high_water_marks': risk_manager.high_water_marks
                },
                
                'trade_executor': {
                    'positions': trade_executor.positions,
                    'entry_prices': trade_executor.entry_prices,
                    'target_prices': trade_executor.target_prices,
                    'stop_losses': trade_executor.stop_losses,
                    'position_levels': trade_executor.position_levels,
                    'base_sizes': trade_executor.base_sizes,
                    'entry_atrs': trade_executor.entry_atrs,
                    'partial_closes': trade_executor.partial_closes,
                    'synced_positions': list(trade_executor.synced_positions),
                    'position_history': trade_executor.position_history[-100:]
                },
                
                'config_summary': config.to_dict()
            }
            
            # 创建备份
            self._create_backup()
            
            # 保存状态
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False, default=self._json_default)
            
            logger.debug("状态保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
            return False
    
    @staticmethod
    def _json_default(obj):
        """自定义JSON编码器，处理不可序列化的类型"""
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        if hasattr(obj, '__dict__'):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _load_state_file(self) -> Optional[Dict]:
        """加载状态文件"""
        for file_name in [self.state_file] + self.backup_files:
            if not os.path.exists(file_name):
                continue
            
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                logger.info(f"从 {file_name} 加载状态")
                return data
                
            except json.JSONDecodeError as e:
                logger.warning(f"状态文件 {file_name} JSON解析失败: {e}")
            except Exception as e:
                logger.warning(f"加载状态文件 {file_name} 失败: {e}")
        
        return None
    
    def _create_backup(self) -> None:
        """创建备份"""
        if not os.path.exists(self.state_file):
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.state_file}.backup_{timestamp}"
            
            shutil.copy2(self.state_file, backup_file)
            
            # 清理旧备份（保留最近5个）
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.warning(f"创建备份失败: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """清理旧备份"""
        try:
            backup_files = glob.glob(f"{self.state_file}.backup_*")
            
            if len(backup_files) > 5:
                backup_files.sort(key=os.path.getmtime)
                files_to_delete = backup_files[:-5]  # 保留最近5个
                
                for file_path in files_to_delete:
                    os.remove(file_path)
                    logger.debug(f"删除旧备份: {file_path}")
                    
        except Exception as e:
            logger.warning(f"清理旧备份失败: {e}")
    
    def export_state(self, export_file: str = "state_export.json") -> bool:
        """导出状态"""
        try:
            state_data = self._load_state_file()
            if not state_data:
                return False
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"状态已导出到 {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出状态失败: {e}")
            return False
    
    def import_state(self, import_file: str) -> bool:
        """导入状态"""
        try:
            if not os.path.exists(import_file):
                logger.error(f"导入文件不存在: {import_file}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # 验证状态数据
            if not self._validate_state_data(state_data):
                logger.error("状态数据验证失败")
                return False
            
            # 保存到状态文件
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"状态已从 {import_file} 导入")
            return True
            
        except Exception as e:
            logger.error(f"导入状态失败: {e}")
            return False
    
    def _validate_state_data(self, state_data: Dict) -> bool:
        """验证状态数据"""
        try:
            # 检查必需字段
            required_fields = ['timestamp', 'version']
            for field in required_fields:
                if field not in state_data:
                    logger.error(f"缺少必需字段: {field}")
                    return False
            
            # 检查版本兼容性
            version = state_data.get('version', '')
            if not version.startswith('2.'):
                logger.error(f"不兼容的版本: {version}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证状态数据失败: {e}")
            return False
    
    def clear_state(self) -> bool:
        """清除状态"""
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
                logger.info("状态文件已清除")
            
            # 清理备份文件（安全验证文件名）
            backup_files = glob.glob(f"{self.state_file}.backup_*")
            for file_path in backup_files:
                if os.path.basename(file_path).startswith(os.path.basename(self.state_file)):
                    os.remove(file_path)
            
            logger.info("所有状态已清除")
            return True
            
        except Exception as e:
            logger.error(f"清除状态失败: {e}")
            return False


# 创建全局状态管理器实例
state_manager = StateManager()
state_store = state_manager  # 别名，保持向后兼容