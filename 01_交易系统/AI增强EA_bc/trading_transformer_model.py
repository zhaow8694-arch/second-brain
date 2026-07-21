import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import ta
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class TradingDataProcessor:
    """专门为EA系统设计的数据处理器"""
    
    def __init__(self, sequence_length=50):
        self.sequence_length = sequence_length  # 与EA中的50个数据点对应
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def engineer_features(self, df):
        """特征工程 - 基于EA中使用的技术指标"""
        # 基础价格特征
        df['returns'] = df['close'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['price_range'] = (df['high'] - df['low']) / df['close']
        df['volume_price'] = df['volume'] * df['close']
        
        # MA指标 (对应EA中的ma_fast, ma_slow, ma_long)
        df['ma_5'] = ta.trend.sma_indicator(df['close'], window=5)
        df['ma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['ma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['ma_200'] = ta.trend.sma_indicator(df['close'], window=200)
        
        # MA交叉信号
        df['ma_cross_5_20'] = (df['ma_5'] > df['ma_20']).astype(int)
        df['ma_cross_20_50'] = (df['ma_20'] > df['ma_50']).astype(int)
        df['ma_divergence'] = (df['ma_5'] - df['ma_20']) / df['ma_20']
        
        # RSI指标 (对应EA中的RSI)
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        df['rsi_momentum'] = df['rsi'].diff()
        
        # ATR指标 (对应EA中的ATR)
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        df['atr_normalized'] = df['atr'] / df['close']
        df['atr_momentum'] = df['atr'].diff()
        
        # ADX指标 (对应EA中的ADX)
        df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
        df['adx_strong_trend'] = (df['adx'] > 25).astype(int)
        
        # MACD指标
        df['macd'] = ta.trend.macd_diff(df['close'])
        df['macd_signal'] = ta.trend.macd_signal(df['close'])
        df['macd_histogram'] = ta.trend.macd(df['close'])
        
        # 波动率特征 (对应EA中的市场监控)
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
        
        # 支撑阻力特征 (对应EA中的GetNearestSupport/Resistance)
        df['resistance_distance'] = (df['high'].rolling(20).max() - df['close']) / df['close']
        df['support_distance'] = (df['close'] - df['low'].rolling(20).min()) / df['close']
        
        # 时间特征
        df['hour'] = pd.to_datetime(df.index).hour
        df['day_of_week'] = pd.to_datetime(df.index).dayofweek
        df['is_trading_hour'] = ((df['hour'] >= 8) & (df['hour'] <= 22)).astype(int)
        
        # 市场状态特征 (对应EA中的市场评分)
        df['market_score'] = (
            (1 - abs(df['volatility_ratio'] - 1)) * 0.3 +  # 波动率评分
            (df['adx'] / 100) * 0.4 +                       # 趋势强度评分  
            (df['volume_ratio'].clip(0, 2) / 2) * 0.3       # 成交量评分
        )
        
        return df
    
    def create_labels(self, df, future_periods=5, threshold=0.001):
        """
        创建标签 - 使用更平衡的阈值，减少极端预测
        0: 看跌, 1: 震荡, 2: 看涨
        """
        # 计算未来收益率
        df['future_return'] = df['close'].shift(-future_periods) / df['close'] - 1
        
        # 使用更平衡的百分位数来创建标签
        returns = df['future_return'].dropna()
        
        # 使用40%和60%分位数，增加震荡类别比例
        lower_threshold = returns.quantile(0.40)
        upper_threshold = returns.quantile(0.60)
        
        print(f"平衡阈值: 看跌<{lower_threshold:.4f}, 震荡[{lower_threshold:.4f}, {upper_threshold:.4f}], 看涨>{upper_threshold:.4f}")
        
        # 三分类标签
        labels = []
        for ret in df['future_return']:
            if pd.isna(ret):
                labels.append(-1)  # 无效标签
            elif ret < lower_threshold:
                labels.append(0)   # 看跌
            elif ret > upper_threshold:
                labels.append(2)   # 看涨  
            else:
                labels.append(1)   # 震荡
                
        df['label'] = labels
        return df
    
    def prepare_sequences(self, df):
        """准备序列数据"""
        # 选择特征列 (排除标签和一些辅助列)
        feature_cols = [col for col in df.columns if col not in 
                       ['label', 'future_return', 'time', 'open', 'high', 'low', 'close', 'volume']]
        
        # 移除包含NaN的列
        feature_cols = [col for col in feature_cols if not df[col].isna().any()]
        self.feature_columns = feature_cols
        
        print(f"使用 {len(feature_cols)} 个特征: {feature_cols[:10]}...")
        
        # 标准化特征
        feature_data = self.scaler.fit_transform(df[feature_cols].values)
        
        # 创建序列数据
        X, y = [], []
        for i in range(self.sequence_length, len(df)):
            if df['label'].iloc[i] != -1:  # 跳过无效标签
                X.append(feature_data[i-self.sequence_length:i])
                y.append(df['label'].iloc[i])
        
        return np.array(X), np.array(y)

class PositionalEncoding(nn.Module):
    """位置编码 - 为时间序列添加位置信息"""
    
    def __init__(self, d_model, max_len=100):
        super().__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                            (-torch.log(torch.tensor(10000.0)) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        return x + self.pe[:x.size(0), :]

class TradingTransformer(nn.Module):
    """专门为交易预测设计的Transformer模型 - 优化版本"""
    
    def __init__(self, input_dim, d_model=64, nhead=4, num_layers=3, 
                 num_classes=3, dropout=0.2, max_len=100):
        super().__init__()
        
        # 输入投影层
        self.input_projection = nn.Linear(input_dim, d_model)
        
        # 位置编码
        self.pos_encoder = PositionalEncoding(d_model, max_len)
        
        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead, 
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # 注意力池化层
        self.attention_pool = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=nhead,
            dropout=dropout,
            batch_first=True
        )
        
        # 分类头
        self.classifier = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, num_classes)
        )
        
        # 初始化权重
        self.init_weights()
    
    def init_weights(self):
        """权重初始化"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        batch_size, seq_len, _ = x.shape
        
        # 输入投影
        x = self.input_projection(x)  # (batch_size, seq_len, d_model)
        
        # 位置编码
        x = x.transpose(0, 1)  # (seq_len, batch_size, d_model)
        x = self.pos_encoder(x)
        x = x.transpose(0, 1)  # (batch_size, seq_len, d_model)
        
        # Transformer编码
        encoded = self.transformer(x)  # (batch_size, seq_len, d_model)
        
        # 注意力池化 - 学习重要的时间步
        query = encoded.mean(dim=1, keepdim=True)  # (batch_size, 1, d_model)
        pooled, attention_weights = self.attention_pool(query, encoded, encoded)
        pooled = pooled.squeeze(1)  # (batch_size, d_model)
        
        # 分类
        logits = self.classifier(pooled)  # (batch_size, num_classes)
        
        return logits, attention_weights

class TradingModelTrainer:
    """模型训练器 - 优化版本"""
    
    def __init__(self, model, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.model = model.to(device)
        self.device = device
        # 使用平衡的类别权重，避免极端预测
        self.criterion = nn.CrossEntropyLoss(weight=torch.tensor([1.2, 1.0, 1.2]).to(device))
        self.optimizer = optim.AdamW(model.parameters(), lr=5e-5, weight_decay=1e-4)  # 降低学习率
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=100)
        
        # 温度缩放参数 - 用于校准置信度
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)
        
        # 温度缩放参数 - 用于校准置信度
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)
        
    def train_epoch(self, train_loader):
        """训练一个epoch"""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(self.device).float()
            batch_y = batch_y.to(self.device).long()
            
            self.optimizer.zero_grad()
            
            logits, _ = self.model(batch_x)
            loss = self.criterion(logits, batch_y)
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            total_loss += loss.item()
            _, predicted = torch.max(logits.data, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
        
        return total_loss / len(train_loader), correct / total
    
    def validate(self, val_loader):
        """验证模型"""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        class_correct = [0, 0, 0]
        class_total = [0, 0, 0]
        
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(self.device).float()
                batch_y = batch_y.to(self.device).long()
                
                logits, _ = self.model(batch_x)
                loss = self.criterion(logits, batch_y)
                
                total_loss += loss.item()
                _, predicted = torch.max(logits, 1)
                total += batch_y.size(0)
                correct += (predicted == batch_y).sum().item()
                
                # 分类别准确率
                for i in range(batch_y.size(0)):
                    label = batch_y[i].item()
                    class_total[label] += 1
                    if predicted[i] == batch_y[i]:
                        class_correct[label] += 1
        
        # 计算分类别准确率
        class_acc = [class_correct[i] / max(class_total[i], 1) for i in range(3)]
        
        return total_loss / len(val_loader), correct / total, class_acc
    
    def train(self, train_loader, val_loader, epochs=100, patience=15):
        """完整训练流程"""
        best_val_acc = 0
        patience_counter = 0
        
        for epoch in range(epochs):
            # 训练
            train_loss, train_acc = self.train_epoch(train_loader)
            
            # 验证
            val_loss, val_acc, class_acc = self.validate(val_loader)
            
            # 学习率调度
            self.scheduler.step()
            
            print(f'Epoch {epoch+1}/{epochs}:')
            print(f'  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}')
            print(f'  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}')
            print(f'  Class Acc - 看跌: {class_acc[0]:.3f}, 震荡: {class_acc[1]:.3f}, 看涨: {class_acc[2]:.3f}')
            print(f'  LR: {self.optimizer.param_groups[0]["lr"]:.6f}')
            
            # 早停机制
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                torch.save(self.model.state_dict(), 'best_trading_model.pth')
                print(f'  💾 保存最佳模型 (Val Acc: {best_val_acc:.4f})')
            else:
                patience_counter += 1
                
            if patience_counter >= patience:
                print(f'早停触发，最佳验证准确率: {best_val_acc:.4f}')
                break
            
            print('-' * 60)
        
        # 加载最佳模型
        self.model.load_state_dict(torch.load('best_trading_model.pth'))
        return best_val_acc

def load_data(file_path):
    """加载数据 - 支持MT4和标准格式"""
    try:
        # 尝试读取CSV文件
        df = pd.read_csv(file_path, header=None)
        
        # 检查是否为MT4格式 (7列：日期,时间,开,高,低,收,量)
        if df.shape[1] == 7:
            # MT4格式 - 7列
            df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'volume']
            # 合并日期和时间
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
            df = df.drop(['date', 'time'], axis=1)
            df.set_index('datetime', inplace=True)
            print("检测到MT4格式(7列)，已自动转换")
        elif df.shape[1] == 6:
            # 标准格式或无表头的MT4格式
            # 检查第一行是否为数据
            first_row = df.iloc[0]
            try:
                # 尝试解析第一行的日期
                pd.to_datetime(str(first_row[0]) + ' ' + str(first_row[1]))
                # 如果成功，说明是MT4格式无表头
                df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'volume']
                df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                df = df.drop(['date', 'time'], axis=1)
                df.set_index('datetime', inplace=True)
                print("检测到MT4格式(无表头)，已自动转换")
            except:
                # 标准格式但可能有表头问题
                df = pd.read_csv(file_path)
                required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
                if not all(col in df.columns for col in required_cols):
                    print(f"数据文件格式不支持，需要包含列: {required_cols}")
                    return None
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
        else:
            print(f"不支持的数据格式，列数: {df.shape[1]}")
            return None
        
        # 确保数据类型正确
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # 移除无效数据
        df = df.dropna()
        
        # 确保数据按时间排序
        df.sort_index(inplace=True)
        
        print(f"数据加载成功: {len(df)} 条记录")
        print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
        print(f"价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
        
        return df
        
    except Exception as e:
        print(f"数据加载失败: {e}")
        return None

def create_sample_data():
    """创建示例数据用于测试"""
    print("创建示例数据...")
    
    # 生成5000个数据点
    dates = pd.date_range(start='2023-01-01', periods=5000, freq='1H')
    
    # 模拟价格走势
    np.random.seed(42)
    price = 2000
    prices = []
    
    for i in range(len(dates)):
        # 添加趋势和随机波动
        trend = 0.0001 * np.sin(i * 0.01)  # 长期趋势
        noise = np.random.normal(0, 0.002)  # 随机噪声
        price_change = trend + noise
        price *= (1 + price_change)
        prices.append(price)
    
    # 生成OHLCV数据
    data = []
    for i, price in enumerate(prices):
        volatility = abs(np.random.normal(0, 0.001))
        
        open_price = price
        high_price = price * (1 + volatility)
        low_price = price * (1 - volatility)
        close_price = price * (1 + np.random.normal(0, 0.0005))
        volume = np.random.randint(1000, 5000)
        
        data.append({
            'time': dates[i],
            'open': open_price,
            'high': high_price, 
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.to_csv('sample_trading_data.csv', index=False)
    print("示例数据已保存到 sample_trading_data.csv")
    
    return df

def main():
    """主训练流程"""
    print("🚀 开始训练EA专用Transformer模型")
    print("=" * 60)
    
    # 加载数据
    df = load_data('xinXAUUSD15.csv')  # 使用正确的数据文件
    if df is None:
        df = create_sample_data()  # 如果失败则创建示例数据
        df.set_index('time', inplace=True)
    
    print(f"原始数据形状: {df.shape}")
    
    # 数据处理
    processor = TradingDataProcessor(sequence_length=50)
    
    # 特征工程
    print("执行特征工程...")
    df = processor.engineer_features(df)
    
    # 创建标签
    print("创建标签...")
    df = processor.create_labels(df, future_periods=5, threshold=0.002)
    
    # 移除NaN值
    df = df.dropna()
    print(f"清理后数据形状: {df.shape}")
    
    # 检查标签分布
    label_counts = df['label'].value_counts().sort_index()
    print(f"标签分布: {dict(label_counts)}")
    
    if len(label_counts) < 3:
        print("警告: 标签类别不足，调整阈值...")
        df = processor.create_labels(df, future_periods=3, threshold=0.001)
        df = df.dropna()
        label_counts = df['label'].value_counts().sort_index()
        print(f"调整后标签分布: {dict(label_counts)}")
    
    # 准备序列数据
    print("准备序列数据...")
    X, y = processor.prepare_sequences(df)
    print(f"序列数据形状: X={X.shape}, y={y.shape}")
    
    if len(X) == 0:
        print("错误: 没有可用的训练数据")
        return
    
    # 数据分割
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    print(f"训练集: {X_train.shape[0]} 样本")
    print(f"验证集: {X_val.shape[0]} 样本") 
    print(f"测试集: {X_test.shape[0]} 样本")
    
    # 创建数据加载器
    train_dataset = torch.utils.data.TensorDataset(
        torch.FloatTensor(X_train), torch.LongTensor(y_train)
    )
    val_dataset = torch.utils.data.TensorDataset(
        torch.FloatTensor(X_val), torch.LongTensor(y_val)
    )
    test_dataset = torch.utils.data.TensorDataset(
        torch.FloatTensor(X_test), torch.LongTensor(y_test)
    )
    
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32, shuffle=False)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    # 创建模型
    input_dim = X.shape[2]
    print(f"输入特征维度: {input_dim}")
    
    model = TradingTransformer(
        input_dim=input_dim,
        d_model=64,      # 减少模型复杂度
        nhead=4,         # 减少注意力头数
        num_layers=3,    # 减少层数
        num_classes=3,
        dropout=0.2      # 增加dropout防止过拟合
    )
    
    print(f"模型参数数量: {sum(p.numel() for p in model.parameters()):,}")
    
    # 训练模型
    trainer = TradingModelTrainer(model)
    print("\n开始训练...")
    best_acc = trainer.train(train_loader, val_loader, epochs=100, patience=15)
    
    # 测试模型
    print("\n最终测试...")
    test_loss, test_acc, test_class_acc = trainer.validate(test_loader)
    print(f"测试准确率: {test_acc:.4f}")
    print(f"分类别测试准确率 - 看跌: {test_class_acc[0]:.3f}, 震荡: {test_class_acc[1]:.3f}, 看涨: {test_class_acc[2]:.3f}")
    
    # 保存处理器
    import joblib
    joblib.dump(processor, 'trading_data_processor.pkl')
    print("数据处理器已保存到 trading_data_processor.pkl")
    
    print("\n🎉 训练完成！")
    print("📁 模型文件: best_trading_model.pth")
    print("📁 处理器文件: trading_data_processor.pkl")

if __name__ == "__main__":
    main() 