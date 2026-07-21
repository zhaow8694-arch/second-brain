import torch
import pandas as pd
import numpy as np
import joblib
import os
import time
from datetime import datetime
import ta
import warnings
warnings.filterwarnings('ignore')

# 导入模型类
from trading_transformer_model import TradingTransformer, TradingDataProcessor

class EATradingPredictor:
    """EA交易预测服务 - 原始版本"""
    
    def __init__(self, model_path='best_trading_model.pth', processor_path='trading_data_processor.pkl'):
        self.model_path = model_path
        self.processor_path = processor_path
        self.model = None
        self.processor = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.last_prediction_time = 0
        self.prediction_cache = None
        self.load_model()
        
    def load_model(self):
        """加载训练好的模型和数据处理器"""
        try:
            # 加载数据处理器
            if os.path.exists(self.processor_path):
                self.processor = joblib.load(self.processor_path)
                print(f"✅ 数据处理器加载成功: {self.processor_path}")
            else:
                print(f"❌ 数据处理器文件不存在: {self.processor_path}")
                return False
            
            # 加载模型
            if os.path.exists(self.model_path):
                # 重新创建模型架构
                from trading_transformer_model import TradingTransformer
                
                # 获取特征维度
                input_dim = len(self.processor.feature_columns)
                
                self.model = TradingTransformer(
                    input_dim=input_dim,
                    d_model=64,      # 使用新架构以匹配现有模型
                    nhead=4,         # 使用新架构以匹配现有模型
                    num_layers=3,    # 使用新架构以匹配现有模型
                    num_classes=3,
                    dropout=0.2      # 使用新架构以匹配现有模型
                )
                
                # 加载权重并确保设备一致
                state_dict = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.model.to(self.device)
                self.model.eval()
                
                # 确保模型所有参数都在正确设备上
                for param in self.model.parameters():
                    param.data = param.data.to(self.device)
                
                print(f"✅ 模型加载成功: {self.model_path}")
                print(f"🎯 输入特征维度: {input_dim}")
                print(f"🔧 设备: {self.device}")
                return True
            else:
                print(f"❌ 模型文件不存在: {self.model_path}")
                return False
                
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            return False
    
    def parse_market_data(self, file_path='market_data.csv'):
        """解析EA发送的市场数据"""
        try:
            if not os.path.exists(file_path):
                return None
                
            # 读取数据
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 47:  # 至少需要时间信息 + 45个数据点（降低要求）
                return None
            
            # 解析时间信息（兼容分号和逗号格式）
            server_time_line = lines[0].strip().split(';') if ';' in lines[0] else lines[0].strip().split(',')
            client_time_line = lines[1].strip().split(';') if ';' in lines[1] else lines[1].strip().split(',')
            
            if len(server_time_line) >= 2:
                server_time = server_time_line[1]
                print(f"📅 服务器时间: {server_time}")
            
            # 解析OHLCV数据（兼容分号和逗号格式）
            data = []
            for line in lines[2:]:  # 跳过前两行时间信息
                # 自动检测分隔符
                parts = line.strip().split(';') if ';' in line else line.strip().split(',')
                if len(parts) >= 6:  # time, open, high, low, close, volume
                    try:
                        data.append({
                            'time': parts[0],
                            'open': float(parts[1]),
                            'high': float(parts[2]),
                            'low': float(parts[3]),
                            'close': float(parts[4]),
                            'volume': float(parts[5])
                        })
                    except ValueError:
                        continue
            
            if len(data) < 45:  # 降低最小数据点要求
                print(f"⚠️ 数据点不足: {len(data)} < 45")
                return None
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            df.sort_index(inplace=True)
            
            print(f"📊 解析数据成功: {len(df)} 个数据点")
            return df
            
        except Exception as e:
            print(f"❌ 数据解析失败: {e}")
            return None
    
    def engineer_features(self, df):
        """特征工程 - 与训练时保持一致"""
        try:
            # 基础价格特征
            df['returns'] = df['close'].pct_change()
            df['high_low_ratio'] = df['high'] / df['low']
            df['price_range'] = (df['high'] - df['low']) / df['close']
            df['volume_price'] = df['volume'] * df['close']
            
            # MA指标
            df['ma_5'] = ta.trend.sma_indicator(df['close'], window=5)
            df['ma_20'] = ta.trend.sma_indicator(df['close'], window=20)
            df['ma_50'] = ta.trend.sma_indicator(df['close'], window=50)
            df['ma_200'] = ta.trend.sma_indicator(df['close'], window=200)
            
            # MA交叉信号
            df['ma_cross_5_20'] = (df['ma_5'] > df['ma_20']).astype(int)
            df['ma_cross_20_50'] = (df['ma_20'] > df['ma_50']).astype(int)
            # MA背离计算 - 添加除零保护
            df['ma_divergence'] = np.where(df['ma_20'] != 0, 
                                         (df['ma_5'] - df['ma_20']) / df['ma_20'], 
                                         0)
            
            # RSI指标
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
            df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
            df['rsi_momentum'] = df['rsi'].diff()
            
            # ATR指标
            df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
            # ATR标准化 - 添加除零保护
            df['atr_normalized'] = np.where(df['close'] != 0,
                                          df['atr'] / df['close'],
                                          0)
            df['atr_momentum'] = df['atr'].diff()
            
            # ADX指标
            df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
            df['adx_strong_trend'] = (df['adx'] > 25).astype(int)
            
            # MACD指标
            df['macd'] = ta.trend.macd_diff(df['close'])
            df['macd_signal'] = ta.trend.macd_signal(df['close'])
            df['macd_histogram'] = ta.trend.macd(df['close'])
            
            # 波动率特征
            df['volatility'] = df['returns'].rolling(window=20).std()
            df['volatility_ratio'] = df['volatility'] / df['volatility'].rolling(window=50).mean()
            
            # 成交量特征
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['volume_momentum'] = df['volume'].pct_change()
            
            # 价格位置特征
            df['price_position'] = (df['close'] - df['low'].rolling(20).min()) / \
                                  (df['high'].rolling(20).max() - df['low'].rolling(20).min())
            
            # 趋势强度特征
            df['trend_strength'] = df['close'].rolling(10).apply(
                lambda x: 1 if x.iloc[-1] > x.iloc[0] else -1
            )
            
            # 支撑阻力特征
            df['resistance_distance'] = (df['high'].rolling(20).max() - df['close']) / df['close']
            df['support_distance'] = (df['close'] - df['low'].rolling(20).min()) / df['close']
            
            # 时间特征
            df['hour'] = pd.to_datetime(df.index).hour
            df['day_of_week'] = pd.to_datetime(df.index).dayofweek
            df['is_trading_hour'] = ((df['hour'] >= 8) & (df['hour'] <= 22)).astype(int)
            
            # 市场状态特征
            df['market_score'] = (
                (1 - abs(df['volatility_ratio'] - 1)) * 0.3 +
                (df['adx'] / 100) * 0.4 +
                (df['volume_ratio'].clip(0, 2) / 2) * 0.3
            )
            
            # 智能填充NaN值 - 避免数据泄露和异常值
            # 1. 只使用后向填充，避免未来信息泄露
            df = df.fillna(method='bfill')
            
            # 2. 为不同类型指标设置合理的默认值
            # 价格类指标：使用中位数
            price_features = ['ma_5', 'ma_20', 'ma_50', 'ma_200']
            for feature in price_features:
                if feature in df.columns and df[feature].isnull().any():
                    df[feature] = df[feature].fillna(df['close'].median())
            
            # RSI类指标：使用50（中性值）
            if 'rsi' in df.columns:
                df['rsi'] = df['rsi'].fillna(50)
            
            # 交叉信号：使用0
            cross_features = ['ma_cross_5_20', 'ma_cross_20_50', 'rsi_oversold', 'rsi_overbought', 'adx_strong_trend', 'is_trading_hour']
            for feature in cross_features:
                if feature in df.columns:
                    df[feature] = df[feature].fillna(0)
            
            # 其他特征：使用0
            df = df.fillna(0)
            
            # 处理无穷值 - 用极值替换而不是0
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df[col].dtype in ['float64', 'float32']:
                    # 将无穷值替换为该列的99.9%分位数或0.1%分位数
                    finite_values = df[col].replace([np.inf, -np.inf], np.nan).dropna()
                    if len(finite_values) > 0:
                        upper_bound = finite_values.quantile(0.999)
                        lower_bound = finite_values.quantile(0.001)
                        df[col] = df[col].replace([np.inf], upper_bound)
                        df[col] = df[col].replace([-np.inf], lower_bound)
            
            print(f"✅ 特征工程完成，nan值: {df.isnull().sum().sum()}")
            
            return df
            
        except Exception as e:
            print(f"❌ 特征工程失败: {e}")
            return None
    
    def make_prediction(self, df):
        """进行AI预测"""
        try:
            if self.model is None or self.processor is None:
                print("❌ 模型或处理器未加载")
                return None, None
            
            # 特征工程
            df_features = self.engineer_features(df.copy())
            if df_features is None:
                return None, None
            
            # 选择特征列
            available_features = [col for col in self.processor.feature_columns if col in df_features.columns]
            if len(available_features) != len(self.processor.feature_columns):
                missing_features = set(self.processor.feature_columns) - set(available_features)
                print(f"⚠️ 缺少特征: {missing_features}")
            
            # 准备输入数据
            feature_data = df_features[available_features].values
            if len(feature_data) < 50:
                print(f"❌ 数据点不足: {len(feature_data)} < 50")
                return None, None
            
            # 标准化
            feature_data = self.processor.scaler.transform(feature_data)
            
            # 取最后50个数据点作为输入序列
            input_sequence = feature_data[-50:]
            input_tensor = torch.FloatTensor(input_sequence).unsqueeze(0).to(self.device)  # (1, 50, features)
            
            # 检查输入数据是否包含nan
            if np.isnan(input_sequence).any():
                print("⚠️ 输入序列包含nan值，尝试修复...")
                input_sequence = np.nan_to_num(input_sequence, nan=0.0)
            
            # 模型推理
            with torch.no_grad():
                logits, attention_weights = self.model(input_tensor)
                
                # 检查模型输出是否为nan
                if torch.isnan(logits).any():
                    print("❌ 模型输出包含nan值")
                    return None, None
                
                probabilities = torch.softmax(logits, dim=1)
                prediction = torch.argmax(logits, dim=1).item()
                confidence = probabilities[0][prediction].item()
                
                # 再次检查置信度是否为nan
                if np.isnan(confidence):
                    print("⚠️ 置信度为nan，使用默认值0.5")
                    confidence = 0.5
            
            # 预测含义
            prediction_meanings = {0: "看跌", 1: "震荡", 2: "看涨"}
            
            print(f"🤖 AI预测: {prediction} ({prediction_meanings[prediction]})")
            print(f"🎯 置信度: {confidence:.4f}")
            print(f"📊 概率分布: 看跌={probabilities[0][0]:.3f}, 震荡={probabilities[0][1]:.3f}, 看涨={probabilities[0][2]:.3f}")
            
            return prediction, confidence
            
        except Exception as e:
            print(f"❌ 预测失败: {e}")
            return None, None
    
    def make_prediction_from_file(self, file_path):
        """从文件读取数据并进行预测的便捷方法"""
        df = self.parse_market_data(file_path)
        if df is not None:
            return self.make_prediction(df)
        return None, None
    
    def write_prediction(self, prediction, confidence, output_file='ai_prediction.txt'):
        """写入预测结果"""
        try:
            timestamp = int(time.time())
            prediction_line = f"{prediction},{confidence:.6f},{timestamp}\n"
            
            with open(output_file, 'w') as f:
                f.write(prediction_line)
            
            print(f"📝 预测结果已写入: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ 写入预测失败: {e}")
            return False
    
    def process_request(self, data_file='market_data.csv', output_file='ai_prediction.txt'):
        """处理单次预测请求"""
        # 解析市场数据
        df = self.parse_market_data(data_file)
        if df is None:
            return False
        
        # 进行预测
        prediction, confidence = self.make_prediction(df)
        if prediction is None:
            return False
        
        # 写入结果
        return self.write_prediction(prediction, confidence, output_file)

