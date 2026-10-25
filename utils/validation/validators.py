"""
验证器模块
提供数据、策略和风险的验证功能
"""

import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from ..core.logger_manager import get_logger


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.logger = get_logger('utils.validator.data')
    
    def validate_ohlcv_data(self, data: pd.DataFrame) -> ValidationResult:
        """
        验证OHLCV数据
        
        Args:
            data: OHLCV数据DataFrame
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            # 检查必需列
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                errors.append(f"缺少必需列: {missing_columns}")
            
            # 检查数据类型
            if not data.empty:
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in data.columns:
                        if not pd.api.types.is_numeric_dtype(data[col]):
                            errors.append(f"列 {col} 不是数值类型")
                
                # 检查OHLC逻辑关系
                if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
                    invalid_high = data['high'] < data[['open', 'close']].max(axis=1)
                    invalid_low = data['low'] > data[['open', 'close']].min(axis=1)
                    
                    if invalid_high.any():
                        errors.append("存在high值小于open或close的情况")
                    if invalid_low.any():
                        errors.append("存在low值大于open或close的情况")
                
                # 检查缺失值
                missing_count = data.isnull().sum()
                if missing_count.any():
                    warnings.append(f"存在缺失值: {missing_count.to_dict()}")
                
                # 检查异常值
                for col in ['open', 'high', 'low', 'close']:
                    if col in data.columns:
                        # 检查负值
                        negative_count = (data[col] < 0).sum()
                        if negative_count > 0:
                            errors.append(f"列 {col} 存在 {negative_count} 个负值")
                        
                        # 检查零值
                        zero_count = (data[col] == 0).sum()
                        if zero_count > 0:
                            warnings.append(f"列 {col} 存在 {zero_count} 个零值")
                
                # 检查时间序列连续性
                if 'datetime' in data.columns or data.index.name == 'datetime':
                    time_index = data.index if data.index.name == 'datetime' else data['datetime']
                    if len(time_index) > 1:
                        time_diff = pd.Series(time_index).diff().dropna()
                        if time_diff.std() > time_diff.mean() * 2:
                            warnings.append("时间序列可能存在不连续性")
            
            details['row_count'] = len(data)
            details['column_count'] = len(data.columns)
            details['missing_values'] = data.isnull().sum().to_dict() if not data.empty else {}
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def validate_trade_data(self, trades: List[Dict[str, Any]]) -> ValidationResult:
        """
        验证交易数据
        
        Args:
            trades: 交易记录列表
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            if not trades:
                warnings.append("交易记录为空")
                return ValidationResult(True, errors, warnings, details)
            
            required_fields = ['entry_time', 'exit_time', 'entry_price', 'exit_price', 'quantity', 'pnl']
            
            for i, trade in enumerate(trades):
                # 检查必需字段
                missing_fields = [field for field in required_fields if field not in trade]
                if missing_fields:
                    errors.append(f"交易 {i} 缺少必需字段: {missing_fields}")
                
                # 检查数据类型和逻辑
                if 'entry_time' in trade and 'exit_time' in trade:
                    if trade['entry_time'] >= trade['exit_time']:
                        errors.append(f"交易 {i} 入场时间晚于或等于出场时间")
                
                if 'entry_price' in trade and 'exit_price' in trade:
                    if trade['entry_price'] <= 0 or trade['exit_price'] <= 0:
                        errors.append(f"交易 {i} 价格必须大于0")
                
                if 'quantity' in trade:
                    if trade['quantity'] <= 0:
                        errors.append(f"交易 {i} 数量必须大于0")
                
                if 'pnl' in trade:
                    # PnL可以是负数，但应该合理
                    if abs(trade['pnl']) > 1000000:  # 假设最大PnL为100万
                        warnings.append(f"交易 {i} PnL值异常: {trade['pnl']}")
            
            details['total_trades'] = len(trades)
            details['winning_trades'] = sum(1 for t in trades if t.get('pnl', 0) > 0)
            details['losing_trades'] = sum(1 for t in trades if t.get('pnl', 0) < 0)
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)


