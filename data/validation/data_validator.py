"""
数据验证和清洗模块
提供数据质量检查、异常值检测和数据清洗功能
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.core.logger_manager import get_logger
from utils.validation.exceptions import DataException


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        """初始化数据验证器"""
        self.logger = get_logger('data_validator')
    
    def validate_ohlcv_data(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
        """
        验证OHLCV数据
        
        Args:
            df: OHLCV数据DataFrame
            symbol: 交易对
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            # 检查DataFrame是否为空
            if df.empty:
                errors.append("数据为空")
                return False, errors
            
            # 检查必需的列
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                errors.append(f"缺少必需的列: {missing_columns}")
            
            # 检查数据类型
            for col in required_columns:
                if col in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        errors.append(f"列 {col} 不是数值类型")
            
            # 检查价格逻辑
            if 'open' in df.columns and 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
                # 检查OHLC逻辑
                invalid_high = df['high'] < df[['open', 'close']].max(axis=1)
                invalid_low = df['low'] > df[['open', 'close']].min(axis=1)
                
                if invalid_high.any():
                    errors.append(f"存在最高价小于开盘价或收盘价的记录: {invalid_high.sum()} 条")
                
                if invalid_low.any():
                    errors.append(f"存在最低价大于开盘价或收盘价的记录: {invalid_low.sum()} 条")
            
            # 检查负值
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    negative_count = (df[col] < 0).sum()
                    if negative_count > 0:
                        errors.append(f"列 {col} 存在负值: {negative_count} 条")
            
            # 检查异常值
            for col in ['open', 'high', 'low', 'close']:
                if col in df.columns:
                    # 使用IQR方法检测异常值
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                    if len(outliers) > 0:
                        errors.append(f"列 {col} 存在异常值: {len(outliers)} 条")
            
            # 检查时间序列连续性
            if not df.index.empty and isinstance(df.index[0], datetime):
                time_diff = df.index.to_series().diff()
                expected_freq = self._detect_expected_frequency(df.index)
                
                if expected_freq:
                    # 检查是否有缺失的时间点
                    expected_times = pd.date_range(
                        start=df.index[0], 
                        end=df.index[-1], 
                        freq=expected_freq
                    )
                    missing_times = expected_times.difference(df.index)
                    if len(missing_times) > 0:
                        errors.append(f"时间序列不连续，缺失 {len(missing_times)} 个时间点")
            
            # 检查重复时间戳
            if df.index.duplicated().any():
                errors.append(f"存在重复的时间戳: {df.index.duplicated().sum()} 条")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {e}")
            return False, errors
    
    def _detect_expected_frequency(self, index: pd.DatetimeIndex) -> Optional[str]:
        """检测预期的时间频率"""
        if len(index) < 2:
            return None
        
        # 计算时间差
        time_diff = index.to_series().diff().dropna()
        
        if time_diff.empty:
            return None
        
        # 获取最常见的时间差
        most_common_diff = time_diff.mode().iloc[0] if not time_diff.mode().empty else time_diff.median()
        
        # 转换为频率字符串
        if most_common_diff <= timedelta(minutes=1):
            return '1min'
        elif most_common_diff <= timedelta(minutes=5):
            return '5min'
        elif most_common_diff <= timedelta(minutes=15):
            return '15min'
        elif most_common_diff <= timedelta(minutes=30):
            return '30min'
        elif most_common_diff <= timedelta(hours=1):
            return '1h'
        elif most_common_diff <= timedelta(hours=4):
            return '4h'
        elif most_common_diff <= timedelta(days=1):
            return '1d'
        else:
            return None
    
    def clean_ohlcv_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        清洗OHLCV数据
        
        Args:
            df: OHLCV数据DataFrame
            symbol: 交易对
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        try:
            if df.empty:
                return df
            
            # 创建副本
            cleaned_df = df.copy()
            
            # 1. 移除重复的时间戳
            cleaned_df = cleaned_df[~cleaned_df.index.duplicated(keep='last')]
            
            # 2. 按时间排序
            cleaned_df = cleaned_df.sort_index()
            
            # 3. 修复OHLC逻辑错误
            if all(col in cleaned_df.columns for col in ['open', 'high', 'low', 'close']):
                # 确保high >= max(open, close)
                cleaned_df['high'] = cleaned_df[['open', 'close']].max(axis=1).combine(
                    cleaned_df['high'], max
                )
                
                # 确保low <= min(open, close)
                cleaned_df['low'] = cleaned_df[['open', 'close']].min(axis=1).combine(
                    cleaned_df['low'], min
                )
            
            # 4. 处理负值
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in cleaned_df.columns:
                    # 将负值替换为前一个有效值
                    cleaned_df[col] = cleaned_df[col].replace([-np.inf, np.inf], np.nan)
                    cleaned_df[col] = cleaned_df[col].fillna(method='ffill')
                    cleaned_df[col] = cleaned_df[col].fillna(method='bfill')
                    
                    # 如果仍有负值，设为0
                    cleaned_df.loc[cleaned_df[col] < 0, col] = 0
            
            # 5. 处理异常值（使用移动平均替换）
            for col in ['open', 'high', 'low', 'close']:
                if col in cleaned_df.columns:
                    # 计算移动平均
                    ma = cleaned_df[col].rolling(window=5, center=True).mean()
                    
                    # 使用IQR方法检测异常值
                    Q1 = cleaned_df[col].quantile(0.25)
                    Q3 = cleaned_df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    # 替换异常值
                    mask = (cleaned_df[col] < lower_bound) | (cleaned_df[col] > upper_bound)
                    cleaned_df.loc[mask, col] = ma[mask]
            
            # 6. 填充缺失值
            cleaned_df = cleaned_df.ffill().bfill()
            
            self.logger.info(f"数据清洗完成: {symbol} {len(df)} -> {len(cleaned_df)} 条记录")
            return cleaned_df
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {e}")
            return df
    
    def validate_trade_record(self, trade_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证交易记录
        
        Args:
            trade_data: 交易记录数据
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            # 检查必需字段
            required_fields = ['symbol', 'side', 'quantity', 'price', 'datetime']
            missing_fields = [field for field in required_fields if field not in trade_data]
            if missing_fields:
                errors.append(f"缺少必需字段: {missing_fields}")
            
            # 检查数据类型和值
            if 'quantity' in trade_data:
                if not isinstance(trade_data['quantity'], (int, float)) or trade_data['quantity'] <= 0:
                    errors.append("数量必须为正数")
            
            if 'price' in trade_data:
                if not isinstance(trade_data['price'], (int, float)) or trade_data['price'] <= 0:
                    errors.append("价格必须为正数")
            
            if 'side' in trade_data:
                if trade_data['side'] not in ['buy', 'sell']:
                    errors.append("交易方向必须是 'buy' 或 'sell'")
            
            if 'symbol' in trade_data:
                if not isinstance(trade_data['symbol'], str) or '/' not in trade_data['symbol']:
                    errors.append("交易对格式无效")
            
            if 'datetime' in trade_data:
                if not isinstance(trade_data['datetime'], datetime):
                    errors.append('datetime字段必须为datetime类型')
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {e}")
            return False, errors
    
    def get_data_quality_report(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        生成数据质量报告
        
        Args:
            df: OHLCV数据DataFrame
            symbol: 交易对
            
        Returns:
            Dict[str, Any]: 数据质量报告
        """
        try:
            report = {
                'symbol': symbol,
                'total_records': len(df),
                'time_range': {
                    'start': df.index[0].isoformat() if not df.empty else None,
                    'end': df.index[-1].isoformat() if not df.empty else None
                },
                'data_completeness': {},
                'data_quality': {},
                'statistics': {}
            }
            
            if df.empty:
                return report
            
            # 数据完整性检查
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    missing_count = df[col].isna().sum()
                    report['data_completeness'][col] = {
                        'missing_count': missing_count,
                        'completeness_rate': (len(df) - missing_count) / len(df) * 100
                    }
            
            # 数据质量检查
            is_valid, errors = self.validate_ohlcv_data(df, symbol)
            report['data_quality']['is_valid'] = is_valid
            report['data_quality']['errors'] = errors
            
            # 统计信息
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    report['statistics'][col] = {
                        'mean': df[col].mean(),
                        'std': df[col].std(),
                        'min': df[col].min(),
                        'max': df[col].max(),
                        'median': df[col].median()
                    }
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成数据质量报告失败: {e}")
            return {'error': str(e)}


# 全局验证器实例
data_validator = DataValidator() 