class RealTimePredictiveService:
    """实时预测式AI服务 - 主动预测模式"""
    
    def __init__(self, model_path='best_trading_model.pth', processor_path='trading_data_processor.pkl'):
        self.predictor = EATradingPredictor(model_path, processor_path)
        self.last_prediction = None
        self.last_prediction_time = 0
        self.prediction_cache_duration = 5  # 5秒缓存
        self.last_data_hash = None
        
    def get_data_hash(self, data_file):
        """获取数据文件的哈希值，用于检测数据变化"""
        try:
            if not os.path.exists(data_file):
                return None
            
            # 读取最后几行数据生成哈希
            with open(data_file, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 5:
                return None
                
            # 使用最后5行数据的内容生成哈希
            last_lines = ''.join(lines[-5:])
            import hashlib
            return hashlib.md5(last_lines.encode()).hexdigest()
            
        except Exception as e:
            print(f"❌ 获取数据哈希失败: {e}")
            return None
    
    def should_update_prediction(self, data_file):
        """判断是否需要更新预测"""
        current_time = time.time()
        
        # 检查时间缓存
        if current_time - self.last_prediction_time < self.prediction_cache_duration:
            return False
            
        # 检查数据变化
        current_hash = self.get_data_hash(data_file)
        if current_hash is None:
            return False
            
        if current_hash != self.last_data_hash:
            self.last_data_hash = current_hash
            return True
            
        return False
    
    def make_proactive_prediction(self, data_file, output_file):
        """主动进行预测"""
        try:
            # 检查是否需要更新预测
            if not self.should_update_prediction(data_file):
                return True  # 使用缓存预测
            
            print(f"\n🔄 检测到数据变化，进行实时预测: {datetime.now().strftime('%H:%M:%S')}")
            
            # 解析最新数据
            df = self.predictor.parse_market_data(data_file)
            if df is None:
                print("❌ 数据解析失败")
                return False
            
            # 进行预测
            prediction, confidence = self.predictor.make_prediction(df)
            if prediction is None:
                print("❌ 预测失败")
                return False
            
            # 立即写入预测结果
            success = self.predictor.write_prediction(prediction, confidence, output_file)
            if success:
                self.last_prediction = (prediction, confidence)
                self.last_prediction_time = time.time()
                print("⚡ 实时预测完成，结果已缓存")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 实时预测失败: {e}")
            return False

def continuous_monitor(data_file='market_data.csv', output_file='ai_prediction.txt', check_interval=1, mt4_files_path=None):
    """持续监控模式"""
    print("🚀 启动EA AI预测服务")
    print("=" * 60)
    
    # 初始化预测器
    predictor = EATradingPredictor()
    
    if predictor.model is None:
        print("❌ 无法加载模型，退出服务")
        return
    
    # 处理MT4 Files路径
    if mt4_files_path:
        data_file = os.path.join(mt4_files_path, data_file)
        output_file = os.path.join(mt4_files_path, output_file)
        print(f"📁 使用MT4 Files路径: {mt4_files_path}")
    
    print(f"👀 监控文件: {data_file}")
    print(f"📝 输出文件: {output_file}")
    print(f"⏱️ 检查间隔: {check_interval}秒")
    print("🔄 开始持续监控...")
    print("按 Ctrl+C 停止服务")
    print("-" * 60)
    
    last_modified = 0
    
    try:
        while True:
            try:
                # 检查文件是否存在和更新
                if os.path.exists(data_file):
                    current_modified = os.path.getmtime(data_file)
                    
                    # 如果文件有更新
                    if current_modified > last_modified:
                        print(f"\n🔔 检测到数据文件更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # 处理预测请求
                        success = predictor.process_request(data_file, output_file)
                        
                        if success:
                            print("✅ 预测完成")
                        else:
                            print("❌ 预测失败")
                        
                        last_modified = current_modified
                        print("-" * 40)
                
                else:
                    if last_modified > 0:  # 只在第一次时显示
                        print(f"⏳ 等待数据文件: {data_file}")
                        last_modified = 0
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 收到停止信号，正在退出...")
                break
            except Exception as e:
                print(f"❌ 监控过程中出错: {e}")
                time.sleep(check_interval)
    
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
    
    print("🛑 AI预测服务已停止")

def proactive_continuous_monitor(data_file='market_data.csv', output_file='ai_prediction.txt', 
                                check_interval=0.5, mt4_files_path=None):
    """预测式持续监控 - 主动预测模式"""
    print("🚀 启动预测式实时AI服务")
    print("=" * 60)
    print("🔥 模式: 主动预测 + 实时响应")
    print("⚡ 特性: 数据变化时立即预测，EA无需等待")
    
    # 初始化实时预测服务
    rt_service = RealTimePredictiveService()
    
    if rt_service.predictor.model is None:
        print("❌ 无法加载模型，退出服务")
        return
    
    # 处理MT4 Files路径
    if mt4_files_path:
        data_file = os.path.join(mt4_files_path, data_file)
        output_file = os.path.join(mt4_files_path, output_file)
        print(f"📁 使用MT4 Files路径: {mt4_files_path}")
    
    print(f"👀 监控文件: {data_file}")
    print(f"📝 输出文件: {output_file}")
    print(f"⏱️ 检查间隔: {check_interval}秒")
    print(f"🔄 预测缓存: {rt_service.prediction_cache_duration}秒")
    print("🔄 开始实时预测监控...")
    print("按 Ctrl+C 停止服务")
    print("-" * 60)
    
    consecutive_failures = 0
    max_consecutive_failures = 10
    
    try:
        while True:
            try:
                # 检查文件是否存在
                if os.path.exists(data_file):
                    # 主动进行预测
                    success = rt_service.make_proactive_prediction(data_file, output_file)
                    
                    if success:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            print(f"❌ 连续预测失败{max_consecutive_failures}次，重新初始化服务...")
                            rt_service = RealTimePredictiveService()
                            consecutive_failures = 0
                
                else:
                    if consecutive_failures == 0:  # 只在第一次时显示
                        print(f"⏳ 等待数据文件: {data_file}")
                    consecutive_failures += 1
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 收到停止信号，正在退出...")
                break
            except Exception as e:
                print(f"❌ 监控过程中出错: {e}")
                consecutive_failures += 1
                time.sleep(check_interval)
    
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
    
    print("🛑 实时预测服务已停止")

def test_prediction():
    """测试预测功能"""
    print("🧪 测试AI预测功能")
    print("=" * 40)
    
    # 创建测试数据
    dates = pd.date_range(start='2024-01-01', periods=60, freq='1H')
    np.random.seed(42)
    
    test_data = []
    price = 2000
    
    for date in dates:
        price_change = np.random.normal(0, 0.01)
        price *= (1 + price_change)
        
        volatility = abs(np.random.normal(0, 0.005))
        
        test_data.append({
            'time': date,
            'open': price,
            'high': price * (1 + volatility),
            'low': price * (1 - volatility),
            'close': price * (1 + np.random.normal(0, 0.002)),
            'volume': np.random.randint(1000, 5000)
        })
    
    # 保存测试数据
    df = pd.DataFrame(test_data)
    df.to_csv('test_market_data.csv', index=False)
    
    # 格式化为EA格式
    with open('market_data.csv', 'w') as f:
        f.write(f"ServerTime,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"ClientTime,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for _, row in df.iterrows():
            f.write(f"{row['time']},{row['open']},{row['high']},{row['low']},{row['close']},{row['volume']}\n")
    
    # 测试预测
    predictor = EATradingPredictor()
    if predictor.model is not None:
        success = predictor.process_request()
        if success:
            print("✅ 测试成功")
        else:
            print("❌ 测试失败")
    else:
        print("❌ 模型加载失败，无法测试")

def main():
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            # 测试模式
            print("🧪 测试模式")
            predictor = EATradingPredictor()
            
            if predictor.model is None:
                print("❌ 模型加载失败")
                return
            
            # 测试预测
            test_data_file = 'test_data/test_market_data.csv'
            if os.path.exists(test_data_file):
                result = predictor.process_request(test_data_file, 'test_prediction.txt')
                print(f"✅ 测试{'成功' if result else '失败'}")
            else:
                print(f"❌ 测试数据文件不存在: {test_data_file}")
        
        elif command == 'mt4':
            # MT4模式 - 使用实时预测式服务
            mt4_path = None
            if len(sys.argv) > 2:
                mt4_path = sys.argv[2]
            else:
                # 默认MT4路径
                default_paths = [
                    r"C:\Program Files (x86)\Hantec Markets V MT4 Terminal\MQL4\Files",
                    r"C:\Program Files (x86)\MetaTrader 4\MQL4\Files",
                    r"C:\Program Files\MetaTrader 4\MQL4\Files"
                ]
                
                for path in default_paths:
                    if os.path.exists(path):
                        mt4_path = path
                        break
            
            if mt4_path and os.path.exists(mt4_path):
                print(f"🎯 MT4实时预测模式")
                proactive_continuous_monitor(mt4_files_path=mt4_path, check_interval=0.5)
            else:
                print("❌ 未找到MT4 Files目录，请手动指定路径")
                print("用法: python continuous_ai_monitor.py mt4 \"C:\\Your\\MT4\\Path\\MQL4\\Files\"")
        
        elif command == 'realtime' or command == 'rt':
            # 实时模式
            print("⚡ 实时预测模式")
            proactive_continuous_monitor(check_interval=0.5)
        
        else:
            print("❌ 未知命令")
            print("可用命令:")
            print("  test    - 测试模式")
            print("  mt4     - MT4实时预测模式")
            print("  realtime/rt - 本地实时预测模式")
    
    else:
        # 默认监控模式（向后兼容）
        print("📊 默认监控模式")
        continuous_monitor()

if __name__ == "__main__":
    main() 