class StrategyValidator:
    """策略验证器"""
    
    def __init__(self):
        self.logger = get_logger('utils.validator.strategy')
    
    def validate_strategy_parameters(self, strategy_name: str, 
                                   parameters: Dict[str, Any]) -> ValidationResult:
        """
        验证策略参数
        
        Args:
            strategy_name: 策略名称
            parameters: 策略参数
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            # 通用参数验证
            if 'position_size' in parameters:
                pos_size = parameters['position_size']
                if not (0 < pos_size <= 1):
                    errors.append("仓位大小必须在0-1之间")
            
            # 策略特定验证
            if strategy_name.lower() == 'ma':
                if 'ma_period' in parameters:
                    ma_period = parameters['ma_period']
                    if not isinstance(ma_period, int) or ma_period <= 0:
                        errors.append("MA周期必须是正整数")
                    if ma_period > 1000:
                        warnings.append("MA周期过大，可能影响性能")
            
            elif strategy_name.lower() == 'rsi':
                if 'rsi_period' in parameters:
                    rsi_period = parameters['rsi_period']
                    if not isinstance(rsi_period, int) or rsi_period <= 0:
                        errors.append("RSI周期必须是正整数")
                if 'rsi_overbought' in parameters:
                    overbought = parameters['rsi_overbought']
                    if not (50 <= overbought <= 100):
                        errors.append("RSI超买值必须在50-100之间")
                if 'rsi_oversold' in parameters:
                    oversold = parameters['rsi_oversold']
                    if not (0 <= oversold <= 50):
                        errors.append("RSI超卖值必须在0-50之间")
            
            elif strategy_name.lower() == 'bollinger':
                if 'bb_period' in parameters:
                    bb_period = parameters['bb_period']
                    if not isinstance(bb_period, int) or bb_period <= 0:
                        errors.append("布林带周期必须是正整数")
                if 'bb_std' in parameters:
                    bb_std = parameters['bb_std']
                    if not (0 < bb_std <= 5):
                        errors.append("布林带标准差必须在0-5之间")
            
            details['strategy_name'] = strategy_name
            details['parameter_count'] = len(parameters)
            details['parameters'] = parameters
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def validate_signal(self, signal: Dict[str, Any]) -> ValidationResult:
        """
        验证交易信号
        
        Args:
            signal: 交易信号
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            required_fields = ['action', 'datetime']
            missing_fields = [field for field in required_fields if field not in signal]
            if missing_fields:
                errors.append(f"信号缺少必需字段: {missing_fields}")
            
            # 验证action
            if 'action' in signal:
                action = signal['action']
                valid_actions = ['buy', 'sell', 'hold']
                if action not in valid_actions:
                    errors.append(f"无效的action值: {action}")
            
            # 验证datetime
            if 'datetime' in signal:
                dt = signal['datetime']
                if not isinstance(dt, (datetime, str)):
                    errors.append("datetime必须是datetime对象或字符串")
            
            # 验证confidence
            if 'confidence' in signal:
                confidence = signal['confidence']
                if not (0 <= confidence <= 1):
                    errors.append("confidence必须在0-1之间")
            
            details['signal_type'] = getattr(signal, 'action', 'unknown')
            details['has_confidence'] = 'confidence' in signal
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)


