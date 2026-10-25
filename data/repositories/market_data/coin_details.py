"""
币种详情仓储实现
从data/orm_services中抽象出币种详情相关的数据访问逻辑
"""

from typing import Any, Dict, List, Optional
from .base_repository import CoinDetailsRepositoryInterface
from utils.core.logger_manager import get_logger


class CoinDetailsRepository(CoinDetailsRepositoryInterface):
    """币种详情仓储实现"""
    
    def __init__(self):
        """初始化仓储"""
        self.logger = get_logger("repositories.coin_details")
        # 延迟导入，避免循环依赖
        self._coin_details_service = None
    
    @property
    def coin_details_service(self):
        """获取币种详情服务"""
        if self._coin_details_service is None:
            from data.orm_services import get_crypto_technical_analysis_service
            self._coin_details_service = get_crypto_technical_analysis_service()
        return self._coin_details_service
    
    def get_coin_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取币种详情"""
        try:
            # 从数据库获取币种详情
            details = self.coin_details_service.get_coin_details(symbol)
            return details
        except Exception as e:
            self.logger.error(f"获取{symbol}币种详情失败: {e}")
            return None
    
    def save_coin_details(self, symbol: str, details: Dict[str, Any]) -> bool:
        """保存币种详情"""
        try:
            # 通过服务层保存币种详情
            success = self.coin_details_service.save_coin_details(symbol, details)
            return success
        except Exception as e:
            self.logger.error(f"保存{symbol}币种详情失败: {e}")
            return False
    
    def get_coin_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取币种分析"""
        try:
            # 从数据库获取币种分析数据
            analysis = self.coin_details_service.get_coin_analysis(symbol)
            return analysis
        except Exception as e:
            self.logger.error(f"获取{symbol}币种分析失败: {e}")
            return None
    
    def save_coin_analysis(self, symbol: str, analysis: Dict[str, Any]) -> bool:
        """保存币种分析"""
        try:
            # 通过服务层保存币种分析
            success = self.coin_details_service.save_coin_analysis(symbol, analysis)
            return success
        except Exception as e:
            self.logger.error(f"保存{symbol}币种分析失败: {e}")
            return False
    
    def get_all_coin_details(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有币种详情"""
        try:
            # 从数据库获取所有币种详情
            all_details = self.coin_details_service.get_all_coin_details(limit=limit)
            return all_details
        except Exception as e:
            self.logger.error(f"获取所有币种详情失败: {e}")
            return []
    
    def delete_coin_details(self, symbol: str) -> bool:
        """删除币种详情"""
        try:
            # 通过服务层删除币种详情
            success = self.coin_details_service.delete_coin_details(symbol)
            return success
        except Exception as e:
            self.logger.error(f"删除{symbol}币种详情失败: {e}")
            return False
    
    def update_coin_details(self, symbol: str, updates: Dict[str, Any]) -> bool:
        """更新币种详情"""
        try:
            # 通过服务层更新币种详情
            success = self.coin_details_service.update_coin_details(symbol, updates)
            return success
        except Exception as e:
            self.logger.error(f"更新{symbol}币种详情失败: {e}")
            return False
    
    def get_coin_details_by_rank(self, rank: int) -> Optional[Dict[str, Any]]:
        """根据排名获取币种详情"""
        try:
            # 从数据库根据排名获取币种详情
            details = self.coin_details_service.get_coin_details_by_rank(rank)
            return details
        except Exception as e:
            self.logger.error(f"根据排名{rank}获取币种详情失败: {e}")
            return None
    
    def search_coin_details(self, query: str) -> List[Dict[str, Any]]:
        """搜索币种详情"""
        try:
            # 从数据库搜索币种详情
            results = self.coin_details_service.search_coin_details(query)
            return results
        except Exception as e:
            self.logger.error(f"搜索币种详情失败: {e}")
            return []
