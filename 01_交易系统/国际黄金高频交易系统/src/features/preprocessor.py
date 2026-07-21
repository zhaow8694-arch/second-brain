import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA
import joblib
import os

class FeaturePreprocessor:
    def __init__(self, 
                 scaler_type: str = 'standard',
                 pca_components: Optional[int] = None):
        """
        初始化特征预处理器
        
        Args:
            scaler_type: 标准化方法 ('standard', 'minmax', 'robust')
            pca_components: PCA降维的目标维度，None表示不使用PCA
        """
        self.scaler_type = scaler_type
        self.pca_components = pca_components
        self.scaler = None
        self.pca = None
        self.feature_columns = None
        
    def fit(self, df: pd.DataFrame, feature_columns: List[str]) -> None:
        """训练预处理器"""
        self.feature_columns = feature_columns
        
        # 创建标准化器
        if self.scaler_type == 'standard':
            self.scaler = StandardScaler()
        elif self.scaler_type == 'minmax':
            self.scaler = MinMaxScaler()
        elif self.scaler_type == 'robust':
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown scaler type: {self.scaler_type}")
            
        # 训练标准化器
        self.scaler.fit(df[feature_columns])
        
        # 如果需要PCA，训练PCA
        if self.pca_components is not None:
            scaled_data = self.scaler.transform(df[feature_columns])
            self.pca = PCA(n_components=self.pca_components)
            self.pca.fit(scaled_data)
            
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """转换特征"""
        if self.scaler is None:
            raise ValueError("Preprocessor not fitted yet")
            
        # 标准化
        scaled_data = self.scaler.transform(df[self.feature_columns])
        
        # PCA降维（如果需要）
        if self.pca is not None:
            return self.pca.transform(scaled_data)
        
        return scaled_data
        
    def fit_transform(self, df: pd.DataFrame,
                     feature_columns: List[str]) -> np.ndarray:
        """训练并转换特征"""
        self.fit(df, feature_columns)
        return self.transform(df)
        
    def inverse_transform(self, data: np.ndarray) -> pd.DataFrame:
        """反向转换特征"""
        if self.scaler is None:
            raise ValueError("Preprocessor not fitted yet")
            
        # 如果使用了PCA，先反向转换PCA
        if self.pca is not None:
            data = self.pca.inverse_transform(data)
            
        # 反向标准化
        original_data = self.scaler.inverse_transform(data)
        
        return pd.DataFrame(original_data, columns=self.feature_columns)
        
    def save(self, directory: str) -> None:
        """保存预处理器到文件"""
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        # 保存标准化器
        scaler_path = os.path.join(directory, 'scaler.joblib')
        joblib.dump(self.scaler, scaler_path)
        
        # 保存PCA（如果存在）
        if self.pca is not None:
            pca_path = os.path.join(directory, 'pca.joblib')
            joblib.dump(self.pca, pca_path)
            
        # 保存特征列名
        columns_path = os.path.join(directory, 'feature_columns.joblib')
        joblib.dump(self.feature_columns, columns_path)
        
    @classmethod
    def load(cls, directory: str) -> 'FeaturePreprocessor':
        """从文件加载预处理器"""
        # 加载标准化器
        scaler_path = os.path.join(directory, 'scaler.joblib')
        scaler = joblib.load(scaler_path)
        
        # 确定标准化器类型
        if isinstance(scaler, StandardScaler):
            scaler_type = 'standard'
        elif isinstance(scaler, MinMaxScaler):
            scaler_type = 'minmax'
        elif isinstance(scaler, RobustScaler):
            scaler_type = 'robust'
        else:
            raise ValueError("Unknown scaler type")
            
        # 检查是否存在PCA
        pca_path = os.path.join(directory, 'pca.joblib')
        pca_components = None
        if os.path.exists(pca_path):
            pca = joblib.load(pca_path)
            pca_components = pca.n_components_
            
        # 创建预处理器实例
        preprocessor = cls(scaler_type=scaler_type,
                         pca_components=pca_components)
        preprocessor.scaler = scaler
        if pca_components is not None:
            preprocessor.pca = pca
            
        # 加载特征列名
        columns_path = os.path.join(directory, 'feature_columns.joblib')
        preprocessor.feature_columns = joblib.load(columns_path)
        
        return preprocessor
        
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """获取特征重要性（仅当使用PCA时）"""
        if self.pca is None:
            return None
            
        # 计算每个原始特征对主成分的贡献
        feature_importance = {}
        for i, feature in enumerate(self.feature_columns):
            # 使用特征向量的绝对值之和作为重要性度量
            importance = np.abs(self.pca.components_[:, i]).sum()
            feature_importance[feature] = importance
            
        # 归一化重要性分数
        total_importance = sum(feature_importance.values())
        feature_importance = {
            k: v / total_importance
            for k, v in feature_importance.items()
        }
        
        return dict(sorted(feature_importance.items(),
                         key=lambda x: x[1],
                         reverse=True)) 