class RiskValidator:
    """风险验证器"""
    
    def __init__(self):
        self.logger = get_logger('utils.validator.risk')
    
    def validate_risk_limits(self, current_position: float, 
                            new_position: float,
                            account_value: float,
                            risk_config: Dict[str, Any]) -> ValidationResult:
        """
        验证风险限制
        
        Args:
            current_position: 当前仓位
            new_position: 新仓位
            account_value: 账户价值
            risk_config: 风险配置
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            # 检查最大仓位限制
            max_position_size = risk_config.get('max_position_size', 0.1)
            position_ratio = abs(new_position) / account_value if account_value > 0 else 0
            
            if position_ratio > max_position_size:
                errors.append(f"仓位比例 {position_ratio:.2%} 超过最大限制 {max_position_size:.2%}")
            
            # 检查最大回撤限制
            max_drawdown = risk_config.get('max_drawdown', 0.2)
            # 这里需要根据实际回撤计算逻辑来实现
            
            # 检查每日交易次数限制
            max_trades_per_day = risk_config.get('max_trades_per_day', 10)
            # 这里需要根据实际交易记录来实现
            
            details['position_ratio'] = position_ratio
            details['max_position_size'] = max_position_size
            details['account_value'] = account_value
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def validate_stop_loss(self, entry_price: float, 
                          current_price: float,
                          stop_loss_pct: float) -> ValidationResult:
        """
        验证止损条件
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            stop_loss_pct: 止损百分比
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            if entry_price <= 0 or current_price <= 0:
                errors.append("价格必须大于0")
            
            if stop_loss_pct <= 0 or stop_loss_pct > 1:
                errors.append("止损百分比必须在0-1之间")
            
            # 计算止损价格
            stop_loss_price = entry_price * (1 - stop_loss_pct)
            
            # 检查是否触发止损
            if current_price <= stop_loss_price:
                warnings.append("当前价格已触发止损条件")
            
            details['entry_price'] = entry_price
            details['current_price'] = current_price
            details['stop_loss_price'] = stop_loss_price
            details['price_change_pct'] = (current_price - entry_price) / entry_price
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def validate_take_profit(self, entry_price: float,
                            current_price: float,
                            take_profit_pct: float) -> ValidationResult:
        """
        验证止盈条件
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            take_profit_pct: 止盈百分比
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            if entry_price <= 0 or current_price <= 0:
                errors.append("价格必须大于0")
            
            if take_profit_pct <= 0 or take_profit_pct > 1:
                errors.append("止盈百分比必须在0-1之间")
            
            # 计算止盈价格
            take_profit_price = entry_price * (1 + take_profit_pct)
            
            # 检查是否触发止盈
            if current_price >= take_profit_price:
                warnings.append("当前价格已触发止盈条件")
            
            details['entry_price'] = entry_price
            details['current_price'] = current_price
            details['take_profit_price'] = take_profit_price
            details['price_change_pct'] = (current_price - entry_price) / entry_price
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details) 


# 基础验证函数
def validate_symbol(symbol: str) -> bool:
    """
    验证交易对格式
    
    Args:
        symbol: 交易对，如 'BTC/USDT'
        
    Returns:
        bool: 是否有效
    """
    if not isinstance(symbol, str):
        return False
    
    # 检查格式：BASE/QUOTE
    if '/' not in symbol:
        return False
    
    base, quote = symbol.split('/', 1)
    
    # 检查基础货币和报价货币
    if not base or not quote:
        return False
    
    # 检查长度（通常3-10个字符）
    if len(base) < 1 or len(base) > 10 or len(quote) < 1 or len(quote) > 10:
        return False
    
    # 检查字符（只允许字母和数字）
    if not base.isalnum() or not quote.isalnum():
        return False
    
    return True


def validate_timeframe(timeframe: str) -> bool:
    """
    验证时间周期格式
    
    Args:
        timeframe: 时间周期，如 '1m', '5m', '1h', '1d'
        
    Returns:
        bool: 是否有效
    """
    if not isinstance(timeframe, str):
        return False
    
    # 支持的时间周期
    valid_timeframes = [
        '1m', '3m', '5m', '15m', '30m',  # 分钟
        '1h', '2h', '4h', '6h', '8h', '12h',  # 小时
        '1d', '3d', '1w', '1M'  # 天、周、月
    ]
    
    return timeframe in valid_timeframes


def validate_amount(amount: float, min_amount: float = 0.0, max_amount: float = float('inf')) -> bool:
    """
    验证数量
    
    Args:
        amount: 数量
        min_amount: 最小数量
        max_amount: 最大数量
        
    Returns:
        bool: 是否有效
    """
    if not isinstance(amount, (int, float)):
        return False
    
    if amount < min_amount:
        return False
    
    if amount > max_amount:
        return False
    
    return True


# 通用验证工具
class UniversalValidator:
    """通用验证器"""
    
    def __init__(self):
        self.logger = get_logger('utils.validator.universal')
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_phone(self, phone: str) -> bool:
        """验证手机号格式（中国）"""
        import re
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    def validate_url(self, url: str) -> bool:
        """验证URL格式"""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    def validate_json(self, json_str: str) -> bool:
        """验证JSON格式"""
        import json
        try:
            json.loads(json_str)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def validate_date_range(self, start_date: datetime, end_date: datetime) -> bool:
        """验证日期范围"""
        return start_date <= end_date
    
    def validate_file_exists(self, file_path: str) -> bool:
        """验证文件是否存在"""
        import os
        return os.path.exists(file_path)
    
    def validate_directory_writable(self, dir_path: str) -> bool:
        """验证目录是否可写"""
        import os
        return os.path.exists(dir_path) and os.access(dir_path, os.W_OK)


# 数据质量检查器
class DataQualityChecker:
    """数据质量检查器"""
    
    def __init__(self):
        self.logger = get_logger('utils.validator.quality')
    
    def check_missing_values(self, data: pd.DataFrame, threshold: float = 0.1) -> Dict[str, Any]:
        """
        检查缺失值
        
        Args:
            data: 数据框
            threshold: 缺失值比例阈值
            
        Returns:
            Dict: 检查结果
        """
        missing_stats = data.isnull().sum()
        missing_ratio = missing_stats / len(data)
        
        high_missing = missing_ratio[missing_ratio > threshold]
        
        return {
            'total_missing': missing_stats.sum(),
            'missing_ratio': missing_ratio.to_dict(),
            'high_missing_columns': high_missing.to_dict(),
            'is_quality_good': len(high_missing) == 0
        }
    
    def check_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        检查重复数据
        
        Args:
            data: 数据框
            
        Returns:
            Dict: 检查结果
        """
        duplicate_count = data.duplicated().sum()
        duplicate_ratio = duplicate_count / len(data)
        
        return {
            'duplicate_count': duplicate_count,
            'duplicate_ratio': duplicate_ratio,
            'is_quality_good': duplicate_ratio < 0.05  # 5%阈值
        }
    
    def check_outliers(self, data: pd.DataFrame, columns: List[str] = None) -> Dict[str, Any]:
        """
        检查异常值（使用IQR方法）
        
        Args:
            data: 数据框
            columns: 要检查的列，None表示所有数值列
            
        Returns:
            Dict: 检查结果
        """
        if columns is None:
            columns = data.select_dtypes(include=['number']).columns.tolist()
        
        outlier_info = {}
        total_outliers = 0
        
        for col in columns:
            if col in data.columns:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)]
                outlier_count = len(outliers)
                total_outliers += outlier_count
                
                outlier_info[col] = {
                    'count': outlier_count,
                    'ratio': outlier_count / len(data),
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                }
        
        return {
            'outlier_info': outlier_info,
            'total_outliers': total_outliers,
            'is_quality_good': total_outliers < len(data) * 0.1  # 10%阈值
        }
    
    def comprehensive_check(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        综合数据质量检查
        
        Args:
            data: 数据框
            
        Returns:
            Dict: 综合检查结果
        """
        missing_result = self.check_missing_values(data)
        duplicate_result = self.check_duplicates(data)
        outlier_result = self.check_outliers(data)
        
        overall_quality = (
            missing_result['is_quality_good'] and
            duplicate_result['is_quality_good'] and
            outlier_result['is_quality_good']
        )
        
        return {
            'overall_quality': overall_quality,
            'missing_values': missing_result,
            'duplicates': duplicate_result,
            'outliers': outlier_result,
            'recommendations': self._generate_recommendations(
                missing_result, duplicate_result, outlier_result
            )
        }
    
    def _generate_recommendations(self, missing_result: Dict, duplicate_result: Dict, outlier_result: Dict) -> List[str]:
        """生成数据质量改进建议"""
        recommendations = []
        
        if not missing_result['is_quality_good']:
            recommendations.append("存在高比例缺失值，建议进行数据清洗或插值处理")
        
        if not duplicate_result['is_quality_good']:
            recommendations.append("存在较多重复数据，建议去重处理")
        
        if not outlier_result['is_quality_good']:
            recommendations.append("存在较多异常值，建议检查数据来源或进行异常值处理")
        
        if not recommendations:
            recommendations.append("数据质量良好，无需特殊处理")
        
        return recommendations


# 导出验证函数
__all__ = [
    'DataValidator', 'StrategyValidator', 'RiskValidator',
    'ValidationResult', 'validate_symbol', 'validate_timeframe', 'validate_amount',
    'UniversalValidator', 'DataQualityChecker'
] 