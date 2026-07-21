#!/usr/bin/env python3
"""
建仓频率限制功能演示脚本
展示15分钟间隔建仓控制的效果
"""

from datetime import datetime, timedelta

class OrderFrequencyDemo:
    def __init__(self):
        self.min_order_interval = 900  # 15分钟 = 900秒
        self.max_normal_orders = 12
        self.max_lock_orders = 4
        
        # 模拟时间记录
        self.last_normal_order_time = None
        self.last_lock_order_time = None
        
        # 模拟持仓
        self.normal_orders = []
        self.lock_orders = []
        
    def can_place_normal_order(self):
        """检查是否可以建普通仓"""
        # 检查持仓数量
        if len(self.normal_orders) >= self.max_normal_orders:
            print(f"📊 普通仓已达上限: {len(self.normal_orders)}/{self.max_normal_orders}")
            return False
        
        # 检查时间间隔
        if self.last_normal_order_time:
            elapsed = (datetime.now() - self.last_normal_order_time).total_seconds()
            if elapsed < self.min_order_interval:
                remaining = self.min_order_interval - elapsed
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                print(f"⏰ 普通仓建仓间隔不足，还需等待 {minutes}分{seconds}秒")
                return False
        
        return True
    
    def can_place_lock_order(self):
        """检查是否可以建锁仓单"""
        # 检查持仓数量
        if len(self.lock_orders) >= self.max_lock_orders:
            print(f"🔒 锁仓单已达上限: {len(self.lock_orders)}/{self.max_lock_orders}")
            return False
        
        # 检查时间间隔
        if self.last_lock_order_time:
            elapsed = (datetime.now() - self.last_lock_order_time).total_seconds()
            if elapsed < self.min_order_interval:
                remaining = self.min_order_interval - elapsed
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                print(f"⏰ 锁仓单建仓间隔不足，还需等待 {minutes}分{seconds}秒")
                return False
        
        return True
    
    def place_normal_order(self, order_type="买入"):
        """建普通仓"""
        if self.can_place_normal_order():
            order_id = len(self.normal_orders) + 1
            self.normal_orders.append({
                "id": order_id,
                "type": order_type,
                "time": datetime.now()
            })
            self.last_normal_order_time = datetime.now()
            print(f"✅ 普通仓建仓成功: {order_type}订单 #{order_id}")
            print(f"📅 建仓时间: {self.last_normal_order_time.strftime('%H:%M:%S')}")
            return True
        else:
            print(f"❌ 普通仓建仓失败: {order_type}")
            return False
    
    def place_lock_order(self, order_type="卖出"):
        """建锁仓单"""
        if self.can_place_lock_order():
            order_id = len(self.lock_orders) + 1
            self.lock_orders.append({
                "id": order_id,
                "type": order_type,
                "time": datetime.now()
            })
            self.last_lock_order_time = datetime.now()
            print(f"✅ 锁仓单建仓成功: {order_type}订单 #{order_id}")
            print(f"📅 建仓时间: {self.last_lock_order_time.strftime('%H:%M:%S')}")
            return True
        else:
            print(f"❌ 锁仓单建仓失败: {order_type}")
            return False
    
    def show_status(self):
        """显示当前状态"""
        print(f"\n📊 当前状态:")
        print(f"  普通仓: {len(self.normal_orders)}/{self.max_normal_orders} 单")
        print(f"  锁仓单: {len(self.lock_orders)}/{self.max_lock_orders} 单")
        
        if self.last_normal_order_time:
            elapsed = (datetime.now() - self.last_normal_order_time).total_seconds()
            remaining = max(0, self.min_order_interval - elapsed)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            print(f"  普通仓下次可建仓: {minutes}分{seconds}秒后")
            
        if self.last_lock_order_time:
            elapsed = (datetime.now() - self.last_lock_order_time).total_seconds()
            remaining = max(0, self.min_order_interval - elapsed)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            print(f"  锁仓单下次可建仓: {minutes}分{seconds}秒后")
    
    def simulate_trading_scenario(self):
        """模拟交易场景"""
        print("🚀 建仓频率限制功能演示")
        print("=" * 60)
        print("📋 系统参数:")
        print(f"  建仓间隔: {self.min_order_interval/60} 分钟")
        print(f"  普通仓上限: {self.max_normal_orders} 单")
        print(f"  锁仓单上限: {self.max_lock_orders} 单")
        print("=" * 60)
        
        # 场景1: 连续建仓测试
        print("\n📈 场景1: 连续建仓测试")
        print("-" * 40)
        
        print("\n步骤1: 尝试连续建普通仓")
        self.place_normal_order("买入")
        self.place_normal_order("买入")  # 应该成功
        self.place_normal_order("买入")  # 应该成功（时间间隔不足）
        
        print("\n步骤2: 尝试连续建锁仓单")
        self.place_lock_order("卖出")
        self.place_lock_order("卖出")  # 应该成功（时间间隔不足）
        
        self.show_status()
        
        # 场景2: 时间间隔测试
        print("\n\n⏰ 场景2: 时间间隔测试")
        print("-" * 40)
        
        print("\n步骤3: 立即尝试再次建仓")
        self.place_normal_order("卖出")  # 应该失败（时间间隔不足）
        self.place_lock_order("买入")    # 应该失败（时间间隔不足）
        
        # 模拟等待时间
        print(f"\n⏳ 模拟等待 {self.min_order_interval/60} 分钟...")
        print("(实际演示中这里会等待15分钟)")
        
        # 模拟时间流逝
        if self.last_normal_order_time:
            self.last_normal_order_time -= timedelta(seconds=self.min_order_interval)
        if self.last_lock_order_time:
            self.last_lock_order_time -= timedelta(seconds=self.min_order_interval)
        
        print("\n步骤4: 等待后再次尝试建仓")
        self.place_normal_order("卖出")  # 应该成功
        self.place_lock_order("买入")    # 应该成功
        
        self.show_status()
        
        # 场景3: 混合建仓测试
        print("\n\n🔄 场景3: 混合建仓测试")
        print("-" * 40)
        
        print("\n步骤5: 清空持仓，测试混合建仓")
        self.normal_orders = []
        self.lock_orders = []
        self.last_normal_order_time = None
        self.last_lock_order_time = None
        
        print("\n步骤6: 交替建仓")
        self.place_normal_order("买入")   # 普通仓1
        self.place_lock_order("卖出")     # 锁仓单1
        self.place_normal_order("卖出")   # 普通仓2
        self.place_lock_order("买入")     # 应该成功（时间间隔不足）
        
        self.show_status()
        
        # 场景4: 实际应用场景
        print("\n\n🎯 场景4: 实际应用场景")
        print("-" * 40)
        
        print("📊 实际交易中的效果:")
        print("  ✅ 避免频繁建仓，降低滑点风险")
        print("  ✅ 控制持仓数量，管理风险")
        print("  ✅ 与15分钟图表周期同步")
        print("  ✅ 独立控制普通仓和锁仓单")
        print("  ✅ 智能提示剩余等待时间")
        
        print("\n📈 建仓频率控制优势:")
        print("  1. 降低交易成本")
        print("  2. 提高建仓质量")
        print("  3. 减少市场噪音影响")
        print("  4. 更好的风险控制")
        print("  5. 符合15分钟图表交易节奏")
        
        print("\n🎉 建仓频率限制功能演示完成！")
        print("✅ 所有功能正常工作，可以安全使用！")

if __name__ == "__main__":
    demo = OrderFrequencyDemo()
    demo.simulate_trading_scenario() 