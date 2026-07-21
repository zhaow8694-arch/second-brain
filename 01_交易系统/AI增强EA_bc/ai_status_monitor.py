#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI状态监控脚本
实时监控AI服务状态和预测结果
"""

import os
import time
import pandas as pd
from datetime import datetime
import subprocess

class AIStatusMonitor:
    def __init__(self):
        self.last_prediction = None
        self.last_confidence = None
        self.last_update_time = None
        
    def get_prediction_info(self):
        """获取当前AI预测信息"""
        try:
            if os.path.exists('ai_prediction.txt'):
                with open('ai_prediction.txt', 'r') as f:
                    content = f.read().strip()
                    if ',' in content:
                        parts = content.split(',')
                        if len(parts) >= 2:
                            prediction = int(parts[0])
                            confidence = float(parts[1])
                            timestamp = int(parts[2]) if len(parts) > 2 else 0
                            
                            # 转换时间戳
                            if timestamp > 0:
                                update_time = datetime.fromtimestamp(timestamp)
                            else:
                                update_time = datetime.fromtimestamp(os.path.getmtime('ai_prediction.txt'))
                            
                            return {
                                'prediction': prediction,
                                'confidence': confidence,
                                'update_time': update_time,
                                'content': content
                            }
        except Exception as e:
            print(f"读取预测文件失败: {e}")
        
        return None
    
    def get_prediction_direction(self, prediction):
        """获取预测方向描述"""
        if prediction == 1:
            return "买入 📈"
        elif prediction == 2:
            return "卖出 📉"
        else:
            return "持有 ⏸️"
    
    def get_confidence_level(self, confidence):
        """获取置信度等级"""
        if confidence >= 0.9:
            return "极高 🚀"
        elif confidence >= 0.8:
            return "高 ⭐"
        elif confidence >= 0.7:
            return "中 🔶"
        elif confidence >= 0.6:
            return "低 ⚠️"
        else:
            return "很低 ❌"
    
    def check_python_process(self):
        """检查Python进程状态"""
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True, shell=True)
            if 'python.exe' in result.stdout:
                lines = [line for line in result.stdout.strip().split('\n') if 'python.exe' in line]
                return len(lines), lines
            return 0, []
        except Exception as e:
            print(f"检查进程失败: {e}")
            return 0, []
    
    def check_market_data(self):
        """检查市场数据状态"""
        try:
            if os.path.exists('market_data.csv'):
                file_time = datetime.fromtimestamp(os.path.getmtime('market_data.csv'))
                file_size = os.path.getsize('market_data.csv')
                return {
                    'exists': True,
                    'update_time': file_time,
                    'size': file_size
                }
            return {'exists': False}
        except Exception as e:
            return {'exists': False, 'error': str(e)}
    
    def display_status(self):
        """显示AI服务状态"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 60)
        print("🤖 AI增强风险管理EA - 状态监控")
        print("=" * 60)
        
        # 检查Python进程
        process_count, process_lines = self.check_python_process()
        print(f"🐍 Python AI服务: {'✅ 运行中' if process_count > 0 else '❌ 未运行'}")
        if process_count > 0:
            print(f"   进程数量: {process_count}")
        
        # 检查市场数据
        market_data = self.check_market_data()
        if market_data['exists']:
            print(f"📊 市场数据: ✅ 可用")
            print(f"   更新时间: {market_data['update_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   文件大小: {market_data['size']} 字节")
        else:
            print(f"📊 市场数据: ❌ 不可用")
        
        # 获取AI预测
        pred_info = self.get_prediction_info()
        if pred_info:
            print(f"🎯 AI预测: ✅ 活跃")
            print(f"   预测方向: {self.get_prediction_direction(pred_info['prediction'])}")
            print(f"   置信度: {pred_info['confidence']:.3f} ({self.get_confidence_level(pred_info['confidence'])})")
            print(f"   更新时间: {pred_info['update_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 检查是否是新预测
            if (self.last_prediction != pred_info['prediction'] or 
                self.last_confidence != pred_info['confidence']):
                print(f"🔄 预测已更新!")
                self.last_prediction = pred_info['prediction']
                self.last_confidence = pred_info['confidence']
                self.last_update_time = pred_info['update_time']
        else:
            print(f"🎯 AI预测: ❌ 无预测数据")
        
        print("\n" + "=" * 60)
        print(f"⏰ 监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("按 Ctrl+C 退出监控")
        print("=" * 60)
    
    def start_monitoring(self, interval=2):
        """开始监控"""
        print("🚀 启动AI状态监控...")
        print(f"📊 监控间隔: {interval} 秒")
        print("按 Ctrl+C 退出\n")
        
        try:
            while True:
                self.display_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 监控已停止")

def main():
    monitor = AIStatusMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main() 