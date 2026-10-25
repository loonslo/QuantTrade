# -*- coding: utf-8 -*-
"""
美股基本面数据ORM服务
处理美股基本面指标数据的CRUD操作
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import and_, desc

from services.orm.base_orm_service import BaseORMService
from data.models.market_data.us_stocks_fundamental_model import USStockFundamental
from utils.time.timestamp_utils import TimestampConverter


class USStockFundamentalORM(BaseORMService):
    """美股基本面数据ORM服务"""

    def __init__(self):
        super().__init__('us_stock_fundamental_orm', USStockFundamental)

    async def _execute_sync(self):
        """执行同步任务"""
        self.logger.info("美股基本面数据同步任务执行")
        pass

    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置"""
        return {
            "task_name": "us_stock_fundamental_sync",
            "description": "美股基本面数据同步",
            "enabled": True
        }

    def save_fundamental(self, symbol: str, data: Dict[str, Any]) -> bool:
        """
        保存基本面数据
        
        Args:
            symbol: 股票代码
            data: 基本面数据 {
                'pe_ratio': 25.5,
                'pb_ratio': 8.2,
                'ps_ratio': 7.1,
                'roe': 0.25,
                'roa': 0.12,
                'profit_margin': 0.22,
                'revenue_growth': 15.5,
                'earnings_growth': 20.3,
                'dividend_yield': 0.5,
                'market_cap': 2800000000000,
                'price': 175.5,
                'beta': 1.2,
                'source': 'finnhub'
            }
            
        Returns:
            bool: 保存是否成功
        """
        try:
            record_data = {
                "symbol": symbol.upper(),
                "timestamp": TimestampConverter.get_current_datetime_for_db(),
                # 估值
                "pe_ratio": data.get('pe_ratio'),
                "pb_ratio": data.get('pb_ratio'),
                "ps_ratio": data.get('ps_ratio'),
                # 盈利能力
                "roe": data.get('roe'),
                "roa": data.get('roa'),
                "profit_margin": data.get('profit_margin'),
                # 成长性
                "revenue_growth": data.get('revenue_growth'),
                "earnings_growth": data.get('earnings_growth'),
                # 股息
                "dividend_yield": data.get('dividend_yield'),
                # 市值
                "market_cap": data.get('market_cap'),
                "price": data.get('price'),
                "beta": data.get('beta'),
                # 来源
                "source": data.get('source', 'finnhub'),
                "is_valid": True
            }

            result = self.create_model_record(record_data)
            if result:
                self.logger.debug(f"新增 {symbol} 基本面数据")
                return True
            return False

        except Exception as e:
            self.logger.error(f"保存 {symbol} 基本面数据失败: {e}")
            return False

    def get_latest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新的基本面数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            基本面数据字典或None
        """
        try:
            records = self.get_model_records_by_conditions(
                conditions={
                    "symbol": symbol.upper(),
                    "is_valid": True
                },
                limit=1,
                order_by="timestamp"
            )

            if records:
                record = records[0]
                return {
                    "symbol": record.symbol,
                    "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                    "pe_ratio": record.pe_ratio,
                    "pb_ratio": record.pb_ratio,
                    "ps_ratio": record.ps_ratio,
                    "roe": record.roe,
                    "roa": record.roa,
                    "profit_margin": record.profit_margin,
                    "revenue_growth": record.revenue_growth,
                    "earnings_growth": record.earnings_growth,
                    "dividend_yield": record.dividend_yield,
                    "market_cap": record.market_cap,
                    "price": record.price,
                    "beta": record.beta,
                    "source": record.source
                }

            return None

        except Exception as e:
            self.logger.error(f"获取 {symbol} 最新基本面失败: {e}")
            return None

    def get_by_criteria(self, pe_max: float = None, roe_min: float = None, sector: str = None) -> List[Dict[str, Any]]:
        """
        按条件筛选基本面数据
        
        Args:
            pe_max: 市盈率上限
            roe_min: 净资产收益率下限
            sector: 行业（暂不支持精确筛选，仅用于记录）
            
        Returns:
            符合条件的基本面数据列表
        """
        try:
            # 获取所有有效记录
            records = self.get_model_records_by_conditions(
                conditions={"is_valid": True},
                order_by="timestamp",
                limit=10000
            )

            results = []
            for record in records:
                data = {
                    "symbol": record.symbol,
                    "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                    "pe_ratio": record.pe_ratio,
                    "pb_ratio": record.pb_ratio,
                    "ps_ratio": record.ps_ratio,
                    "roe": record.roe,
                    "roa": record.roa,
                    "profit_margin": record.profit_margin,
                    "revenue_growth": record.revenue_growth,
                    "earnings_growth": record.earnings_growth,
                    "dividend_yield": record.dividend_yield,
                    "market_cap": record.market_cap,
                    "price": record.price,
                    "beta": record.beta,
                    "source": record.source
                }

                # 应用筛选条件
                if pe_max is not None and record.pe_ratio is not None and record.pe_ratio > pe_max:
                    continue
                if roe_min is not None and record.roe is not None and record.roe < roe_min:
                    continue
                    
                results.append(data)

            return results

        except Exception as e:
            self.logger.error(f"按条件筛选基本面数据失败: {e}")
            return []

    def save_batch_fundamentals(self, data_list: List[Dict[str, Any]]) -> bool:
        """
        批量保存多只股票的基本面数据

        Args:
            data_list: 基本面数据列表，每项格式同 save_fundamental 的 data 参数
            例如: [
                {'symbol': 'AAPL', 'pe_ratio': 25.5, ...},
                {'symbol': 'MSFT', 'pe_ratio': 30.0, ...},
            ]

        Returns:
            bool: 是否全部保存成功
        """
        try:
            success_count = 0
            fail_count = 0

            for data in data_list:
                symbol = data.get('symbol', 'UNKNOWN')
                try:
                    result = self.save_fundamental(symbol, data)
                    if result:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    self.logger.error(f"批量保存 {symbol} 失败: {e}")
                    fail_count += 1

            self.logger.info(f"批量保存完成: 成功 {success_count}, 失败 {fail_count}")
            return fail_count == 0

        except Exception as e:
            self.logger.error(f"批量保存基本面数据失败: {e}")
            return False

    def get_history(self, symbol: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        获取历史基本面数据

        Args:
            symbol: 股票代码
            limit: 返回条数

        Returns:
            历史基本面数据列表
        """
        try:
            records = self.get_model_records_by_conditions(
                conditions={
                    "symbol": symbol.upper(),
                    "is_valid": True
                },
                order_by="timestamp",
                limit=limit
            )

            results = []
            for record in records:
                results.append({
                    "symbol": record.symbol,
                    "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                    "pe_ratio": record.pe_ratio,
                    "pb_ratio": record.pb_ratio,
                    "ps_ratio": record.ps_ratio,
                    "roe": record.roe,
                    "roa": record.roa,
                    "profit_margin": record.profit_margin,
                    "revenue_growth": record.revenue_growth,
                    "earnings_growth": record.earnings_growth,
                    "dividend_yield": record.dividend_yield,
                    "market_cap": record.market_cap,
                    "price": record.price,
                    "beta": record.beta,
                    "source": record.source
                })

            return results

        except Exception as e:
            self.logger.error(f"获取 {symbol} 历史基本面失败: {e}")
            return []


# 单例模式
_us_stock_fundamental_orm_instance = None


def get_us_stock_fundamental_orm() -> USStockFundamentalORM:
    """获取美股基本面ORM服务单例"""
    global _us_stock_fundamental_orm_instance
    if _us_stock_fundamental_orm_instance is None:
        _us_stock_fundamental_orm_instance = USStockFundamentalORM()
    return _us_stock_fundamental_orm_instance
