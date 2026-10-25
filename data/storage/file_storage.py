"""
文件存储模块
提供基于文件的数据存储功能
"""

import pandas as pd
import json
import pickle
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import os
from utils.core.logger_manager import get_logger
from data.models.strategy.trade_records_model import TradeRecordModel


class FileStorage:
    """文件存储管理器"""
    
    def __init__(self, base_path: str = "data_files"):
        """
        初始化文件存储
        
        Args:
            base_path: 基础存储路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.base_path / "market_data").mkdir(exist_ok=True)
        (self.base_path / "trade_records").mkdir(exist_ok=True)
        (self.base_path / "metadata").mkdir(exist_ok=True)
        
        self.logger = get_logger('file_storage')
    
    def save_market_data_csv(self, data: pd.DataFrame, symbol: str, 
                            timeframe: str = "1m") -> bool:
        """
        保存市场数据为CSV文件
        
        Args:
            data: 市场数据DataFrame
            symbol: 交易对
            timeframe: 时间周期
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 清理symbol名称，用于文件名
            safe_symbol = symbol.replace('/', '_')
            filename = f"{safe_symbol}_{timeframe}.csv"
            filepath = self.base_path / "market_data" / filename
            
            # 保存数据
            data.to_csv(filepath)
            
            # 保存元数据
            metadata = {
                'symbol': symbol,
                'timeframe': timeframe,
                'data_points': len(data),
                'start_time': data.index[0].isoformat() if not data.empty else None,
                'end_time': data.index[-1].isoformat() if not data.empty else None,
                'created_at': datetime.now().isoformat(),
                'file_size': filepath.stat().st_size if filepath.exists() else 0
            }
            
            metadata_file = self.base_path / "metadata" / f"{safe_symbol}_{timeframe}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"保存市场数据CSV: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存市场数据CSV失败: {e}")
            return False
    
    def load_market_data_csv(self, symbol: str, timeframe: str = "1m") -> pd.DataFrame:
        """
        从CSV文件加载市场数据
        
        Args:
            symbol: 交易对
            timeframe: 时间周期
            
        Returns:
            pd.DataFrame: 市场数据
        """
        try:
            safe_symbol = symbol.replace('/', '_')
            filename = f"{safe_symbol}_{timeframe}.csv"
            filepath = self.base_path / "market_data" / filename
            
            if not filepath.exists():
                self.logger.warning(f"文件不存在: {filepath}")
                return pd.DataFrame()
            
            # 加载数据
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            self.logger.info(f"加载市场数据CSV: {filepath} {len(df)} 条")
            return df
            
        except Exception as e:
            self.logger.error(f"加载市场数据CSV失败: {e}")
            return pd.DataFrame()
    
    def save_market_data_pickle(self, data: pd.DataFrame, symbol: str, 
                               timeframe: str = "1m") -> bool:
        """
        保存市场数据为Pickle文件
        
        Args:
            data: 市场数据DataFrame
            symbol: 交易对
            timeframe: 时间周期
            
        Returns:
            bool: 是否保存成功
        """
        try:
            safe_symbol = symbol.replace('/', '_')
            filename = f"{safe_symbol}_{timeframe}.pkl"
            filepath = self.base_path / "market_data" / filename
            
            # 保存数据
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            # 保存元数据
            metadata = {
                'symbol': symbol,
                'timeframe': timeframe,
                'data_points': len(data),
                'start_time': data.index[0].isoformat() if not data.empty else None,
                'end_time': data.index[-1].isoformat() if not data.empty else None,
                'created_at': datetime.now().isoformat(),
                'file_size': filepath.stat().st_size if filepath.exists() else 0
            }
            
            metadata_file = self.base_path / "metadata" / f"{safe_symbol}_{timeframe}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"保存市场数据Pickle: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存市场数据Pickle失败: {e}")
            return False
    
    def load_market_data_pickle(self, symbol: str, timeframe: str = "1m") -> pd.DataFrame:
        """
        从Pickle文件加载市场数据
        
        Args:
            symbol: 交易对
            timeframe: 时间周期
            
        Returns:
            pd.DataFrame: 市场数据
        """
        try:
            safe_symbol = symbol.replace('/', '_')
            filename = f"{safe_symbol}_{timeframe}.pkl"
            filepath = self.base_path / "market_data" / filename
            
            if not filepath.exists():
                self.logger.warning(f"文件不存在: {filepath}")
                return pd.DataFrame()
            
            # 加载数据
            with open(filepath, 'rb') as f:
                df = pickle.load(f)
            
            self.logger.info(f"加载市场数据Pickle: {filepath} {len(df)} 条")
            return df
            
        except Exception as e:
            self.logger.error(f"加载市场数据Pickle失败: {e}")
            return pd.DataFrame()
    
    def save_trade_records_json(self, trades: List[TradeRecordModel], 
                               filename: Optional[str] = None) -> bool:
        """
        保存交易记录为JSON文件
        
        Args:
            trades: 交易记录列表
            filename: 文件名
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if filename is None:
                timestr = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"trade_records_{timestr}.json"
            
            filepath = self.base_path / "trade_records" / filename
            
            # 转换为字典列表
            trade_dicts = [trade.to_dict() for trade in trades]
            
            # 保存数据
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trade_dicts, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"保存交易记录JSON: {filepath} {len(trades)} 条")
            return True
            
        except Exception as e:
            self.logger.error(f"保存交易记录JSON失败: {e}")
            return False
    
    def load_trade_records_json(self, filename: str) -> List[TradeRecordModel]:
        """
        从JSON文件加载交易记录
        
        Args:
            filename: 文件名
            
        Returns:
            List[TradeRecordModel]: 交易记录列表
        """
        try:
            filepath = self.base_path / "trade_records" / filename
            
            if not filepath.exists():
                self.logger.warning(f"文件不存在: {filepath}")
                return []
            
            # 加载数据
            with open(filepath, 'r', encoding='utf-8') as f:
                trade_dicts = json.load(f)
            
            # 转换为TradeRecordModel对象
            trades = []
            for trade_dict in trade_dicts:
                # 处理时间戳
                if 'datetime' in trade_dict:
                    trade_dict['datetime'] = datetime.fromisoformat(trade_dict['datetime'])
                
                trade = TradeRecordModel.from_dict(trade_dict)
                trades.append(trade)
            
            self.logger.info(f"加载交易记录JSON: {filepath} {len(trades)} 条")
            return trades
            
        except Exception as e:
            self.logger.error(f"加载交易记录JSON失败: {e}")
            return []
    
    def save_trade_records_pickle(self, trades: List[TradeRecordModel], 
                                 filename: Optional[str] = None) -> bool:
        """
        保存交易记录为Pickle文件
        
        Args:
            trades: 交易记录列表
            filename: 文件名
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if filename is None:
                timestr = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"trade_records_{timestr}.pkl"
            
            filepath = self.base_path / "trade_records" / filename
            
            # 保存数据
            with open(filepath, 'wb') as f:
                pickle.dump(trades, f)
            
            self.logger.info(f"保存交易记录Pickle: {filepath} {len(trades)} 条")
            return True
            
        except Exception as e:
            self.logger.error(f"保存交易记录Pickle失败: {e}")
            return False
    
    def load_trade_records_pickle(self, filename: str) -> List[TradeRecordModel]:
        """
        从Pickle文件加载交易记录
        
        Args:
            filename: 文件名
            
        Returns:
            List[TradeRecordModel]: 交易记录列表
        """
        try:
            filepath = self.base_path / "trade_records" / filename
            
            if not filepath.exists():
                self.logger.warning(f"文件不存在: {filepath}")
                return []
            
            # 加载数据
            with open(filepath, 'rb') as f:
                trades = pickle.load(f)
            
            self.logger.info(f"加载交易记录Pickle: {filepath} {len(trades)} 条")
            return trades
            
        except Exception as e:
            self.logger.error(f"加载交易记录Pickle失败: {e}")
            return []
    
    def get_available_files(self) -> Dict[str, List[str]]:
        """获取可用的文件列表"""
        try:
            files = {
                'market_data': [],
                'trade_records': [],
                'metadata': []
            }
            
            # 扫描市场数据文件
            market_data_path = self.base_path / "market_data"
            if market_data_path.exists():
                for file in market_data_path.iterdir():
                    if file.is_file():
                        files['market_data'].append(file.name)
            
            # 扫描交易记录文件
            trade_records_path = self.base_path / "trade_records"
            if trade_records_path.exists():
                for file in trade_records_path.iterdir():
                    if file.is_file():
                        files['trade_records'].append(file.name)
            
            # 扫描元数据文件
            metadata_path = self.base_path / "metadata"
            if metadata_path.exists():
                for file in metadata_path.iterdir():
                    if file.is_file():
                        files['metadata'].append(file.name)
            
            return files
            
        except Exception as e:
            self.logger.error(f"获取文件列表失败: {e}")
            return {}
    
    def delete_file(self, file_type: str, filename: str) -> bool:
        """
        删除文件
        
        Args:
            file_type: 文件类型 ('market_data', 'trade_records', 'metadata')
            filename: 文件名
            
        Returns:
            bool: 是否删除成功
        """
        try:
            filepath = self.base_path / file_type / filename
            
            if filepath.exists():
                filepath.unlink()
                self.logger.info(f"删除文件: {filepath}")
                return True
            else:
                self.logger.warning(f"文件不存在: {filepath}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除文件失败: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        try:
            info = {
                'base_path': str(self.base_path),
                'total_size': 0,
                'file_counts': {},
                'available_space': 0
            }
            
            # 计算总大小和文件数量
            for subdir in ['market_data', 'trade_records', 'metadata']:
                subdir_path = self.base_path / subdir
                if subdir_path.exists():
                    total_size = sum(f.stat().st_size for f in subdir_path.rglob('*') if f.is_file())
                    file_count = len(list(subdir_path.rglob('*')))
                    
                    info['total_size'] += total_size
                    info['file_counts'][subdir] = file_count
            
            # 获取可用空间
            try:
                stat = os.statvfs(self.base_path)
                info['available_space'] = stat.f_frsize * stat.f_bavail
            except:
                info['available_space'] = 0
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取存储信息失败: {e}")
            return {} 