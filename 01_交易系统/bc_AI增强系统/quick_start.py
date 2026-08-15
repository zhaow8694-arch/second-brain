#!/usr/bin/env python3
"""
EA AI模型快速启动脚本
一键完成环境检查、模型训练和服务启动
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8+")
        print(f"当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = {
        'torch': 'torch',
        'pandas': 'pandas', 
        'numpy': 'numpy',
        'sklearn': 'scikit-learn',
        'ta': 'ta',
        'joblib': 'joblib'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (需要安装)")
            missing_packages.append(pip_name)
    
    return missing_packages

def install_dependencies(packages):
    """安装缺失的依赖包"""
    if not packages:
        return True
        
    print(f"\n📦 安装缺失的依赖包: {', '.join(packages)}")
    try:
        cmd = [sys.executable, '-m', 'pip', 'install'] + packages
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 依赖包安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        print("请手动安装:")
        print(f"pip install {' '.join(packages)}")
        return False

def check_data_file():
    """检查数据文件"""
    data_files = ['XAUUSD15.csv', 'market_data.csv', 'trading_data.csv']
    
    for file_name in data_files:
        if os.path.exists(file_name):
            print(f"✅ 找到数据文件: {file_name}")
            return file_name
    
    print("⚠️  未找到数据文件")
    print("支持的文件名: XAUUSD15.csv, market_data.csv, trading_data.csv")
    
    # 提示用户选择
    choice = input("是否使用示例数据进行训练? (y/n): ")
    if choice.lower() in ['y', 'yes']:
        return 'sample'
    else:
        print("请将您的数据文件重命名为上述文件名之一")
        return None

def check_model_files():
    """检查模型文件"""
    model_file = 'best_trading_model.pth'
    processor_file = 'trading_data_processor.pkl'
    
    has_model = os.path.exists(model_file)
    has_processor = os.path.exists(processor_file)
    
    if has_model and has_processor:
        print("✅ 找到训练好的模型文件")
        return True
    else:
        print("⚠️  未找到模型文件，需要先训练")
        return False

def train_model():
    """训练模型"""
    print("\n🚀 开始训练AI模型...")
    print("=" * 50)
    
    try:
        import trading_transformer_model
        trading_transformer_model.main()
        
        # 检查训练结果
        if os.path.exists('best_trading_model.pth') and os.path.exists('trading_data_processor.pkl'):
            print("✅ 模型训练成功!")
            return True
        else:
            print("❌ 模型训练失败，未找到输出文件")
            return False
            
    except Exception as e:
        print(f"❌ 训练过程出错: {e}")
        return False

def start_ai_service():
    """启动AI服务"""
    print("\n🤖 启动AI预测服务...")
    print("=" * 50)
    
    try:
        import continuous_ai_monitor
        continuous_ai_monitor.continuous_monitor()
    except KeyboardInterrupt:
        print("\n👋 AI服务已停止")
    except Exception as e:
        print(f"❌ AI服务启动失败: {e}")

def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("🚀 EA AI模型管理工具")
    print("="*60)
    print("1. 完整流程 (检查环境 → 训练模型 → 启动服务)")
    print("2. 仅训练模型")
    print("3. 仅启动AI服务")
    print("4. 测试AI服务")
    print("5. 环境检查")
    print("6. 退出")
    print("="*60)
    
    choice = input("请选择操作 (1-6): ")
    return choice

def test_ai_service():
    """测试AI服务"""
    print("\n🧪 测试AI预测服务...")
    print("=" * 50)
    
    try:
        import continuous_ai_monitor
        continuous_ai_monitor.test_prediction()
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主函数"""
    print("🎯 EA专用AI模型快速启动工具")
    print("=" * 60)
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            # 完整流程
            print("\n📋 开始完整流程...")
            
            # 1. 检查环境
            if not check_python_version():
                continue
                
            missing = check_dependencies()
            if missing:
                if not install_dependencies(missing):
                    continue
            
            # 2. 检查数据
            data_file = check_data_file()
            if data_file is None:
                continue
            
            # 3. 检查模型
            if not check_model_files():
                # 训练模型
                if not train_model():
                    continue
            
            # 4. 启动服务
            start_ai_service()
            
        elif choice == '2':
            # 仅训练模型
            if not train_model():
                print("训练失败，请检查数据文件和环境")
                
        elif choice == '3':
            # 仅启动服务
            if not check_model_files():
                print("❌ 未找到模型文件，请先训练模型")
                continue
            start_ai_service()
            
        elif choice == '4':
            # 测试服务
            test_ai_service()
            
        elif choice == '5':
            # 环境检查
            print("\n🔍 环境检查...")
            check_python_version()
            missing = check_dependencies()
            if missing:
                print(f"需要安装: {missing}")
            else:
                print("✅ 环境检查通过")
            check_data_file()
            check_model_files()
            
        elif choice == '6':
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效选择，请输入1-6")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        print("请检查环境和文件是否正确") 