#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务启动脚本
一键启动所有AI相关服务
"""

import os
import sys
import time
import subprocess
import threading
from datetime import datetime

class AIServiceManager:
    def __init__(self):
        self.processes = []
        self.is_running = False
        
    def check_dependencies(self):
        """检查依赖项"""
        print("🔍 检查AI服务依赖项...")
        
        required_files = [
            'continuous_ai_monitor.py',
            'trading_transformer_model.py',
            'trading_data_processor.pkl'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
            else:
                print(f"  ✅ {file}")
        
        if missing_files:
            print(f"❌ 缺失文件: {', '.join(missing_files)}")
            return False
        
        # 检查Python环境
        try:
            result = subprocess.run(['py', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Python: {result.stdout.strip()}")
            else:
                print("❌ Python环境不可用")
                return False
        except Exception as e:
            print(f"❌ 检查Python环境失败: {e}")
            return False
        
        # 检查必要的Python包
        required_packages = ['torch', 'pandas', 'numpy', 'joblib', 'ta']
        print("📦 检查Python包...")
        for package in required_packages:
            try:
                __import__(package)
                print(f"  ✅ {package}")
            except ImportError:
                print(f"  ❌ {package} - 未安装")
                return False
        
        print("✅ 所有依赖项检查通过")
        return True
    
    def start_ai_monitor(self):
        """启动AI监控服务"""
        print("🚀 启动AI监控服务...")
        try:
            # 启动AI监控服务
            process = subprocess.Popen(
                ['py', 'continuous_ai_monitor.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(('AI监控服务', process))
            print("✅ AI监控服务已启动")
            return True
        except Exception as e:
            print(f"❌ 启动AI监控服务失败: {e}")
            return False
    
    def start_status_monitor(self):
        """启动状态监控"""
        print("📊 启动状态监控...")
        try:
            # 启动状态监控
            process = subprocess.Popen(
                ['py', 'ai_status_monitor.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(('状态监控', process))
            print("✅ 状态监控已启动")
            return True
        except Exception as e:
            print(f"❌ 启动状态监控失败: {e}")
            return False
    
    def check_services_status(self):
        """检查服务状态"""
        print("🔍 检查服务状态...")
        
        # 检查Python进程
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True, shell=True)
            if 'python.exe' in result.stdout:
                lines = [line for line in result.stdout.strip().split('\n') if 'python.exe' in line]
                print(f"✅ 发现 {len(lines)} 个Python进程")
                return True
            else:
                print("❌ 未发现Python进程")
                return False
        except Exception as e:
            print(f"❌ 检查进程状态失败: {e}")
            return False
    
    def wait_for_ai_prediction(self, timeout=30):
        """等待AI预测生成"""
        print(f"⏳ 等待AI预测生成 (最多{timeout}秒)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if os.path.exists('ai_prediction.txt'):
                try:
                    with open('ai_prediction.txt', 'r') as f:
                        content = f.read().strip()
                        if content and ',' in content:
                            print("✅ AI预测已生成")
                            return True
                except:
                    pass
            time.sleep(1)
        
        print("❌ AI预测生成超时")
        return False
    
    def display_startup_info(self):
        """显示启动信息"""
        print("\n" + "=" * 60)
        print("🤖 AI增强风险管理EA - 服务启动完成")
        print("=" * 60)
        print("📋 服务状态:")
        print("  ✅ AI监控服务: 运行中")
        print("  ✅ 状态监控: 运行中")
        print("  ✅ 文件监控: 运行中")
        print("\n📊 监控文件:")
        print("  📄 market_data.csv - 市场数据")
        print("  📄 ai_prediction.txt - AI预测结果")
        print("\n🎯 当前AI预测:")
        
        if os.path.exists('ai_prediction.txt'):
            try:
                with open('ai_prediction.txt', 'r') as f:
                    content = f.read().strip()
                    if ',' in content:
                        parts = content.split(',')
                        prediction = int(parts[0])
                        confidence = float(parts[1])
                        direction = "买入" if prediction == 1 else "卖出" if prediction == 2 else "持有"
                        print(f"  🎯 方向: {direction}")
                        print(f"  📈 置信度: {confidence:.3f}")
            except:
                print("  ❌ 无法读取预测")
        else:
            print("  ⏳ 等待预测生成...")
        
        print("\n💡 使用说明:")
        print("  1. 在MT4中加载 AI_Enhanced_Risk_EA.mq4")
        print("  2. 确保EnableAI参数设置为true")
        print("  3. EA将自动读取AI预测进行交易决策")
        print("  4. 使用 ai_status_monitor.py 实时监控状态")
        print("\n🛑 停止服务: 按 Ctrl+C")
        print("=" * 60)
    
    def start_all_services(self):
        """启动所有AI服务"""
        print("🚀 启动AI增强风险管理EA服务...")
        print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查依赖项
        if not self.check_dependencies():
            print("❌ 依赖项检查失败，无法启动服务")
            return False
        
        # 启动AI监控服务
        if not self.start_ai_monitor():
            print("❌ AI监控服务启动失败")
            return False
        
        # 等待服务启动
        time.sleep(3)
        
        # 检查服务状态
        if not self.check_services_status():
            print("❌ 服务状态检查失败")
            return False
        
        # 等待AI预测生成
        if not self.wait_for_ai_prediction():
            print("⚠️ AI预测生成超时，但服务仍在运行")
        
        # 启动状态监控
        self.start_status_monitor()
        
        # 显示启动信息
        self.display_startup_info()
        
        self.is_running = True
        return True
    
    def stop_all_services(self):
        """停止所有服务"""
        print("\n🛑 停止AI服务...")
        
        # 停止所有进程
        for name, process in self.processes:
            try:
                process.terminate()
                print(f"✅ {name} 已停止")
            except:
                pass
        
        self.processes.clear()
        self.is_running = False
        print("👋 所有AI服务已停止")

def main():
    manager = AIServiceManager()
    
    try:
        if manager.start_all_services():
            print("\n🎉 AI服务启动成功!")
            print("💡 现在可以在MT4中加载EA了")
            
            # 保持运行
            try:
                while manager.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ AI服务启动失败")
            return 1
    except KeyboardInterrupt:
        print("\n👋 用户中断")
    finally:
        manager.stop_all_services()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 